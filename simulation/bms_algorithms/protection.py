"""BMS Protection Module - Overvoltage, undervoltage, overcurrent, overtemperature, etc.

Monitors battery parameters and triggers protection actions when thresholds are exceeded.
Protection levels: WARNING -> ALARM -> PROTECT (limit/cutoff)
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ProtectionThresholds:
    """Protection threshold configuration for NMC cells."""
    # Voltage thresholds (V)
    overvoltage_warning: float = 4.15
    overvoltage_alarm: float = 4.18
    overvoltage_protect: float = 4.20

    undervoltage_warning: float = 3.20
    undervoltage_alarm: float = 3.10
    undervoltage_protect: float = 3.00

    # Current thresholds (A) - positive = discharge
    overcurrent_discharge_warning: float = 80.0   # 2C for 40Ah
    overcurrent_discharge_alarm: float = 100.0     # 2.5C
    overcurrent_discharge_protect: float = 120.0   # 3C

    overcurrent_charge_warning: float = -40.0       # 1C charge
    overcurrent_charge_alarm: float = -50.0
    overcurrent_charge_protect: float = -60.0

    short_circuit_current: float = 200.0            # Short circuit threshold

    # Temperature thresholds (C)
    overtemperature_warning: float = 45.0
    overtemperature_alarm: float = 55.0
    overtemperature_protect: float = 60.0

    lowtemperature_warning: float = 10.0
    lowtemperature_alarm: float = 5.0
    lowtemperature_protect: float = 0.0

    # SOC thresholds
    high_soc_warning: float = 95.0
    low_soc_warning: float = 20.0
    low_soc_alarm: float = 10.0

    # Cell imbalance threshold (mV)
    imbalance_warning: float = 30.0
    imbalance_alarm: float = 50.0


@dataclass
class ProtectionState:
    """Current protection state."""
    active_protections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    alarms: List[str] = field(default_factory=list)
    charge_allowed: bool = True
    discharge_allowed: bool = True
    charge_current_limit: float = 0.0  # 0 = no limit
    discharge_current_limit: float = 0.0
    fault_status: str = "normal"  # normal / warning / alarm / fault


class ProtectionModule:
    def __init__(self, thresholds=None):
        self.thresholds = thresholds or ProtectionThresholds()
        self.state = ProtectionState()
        self._protection_history = []  # Track when protections trigger/clear

    def update(self, current: float, cell_voltages: List[float],
               temperature: float, soc: float) -> Dict:
        """Evaluate all protection conditions for one time step.

        Args:
            current: Pack current (A), positive=discharge
            cell_voltages: List of individual cell voltages
            temperature: Pack temperature (C)
            soc: Pack SOC (0-100%)

        Returns:
            dict with protection state details
        """
        t = self.thresholds
        s = self.state

        # Reset state
        s.warnings = []
        s.alarms = []
        s.active_protections = []
        s.charge_allowed = True
        s.discharge_allowed = True
        s.charge_current_limit = 0.0
        s.discharge_current_limit = 0.0

        max_v = max(cell_voltages)
        min_v = min(cell_voltages)
        imbalance_mv = (max_v - min_v) * 1000

        # --- Overvoltage protection ---
        if max_v >= t.overvoltage_protect:
            s.active_protections.append("overvoltage_protect")
            s.charge_allowed = False
            s.alarms.append(f"过压保护: 最高单体 {max_v:.3f}V >= {t.overvoltage_protect}V")
        elif max_v >= t.overvoltage_alarm:
            s.alarms.append(f"过压告警: 最高单体 {max_v:.3f}V")
            s.charge_current_limit = 10.0  # Limit charge current
        elif max_v >= t.overvoltage_warning:
            s.warnings.append(f"过压预警: 最高单体 {max_v:.3f}V")

        # --- Undervoltage protection ---
        if min_v <= t.undervoltage_protect:
            s.active_protections.append("undervoltage_protect")
            s.discharge_allowed = False
            s.alarms.append(f"欠压保护: 最低单体 {min_v:.3f}V <= {t.undervoltage_protect}V")
        elif min_v <= t.undervoltage_alarm:
            s.alarms.append(f"欠压告警: 最低单体 {min_v:.3f}V")
            s.discharge_current_limit = 10.0
        elif min_v <= t.undervoltage_warning:
            s.warnings.append(f"欠压预警: 最低单体 {min_v:.3f}V")

        # --- Overcurrent discharge protection ---
        if current >= t.short_circuit_current:
            s.active_protections.append("short_circuit")
            s.discharge_allowed = False
            s.alarms.append(f"短路保护: 电流 {current:.1f}A")
        elif current >= t.overcurrent_discharge_protect:
            s.active_protections.append("overcurrent_discharge_protect")
            s.discharge_allowed = False
            s.alarms.append(f"放电过流保护: {current:.1f}A >= {t.overcurrent_discharge_protect}A")
        elif current >= t.overcurrent_discharge_alarm:
            s.alarms.append(f"放电过流告警: {current:.1f}A")
            s.discharge_current_limit = t.overcurrent_discharge_warning
        elif current >= t.overcurrent_discharge_warning:
            s.warnings.append(f"放电过流预警: {current:.1f}A")

        # --- Overcurrent charge protection ---
        if current <= t.overcurrent_charge_protect:
            s.active_protections.append("overcurrent_charge_protect")
            s.charge_allowed = False
            s.alarms.append(f"充电过流保护: {current:.1f}A")
        elif current <= t.overcurrent_charge_alarm:
            s.alarms.append(f"充电过流告警: {current:.1f}A")
            s.charge_current_limit = abs(t.overcurrent_charge_warning)

        # --- Overtemperature protection ---
        if temperature >= t.overtemperature_protect:
            s.active_protections.append("overtemperature_protect")
            s.charge_allowed = False
            s.discharge_allowed = False
            s.alarms.append(f"过温保护: {temperature:.1f}C >= {t.overtemperature_protect}C")
        elif temperature >= t.overtemperature_alarm:
            s.alarms.append(f"过温告警: {temperature:.1f}C")
            s.charge_current_limit = 10.0
            s.discharge_current_limit = 30.0
        elif temperature >= t.overtemperature_warning:
            s.warnings.append(f"过温预警: {temperature:.1f}C")

        # --- Low temperature protection ---
        if temperature <= t.lowtemperature_protect:
            s.active_protections.append("lowtemperature_protect")
            s.charge_allowed = False  # No charging below 0C (lithium plating risk)
            s.alarms.append(f"低温保护: {temperature:.1f}C <= {t.lowtemperature_protect}C, 禁止充电")
        elif temperature <= t.lowtemperature_alarm:
            s.alarms.append(f"低温告警: {temperature:.1f}C, 限制充电电流")
            s.charge_current_limit = 5.0  # Very low charge current
        elif temperature <= t.lowtemperature_warning:
            s.warnings.append(f"低温预警: {temperature:.1f}C")
            s.charge_current_limit = 15.0

        # --- SOC warnings ---
        if soc >= t.high_soc_warning:
            s.warnings.append(f"SOC 高: {soc:.1f}%")
        if soc <= t.low_soc_alarm:
            s.alarms.append(f"SOC 低告警: {soc:.1f}%")
        elif soc <= t.low_soc_warning:
            s.warnings.append(f"SOC 低预警: {soc:.1f}%")

        # --- Cell imbalance ---
        if imbalance_mv >= t.imbalance_alarm:
            s.alarms.append(f"单体不均衡告警: {imbalance_mv:.1f}mV")
        elif imbalance_mv >= t.imbalance_warning:
            s.warnings.append(f"单体不均衡预警: {imbalance_mv:.1f}mV")

        # --- Determine overall fault status ---
        if s.active_protections:
            s.fault_status = "fault"
        elif s.alarms:
            s.fault_status = "alarm"
        elif s.warnings:
            s.fault_status = "warning"
        else:
            s.fault_status = "normal"

        return {
            "fault_status": s.fault_status,
            "active_protections": s.active_protections,
            "warnings": s.warnings,
            "alarms": s.alarms,
            "charge_allowed": s.charge_allowed,
            "discharge_allowed": s.discharge_allowed,
            "charge_current_limit": s.charge_current_limit,
            "discharge_current_limit": s.discharge_current_limit,
            "max_cell_voltage": max_v,
            "min_cell_voltage": min_v,
            "imbalance_mv": imbalance_mv,
        }
