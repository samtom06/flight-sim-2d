from __future__ import annotations
import numpy as np
from typing import Callable, Iterable, Tuple
from scipy.integrate import solve_ivp

RHS = Callable[[float, np.ndarray, dict], np.ndarray]
Event = Callable[[float, np.ndarray, dict], float]

def _wrap_event(ev: Event, params: dict):
    return lambda t, y: ev(t, y, params)

def integrate_ivp(rhs: RHS, s0, t_max: float, params: dict,
                  events: Iterable[Event] | None = None) -> Tuple[np.ndarray, np.ndarray]:
    evlist = None if events is None else [_wrap_event(e, params) for e in events]
    sol = solve_ivp(lambda t, y: rhs(t, y, params),
                    (0.0, float(t_max)), s0,
                    method="RK45", rtol=1e-6, atol=1e-9, max_step=0.1,
                    events=evlist, dense_output=False)
    return sol.t, sol.y.T

def integrate_fixed_step(
    rhs: RHS,
    s0,
    t_max: float,
    params: dict,
    dt: float = 0.05,
    step_cb: Callable[[float, np.ndarray], None] | None = None,
    events: Iterable[Event] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    t = 0.0
    y = np.asarray(s0, dtype=float)
    ts = [t]
    Ys = [y.copy()]
    evs = list(events or [])

    def rk4(f, t, y, h):
        k1 = f(t, y, params)
        k2 = f(t + 0.5 * h, y + 0.5 * h * k1, params)
        k3 = f(t + 0.5 * h, y + 0.5 * h * k2, params)
        k4 = f(t + h, y + h * k3, params)
        return y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

    while t < t_max:
        for e in evs:
            if getattr(e, "terminal", False) and e(t, y, params) <= 0.0:
                return np.asarray(ts), np.asarray(Ys)

        y = rk4(rhs, t, y, dt)
        t += dt
        ts.append(t)
        Ys.append(y.copy())

        if step_cb is not None:
            step_cb(t, y)

    return np.asarray(ts), np.asarray(Ys)
