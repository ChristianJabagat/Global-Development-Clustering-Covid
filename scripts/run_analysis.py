"""Command-line entry point for the EconClustering analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from econ_clustering import run_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the WDI country clustering analysis and export tables/figures."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_ROOT / "WDICSV.csv",
        help="Path to the World Development Indicators CSV file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Directory where analysis artifacts will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = run_analysis(args.data, args.output)
    print("Analysis complete. Key outputs:")
    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
