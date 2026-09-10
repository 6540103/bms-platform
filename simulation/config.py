"""BMS Simulation Configuration - 48V 13S NMC battery pack"""

# Battery pack configuration
PACK_CONFIG = {
    "num_cells": 13,                # 13S for 48V nominal
    "nominal_capacity_ah": 40.0,    # Default 40Ah (configurable: 30/40/60)
    "nominal_voltage": 48.0,         # Nominal pack voltage
    "cell_chemistry": "NMC",         # Ternary lithium (Nickel-Manganese-Cobalt)
}

# Cell parameters (typical NMC cell)
CELL_PARAMS = {
    "ocv_full": 4.20,       # Full charge voltage (V)
    "ocv_empty": 3.00,      # Empty voltage (V)
    "r0_base": 0.003,       # Base ohmic resistance (Ohm) ~3mOhm
    "r1_base": 0.002,       # Polarization resistance (Ohm) ~2mOhm
    "c1_base": 3000.0,      # Polarization capacitance (F)
    "param_variation": 0.02,  # +/-2% parameter variation between cells
    "soc_variation": 0.01,    # +/-1% initial SOC variation
}

# OCV-SOC lookup table (SOC fraction 0-1 -> OCV in Volts)
# Typical NMC discharge curve
OCV_SOC_TABLE = [
    (0.00, 3.00),
    (0.05, 3.40),
    (0.10, 3.55),
    (0.20, 3.68),
    (0.30, 3.74),
    (0.40, 3.79),
    (0.50, 3.83),
    (0.60, 3.88),
    (0.70, 3.93),
    (0.80, 4.00),
    (0.90, 4.10),
    (0.95, 4.15),
    (1.00, 4.20),
]

# Thermal model (simplified lumped-parameter)
THERMAL_CONFIG = {
    "ambient_temp": 25.0,        # Ambient temperature (C)
    "thermal_resistance": 0.02,  # Thermal resistance (C/W)
    "thermal_capacity": 5000.0,  # Thermal capacity (J/C)
    "initial_temp": 25.0,        # Initial pack temperature (C)
}

# Simulation configuration
SIMULATION_CONFIG = {
    "time_step": 1.0,          # Simulation time step (seconds)
    "real_time": True,          # Run in real-time (sleep between steps)
    "initial_soc": 0.90,        # Start at 90% SOC
}

# Kafka configuration
KAFKA_CONFIG = {
    "bootstrap_servers": "192.168.1.26:9092",
    "realtime_topic": "bms.realtime",
    "events_topic": "bms.events",
    "commands_topic": "bms.commands",
    "client_id": "bms-simulator",
}

# Default current profile: list of (current_amps, duration_seconds)
# Positive = discharge, Negative = charge, 0 = rest
DEFAULT_PROFILE = [
    (20.0, 600),     # Discharge at 20A for 10 min
    (0.0, 60),        # Rest for 1 min
    (20.0, 600),      # Discharge at 20A for 10 min
    (0.0, 60),        # Rest for 1 min
    (-15.0, 1200),    # Charge at 15A for 20 min
    (0.0, 60),        # Rest for 1 min
]
