"""Download the World Bank WDI CSV archive and extract WDICSV.csv.

The raw CSV is intentionally not tracked in Git because it exceeds GitHub's
normal file-size limit.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile


WDI_ZIP_URL = "https://databank.worldbank.org/data/download/WDI_CSV.zip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and extract World Bank WDI data.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / "WDI_CSV.zip"
    csv_path = args.output_dir / "WDICSV.csv"

    print(f"Downloading {WDI_ZIP_URL}")
    urlretrieve(WDI_ZIP_URL, archive_path)

    with ZipFile(archive_path) as archive:
        archive.extract("WDICSV.csv", args.output_dir)

    print(f"Extracted {csv_path}")
    print(f"Archive retained at {archive_path}")


if __name__ == "__main__":
    main()
