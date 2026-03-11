"""
prepare_datasets.py
--------------------
Loads, cleans, and normalises all raw datasets downloaded by
download_kaggle_datasets.py, then writes processed CSVs to data/processed/.

USAGE
-----
    # Process all categories:
    python scripts/prepare_datasets.py

    # Process only one category:
    python scripts/prepare_datasets.py --only gps
    python scripts/prepare_datasets.py --only roads
    python scripts/prepare_datasets.py --only addresses
    python scripts/prepare_datasets.py --only locations

OUTPUT
------
    data/processed/gps_clean.csv
    data/processed/roads_clean.csv
    data/processed/addresses_clean.csv
    data/processed/locations_clean.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIRS = {
    "gps":       PROJECT_ROOT / "data" / "gps",
    "roads":     PROJECT_ROOT / "data" / "roads",
    "addresses": PROJECT_ROOT / "data" / "addresses",
    "locations": PROJECT_ROOT / "data" / "locations",
}
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Candidate column names for latitude / longitude (case-insensitive)
LAT_CANDIDATES  = ["latitude",  "lat",  "y",  "lat_deg"]
LON_CANDIDATES  = ["longitude", "lon",  "lng", "long", "x", "lon_deg"]


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def find_csv_files(directory: Path) -> list[Path]:
    """Recursively find all CSV files in *directory*."""
    return sorted(directory.rglob("*.csv"))


def load_csv(path: Path) -> Optional[pd.DataFrame]:
    """Load a CSV file with error handling. Returns None on failure."""
    try:
        df = pd.read_csv(path, low_memory=False)
        print(f"    Loaded  {path.name}  ({len(df):,} rows × {len(df.columns)} cols)")
        return df
    except Exception as exc:
        print(f"    [WARN] Could not read {path.name}: {exc}")
        return None


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase all column names and strip surrounding whitespace."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def detect_coord_columns(df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
    """
    Return (lat_col, lon_col) by scanning column names against known candidates.
    Returns (None, None) if coordinate columns cannot be found.
    """
    cols = set(df.columns)
    lat_col = next((c for c in LAT_CANDIDATES if c in cols), None)
    lon_col = next((c for c in LON_CANDIDATES if c in cols), None)
    return lat_col, lon_col


def coerce_coordinates(df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    """
    Convert lat/lon columns to float64.
    Rows with non-parseable or out-of-range values are dropped.
    """
    for col in (lat_col, lon_col):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=[lat_col, lon_col])

    # Enforce geographic bounds
    df = df[
        df[lat_col].between(-90.0, 90.0) &
        df[lon_col].between(-180.0, 180.0)
    ]
    dropped = before - len(df)
    if dropped:
        print(f"    Dropped {dropped:,} rows with invalid coordinates.")
    return df


def drop_high_null_columns(df: pd.DataFrame, threshold: float = 0.9) -> pd.DataFrame:
    """Drop columns where more than *threshold* fraction of values are null."""
    null_frac = df.isnull().mean()
    to_drop = null_frac[null_frac > threshold].index.tolist()
    if to_drop:
        print(f"    Dropping {len(to_drop)} high-null columns: {to_drop}")
        df = df.drop(columns=to_drop)
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        print(f"    Dropped {dropped:,} duplicate rows.")
    return df


def save_processed(df: pd.DataFrame, name: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{name}_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"    Saved  → {out_path}  ({len(df):,} rows)")
    return out_path


# ---------------------------------------------------------------------------
# Category-specific processors
# ---------------------------------------------------------------------------

def process_gps(raw_dir: Path) -> Optional[pd.DataFrame]:
    """
    GPS taxi trajectory data.
    Expected columns: id/taxi_id, datetime/timestamp, longitude, latitude
    Multiple small CSV files are concatenated into one dataframe.
    """
    csv_files = find_csv_files(raw_dir)
    if not csv_files:
        print("    [SKIP] No CSV files found in data/gps/")
        return None

    frames: list[pd.DataFrame] = []
    for f in csv_files[:500]:          # cap at 500 files for large datasets
        df = load_csv(f)
        if df is not None:
            frames.append(df)

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = normalise_columns(df)
    df = drop_high_null_columns(df)

    # T-Drive format: no header → assign names
    if df.shape[1] == 4 and not {"latitude", "longitude"}.issubset(set(df.columns)):
        df.columns = ["taxi_id", "timestamp", "longitude", "latitude"]

    lat_col, lon_col = detect_coord_columns(df)
    if lat_col and lon_col:
        df = coerce_coordinates(df, lat_col, lon_col)

    # Normalise timestamp column if present
    for ts_col in ("timestamp", "datetime", "time", "date_time"):
        if ts_col in df.columns:
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
            df = df.dropna(subset=[ts_col])
            break

    df = drop_duplicates(df)
    return df


def process_roads(raw_dir: Path) -> Optional[pd.DataFrame]:
    """
    Road / street network dataset.
    Expected columns vary; we look for geometry or lat/lon pairs.
    """
    csv_files = find_csv_files(raw_dir)
    if not csv_files:
        print("    [SKIP] No CSV files found in data/roads/")
        return None

    frames: list[pd.DataFrame] = []
    for f in csv_files:
        df = load_csv(f)
        if df is not None:
            frames.append(df)

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = normalise_columns(df)
    df = drop_high_null_columns(df)
    df = df.dropna(how="all")
    df = drop_duplicates(df)

    # Coerce coordinates if present
    lat_col, lon_col = detect_coord_columns(df)
    if lat_col and lon_col:
        df = coerce_coordinates(df, lat_col, lon_col)

    return df


def process_addresses(raw_dir: Path) -> Optional[pd.DataFrame]:
    """
    Address / geocoding dataset.
    Expected columns: number, street, city, region, postcode, lat, lon
    """
    csv_files = find_csv_files(raw_dir)
    if not csv_files:
        print("    [SKIP] No CSV files found in data/addresses/")
        return None

    frames: list[pd.DataFrame] = []
    for f in csv_files:
        df = load_csv(f)
        if df is not None:
            frames.append(df)

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = normalise_columns(df)
    df = drop_high_null_columns(df)

    # Fill missing address components with empty string
    text_cols = [c for c in ("number", "street", "city", "region", "postcode") if c in df.columns]
    df[text_cols] = df[text_cols].fillna("").astype(str).apply(lambda s: s.str.strip())

    lat_col, lon_col = detect_coord_columns(df)
    if lat_col and lon_col:
        df = coerce_coordinates(df, lat_col, lon_col)

    df = drop_duplicates(df)
    return df


def process_locations(raw_dir: Path) -> Optional[pd.DataFrame]:
    """
    Foursquare / check-in location dataset.
    Expected columns: user_id, venue_id, venue_category, latitude, longitude,
                      timezone_offset, utc_time
    """
    csv_files = find_csv_files(raw_dir)
    if not csv_files:
        print("    [SKIP] No CSV files found in data/locations/")
        return None

    frames: list[pd.DataFrame] = []
    for f in csv_files:
        df = load_csv(f)
        if df is not None:
            frames.append(df)

    if not frames:
        return None

    df = pd.concat(frames, ignore_index=True)
    df = normalise_columns(df)
    df = drop_high_null_columns(df)

    # Detect and parse timestamp
    for ts_col in ("utc_time", "timestamp", "datetime", "checkin_time"):
        if ts_col in df.columns:
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
            df = df.dropna(subset=[ts_col])
            break

    lat_col, lon_col = detect_coord_columns(df)
    if lat_col and lon_col:
        df = coerce_coordinates(df, lat_col, lon_col)

    df = drop_duplicates(df)
    return df


# ---------------------------------------------------------------------------
# Processor registry
# ---------------------------------------------------------------------------

PROCESSORS = {
    "gps":       process_gps,
    "roads":     process_roads,
    "addresses": process_addresses,
    "locations": process_locations,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean and prepare Kaggle datasets for the Geospatial Engine."
    )
    parser.add_argument(
        "--only",
        choices=list(PROCESSORS.keys()),
        default=None,
        help="Process only a specific dataset category.",
    )
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    targets = (
        {args.only: PROCESSORS[args.only]}
        if args.only
        else PROCESSORS
    )

    results: dict[str, bool] = {}

    for key, processor_fn in targets.items():
        raw_dir = RAW_DIRS[key]
        print(f"\n{'─' * 60}")
        print(f"[{key.upper()}]  Processing {raw_dir}")
        print(f"{'─' * 60}")

        if not raw_dir.exists() or not any(raw_dir.rglob("*.csv")):
            print(f"  [SKIP] No CSV data found in {raw_dir}")
            print(f"         Run download_kaggle_datasets.py --only {key} first.")
            results[key] = False
            continue

        df = processor_fn(raw_dir)

        if df is None or df.empty:
            print(f"  [WARN] No usable data produced for '{key}'.")
            results[key] = False
            continue

        print(f"  Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
        save_processed(df, key)
        results[key] = True

    # Summary
    print(f"\n{'=' * 60}")
    print("PROCESSING SUMMARY")
    print(f"{'=' * 60}")
    for key, ok in results.items():
        status = "[OK]    " if ok else "[SKIP]  "
        dest   = PROCESSED_DIR / f"{key}_clean.csv"
        print(f"  {status}  {key:12s}  →  {dest if ok else 'not produced'}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
