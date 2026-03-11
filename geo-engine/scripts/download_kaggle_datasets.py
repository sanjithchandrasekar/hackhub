"""
download_kaggle_datasets.py
----------------------------
Downloads all required datasets for the Intelligent Geospatial Engine
from Kaggle using the Kaggle API CLI.

PREREQUISITES
-------------
1. Install Kaggle API:
       pip install kaggle

2. Place your Kaggle API credentials at:
       Windows : C:\\Users\\<YourUser>\\.kaggle\\kaggle.json
       Linux   : ~/.kaggle/kaggle.json

   kaggle.json format:
       {"username": "your_username", "key": "your_api_key"}

3. Get your API key from:
       https://www.kaggle.com/settings  →  API  →  Create New Token

USAGE
-----
    python scripts/download_kaggle_datasets.py

    # Download only specific categories:
    python scripts/download_kaggle_datasets.py --only gps
    python scripts/download_kaggle_datasets.py --only roads
    python scripts/download_kaggle_datasets.py --only addresses
    python scripts/download_kaggle_datasets.py --only locations

    # Skip cleanup of zip files:
    python scripts/download_kaggle_datasets.py --keep-zips
"""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------
# Each entry:
#   key        : short category name used with --only flag
#   dataset    : Kaggle dataset slug  (owner/dataset-name)
#   dest       : destination folder relative to project root
#   description: human-readable label shown in progress output
# ---------------------------------------------------------------------------
DATASETS = [
    {
        "key": "gps",
        "dataset": "arashnic/tdrive-taxi-trajectories",
        "dest": "data/gps",
        "description": "GPS Taxi Trajectory Dataset (T-Drive)",
    },
    {
        "key": "roads",
        "dataset": "crailtap/street-network-dataset",
        "dest": "data/roads",
        "description": "Street / Road Network Dataset",
    },
    {
        "key": "addresses",
        "dataset": "openaddresses/openaddresses-us-sample",
        "dest": "data/addresses",
        "description": "Open Addresses – US Sample",
    },
    {
        "key": "locations",
        "dataset": "chetanism/foursquare-location-data",
        "dest": "data/locations",
        "description": "Foursquare Location / Check-in Dataset",
    },
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_kaggle_credentials() -> None:
    """Verify that kaggle.json credentials file exists."""
    cred_path = Path.home() / ".kaggle" / "kaggle.json"
    if not cred_path.exists():
        print(
            "\n[ERROR] Kaggle credentials not found.\n"
            f"  Expected location : {cred_path}\n"
            "  Steps to fix:\n"
            "    1. Go to https://www.kaggle.com/settings\n"
            "    2. API section → 'Create New Token'\n"
            "    3. Move the downloaded kaggle.json to the path above.\n"
        )
        sys.exit(1)
    print(f"[OK] Kaggle credentials found at {cred_path}")


def ensure_dir(path: str) -> Path:
    """Create directory if it doesn't exist and return a Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_dataset(dataset: str, dest: str) -> bool:
    """
    Run `kaggle datasets download` and return True on success.
    """
    cmd = [
        sys.executable, "-m", "kaggle",
        "datasets", "download",
        "-d", dataset,
        "-p", dest,
    ]
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"  [WARN] Download failed for dataset '{dataset}' (exit {result.returncode})")
        return False
    return True


def unzip_all(dest: str, keep_zips: bool = False) -> None:
    """Unzip every .zip file found inside *dest*."""
    dest_path = Path(dest)
    zip_files = list(dest_path.glob("*.zip"))

    if not zip_files:
        print("  No zip files found – skipping extraction.")
        return

    for zip_file in zip_files:
        print(f"  Extracting {zip_file.name} …")
        try:
            with zipfile.ZipFile(zip_file, "r") as zf:
                zf.extractall(dest_path)
            if not keep_zips:
                zip_file.unlink()
                print(f"  Removed {zip_file.name}")
        except zipfile.BadZipFile:
            print(f"  [WARN] {zip_file.name} is not a valid zip file – skipping.")


def print_summary(results: dict) -> None:
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    for key, (desc, success) in results.items():
        status = "[SUCCESS]" if success else "[FAILED] "
        print(f"  {status}  {desc}")
    print("=" * 60)
    failed = [k for k, (_, ok) in results.items() if not ok]
    if failed:
        print(
            f"\n  {len(failed)} dataset(s) failed to download.\n"
            "  Check your Kaggle credentials and dataset slugs.\n"
            "  You can retry individual categories with:\n"
            "    python scripts/download_kaggle_datasets.py --only <category>\n"
        )
    else:
        print("\n  All datasets downloaded successfully.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Kaggle datasets for the Intelligent Geospatial Engine."
    )
    parser.add_argument(
        "--only",
        choices=[d["key"] for d in DATASETS],
        default=None,
        help="Download only a specific dataset category.",
    )
    parser.add_argument(
        "--keep-zips",
        action="store_true",
        default=False,
        help="Keep zip files after extraction (default: delete after unzip).",
    )
    args = parser.parse_args()

    # Change working directory to project root (one level above scripts/)
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    print(f"[INFO] Working directory: {project_root}\n")

    check_kaggle_credentials()

    # Filter datasets if --only was provided
    targets = [d for d in DATASETS if args.only is None or d["key"] == args.only]

    results: dict = {}

    for entry in targets:
        key = entry["key"]
        desc = entry["description"]
        dataset = entry["dataset"]
        dest = entry["dest"]

        print(f"\n{'─' * 60}")
        print(f"[{key.upper()}]  {desc}")
        print(f"  Kaggle slug : {dataset}")
        print(f"  Destination : {dest}")
        print(f"{'─' * 60}")

        ensure_dir(dest)
        success = download_dataset(dataset, dest)

        if success:
            unzip_all(dest, keep_zips=args.keep_zips)

        results[key] = (desc, success)

    print_summary(results)


if __name__ == "__main__":
    main()
