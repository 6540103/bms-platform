"""SOH (State of Health) Estimator - Capacity fade and internal resistance growth.

Estimates battery health based on:
1. Capacity-based SOH: current full charge capacity / nominal capacity
2. Resistance-based SOH: initial internal resistance / current resistance
3. Cycle counting and aging model
4. Temperature-accelerated aging
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SOHConfig:
    """SOH estimation configuration."""
    nominal_capacity_ah: float = 40.0
    nominal_internal_resistance: float = 0.003  # 3mOhm per cell
    # Aging model parameters (simplified)
    capacity_fade_per_cycle: float = 0.00002    # 0.002% per cycle (typical NMC)
    resistance_growth_per_cycle: float = 0.00004  # 0.004% per cycle
    calendar_aging_per_day: float = 0.00005      # Calendar aging
    temp_aging_factor: float = 0.0002             # Extra aging per degree above 25C
    soh_warning_threshold: float = 80.0
    soh_alarm_threshold: float = 70.0


class SOHEstimator:
    def __init__(self, config=None):
        self.config = config or SOHConfig()
        self.cycle_count = 0
        self.total_charge_throughput_ah = 0.0  # Total Ah charged
        self.total_discharge_throughput_ah = 0.0
        self.calendar_days = 0.0

        # Estimated SOH values
        self.capacity_soh = 100.0   # Capacity-based SOH (%)
        self.resistance_soh = 100.0  # Resistance-based SOH (%)
        self.combined_soh = 100.0    # Combined SOH (%)

        # Estimated current parameters
        self.estimated_capacity_ah = self.config.nominal_capacity_ah
        self.estimated_internal_resistance = self.config.nominal_internal_resistance

        # For capacity measurement (track full charge/discharge)
        self._last_full_charge_soc = None
        self._charge_since_full = 0.0
        self._discharge_since_full = 0.0
        self._measured_capacity = None  # Last measured full capacity

        # Temperature history for aging
        self._avg_temperature = 25.0
        self._temp_samples = 0

    def set_cycle_count(self, count: int):
        """Set cycle count from external source."""
        self.cycle_count = count

    def update(self, current: float, temperature: float, dt: float,
               soc: float, cell_voltages: Optional[List[float]] = None) -> Dict:
        """Update SOH estimate for one time step.

        Args:
            current: Pack current (A), positive=discharge
            temperature: Pack temperature (C)
            dt: Time step (seconds)
            soc: Current SOC (0-100%)
            cell_voltages: Optional list of cell voltages for resistance estimation

        Returns:
            dict with SOH estimates
        """
        cfg = self.config

        # Track charge/discharge throughput
        if current > 0:
            self.total_discharge_throughput_ah += current * dt / 3600.0
        elif current < 0:
            self.total_charge_throughput_ah += abs(current) * dt / 3600.0

        # Calendar aging
        self.calendar_days += dt / 86400.0

        # Temperature averaging for aging calculation
        self._temp_samples += 1
        self._avg_temperature += (temperature - self._avg_temperature) / self._temp_samples

        # --- Capacity-based SOH (aging model) ---
        # Capacity fade = cycles * fade_per_cycle + calendar * fade_per_day + temp effect
        cycle_fade = self.cycle_count * cfg.capacity_fade_per_cycle * 100
        calendar_fade = self.calendar_days * cfg.calendar_aging_per_day * 100
        temp_excess = max(0, self._avg_temperature - 25.0)
        temp_fade = temp_excess * cfg.temp_aging_factor * self.cycle_count * 100

        total_capacity_fade = min(cycle_fade + calendar_fade + temp_fade, 50.0)
        self.capacity_soh = 100.0 - total_capacity_fade
        self.estimated_capacity_ah = cfg.nominal_capacity_ah * (self.capacity_soh / 100.0)

        # --- Resistance-based SOH ---
        resistance_growth = (
            self.cycle_count * cfg.resistance_growth_per_cycle * 100
            + self.calendar_days * cfg.calendar_aging_per_day * 50
        )
        self.resistance_soh = max(100.0 - resistance_growth, 50.0)
        self.estimated_internal_resistance = (
            cfg.nominal_internal_resistance * (100.0 / self.resistance_soh)
        )

        # If we have cell voltages and current, estimate actual resistance
        if cell_voltages and abs(current) > 1.0:
            # Simple DC resistance estimate: dV/dI (simplified)
            # In practice this requires comparing resting voltage to loaded voltage
            avg_v = np.mean(cell_voltages)
            # This is a rough estimate; real implementation needs resting baseline
            estimated_r = abs(avg_v - 3.8 * len(cell_voltages)) / max(abs(current), 1.0)
            if 0.001 < estimated_r < 0.02:
                # Blend with model estimate
                model_r = self.estimated_internal_resistance
                self.estimated_internal_resistance = 0.9 * model_r + 0.1 * estimated_r
                actual_resistance_soh = (
                    cfg.nominal_internal_resistance / self.estimated_internal_resistance * 100
                )
                self.resistance_soh = 0.95 * self.resistance_soh + 0.05 * actual_resistance_soh

        # --- Combined SOH (weighted average) ---
        self.combined_soh = 0.6 * self.capacity_soh + 0.4 * self.resistance_soh

        # --- Health status ---
        if self.combined_soh <= cfg.soh_alarm_threshold:
            health_status = "poor"
        elif self.combined_soh <= cfg.soh_warning_threshold:
            health_status = "warning"
        else:
            health_status = "good"

        return {
            "combined_soh": float(self.combined_soh),
            "capacity_soh": float(self.capacity_soh),
            "resistance_soh": float(self.resistance_soh),
            "estimated_capacity_ah": float(self.estimated_capacity_ah),
            "estimated_internal_resistance_mohm": float(self.estimated_internal_resistance * 1000),
            "cycle_count": int(self.cycle_count),
            "total_charge_throughput_ah": float(self.total_charge_throughput_ah),
            "total_discharge_throughput_ah": float(self.total_discharge_throughput_ah),
            "calendar_days": float(self.calendar_days),
            "health_status": health_status,
        }
