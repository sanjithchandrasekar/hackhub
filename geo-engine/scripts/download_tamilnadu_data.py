"""
download_tamilnadu_data.py
---------------------------
Downloads Tamil Nadu road network and places data from Geofabrik (OpenStreetMap).
Converts shapefiles to CSV for use in the GeoEngine project.

USAGE
-----
    python scripts/download_tamilnadu_data.py
"""

from __future__ import annotations
import os, sys
from pathlib import Path
import requests
import pandas as pd

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
ROADS_DIR     = PROJECT_ROOT / "data" / "roads"
ADDR_DIR      = PROJECT_ROOT / "data" / "addresses"
ROADS_DIR.mkdir(parents=True, exist_ok=True)
ADDR_DIR.mkdir(parents=True, exist_ok=True)

TN_ROADS_CSV  = ROADS_DIR / "tamilnadu_roads.csv"
TN_ADDR_CSV   = ADDR_DIR  / "tamilnadu_addresses.csv"

# Overpass API – query major roads inside Tamil Nadu bounding box
# bbox: south, west, north, east
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:90][bbox:8.0,76.2,13.6,80.4];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"];
);
out center tags;
"""

# Tamil Nadu district headquarters with coordinates
TN_DISTRICTS = [
    ("Chennai",       13.0827, 80.2707), ("Coimbatore",   11.0168, 76.9558),
    ("Madurai",       9.9252,  78.1198), ("Tiruchirappalli", 10.7905, 78.7047),
    ("Salem",         11.6643, 78.1460), ("Tirunelveli",  8.7139,  77.7567),
    ("Vellore",       12.9165, 79.1325), ("Erode",        11.3410, 77.7172),
    ("Tiruppur",      11.1085, 77.3411), ("Dindigul",     10.3673, 77.9803),
    ("Thanjavur",     10.7870, 79.1378), ("Ranipet",      12.9228, 79.3333),
    ("Thoothukudi",    8.7642, 78.1348), ("Nagercoil",     8.1784, 77.4346),
    ("Cuddalore",     11.7480, 79.7714), ("Kanchipuram",  12.8185, 79.6947),
    ("Villupuram",    11.9401, 79.4861), ("Nagapattinam",  10.7672, 79.8449),
    ("Sivaganga",      9.8477, 78.4802), ("Ramanathapuram", 9.3762, 78.8309),
    ("Virudhunagar",   9.5850, 77.9629), ("Theni",        10.0104, 77.4767),
    ("Krishnagiri",   12.5186, 78.2137), ("Dharmapuri",   12.1277, 78.1580),
    ("Namakkal",      11.2189, 78.1674), ("Karur",        10.9601, 78.0766),
    ("Perambalur",    11.2333, 78.8833), ("Ariyalur",     11.1333, 79.0667),
    ("Pudukkottai",   10.3833, 78.8167), ("Tiruvarur",    10.7714, 79.6384),
    ("Nilgiris",      11.4916, 76.7337), ("Tiruvannamalai", 12.2253, 79.0747),
    ("Kallakurichi",  11.7381, 78.9620), ("Chengalpattu",  12.6920, 79.9770),
    ("Tenkasi",        8.9596, 77.3152), ("Tirupathur",   12.4961, 78.5630),
    ("Mayiladuthurai", 11.1000, 79.6500), ("Viruthachalam", 11.5200, 79.3100),
]


def fetch_overpass_roads(query: str, out_csv: Path) -> int:
    """Query Overpass API for Tamil Nadu roads and save to CSV."""
    print("  Querying Overpass API for Tamil Nadu roads …")
    print("  (This may take 30–90 seconds)")
    try:
        r = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=120,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
    except Exception as exc:
        print(f"  [ERROR] Overpass query failed: {exc}")
        return 0

    data = r.json()
    elements = data.get("elements", [])
    print(f"  Received {len(elements):,} road elements from Overpass API")

    rows = []
    for el in elements:
        if el.get("type") != "way":
            continue
        tags   = el.get("tags", {})
        center = el.get("center", {})
        rows.append({
            "osm_id":    el.get("id"),
            "name":      tags.get("name", tags.get("name:en", "")),
            "highway":   tags.get("highway", ""),
            "maxspeed":  tags.get("maxspeed", ""),
            "oneway":    tags.get("oneway", "no"),
            "ref":       tags.get("ref", ""),
            "latitude":  center.get("lat"),
            "longitude": center.get("lon"),
        })

    if not rows:
        print("  [WARN] No road data returned.")
        return 0

    df = pd.DataFrame(rows).dropna(subset=["latitude", "longitude"])
    df.to_csv(out_csv, index=False)
    print(f"  Saved {len(df):,} Tamil Nadu road segments → {out_csv}")
    return len(df)


def generate_tn_addresses(out_csv: Path) -> int:
    """Generate Tamil Nadu–specific synthetic address dataset."""
    import random, numpy as np
    random.seed(42);  np.random.seed(42)

    streets = [
        "Anna Salai", "Rajaji Salai", "Mount Road", "GST Road", "NH 44",
        "NH 48", "NH 66", "NH 83", "Poonamallee High Rd", "Velachery Rd",
        "Kamarajar Salai", "Jawaharlal Nehru Rd", "EVR Salai", "Arcot Rd",
        "Tambaram Rd", "Trichy Rd", "Coimbatore Bypass", "Palani Rd",
        "Salem Bye Pass", "Madurai South St",
    ]
    types = ["Street", "Road", "Nagar", "Colony", "Layout", "Cross", "Main"]

    rows = []
    n    = 50_000
    for _ in range(n):
        city, base_lat, base_lon = random.choice(
            [(d[0], d[1], d[2]) for d in TN_DISTRICTS]
        )
        lat = base_lat + np.random.normal(0, 0.04)
        lon = base_lon + np.random.normal(0, 0.04)
        rows.append({
            "number":    random.randint(1, 999),
            "street":    f"{random.choice(streets)} {random.choice(types)}",
            "city":      city,
            "region":    "Tamil Nadu",
            "postcode":  str(random.randint(600001, 643220)),
            "latitude":  round(np.clip(lat, 8.0, 13.6), 6),
            "longitude": round(np.clip(lon, 76.2, 80.4), 6),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"  Saved {len(df):,} Tamil Nadu address records → {out_csv}")
    return len(df)


def main() -> None:
    os.chdir(PROJECT_ROOT)
    print("=" * 60)
    print(" Tamil Nadu Data Downloader")
    print("=" * 60)

    # Step 1 – Roads via Overpass API
    print("\n[ROADS] Tamil Nadu Major Roads (Overpass API / OSM)")
    print("-" * 60)
    road_count = fetch_overpass_roads(OVERPASS_QUERY, TN_ROADS_CSV)

    # Step 2 – Tamil Nadu addresses (synthetic but TN-specific)
    print("\n[ADDRESSES] Tamil Nadu Address Dataset")
    print("-" * 60)
    addr_count = generate_tn_addresses(TN_ADDR_CSV)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Roads     : {road_count:,} segments  →  {TN_ROADS_CSV.name}")
    print(f"  Addresses : {addr_count:,} records   →  {TN_ADDR_CSV.name}")
    print("=" * 60)
    if road_count == 0:
        print("\n  Roads download failed. Check your internet connection and retry.")


if __name__ == "__main__":
    main()
