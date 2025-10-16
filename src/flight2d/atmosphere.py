from __future__ import annotations
import numpy as np
from .constants import RHO0

def rho_constant(_: float, rho0: float = RHO0) -> float:
    return float(rho0)

def rho_isa_linear(h_m: float, rho0: float, lapse: float) -> float:
    # crude linear drop with altitude; clamped to >= 0
    return float(max(0.0, rho0 * (1.0 - lapse * h_m)))

def rho_exp(h_m: float, rho0: float, H: float = 8500.0) -> float:
    # exponential scale height model
    return float(rho0 * np.exp(-h_m / H))

def get_rho_fn(name: str):
    table = {
        "constant": rho_constant,
        "isa_linear": lambda h, rho0, lapse: rho_isa_linear(h, rho0, lapse),
        "exp": lambda h, rho0, lapse_unused: rho_exp(h, rho0, 8500.0),
    }
    if name not in table:
        raise ValueError(f"Unknown atmosphere '{name}'")
    return table[name]
