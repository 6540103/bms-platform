"""Simulation engine - manages time stepping, current profiles, BMS algorithms, and callbacks."""

import time
import threading
from battery_pack import BatteryPack
from config import SIMULATION_CONFIG, DEFAULT_PROFILE
from bms_algorithms import BMSManager


class SimulationEngine:
    def __init__(self, capacity_ah=None, initial_soc=None, real_time=None):
        self.dt = SIMULATION_CONFIG["time_step"]
        self.real_time = real_time if real_time is not None else SIMULATION_CONFIG["real_time"]
        self.initial_soc = initial_soc or SIMULATION_CONFIG["initial_soc"]

        self.pack = BatteryPack(capacity_ah=capacity_ah, initial_soc=self.initial_soc)
        self.profile = list(DEFAULT_PROFILE)
        self.profile_index = 0
        self.profile_time = 0.0
        self.running = False
        self.paused = False
        self.current_override = None  # If set, overrides profile current
        self._lock = threading.Lock()
        self._callbacks = []

        # BMS Manager - integrates SOC estimation, protection, balancing, SOH
        self.bms = BMSManager(
            num_cells=self.pack.num_cells,
            capacity_ah=self.pack.capacity_ah,
            initial_soc=self.initial_soc,
        )
        # Store last protection result for current limiting on next step
        self._last_protection = None

    def add_callback(self, callback):
        """Add a callback function that receives pack state each step."""
        self._callbacks.append(callback)

    def set_current(self, current):
        """Override current in Amperes. Positive=discharge, negative=charge."""
        with self._lock:
            self.current_override = float(current)

    def set_profile(self, profile):
        """Set a new current profile: list of (current_amps, duration_seconds)."""
        with self._lock:
            self.profile = list(profile)
            self.profile_index = 0
            self.profile_time = 0.0

    def reset(self, initial_soc=None):
        """Reset simulation to initial state."""
        with self._lock:
            self.pack.reset(initial_soc)
            self.profile_index = 0
            self.profile_time = 0.0
            self.current_override = None
            # Reset BMS
            soc = initial_soc or self.initial_soc
            self.bms = BMSManager(
                num_cells=self.pack.num_cells,
                capacity_ah=self.pack.capacity_ah,
                initial_soc=soc,
            )
            self._last_protection = None

    def _get_current(self):
        """Get current for this time step (from override or profile)."""
        with self._lock:
            if self.current_override is not None:
                return self.current_override
            if self.profile_index >= len(self.profile):
                return 0.0  # Profile complete, rest
            current, _ = self.profile[self.profile_index]
            return current

    def _apply_protection_limits(self, current):
        """Apply BMS protection limits to the requested current.

        Returns the actual current that should be applied after protection.
        """
        if self._last_protection is None:
            return current

        p = self._last_protection

        # Hard cutoff: discharge not allowed
        if not p["discharge_allowed"] and current > 0:
            return 0.0

        # Hard cutoff: charge not allowed
        if not p["charge_allowed"] and current < 0:
            return 0.0

        # Current limiting: discharge
        if p["discharge_current_limit"] > 0 and current > p["discharge_current_limit"]:
            return p["discharge_current_limit"]

        # Current limiting: charge
        if p["charge_current_limit"] > 0 and current < -p["charge_current_limit"]:
            return -p["charge_current_limit"]

        return current

    def _advance_profile(self):
        """Advance profile by one time step."""
        with self._lock:
            if self.current_override is not None:
                return
            if self.profile_index >= len(self.profile):
                return

            self.profile_time += self.dt
            _, duration = self.profile[self.profile_index]
            if self.profile_time >= duration:
                self.profile_index += 1
                self.profile_time = 0.0
                if self.profile_index < len(self.profile):
                    next_current, next_dur = self.profile[self.profile_index]
                    mode = (
                        "discharge" if next_current > 0
                        else "charge" if next_current < 0
                        else "rest"
                    )
                    print(
                        f"[Profile] Segment {self.profile_index}: "
                        f"{mode} at {abs(next_current)}A for {next_dur}s"
                    )

    def step(self):
        """Execute one simulation step. Returns pack state dict with BMS status."""
        # 1. Get requested current
        requested_current = self._get_current()

        # 2. Apply BMS protection limits from previous step
        actual_current = self._apply_protection_limits(requested_current)

        # 3. Update battery pack model
        self.pack.update(actual_current, self.dt)

        # 4. Advance current profile
        self._advance_profile()

        # 5. Run BMS algorithms with actual measured values
        cell_voltages = self.pack.get_cell_voltages()
        temperature = self.pack.temperature
        bms_status = self.bms.update(
            current=actual_current,
            cell_voltages=cell_voltages,
            temperature=temperature,
            dt=self.dt,
        )

        # Store protection result for next step's current limiting
        self._last_protection = bms_status["protection"]

        # Update SOH estimator cycle count from pack
        self.bms.soh_estimator.set_cycle_count(self.pack.cycle_count)

        # 6. Build state dict (pack state + BMS overrides)
        state = self.pack.get_state()

        # Override SOC/SOH with BMS estimates
        state["soc"] = round(bms_status["soc"]["ekf"] * 100, 2)
        state["soh"] = round(bms_status["soh"]["combined"], 2)
        state["soc_coulomb"] = round(bms_status["soc"]["coulomb"] * 100, 2)
        state["soc_ocv"] = round(bms_status["soc"]["ocv"] * 100, 2)

        # Add BMS status
        state["bms"] = bms_status
        state["bms_status"] = bms_status["bms_status"]
        state["protection_status"] = bms_status["protection"]["fault_status"]
        state["active_protections"] = bms_status["protection"]["active_protections"]
        state["balancing_active"] = bms_status["balancing"]["active"]
        state["balancing_cells"] = bms_status["balancing"]["cells"]
        state["warnings"] = bms_status["protection"]["warnings"]
        state["alarms"] = bms_status["protection"]["alarms"]

        # Track if current was limited
        if abs(actual_current - requested_current) > 0.01:
            state["current_limited"] = True
            state["requested_current"] = round(requested_current, 2)
        else:
            state["current_limited"] = False

        # 7. Call callbacks with full state
        for callback in self._callbacks:
            try:
                callback(state)
            except Exception as e:
                print(f"[Callback error] {e}")

        return state

    def run(self, max_steps=None):
        """Run simulation loop. Returns final pack state."""
        self.running = True
        step_count = 0
        print(f"[Simulation] Starting. dt={self.dt}s, real_time={self.real_time}")
        print(
            f"[Simulation] Pack: {self.pack.num_cells}S, "
            f"{self.pack.capacity_ah}Ah, SOC={self.pack.soc*100:.1f}%, "
            f"V={self.pack.pack_voltage:.2f}V"
        )
        print("[BMS] Algorithms active: SOC(EKF), Protection, Balancing, SOH")

        try:
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                start_time = time.time()
                state = self.step()
                step_count += 1

                if step_count % 60 == 0:
                    bms = state.get("bms", {})
                    prot = bms.get("protection", {})
                    print(
                        f"[Sim] t={state['sim_time']:.0f}s "
                        f"SOC={state['soc']:.1f}% "
                        f"V={state['pack_voltage']:.2f}V "
                        f"I={state['current']:.1f}A "
                        f"T={state['temperature'][0]:.1f}C "
                        f"BMS={state['bms_status']}"
                        + (f" PROT={','.join(prot.get('active_protections', []))}"
                           if prot.get('active_protections') else "")
                    )

                if max_steps and step_count >= max_steps:
                    print(f"[Simulation] Reached max_steps={max_steps}, stopping")
                    break

                # Real-time pacing
                if self.real_time:
                    elapsed = time.time() - start_time
                    sleep_time = self.dt - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n[Simulation] Interrupted by user")
        finally:
            self.running = False
            print(
                f"[Simulation] Stopped after {step_count} steps "
                f"({step_count * self.dt:.0f}s simulation time)"
            )

        return self.pack.get_state()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
