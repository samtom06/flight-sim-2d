from __future__ import annotations
import numpy as np

def cd_simple(cd: float) -> float:
    return float(cd)

def cl_simple(cl_cmd: float) -> float:
    return float(cl_cmd)

def cd_polar(cd0: float, k: float, cl: float) -> float:
    return float(cd0 + k * cl * cl)

def cl_linear(alpha_rad: float, cl_alpha: float, alpha0_rad: float, cl_max: float) -> float:
    cl = cl_alpha * (alpha_rad - alpha0_rad)
    return float(np.clip(cl, -cl_max, cl_max))
