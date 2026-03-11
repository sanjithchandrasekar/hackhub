"""
download_public_datasets.py
----------------------------
Downloads all required datasets from FREE PUBLIC sources.
No Kaggle account needed.

Sources used:
  GPS       – GeoLife GPS Trajectories (Microsoft Research)
  Roads     – Liechtenstein OSM extract (Geofabrik / OpenStreetMap)
  Addresses – Synthetic sample (lat/lon + address fields)
  Locations – Brightkite check-ins (Stanford SNAP)

USAGE
-----
    python scripts/download_public_datasets.py
    python scripts/download_public_datasets.py --only gps
    python scripts/download_public_datasets.py --only roads
    python scripts/download_public_datasets.py --only addresses
    python scripts/download_public_datasets.py --only locations
"""

from __future__ import annotations

import argparse
import gzip
import io
import os
import random
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data"

DIRS = {
    "gps":       DATA_DIR / "gps",
    "roads":     DATA_DIR / "roads",
    "addresses": DATA_DIR / "addresses",
    "locations": DATA_DIR / "locations",
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, label: str = "", resume: bool = False) -> bool:
    """Stream-download *url* to *dest*. Supports HTTP range resume. Returns True on success."""
    label = label or dest.name
    existing = dest.stat().st_size if (resume and dest.exists()) else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    if existing:
        print(f"  Resuming {label} from {existing >> 20} MB …")
    else:
        print(f"  Downloading {label} …")
    try:
        with requests.get(url, stream=True, timeout=180, headers=headers) as r:
            r.raise_for_status()
            total = existing + int(r.headers.get("content-length", 0))
            downloaded = existing
            mode = "ab" if existing else "wb"
            with open(dest, mode) as f:
                for chunk in r.iter_content(chunk_size=1 << 20):  # 1 MB
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r    {pct:.1f}%  ({downloaded >> 20} MB / {total >> 20} MB)", end="", flush=True)
        print(f"\r    Done – {downloaded >> 20} MB saved to {dest}")
        return True
    except Exception as exc:
        print(f"\n  [ERROR] {exc}")
        return False


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    print(f"  Extracting {zip_path.name} …")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    zip_path.unlink()
    print(f"  Extracted → {dest_dir}")


# ---------------------------------------------------------------------------
# 1. GPS – GeoLife Trajectories (Microsoft Research)
#    PLT files → CSV with columns: taxi_id, timestamp, longitude, latitude
# ---------------------------------------------------------------------------

GEOLIFE_URL = (
    "https://download.microsoft.com/download/F/4/8/"
    "F4894AA5-FDBC-481E-9285-D5F8C4C4F039/"
    "Geolife%20GPS%20Trajectories.zip"
)

def _generate_synthetic_gps() -> bool:
    """Fallback: generate realistic synthetic GPS trajectory data."""
    print("  Generating synthetic GPS trajectory data (100 k points) …")
    random.seed(0)
    np.random.seed(0)

    # Simulate 50 taxis in Beijing area
    cities = [
        (39.9042, 116.4074, "Beijing"),
        (31.2304, 121.4737, "Shanghai"),
        (22.3193, 114.1694, "HongKong"),
        (23.1291, 113.2644, "Guangzhou"),
        (30.5728, 104.0668, "Chengdu"),
    ]
    rows = []
    n_taxis = 50
    n_points_per_taxi = 2000
    for taxi_id in range(1, n_taxis + 1):
        city_lat, city_lon, _ = random.choice(cities)
        lat = city_lat + np.random.uniform(-0.1, 0.1)
        lon = city_lon + np.random.uniform(-0.1, 0.1)
        ts = pd.Timestamp("2010-02-01")
        for _ in range(n_points_per_taxi):
            lat  += np.random.normal(0, 0.0005)
            lon  += np.random.normal(0, 0.0005)
            lat   = np.clip(lat,  -90,  90)
            lon   = np.clip(lon, -180, 180)
            ts   += pd.Timedelta(seconds=random.randint(10, 30))
            rows.append({
                "taxi_id":   taxi_id,
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "longitude": round(lon, 6),
                "latitude":  round(lat, 6),
            })
    df = pd.DataFrame(rows)
    out = DIRS["gps"] / "gps_trajectories.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df):,} synthetic GPS points → {out}")
    return True


def download_gps() -> bool:
    dest_dir = DIRS["gps"]
    zip_path = dest_dir / "geolife.zip"

    print("  Attempting GeoLife download from Microsoft Research …")
    ok = download_file(GEOLIFE_URL, zip_path, "GeoLife GPS Trajectories (~298 MB)")

    if ok:
        extract_zip(zip_path, dest_dir)
        print("  Converting PLT → CSV …")
        plt_files = list(dest_dir.rglob("*.plt"))
        print(f"  Found {len(plt_files):,} PLT files")
        rows = []
        for idx, plt_file in enumerate(plt_files):
            user_id = plt_file.parent.parent.name
            try:
                with open(plt_file, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[6:]
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) < 7:
                        continue
                    rows.append({
                        "user_id":   user_id,
                        "latitude":  parts[0],
                        "longitude": parts[1],
                        "timestamp": parts[5] + " " + parts[6],
                    })
            except Exception:
                pass
            if (idx + 1) % 500 == 0:
                print(f"    Processed {idx + 1:,} / {len(plt_files):,} files …", end="\r")
        df = pd.DataFrame(rows)
        df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])
        out = dest_dir / "gps_trajectories.csv"
        df.to_csv(out, index=False)
        print(f"\n  Saved {len(df):,} GPS points → {out}")
        return True

    # Fallback: generate synthetic data
    print("  GeoLife download unavailable – using synthetic GPS data instead.")
    return _generate_synthetic_gps()


# ---------------------------------------------------------------------------
# 2. Roads – Liechtenstein OSM extract (Geofabrik)
#    Shapefile → roads CSV with columns: osm_id, name, highway, geometry_wkt
# ---------------------------------------------------------------------------

ROADS_URL = "https://download.geofabrik.de/europe/liechtenstein-latest-free.shp.zip"

def download_roads() -> bool:
    dest_dir = DIRS["roads"]
    zip_path = dest_dir / "liechtenstein-roads.zip"

    ok = download_file(ROADS_URL, zip_path, "Liechtenstein OSM road network (~4 MB)")
    if not ok:
        return False

    extract_zip(zip_path, dest_dir)

    # Convert roads shapefile to CSV using geopandas
    try:
        import geopandas as gpd
        shp_files = list(dest_dir.rglob("gis_osm_roads_free_1.shp"))
        if not shp_files:
            shp_files = list(dest_dir.rglob("*.shp"))

        if not shp_files:
            print("  [WARN] No shapefile found after extraction.")
            return False

        print(f"  Loading shapefile: {shp_files[0].name} …")
        gdf = gpd.read_file(shp_files[0])

        # Convert to WGS-84 if needed
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Extract centroid lat/lon for each road segment
        gdf["latitude"]    = gdf.geometry.centroid.y
        gdf["longitude"]   = gdf.geometry.centroid.x
        gdf["geometry_wkt"] = gdf.geometry.apply(lambda g: g.wkt if g else None)

        cols = ["osm_id", "name", "fclass", "maxspeed", "oneway",
                "latitude", "longitude", "geometry_wkt"]
        cols = [c for c in cols if c in gdf.columns]
        df = pd.DataFrame(gdf[cols])

        out = dest_dir / "roads.csv"
        df.to_csv(out, index=False)
        print(f"  Saved {len(df):,} road segments → {out}")
        return True

    except ImportError:
        print("  [WARN] geopandas not available for shapefile conversion.")
        return False
    except Exception as exc:
        print(f"  [ERROR] Shapefile conversion failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# 3. Addresses – Synthetic sample dataset
#    Generates realistic-looking address records covering the globe
# ---------------------------------------------------------------------------

def download_addresses() -> bool:
    """Generate a 50,000-row synthetic address CSV (no download required)."""
    dest_dir = DIRS["addresses"]
    print("  Generating synthetic address dataset (50,000 records) …")

    random.seed(42)
    np.random.seed(42)

    street_types = ["St", "Ave", "Blvd", "Rd", "Ln", "Dr", "Way", "Ct", "Pl", "Terrace"]
    street_names = [
        "Main", "Oak", "Maple", "Cedar", "Pine", "Elm", "Washington",
        "Lincoln", "Park", "Lake", "Hill", "River", "Sunset", "Highland",
        "Forest", "Meadow", "Valley", "Ridge", "Willow", "Birch",
    ]
    cities = [
        ("New York",     "NY",  40.7128, -74.0060),
        ("Los Angeles",  "CA",  34.0522, -118.2437),
        ("Chicago",      "IL",  41.8781, -87.6298),
        ("Houston",      "TX",  29.7604, -95.3698),
        ("Phoenix",      "AZ",  33.4484, -112.0740),
        ("Philadelphia", "PA",  39.9526, -75.1652),
        ("San Antonio",  "TX",  29.4241, -98.4936),
        ("San Diego",    "CA",  32.7157, -117.1611),
        ("Dallas",       "TX",  32.7767, -96.7970),
        ("San Jose",     "CA",  37.3382, -121.8863),
    ]

    rows = []
    n = 50_000
    for _ in range(n):
        city, state, base_lat, base_lon = random.choice(cities)
        lat = base_lat + np.random.normal(0, 0.05)
        lon = base_lon + np.random.normal(0, 0.05)
        rows.append({
            "number":   random.randint(1, 9999),
            "street":   f"{random.choice(street_names)} {random.choice(street_types)}",
            "city":     city,
            "region":   state,
            "postcode": f"{random.randint(10000, 99999)}",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        })

    df = pd.DataFrame(rows)
    out = dest_dir / "addresses.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df):,} address records → {out}")
    return True


# ---------------------------------------------------------------------------
# 4. Locations – Brightkite check-ins (Stanford SNAP)
#    TSV: user_id, check-in_time, latitude, longitude, location_id
# ---------------------------------------------------------------------------

BRIGHTKITE_URL = "https://snap.stanford.edu/data/loc-brightkite_totalCheckins.txt.gz"

def download_locations() -> bool:
    dest_dir = DIRS["locations"]
    gz_path  = dest_dir / "brightkite.txt.gz"

    ok = download_file(BRIGHTKITE_URL, gz_path, "Brightkite check-ins – Stanford SNAP (~57 MB)", resume=True)
    if not ok:
        return False

    print("  Decompressing …")
    txt_path = dest_dir / "brightkite_checkins.txt"
    with gzip.open(gz_path, "rb") as f_in, open(txt_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    gz_path.unlink()

    print("  Converting to CSV …")
    df = pd.read_csv(
        txt_path,
        sep="\t",
        header=None,
        names=["user_id", "utc_time", "latitude", "longitude", "location_id"],
        on_bad_lines="skip",
    )
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)]

    out = dest_dir / "locations.csv"
    df.to_csv(out, index=False)
    txt_path.unlink()
    print(f"  Saved {len(df):,} check-in records → {out}")
    return True


# ---------------------------------------------------------------------------
# Registry & main
# ---------------------------------------------------------------------------

DOWNLOADERS = {
    "gps":       download_gps,
    "roads":     download_roads,
    "addresses": download_addresses,
    "locations": download_locations,
}

DESCRIPTIONS = {
    "gps":       "GeoLife GPS Trajectories (Microsoft Research)",
    "roads":     "Liechtenstein Road Network (Geofabrik / OSM)",
    "addresses": "Synthetic Address Dataset (50 k records)",
    "locations": "Brightkite Check-ins (Stanford SNAP)",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download public geospatial datasets (no Kaggle required)."
    )
    parser.add_argument(
        "--only",
        choices=list(DOWNLOADERS.keys()),
        default=None,
        help="Download only a specific category.",
    )
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    targets = (
        {args.only: DOWNLOADERS[args.only]}
        if args.only
        else DOWNLOADERS
    )

    results: dict[str, bool] = {}

    for key, fn in targets.items():
        print(f"\n{'─' * 60}")
        print(f"[{key.upper()}]  {DESCRIPTIONS[key]}")
        print(f"{'─' * 60}")
        results[key] = fn()

    print(f"\n{'=' * 60}")
    print("DOWNLOAD SUMMARY")
    print(f"{'=' * 60}")
    for key, ok in results.items():
        status = "[SUCCESS]" if ok else "[FAILED] "
        print(f"  {status}  {DESCRIPTIONS[key]}")
    print(f"{'=' * 60}\n")

    failed = [k for k, ok in results.items() if not ok]
    if failed:
        print(f"  {len(failed)} dataset(s) failed. Retry with --only <category>.\n")
    else:
        print("  All datasets ready. Run prepare_datasets.py to clean them.\n")


if __name__ == "__main__":
    main()
