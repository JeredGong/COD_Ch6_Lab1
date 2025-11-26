#!/usr/bin/env python3
"""Run mandelbrot with varying thread counts and plot speedup curves."""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent

SPEEDUP_RE = re.compile(r"\((?P<speedup>[-+]?[0-9]*\.?[0-9]+)x speedup from (?P<threads>\d+) threads\)")
SERIAL_RE = re.compile(r"\[mandelbrot serial\]:\s*\[(?P<ms>[0-9.]+)\] ms")
THREAD_RE = re.compile(r"\[mandelbrot thread\]:\s*\[(?P<ms>[0-9.]+)\] ms")


def run_case(exe: Path, threads: int, view: int, extra_args: List[str]) -> Tuple[float, float, float]:
    cmd = [str(exe), "--threads", str(threads), "--view", str(view), *extra_args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stdout)
        sys.stderr.write(exc.stderr)
        raise

    output = result.stdout + result.stderr

    serial_match = SERIAL_RE.search(output)
    thread_match = THREAD_RE.search(output)
    speedup_match = SPEEDUP_RE.search(output)

    if not (serial_match and thread_match and speedup_match):
        raise RuntimeError("Failed to parse program output.\n" + output)

    serial_ms = float(serial_match.group("ms"))
    thread_ms = float(thread_match.group("ms"))
    speedup = float(speedup_match.group("speedup"))
    return serial_ms, thread_ms, speedup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe",
        type=Path,
        default=None,
        help="Path to mandelbrot executable (default: alongside this script)",
    )
    parser.add_argument(
        "--view",
        type=int,
        default=2,
        help="View index passed to the program (default: 2)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        nargs="*",
        default=[1, 2, 4, 6, 8, 12, 14, 16],
        help="Thread counts to evaluate",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Where to store raw measurements (default: script directory)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the plot window (requires matplotlib)",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=None,
        help="Optional path to save the plot as PNG",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Additional arguments to pass to the executable",
    )
    args = parser.parse_args()
    args.threads = sorted(set(args.threads))

    exe = args.exe or (SCRIPT_DIR / "mandelbrot")
    exe = exe.expanduser()
    if not exe.is_absolute():
        exe = (Path.cwd() / exe).resolve()
    args.exe = exe

    csv_path = args.csv or (SCRIPT_DIR / "speedup_view1.csv")
    csv_path = csv_path.expanduser()
    if not csv_path.is_absolute():
        csv_path = (Path.cwd() / csv_path).resolve()
    args.csv = csv_path

    return args


def try_plot(
    points: List[Tuple[int, float]],
    png_path: Path | None,
    show: bool,
    view_index: int,
) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping plot stage", file=sys.stderr)
        return

    plt.style.use("seaborn-v0_8-whitegrid")
    threads, speedups = zip(*points)
    threads = list(threads)
    speedups = list(speedups)

    baseline_threads = min(threads)
    baseline_speedup = speedups[threads.index(baseline_threads)]
    ideal_speedups = [baseline_speedup * (t / baseline_threads) for t in threads]

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.plot(threads, speedups, marker="o", linewidth=2.2, label="Measured speedup")
    ax.plot(
        threads,
        ideal_speedups,
        linestyle="--",
        linewidth=1.6,
        color="#7f7f7f",
        label="Ideal linear",
    )

    ax.set_title(
        f"Mandelbrot Speedup vs Threads (View {view_index})",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("Number of Threads", fontsize=11)
    ax.set_ylabel("Speedup", fontsize=11)
    ax.set_xticks(threads)
    max_y = max(max(speedups), max(ideal_speedups))
    ax.set_ylim(0, max_y * 1.15)
    ax.tick_params(axis="both", labelsize=10)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_facecolor("#f8f9fb")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for x, y in zip(threads, speedups):
        ax.annotate(
            f"{y:.2f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=9,
            color="#2f4b7c",
        )
    fig.tight_layout()

    if png_path:
        plt.savefig(png_path)
        print(f"Saved plot to {png_path}")

    if show:
        plt.show()
    else:
        plt.close()


def main() -> None:
    args = parse_args()

    if not args.exe.exists():
        sys.exit(f"Executable {args.exe} does not exist. Build mandelbrot first.")

    measurements = []
    for t in args.threads:
        serial_ms, thread_ms, speedup = run_case(args.exe, t, args.view, args.extra)
        measurements.append((t, serial_ms, thread_ms, speedup))
        print(
            f"threads={t:2d} serial={serial_ms:8.3f}ms threaded={thread_ms:8.3f}ms speedup={speedup:5.2f}"
        )

    with args.csv.open("w", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(["threads", "serial_ms", "thread_ms", "speedup"])
        writer.writerows(measurements)
    print(f"Wrote {args.csv}")

    speedup_points = [(t, s) for t, _, _, s in measurements]
    if args.png or args.show:
        try_plot(speedup_points, args.png, args.show, args.view)


if __name__ == "__main__":
    main()
