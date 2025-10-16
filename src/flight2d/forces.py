from __future__ import annotations
import numpy as np

def decompose_forces(vx: float, vy: float, L: float, D: float, T: float, theta_T: float):
    """
    Resolve Lift (⊥ velocity), Drag (opposes velocity), and Thrust (at angle theta_T)
    into inertial x,y components. Returns (Fx, Fy).
    """
    gamma = float(np.arctan2(vy, vx))  # atan2 is safe even if vx=vy=0

    Dx, Dy = -D * np.cos(gamma), -D * np.sin(gamma)
    Lx, Ly = -L * np.sin(gamma),  L * np.cos(gamma)
    Tx, Ty =  T * np.cos(theta_T), T * np.sin(theta_T)

    return (Dx + Lx + Tx, Dy + Ly + Ty)
