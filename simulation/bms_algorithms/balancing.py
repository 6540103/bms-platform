"""Cell Balancing Module - Passive balancing with voltage-threshold strategy.

Implements passive (dissipative) cell balancing:
- Monitors cell voltage differences
- Discharges high-voltage cells through balancing resistors
- Triggers when voltage imbalance exceeds threshold
- Only balances during charging or resting (not during high-current discharge)
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class BalancingConfig:
    """Balancing configuration."""
    enable: bool = True
    voltage_threshold_mv: float = 20.0      # Start balancing when diff > 20mV
    stop_threshold_mv: float = 5.0           # Stop when diff < 5mV
    balancing_current_ma: float = 50.0       # Passive balancing current (mA)
    max_balancing_cells: int = 5              # Max cells balancing simultaneously
    min_soc_for_balancing: float = 20.0      # Don't balance below 20% SOC
    only_charge_or_rest: bool = True           # Only balance during charge/rest


class CellBalancer:
    def __init__(self, config=None):
        self.config = config or BalancingConfig()
        self.balancing_cells = []  # List of cell indices currently being balanced
        self.balancing_active = False
        self.total_balanced_ah = 0.0  # Total charge balanced out
        self.balance_cycle_count = 0

    def update(self, cell_voltages: List[float], current: float,
               soc: float, temperature: float) -> Dict:
        """Evaluate and execute cell balancing for one time step.

        Args:
            cell_voltages: List of individual cell voltages
            current: Pack current (A), positive=discharge
            soc: Pack SOC (0-100%)
            temperature: Pack temperature (C)

        Returns:
            dict with balancing state and per-cell balancing currents
        """
        cfg = self.config
        num_cells = len(cell_voltages)
        per_cell_balance_current = [0.0] * num_cells  # in Amperes (negative = discharge)

        if not cfg.enable:
            return {
                "balancing_active": False,
                "balancing_cells": [],
                "per_cell_balance_current_ma": [0.0] * num_cells,
                "imbalance_mv": 0.0,
                "total_balanced_ah": self.total_balanced_ah,
            }

        max_v = max(cell_voltages)
        min_v = min(cell_voltages)
        imbalance_mv = (max_v - min_v) * 1000
        avg_v = sum(cell_voltages) / num_cells

        # Determine if balancing conditions are met
        can_balance = (
            soc >= cfg.min_soc_for_balancing
            and temperature > 0.0  # Don't balance below 0C
            and (not cfg.only_charge_or_rest or current <= 5.0)  # Charge or rest
        )

        # Hysteresis: start at voltage_threshold, stop at stop_threshold
        if self.balancing_active:
            should_balance = imbalance_mv > cfg.stop_threshold_mv and can_balance
        else:
            should_balance = imbalance_mv > cfg.voltage_threshold_mv and can_balance

        if should_balance:
            self.balancing_active = True
            # Find cells above average that need balancing
            cells_to_balance = []
            for i, v in enumerate(cell_voltages):
                if v > avg_v + (cfg.stop_threshold_mv / 1000.0):
                    cells_to_balance.append((i, v))

            # Sort by voltage (highest first) and limit count
            cells_to_balance.sort(key=lambda x: x[1], reverse=True)
            cells_to_balance = cells_to_balance[:cfg.max_balancing_cells]

            self.balancing_cells = [i for i, _ in cells_to_balance]

            # Apply balancing current (discharge high cells)
            balance_current_a = cfg.balancing_current_ma / 1000.0
            for i, _ in cells_to_balance:
                per_cell_balance_current[i] = -balance_current_a

            # Track balanced charge (Ah per second = A * dt/3600, dt=1s)
            self.total_balanced_ah += balance_current_a * len(cells_to_balance) / 3600.0
        else:
            if self.balancing_active:
                self.balance_cycle_count += 1
            self.balancing_active = False
            self.balancing_cells = []

        return {
            "balancing_active": self.balancing_active,
            "balancing_cells": self.balancing_cells,
            "per_cell_balance_current_ma": [-c * 1000 for c in per_cell_balance_current],
            "imbalance_mv": imbalance_mv,
            "avg_voltage": avg_v,
            "total_balanced_ah": self.total_balanced_ah,
            "balance_cycle_count": self.balance_cycle_count,
        }
