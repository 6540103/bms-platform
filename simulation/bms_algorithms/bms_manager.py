"""BMS Manager - Central coordinator for all BMS algorithms.

Integrates:
- SOC estimation (EKF)
- Protection (overvoltage/undervoltage/overcurrent/temperature)
- Cell balancing (passive)
- SOH estimation (capacity + resistance)

Provides a unified interface to the simulation engine and produces
a comprehensive BMS status report each time step.
"""

from typing import Dict, List
from .soc_estimator import SOCEstimator
from .protection import ProtectionModule
from .balancing import CellBalancer
from .soh_estimator import SOHEstimator


class BMSManager:
    def __init__(self, num_cells=13, capacity_ah=40.0, initial_soc=0.9):
        self.num_cells = num_cells
        self.capacity_ah = capacity_ah

        # Initialize all BMS modules
        self.soc_estimator = SOCEstimator(
            initial_soc=initial_soc,
            capacity_ah=capacity_ah,
            num_cells=num_cells,
        )
        self.protection = ProtectionModule()
        self.balancer = CellBalancer()
        self.soh_estimator = SOHEstimator()

        # BMS overall state
        self.bms_status = "normal"  # normal / warning / alarm / fault
        self.total_runtime = 0.0
        self.protection_event_count = 0
        self.balance_event_count = 0

    def update(self, current: float, cell_voltages: List[float],
               temperature: float, dt: float = 1.0) -> Dict:
        """Run all BMS algorithms for one time step.

        Args:
            current: Pack current (A), positive=discharge, negative=charge
            cell_voltages: List of individual cell voltages
            temperature: Pack temperature (C)
            dt: Time step (seconds)

        Returns:
            Comprehensive BMS status dict
        """
        self.total_runtime += dt

        # --- 1. SOC Estimation ---
        self.soc_estimator.set_temperature(temperature)
        soc_result = self.soc_estimator.update(current, cell_voltages, dt)
        soc_percent = soc_result["soc_ekf"] * 100.0

        # --- 2. Protection ---
        protection_result = self.protection.update(
            current=current,
            cell_voltages=cell_voltages,
            temperature=temperature,
            soc=soc_percent,
        )
        if protection_result["active_protections"]:
            self.protection_event_count += 1

        # --- 3. Cell Balancing ---
        balancing_result = self.balancer.update(
            cell_voltages=cell_voltages,
            current=current,
            soc=soc_percent,
            temperature=temperature,
        )
        if balancing_result["balancing_active"]:
            self.balance_event_count += 1

        # Apply balancing current to effective current (for SOC estimation next step)
        # In a real BMS, balancing affects cell voltages and currents
        total_balance_current = sum(balancing_result["per_cell_balance_current_ma"]) / 1000.0

        # --- 4. SOH Estimation ---
        soh_result = self.soh_estimator.update(
            current=current,
            temperature=temperature,
            dt=dt,
            soc=soc_percent,
            cell_voltages=cell_voltages,
        )

        # --- 5. Determine overall BMS status ---
        if protection_result["fault_status"] == "fault":
            self.bms_status = "fault"
        elif protection_result["fault_status"] == "alarm":
            self.bms_status = "alarm"
        elif protection_result["fault_status"] == "warning" or soh_result["health_status"] == "warning":
            self.bms_status = "warning"
        else:
            self.bms_status = "normal"

        # --- 6. Compile comprehensive status ---
        return {
            "bms_status": self.bms_status,
            "total_runtime_s": self.total_runtime,
            "protection_event_count": self.protection_event_count,
            "balance_event_count": self.balance_event_count,

            # SOC
            "soc": {
                "ekf": soc_result["soc_ekf"],
                "coulomb": soc_result["soc_coulomb"],
                "ocv": soc_result["soc_ocv"],
                "min_cell": soc_result["soc_min_cell"],
                "max_cell": soc_result["soc_max_cell"],
                "per_cell": soc_result["per_cell_soc"],
                "temp_factor": soc_result["temp_factor"],
            },

            # Protection
            "protection": {
                "fault_status": protection_result["fault_status"],
                "active_protections": protection_result["active_protections"],
                "warnings": protection_result["warnings"],
                "alarms": protection_result["alarms"],
                "charge_allowed": protection_result["charge_allowed"],
                "discharge_allowed": protection_result["discharge_allowed"],
                "charge_current_limit": protection_result["charge_current_limit"],
                "discharge_current_limit": protection_result["discharge_current_limit"],
                "imbalance_mv": protection_result["imbalance_mv"],
            },

            # Balancing
            "balancing": {
                "active": balancing_result["balancing_active"],
                "cells": balancing_result["balancing_cells"],
                "per_cell_current_ma": balancing_result["per_cell_balance_current_ma"],
                "imbalance_mv": balancing_result["imbalance_mv"],
                "total_balanced_ah": balancing_result["total_balanced_ah"],
            },

            # SOH
            "soh": {
                "combined": soh_result["combined_soh"],
                "capacity": soh_result["capacity_soh"],
                "resistance": soh_result["resistance_soh"],
                "estimated_capacity_ah": soh_result["estimated_capacity_ah"],
                "estimated_resistance_mohm": soh_result["estimated_internal_resistance_mohm"],
                "cycle_count": soh_result["cycle_count"],
                "health_status": soh_result["health_status"],
            },
        }

    def get_status_summary(self) -> str:
        """Get a human-readable status summary."""
        lines = [
            f"BMS Status: {self.bms_status.upper()}",
            f"SOC (EKF): {self.soc_estimator.x[0]*100:.1f}%",
            f"SOH: {self.soh_estimator.combined_soh:.1f}%",
            f"Protections: {', '.join(self.protection.state.active_protections) or 'none'}",
            f"Balancing: {'active' if self.balancer.balancing_active else 'idle'}",
        ]
        return "\n".join(lines)
