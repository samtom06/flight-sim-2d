from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def save_basic_plots(csv_path: str | Path, tag: str = "baseline") -> None:
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    figsdir = Path("data/figures")
    figsdir.mkdir(parents=True, exist_ok=True)

    # Speed vs time
    V = np.hypot(df["vx"].to_numpy(), df["vy"].to_numpy())
    plt.figure(figsize=(8, 6))
    plt.plot(df["t"].to_numpy(), V)
    plt.title("Speed vs Time")
    plt.xlabel("t [s]")
    plt.ylabel("V [m/s]")
    plt.grid(True, alpha=0.3)
    plt.savefig(figsdir / f"{tag}_speed.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Trajectory
    plt.figure(figsize=(8, 6))
    plt.plot(df["x"].to_numpy(), df["y"].to_numpy())
    plt.title("Trajectory")
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.grid(True, alpha=0.3)
    plt.savefig(figsdir / f"{tag}_traj.png", dpi=150, bbox_inches="tight")
    plt.close()


class LivePlotter:
    def __init__(self, title: str = "Live"):
        plt.ion()  # interactive updates during the run

        self.t_data: list[float] = []
        self.v_data: list[float] = []
        self.x_data: list[float] = []
        self.y_data: list[float] = []

        self.fig = plt.figure(figsize=(10, 4.8))
        self.ax1 = self.fig.add_subplot(1, 2, 1)
        self.ax2 = self.fig.add_subplot(1, 2, 2)

        self.line_v, = self.ax1.plot([], [], lw=2)
        self.line_xy, = self.ax2.plot([], [], lw=2)

        self.ax1.set_title("Speed vs Time")
        self.ax1.set_xlabel("t [s]")
        self.ax1.set_ylabel("V [m/s]")
        self.ax1.grid(True, alpha=0.3)

        self.ax2.set_title("Trajectory")
        self.ax2.set_xlabel("x [m]")
        self.ax2.set_ylabel("y [m]")
        self.ax2.grid(True, alpha=0.3)

        try:
            self.fig.canvas.manager.set_window_title(title)  # type: ignore[attr-defined]
        except Exception:
            pass

        plt.tight_layout()

    def update(self, t: float, y: np.ndarray) -> None:
        vx, vy = float(y[2]), float(y[3])
        v = float(np.hypot(vx, vy))

        self.t_data.append(float(t))
        self.v_data.append(v)
        self.x_data.append(float(y[0]))
        self.y_data.append(float(y[1]))

        self.line_v.set_data(self.t_data, self.v_data)
        self.ax1.relim()
        self.ax1.autoscale_view()

        self.line_xy.set_data(self.x_data, self.y_data)
        self.ax2.relim()
        self.ax2.autoscale_view()

        plt.pause(0.001)

    def hold(self) -> None:
        """Block so the live window stays open after the run."""
        plt.ioff()
        plt.show()
