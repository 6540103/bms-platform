"""Battery pack model - 13S series configuration with cell imbalance simulation."""

import time
import numpy as np
from cell import Cell
from config import PACK_CONFIG, THERMAL_CONFIG


class BatteryPack:
    def __init__(self, capacity_ah=None, initial_soc=0.9):
        self.num_cells = PACK_CONFIG["num_cells"]
        self.capacity_ah = capacity_ah or PACK_CONFIG["nominal_capacity_ah"]
        self.initial_soc = initial_soc

        # Create cells with unique seeds for deterministic parameter variation
        self.cells = [
            Cell(
                cell_id=i,
                capacity_ah=self.capacity_ah,
                initial_soc=initial_soc,
                param_seed=i * 100 + 7,
            )
            for i in range(self.num_cells)
        ]

        # Pack-level state
        self.pack_voltage = sum(c.voltage for c in self.cells)
        self.current = 0.0
        self.power = 0.0
        self.soc = min(c.soc for c in self.cells)  # Conservative: use min cell SOC
        self.min_cell_voltage = min(c.voltage for c in self.cells)
        self.max_cell_voltage = max(c.voltage for c in self.cells)
        self.temperature = THERMAL_CONFIG["initial_temp"]
        self.ambient_temp = THERMAL_CONFIG["ambient_temp"]
        self.status = "resting"  # resting / charging / discharging / error
        self.sim_time = 0.0
        self.cycle_count = 0
        self._charge_throughput = 0.0  # For cycle counting

        # Thermal model parameters
        self.r_th = THERMAL_CONFIG["thermal_resistance"]
        self.c_th = THERMAL_CONFIG["thermal_capacity"]

    def update(self, current, dt):
        """Update entire pack for one time step.

        Args:
            current: Current in Amperes (positive=discharge, negative=charge).
            dt: Time step in seconds.

        Returns:
            Pack voltage in Volts.
        """
        self.current = float(current)
        self.sim_time += dt

        # Update all cells (same current flows through series string)
        for cell in self.cells:
            cell.update(current, dt)

        # Pack aggregate calculations
        self.pack_voltage = sum(c.voltage for c in self.cells)
        self.power = self.pack_voltage * current  # Discharge = positive power output
        self.soc = min(c.soc for c in self.cells)  # Conservative SOC estimate

        voltages = [c.voltage for c in self.cells]
        self.min_cell_voltage = min(voltages)
        self.max_cell_voltage = max(voltages)

        # Status determination
        if current > 0.1:
            self.status = "discharging"
        elif current < -0.1:
            self.status = "charging"
        else:
            self.status = "resting"

        # Simplified thermal model:
        # Heat generation = I^2 * R_total (ohmic) + |I * V_p_total| (polarization)
        total_r0 = sum(c.r0 for c in self.cells)
        total_vp = sum(c.v_polarization for c in self.cells)
        heat_gen = current**2 * total_r0 + abs(current * total_vp)

        # Temperature dynamics: dT/dt = (Q_gen - (T-Tamb)/Rth) / Cth
        dT = (heat_gen - (self.temperature - self.ambient_temp) / self.r_th) * dt / self.c_th
        self.temperature = float(np.clip(self.temperature + dT, -20.0, 80.0))

        # Cycle counting (simplified: count full charge throughput)
        self._charge_throughput += abs(current) * dt
        if self._charge_throughput >= self.capacity_ah * 3600.0:
            self.cycle_count += 1
            self._charge_throughput = 0.0

        return self.pack_voltage

    def get_cell_voltages(self):
        return [round(c.voltage, 4) for c in self.cells]

    def get_cell_socs(self):
        return [round(c.soc * 100, 2) for c in self.cells]

    def get_state(self):
        """Return complete pack state dictionary for Kafka / logging."""
        return {
            "timestamp": time.time(),
            "sim_time": round(self.sim_time, 1),
            "pack_voltage": round(self.pack_voltage, 3),
            "current": round(self.current, 3),
            "power": round(self.power, 2),
            "soc": round(self.soc * 100, 2),
            "soh": 100.0,
            "cell_voltage": self.get_cell_voltages(),
            "cell_soc": self.get_cell_socs(),
            "min_cell_voltage": round(self.min_cell_voltage, 4),
            "max_cell_voltage": round(self.max_cell_voltage, 4),
            "voltage_imbalance": round(self.max_cell_voltage - self.min_cell_voltage, 5),
            "temperature": [round(self.temperature, 2), round(self.ambient_temp, 2)],
            "status": self.status,
            "capacity_ah": self.capacity_ah,
            "cycle_count": self.cycle_count,
            "num_cells": self.num_cells,
        }

    def reset(self, initial_soc=None):
        """Reset pack to initial state."""
        soc = initial_soc or self.initial_soc
        for cell in self.cells:
            cell.reset(soc)
        self.pack_voltage = sum(c.voltage for c in self.cells)
        self.current = 0.0
        self.power = 0.0
        self.soc = soc
        self.temperature = THERMAL_CONFIG["initial_temp"]
        self.status = "resting"
        self.sim_time = 0.0
        self.cycle_count = 0
        self._charge_throughput = 0.0
