#!/usr/bin/env python3
"""Run mandelbrot (optional) and visualize per-thread runtimes."""
from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="CSV file produced by ENABLE_THREAD_TIMING instrumentation",
    )
    parser.add_argument(
        "--invoke",
        action="store_true",
        help="Run the mandelbrot binary before plotting",
    )
    parser.add_argument(
        "--exe",
        type=Path,
        default=None,
        help="Path to mandelbrot executable (default: alongside this script)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Thread count to pass to mandelbrot when --invoke is set",
    )
    parser.add_argument(
        "--view",
        type=int,
        default=1,
        help="View index passed to mandelbrot when invoking",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="How many times to run the executable when invoking",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="Run id to visualize (default: use the latest run)",
    )
    parser.add_argument(
        "--sort",
        choices=["duration", "thread"],
        default="duration",
        help="Order bars by duration (highlight imbalance) or by thread id",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=None,
        help="Write the plot to this PNG path",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Arguments appended to mandelbrot command (prefix with --)",
    )
    args = parser.parse_args()

    if args.extra and args.extra[0] == "--":
        args.extra = args.extra[1:]

    csv_path = args.csv or (SCRIPT_DIR / "thread_timings.csv")
    if not csv_path.is_absolute():
        csv_path = (Path.cwd() / csv_path).resolve()
    args.csv = csv_path

    exe_path = args.exe or (SCRIPT_DIR / "mandelbrot")
    if not exe_path.is_absolute():
        exe_path = (Path.cwd() / exe_path).resolve()
    args.exe = exe_path

    return args


def load_records(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file {path} not found. Did you enable ENABLE_THREAD_TIMING?")

    with path.open() as fp:
        reader = csv.DictReader(fp)
        records = [row for row in reader]
    if not records:
        raise RuntimeError(f"CSV file {path} is empty.")
    return records


def pick_run(records: List[Dict[str, str]], requested: int | None) -> List[Dict[str, str]]:
    run_ids = sorted({int(r["run_id"]) for r in records})
    if requested is None:
        target = run_ids[-1]
    else:
        if requested not in run_ids:
            raise ValueError(f"run_id {requested} not present. Available: {run_ids}")
        target = requested
    subset = [r for r in records if int(r["run_id"]) == target]
    subset.sort(key=lambda r: int(r["thread_id"]))
    return subset


def prepare_data(run_records: List[Dict[str, str]], sort_mode: str) -> Dict[str, List[float]]:
    durations = [float(r["duration_ms"]) for r in run_records]
    thread_ids = [int(r["thread_id"]) for r in run_records]
    labels = [r["label"] for r in run_records]
    label = labels[0] if labels else ""

    paired = list(zip(thread_ids, durations))
    if sort_mode == "duration":
        paired.sort(key=lambda it: it[1], reverse=True)
    else:
        paired.sort(key=lambda it: it[0])

    sorted_threads, sorted_durations = zip(*paired)
    return {
        "threads": list(sorted_threads),
        "durations": list(sorted_durations),
        "label": label,
    }


def run_mandelbrot(exe: Path, threads: int | None, view: int, repeat: int, extra: List[str]) -> None:
    if not exe.exists():
        raise FileNotFoundError(f"Executable {exe} not found. Build mandelbrot first.")

    base_cmd = [str(exe)]
    if threads is not None:
        base_cmd += ["--threads", str(threads)]
    if view is not None:
        base_cmd += ["--view", str(view)]
    base_cmd += extra

    for i in range(repeat):
        print(f"[invoke] Run {i + 1}/{repeat}:", " ".join(base_cmd))
        subprocess.run(base_cmd, check=True)


def plot_distributions(data: Dict[str, List[float]], run_id: int, png_path: Path | None, show: bool) -> None:
    try:
        import matplotlib.pyplot as plt
        from matplotlib import cm, colors
    except ImportError as exc:
        raise RuntimeError("matplotlib is required for plotting") from exc

    threads = data["threads"]
    durations = data["durations"]
    label = data["label"]

    cmap = cm.get_cmap("magma")
    norm = colors.Normalize(vmin=min(durations), vmax=max(durations) + 1e-9)
    bar_colors = [cmap(norm(val)) for val in durations]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    y_pos = range(len(threads))
    ax.barh(list(y_pos), durations, color=bar_colors)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([f"T{tid}" for tid in threads])
    ax.invert_yaxis()

    mean_val = sum(durations) / len(durations)
    ax.axvline(mean_val, color="#2f4b7c", linestyle="--", linewidth=1.5, label="Mean time")

    max_duration = max(durations)
    offset = max_duration * 0.01
    for idx, duration in enumerate(durations):
        ax.text(duration + offset, idx, f"{duration:.2f} ms", va="center", fontsize=9)

    ax.set_xlabel("Thread runtime (ms)", fontsize=11)
    title = f"Thread runtime distribution (run {run_id})"
    if label:
        title += f"\n{label}"
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", frameon=False)
    fig.tight_layout()

    if png_path:
        fig.savefig(png_path, dpi=150)
        print(f"Saved plot to {png_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


def main() -> None:
    args = parse_args()
    if args.invoke:
        run_mandelbrot(args.exe, args.threads, args.view, args.repeat, args.extra)
    records = load_records(args.csv)
    run_records = pick_run(records, args.run_id)
    run_id = int(run_records[0]["run_id"])
    data = prepare_data(run_records, args.sort)
    plot_distributions(data, run_id, args.png, args.show)


if __name__ == "__main__":
    main()
