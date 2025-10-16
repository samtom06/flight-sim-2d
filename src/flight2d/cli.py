from __future__ import annotations

from pathlib import Path
from math import radians
import argparse
import json
import numpy as np
import pandas as pd

from .atmosphere import get_rho_fn
from .dynamics import rhs_pointmass, state_from_speed_gamma, event_ground
from .integrators import integrate_ivp, integrate_fixed_step
from .viz import save_basic_plots, LivePlotter


def main() -> None:
    ap = argparse.ArgumentParser(description="2D Flight Path Simulation (baseline)")
    ap.add_argument("--t-max", type=float, default=60.0)
    ap.add_argument("--speed0", type=float, default=70.0)
    ap.add_argument("--gamma0-deg", type=float, default=10.0)
    ap.add_argument("--y0", type=float, default=10.0)
    ap.add_argument("--model", choices=["simple", "polar"], default="polar")
    ap.add_argument("--pitch-deg", type=float, default=15.0)
    ap.add_argument("--thrust", type=float, default=0.0)
    ap.add_argument("--thrust-theta", type=float, default=0.0)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--dt", type=float, default=0.02)  # fixed-step for --live
    args = ap.parse_args()

    # params
    rho_fn = get_rho_fn("isa_linear")
    rho_args = (1.225, 2.3e-5)
    params = {
        "m": 1200.0,
        "S": 16.2,
        "g": 9.80665,
        "T": args.thrust,
        "theta_T": args.thrust_theta,
        "aero_model": args.model,
        "CD0": 0.02,
        "k": 0.045,
        "CL_cmd": 0.4,
        "CL_alpha": 5.5,
        "alpha0_deg": 2.0,
        "CL_max": 1.8,  # margin to reduce clipping
        "rho_fn": rho_fn,
        "rho_args": rho_args,
        "y_floor": 0.0,
        "pitch_deg": args.pitch_deg,
    }

    # integrate
    s0 = state_from_speed_gamma(0.0, args.y0, args.speed0, radians(args.gamma0_deg))
    if args.live:
        plotter = LivePlotter(title=f"{args.model} (live)")
        t, Y = integrate_fixed_step(
            rhs_pointmass, s0, args.t_max, params,
            dt=args.dt,
            step_cb=lambda tt, yy: plotter.update(tt, yy),
            events=[event_ground],
        )
        plotter.hold()  # keep window open after the run
    else:
        t, Y = integrate_ivp(rhs_pointmass, s0, args.t_max, params, events=[event_ground])

    # save CSV
    rundir = Path("data/runs")
    rundir.mkdir(parents=True, exist_ok=True)
    csv = rundir / "baseline.csv"
    df = pd.DataFrame(Y, columns=["x", "y", "vx", "vy"])
    df.insert(0, "t", t)
    df.to_csv(csv, index=False)

    # KPIs (initial)
    V = np.hypot(df["vx"], df["vy"])
    rho0 = float(params["rho_fn"](float(df["y"].iloc[0]), *params["rho_args"]))
    q0 = 0.5 * rho0 * float(V.iloc[0] ** 2)

    if params["aero_model"] == "polar":
        alpha0 = np.deg2rad(params["pitch_deg"]) - np.arctan2(float(df["vy"].iloc[0]), float(df["vx"].iloc[0]))
        CL0 = float(params["CL_alpha"]) * (alpha0 - np.deg2rad(params["alpha0_deg"]))
        CD_eff0 = float(params["CD0"]) + float(params["k"]) * CL0**2
    else:
        CL0 = float(params["CL_cmd"])
        CD_eff0 = float(params["CD0"])

    L0 = q0 * params["S"] * CL0
    D0 = q0 * params["S"] * CD_eff0
    LD0 = float(L0 / max(D0, 1e-12))

    range_m = float(df["x"].iloc[-1] - df["x"].iloc[0])
    alt_drop = float(df["y"].iloc[0] - df["y"].iloc[-1])
    glide_ratio = float(range_m / alt_drop) if alt_drop > 1e-9 else float("nan")

    dKE = 0.5 * params["m"] * (float(V.iloc[-1] ** 2) - float(V.iloc[0] ** 2))
    dPE = params["m"] * params["g"] * (float(df["y"].iloc[-1]) - float(df["y"].iloc[0]))
    dE_total = dKE + dPE
    energy_per_meter = float(-dE_total / max(range_m, 1e-9))

    # KPIs (end-of-run snapshot)
    rho_end = float(params["rho_fn"](float(df["y"].iloc[-1]), *params["rho_args"]))
    q_end = 0.5 * rho_end * float(V.iloc[-1] ** 2)
    if params["aero_model"] == "polar":
        alpha_end = np.deg2rad(params["pitch_deg"]) - np.arctan2(float(df["vy"].iloc[-1]), float(df["vx"].iloc[-1]))
        CL_end = float(params["CL_alpha"]) * (alpha_end - np.deg2rad(params["alpha0_deg"]))
        CD_eff_end = float(params["CD0"]) + float(params["k"]) * CL_end**2
    else:
        alpha_end = float("nan")
        CL_end = float(params["CL_cmd"])
        CD_eff_end = float(params["CD0"])

    L_end = q_end * params["S"] * CL_end
    D_end = q_end * params["S"] * CD_eff_end
    LD_end = float(L_end / max(D_end, 1e-12))

    meta = {
        "kpis": {
            "range_m": range_m,
            "max_alt_m": float(df["y"].max()),
            "time_aloft_s": float(df["t"].iloc[-1]),
            "LD": LD_end,             # end-of-run L/D
            "LD_initial": LD0,        # initial L/D
            "glide_ratio": glide_ratio,
            "energy_per_m": energy_per_meter,
        },
        "final_aero": {
            "alpha_end_deg": float(np.rad2deg(alpha_end)) if np.isfinite(alpha_end) else None,
            "CL_end": float(CL_end),
            "CD_eff_end": float(CD_eff_end),
            "q_end_Pa": float(q_end),
        },
    }
    (rundir / "baseline_meta.json").write_text(json.dumps(meta, indent=2))

    # figures + console summary
    save_basic_plots(csv, tag="baseline")
    print(
        f"range={range_m:.0f} m | max_alt={df['y'].max():.1f} m | time_aloft={df['t'].iloc[-1]:.1f} s | "
        f"L/D={LD_end:.2f} (init {LD0:.2f}) | glide={glide_ratio:.2f} | energy_per_m={energy_per_meter:.0f} J/m | "
        f"model={args.model} | pitch={args.pitch_deg} deg"
    )


if __name__ == "__main__":
    main()
