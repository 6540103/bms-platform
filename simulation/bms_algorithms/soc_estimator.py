"""SOC Estimator - Coulomb counting + OCV correction + Extended Kalman Filter (EKF).

Implements SOC estimation for a single cell using:
1. Coulomb counting (Ah integration) as prediction
2. OCV-SOC lookup for measurement correction
3. EKF for optimal state estimation with Thevenin model
4. Temperature compensation for available capacity
"""

import numpy as np
from config import CELL_PARAMS, OCV_SOC_TABLE


class SOCEstimator:
    def __init__(self, initial_soc=0.9, capacity_ah=40.0, num_cells=13):
        self.num_cells = num_cells
        self.capacity_ah = capacity_ah
        self.nominal_capacity_ah = capacity_ah

        # EKF state: [soc, v1] where v1 is polarization voltage
        self.x = np.array([initial_soc, 0.0])  # state vector
        self.P = np.diag([0.01, 0.001])  # covariance matrix

        # EKF noise parameters
        self.Q = np.diag([1e-6, 1e-6])  # process noise
        self.R = np.array([[0.001]])  # measurement noise (voltage measurement)

        # Cell parameters (average)
        self.r0 = CELL_PARAMS["r0_base"]
        self.r1 = CELL_PARAMS["r1_base"]
        self.c1 = CELL_PARAMS["c1_base"]

        # Coulomb counting accumulator
        self.coulomb_soc = initial_soc
        self.ocv_soc = initial_soc

        # Temperature compensation
        self.temperature = 25.0
        self.temp_compensation_factor = 1.0

        # OCV-SOC interpolation
        self.ocv_soc_points = np.array([p[0] for p in OCV_SOC_TABLE])
        self.ocv_volt_points = np.array([p[1] for p in OCV_SOC_TABLE])

    def set_temperature(self, temp):
        """Update temperature and compute capacity compensation factor."""
        self.temperature = temp
        # Simplified temperature-capacity curve (peaks at 25C)
        if temp < 0:
            self.temp_compensation_factor = 0.85
        elif temp < 10:
            self.temp_compensation_factor = 0.92 + (temp - 0) * 0.008
        elif temp < 40:
            self.temp_compensation_factor = 1.0
        else:
            self.temp_compensation_factor = max(0.95, 1.0 - (temp - 40) * 0.005)

    def ocv_from_soc(self, soc):
        """Convert SOC (0-1) to OCV voltage via interpolation."""
        return float(np.interp(soc, self.ocv_soc_points, self.ocv_volt_points))

    def soc_from_ocv(self, ocv):
        """Convert OCV voltage to SOC (0-1) via inverse interpolation."""
        return float(np.interp(ocv, self.ocv_volt_points, self.ocv_soc_points))

    def update(self, current, cell_voltages, dt):
        """Update SOC estimate for one time step using EKF.

        Args:
            current: Pack current (A), positive=discharge, negative=charge
            cell_voltages: List of individual cell voltages
            dt: Time step (seconds)

        Returns:
            dict with soc_ekf, soc_coulomb, soc_ocv, and per-cell estimates
        """
        # Use average cell voltage for pack-level EKF
        avg_voltage = np.mean(cell_voltages)
        min_voltage = np.min(cell_voltages)

        # --- Coulomb counting ---
        effective_capacity = self.capacity_ah * self.temp_compensation_factor
        delta_soc = (current * dt) / (effective_capacity * 3600.0)
        self.coulomb_soc = np.clip(self.coulomb_soc - delta_soc, 0.0, 1.0)

        # --- OCV correction (only when resting or low current) ---
        if abs(current) < 0.5:
            # Estimate OCV by removing IR drop
            estimated_ocv = avg_voltage + current * self.r0
            self.ocv_soc = self.soc_from_ocv(estimated_ocv)
            # Blend OCV estimate into Coulomb count (gradual correction)
            self.coulomb_soc = 0.95 * self.coulomb_soc + 0.05 * self.ocv_soc

        # --- EKF prediction step ---
        soc_pred = self.x[0] - delta_soc
        tau = self.r1 * self.c1
        v1_pred = self.x[1] * np.exp(-dt / tau) + current * self.r1 * (1 - np.exp(-dt / tau))
        x_pred = np.array([soc_pred, v1_pred])

        # State transition Jacobian (F)
        F = np.array([
            [1.0, 0.0],
            [0.0, np.exp(-dt / tau)]
        ])

        # Predicted covariance
        P_pred = F @ self.P @ F.T + self.Q

        # --- EKF update step ---
        # Measurement: terminal voltage = OCV(soc) - I*R0 - v1
        ocv_pred = self.ocv_from_soc(x_pred[0])
        voltage_pred = ocv_pred - current * self.r0 - x_pred[1]

        # Measurement Jacobian (H) - derivative of voltage w.r.t. state
        # dV/dSOC = dOCV/dSOC (numerical derivative)
        dsoc = 0.001
        ocv_plus = self.ocv_from_soc(min(x_pred[0] + dsoc, 1.0))
        ocv_minus = self.ocv_from_soc(max(x_pred[0] - dsoc, 0.0))
        docv_dsoc = (ocv_plus - ocv_minus) / (2 * dsoc)
        H = np.array([[docv_dsoc, -1.0]])

        # Innovation (measurement residual)
        innovation = avg_voltage - voltage_pred

        # Innovation covariance
        S = H @ P_pred @ H.T + self.R

        # Kalman gain
        K = P_pred @ H.T @ np.linalg.inv(S)

        # State update
        self.x = x_pred + K.flatten() * innovation
        self.x[0] = np.clip(self.x[0], 0.0, 1.0)

        # Covariance update
        self.P = (np.eye(2) - K @ H) @ P_pred

        # --- Per-cell SOC estimation (using min cell as conservative) ---
        # Estimate each cell's SOC based on its voltage relative to average
        per_cell_soc = []
        for v in cell_voltages:
            # Simple per-cell estimate: adjust pack SOC by voltage difference
            v_diff = v - avg_voltage
            # Approximate: 10mV ~ 1% SOC in mid-range
            cell_soc_est = self.x[0] + v_diff * 1.0  # rough per-cell estimate
            per_cell_soc.append(float(np.clip(cell_soc_est, 0.0, 1.0)))

        return {
            "soc_ekf": float(self.x[0]),
            "soc_coulomb": float(self.coulomb_soc),
            "soc_ocv": float(self.ocv_soc),
            "soc_min_cell": float(np.min(per_cell_soc)),
            "soc_max_cell": float(np.max(per_cell_soc)),
            "per_cell_soc": per_cell_soc,
            "ekf_v1": float(self.x[1]),
            "temp_factor": float(self.temp_compensation_factor),
        }
