"""Single battery cell model - Thevenin first-order equivalent circuit model.

Model: OCV(SOC) -- R0 --+-- R1 --+-- V_cell
                         |        |
                         +-- C1 --+
"""

import numpy as np
from config import CELL_PARAMS, OCV_SOC_TABLE


class Cell:
    def __init__(self, cell_id, capacity_ah, initial_soc=0.9, param_seed=0):
        self.cell_id = cell_id
        self.capacity_ah = capacity_ah

        # Apply parameter variation based on seed (deterministic per cell)
        rng = np.random.RandomState(param_seed)
        variation = CELL_PARAMS["param_variation"]
        soc_var = CELL_PARAMS["soc_variation"]

        self.r0 = CELL_PARAMS["r0_base"] * (1 + rng.uniform(-variation, variation))
        self.r1 = CELL_PARAMS["r1_base"] * (1 + rng.uniform(-variation, variation))
        self.c1 = CELL_PARAMS["c1_base"] * (1 + rng.uniform(-variation, variation))
        self.capacity_ah *= (1 + rng.uniform(-variation, variation))
        self.capacity_coulombs = self.capacity_ah * 3600.0

        # State variables
        self.soc = float(np.clip(initial_soc * (1 + rng.uniform(-soc_var, soc_var)), 0.0, 1.0))
        self.v_polarization = 0.0  # Voltage across RC polarization network
        self.voltage = 0.0
        self.current = 0.0

        # OCV lookup arrays for fast interpolation
        self._soc_points = np.array([p[0] for p in OCV_SOC_TABLE], dtype=np.float64)
        self._ocv_points = np.array([p[1] for p in OCV_SOC_TABLE], dtype=np.float64)
        self.voltage = self.get_ocv(self.soc)

    def get_ocv(self, soc):
        """Interpolate OCV from OCV-SOC lookup table."""
        return float(np.interp(soc, self._soc_points, self._ocv_points))

    def update(self, current, dt):
        """Update cell state for one time step.

        Args:
            current: Current in Amperes. Positive = discharge, negative = charge.
            dt: Time step in seconds.

        Returns:
            Terminal voltage in Volts.
        """
        self.current = float(current)

        # Coulomb counting: SOC decreases on discharge (positive current)
        delta_soc = (current * dt) / self.capacity_coulombs
        self.soc = float(np.clip(self.soc - delta_soc, 0.0, 1.0))

        # Polarization voltage (first-order RC network step response)
        tau = self.r1 * self.c1  # Time constant
        if tau > 0:
            decay = np.exp(-dt / tau)
            self.v_polarization = (
                self.v_polarization * decay
                + current * self.r1 * (1.0 - decay)
            )
        else:
            self.v_polarization = current * self.r1

        # Terminal voltage: V = OCV(SOC) - I*R0 - V_polarization
        # Discharge (I>0): voltage drops below OCV
        # Charge (I<0): voltage rises above OCV
        self.voltage = self.get_ocv(self.soc) - current * self.r0 - self.v_polarization

        return self.voltage

    def reset(self, initial_soc=0.9):
        """Reset cell to initial state."""
        self.soc = float(initial_soc)
        self.v_polarization = 0.0
        self.current = 0.0
        self.voltage = self.get_ocv(self.soc)

    def get_state(self):
        """Return cell state as dictionary."""
        return {
            "cell_id": self.cell_id,
            "voltage": round(self.voltage, 4),
            "soc": round(self.soc * 100, 2),
            "current": round(self.current, 3),
            "v_polarization": round(self.v_polarization, 5),
            "r0": self.r0,
            "capacity_ah": round(self.capacity_ah, 2),
        }
