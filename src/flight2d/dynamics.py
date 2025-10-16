from __future__ import annotations
import numpy as np
from math import radians
from .aero import cd_polar, cl_simple, cl_linear, cd_simple
from .forces import decompose_forces

__all__ = ["state_from_speed_gamma", "rhs_pointmass", "event_ground"]

def state_from_speed_gamma(x0: float, y0: float, speed0: float, gamma0_rad: float) -> np.ndarray:
    vx0 = speed0 * np.cos(gamma0_rad)
    vy0 = speed0 * np.sin(gamma0_rad)
    return np.array([x0, y0, vx0, vy0], dtype=float)

def rhs_pointmass(t: float, s: np.ndarray, p: dict) -> np.ndarray:
    # underscore for unused 'x' silences F841 while making intent explicit
    _x, y, vx, vy = (float(s[0]), float(s[1]), float(s[2]), float(s[3]))

    V = float(np.hypot(vx, vy) + 1e-12)
    rho = float(p["rho_fn"](y, *p["rho_args"]))
    q = 0.5 * rho * V * V

    if p["aero_model"] == "simple":
        cl = cl_simple(p["CL_cmd"])
        cd = cd_simple(p["CD0"])
    else:
        # AoA ≈ pitch - flight-path angle
        alpha = radians(p.get("pitch_deg", 0.0)) - np.arctan2(vy, vx)
        cl = cl_linear(alpha, p["CL_alpha"], radians(p["alpha0_deg"]), p["CL_max"])
        cd = cd_polar(p["CD0"], p["k"], cl)

    L = q * cl * p["S"]
    D = q * cd * p["S"]
    fx, fy = decompose_forces(vx, vy, L, D, p["T"], p["theta_T"])

    ax = fx / p["m"]
    ay = fy / p["m"] - p["g"]
    return np.array([vx, vy, ax, ay], dtype=float)

def event_ground(t: float, s: np.ndarray, p: dict) -> float:
    return float(s[1] - p["y_floor"])
event_ground.terminal = True
event_ground.direction = -1
