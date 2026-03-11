"""
download_campus.py
==================
Extracts university, college, and campus boundary polygons for
Tamil Nadu from OpenStreetMap using OSMNX features API.

Saves:
  data/campus/tamilnadu_campuses.geojson   (main output)
  data/campus/tamilnadu_campuses.gpkg      (GeoPackage for PostGIS)
  data/campus/tamilnadu_campuses.csv       (tabular summary)

OSM tags extracted:
  amenity = university | college | school | research_institute
  building = university
  landuse = education

Usage:
    python scripts/download_campus.py
    python scripts/download_campus.py --district Chennai
    python scripts/download_campus.py --type university
"""

import os
import sys
import argparse
import time
import logging
import warnings

warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("download_campus.log")]
)
log = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPUS_DIR   = os.path.join(BASE_DIR, "data", "campus")
GEOJSON_OUT  = os.path.join(CAMPUS_DIR, "tamilnadu_campuses.geojson")
GPKG_OUT     = os.path.join(CAMPUS_DIR, "tamilnadu_campuses.gpkg")
CSV_OUT      = os.path.join(CAMPUS_DIR, "tamilnadu_campuses.csv")

os.makedirs(CAMPUS_DIR, exist_ok=True)

# ── All 38 Tamil Nadu Districts ──────────────────────────────────────────────
TN_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore",
    "Cuddalore", "Dharmapuri", "Dindigul", "Erode",
    "Kallakurichi", "Kancheepuram", "Kanyakumari", "Karur",
    "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam",
    "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga",
    "Tenkasi", "Thanjavur", "Theni", "Thoothukudi",
    "Tiruchirappalli", "Tirunelveli", "Tirupattur", "Tiruppur",
    "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore",
    "Villupuram", "Virudhunagar",
]

# ── OSM Feature Tags to Download ────────────────────────────────────────────
CAMPUS_TAGS = {
    "amenity": ["university", "college", "school", "research_institute"],
    "building": ["university"],
    "landuse": ["education"],
}


def configure_osmnx():
    ox.settings.use_cache = True
    ox.settings.cache_folder = os.path.join(BASE_DIR, "backend", "cache")
    ox.settings.timeout = 180
    os.makedirs(ox.settings.cache_folder, exist_ok=True)


def to_multipolygon(geom):
    """Ensure geometry is MultiPolygon for consistent storage."""
    if geom is None:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    # For GeometryCollections extract polygons
    try:
        polys = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
        if polys:
            merged = unary_union(polys)
            return to_multipolygon(merged)
    except Exception:
        pass
    return None


def assign_campus_type(row: pd.Series) -> str:
    """Derive a clean campus_type label from OSM tags."""
    amenity = str(row.get("amenity", "")).lower()
    building = str(row.get("building", "")).lower()
    landuse = str(row.get("landuse", "")).lower()

    if amenity == "university" or building == "university":
        return "university"
    if amenity == "college":
        return "college"
    if amenity == "school":
        return "school"
    if amenity == "research_institute":
        return "research"
    if landuse == "education":
        return "education_zone"
    return "campus"


def fetch_district_campuses(district: str, retry: int = 3) -> gpd.GeoDataFrame | None:
    """Fetch campus features for one district."""
    place = f"{district}, Tamil Nadu, India"

    for attempt in range(1, retry + 1):
        try:
            log.info(f"  Fetching: {place} (attempt {attempt})")
            gdf = ox.features_from_place(place, tags=CAMPUS_TAGS)

            # Keep only polygon features (campus boundaries)
            gdf = gdf[gdf.geometry.geom_type.isin(
                ["Polygon", "MultiPolygon", "GeometryCollection"]
            )].copy()

            if gdf.empty:
                log.info(f"  No campus polygons found in {district}")
                return gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

            log.info(f"  Found {len(gdf)} campus features in {district}")
            return gdf

        except Exception as e:
            log.warning(f"  Attempt {attempt} failed: {e}")
            if attempt < retry:
                time.sleep(4 * attempt)

    log.error(f"  FAILED: {place}")
    return None


def clean_and_enrich(gdf: gpd.GeoDataFrame, district: str) -> gpd.GeoDataFrame:
    """Standardise columns and compute derived fields."""
    keep_cols = ["geometry", "name", "amenity", "building",
                 "landuse", "operator", "website"]

    # Only keep columns that exist
    available = [c for c in keep_cols if c in gdf.columns]
    gdf = gdf[available].copy()

    # Fill missing columns
    for col in keep_cols:
        if col not in gdf.columns:
            gdf[col] = None

    # Rename
    gdf.rename(columns={"name": "campus_name"}, inplace=True)

    # Fill unnamed features
    gdf["campus_name"] = gdf["campus_name"].fillna("Unnamed Campus")

    # Campus type
    gdf["campus_type"] = gdf.apply(assign_campus_type, axis=1)

    # District / state
    gdf["district"] = district
    gdf["state"]    = "Tamil Nadu"
    gdf["country"]  = "India"

    # Force MultiPolygon
    gdf["geometry"] = gdf["geometry"].apply(to_multipolygon)
    gdf = gdf[gdf["geometry"].notna()].copy()

    # Area in sq metres (use projected CRS for accuracy)
    try:
        projected = gdf.to_crs("EPSG:32644")   # UTM zone 44N covers Tamil Nadu
        gdf["area_sqm"] = projected.geometry.area.round(2)
    except Exception:
        gdf["area_sqm"] = 0.0

    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf


def download_all_districts(districts: list[str]) -> gpd.GeoDataFrame:
    """Download campuses for every district and merge."""
    all_gdfs = []
    failed   = []

    for i, district in enumerate(districts, 1):
        log.info(f"\n[{i}/{len(districts)}] {district}")
        gdf = fetch_district_campuses(district)

        if gdf is None:
            failed.append(district)
            continue

        if not gdf.empty:
            cleaned = clean_and_enrich(gdf, district)
            all_gdfs.append(cleaned)

        time.sleep(1)   # polite rate limiting

    if failed:
        log.warning(f"\nFailed districts: {failed}")

    if not all_gdfs:
        log.error("No campus data downloaded!")
        sys.exit(1)

    merged = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs="EPSG:4326")
    return merged


def remove_duplicates(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Remove duplicate campuses based on OSM ID or overlapping geometry."""
    before = len(gdf)

    # Drop by exact OSM ID duplicates if column exists
    if "osmid" in gdf.columns:
        gdf = gdf.drop_duplicates(subset=["osmid"], keep="first")

    # Drop by name + district
    gdf = gdf.drop_duplicates(
        subset=["campus_name", "district"], keep="first"
    )

    after = len(gdf)
    if before != after:
        log.info(f"  Removed {before - after} duplicates")
    return gdf.reset_index(drop=True)


def save_all(gdf: gpd.GeoDataFrame):
    """Save to GeoJSON, GeoPackage, and CSV."""
    log.info(f"\nSaving {len(gdf)} campuses...")

    # GeoJSON
    gdf.to_file(GEOJSON_OUT, driver="GeoJSON")
    mb = os.path.getsize(GEOJSON_OUT) / 1_048_576
    log.info(f"  GeoJSON saved: {GEOJSON_OUT} ({mb:.2f} MB)")

    # GeoPackage
    gdf.to_file(GPKG_OUT, driver="GPKG", layer="campuses")
    log.info(f"  GeoPackage saved: {GPKG_OUT}")

    # CSV (without geometry)
    csv_df = gdf.drop(columns=["geometry"])
    csv_df.to_csv(CSV_OUT, index=False, encoding="utf-8")
    log.info(f"  CSV saved: {CSV_OUT}")


def print_summary(gdf: gpd.GeoDataFrame):
    log.info("\n" + "=" * 55)
    log.info("  TAMIL NADU CAMPUS DATA - DOWNLOAD COMPLETE")
    log.info("=" * 55)
    log.info(f"  Total campuses : {len(gdf)}")
    log.info(f"  By type:")
    for t, cnt in gdf["campus_type"].value_counts().items():
        log.info(f"    {t:<25}: {cnt}")
    log.info(f"\n  Top 5 districts by campus count:")
    for d, cnt in gdf["district"].value_counts().head(5).items():
        log.info(f"    {d:<25}: {cnt}")
    log.info(f"\n  GeoJSON : {GEOJSON_OUT}")
    log.info(f"  GPKG    : {GPKG_OUT}")
    log.info(f"  CSV     : {CSV_OUT}")
    log.info("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="Download Tamil Nadu campus boundaries")
    parser.add_argument("--district", type=str,
                        help="Download a single district (e.g. Chennai)")
    parser.add_argument("--type", type=str, default=None,
                        help="Filter by campus type after download")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if output already exists")
    args = parser.parse_args()

    if os.path.exists(GEOJSON_OUT) and not args.force:
        gdf = gpd.read_file(GEOJSON_OUT)
        log.info(f"Campus data already exists ({len(gdf)} campuses). Use --force to re-download.")
        print_summary(gdf)
        return

    configure_osmnx()

    start = time.time()

    if args.district:
        gdf_raw = fetch_district_campuses(args.district)
        if gdf_raw is None or gdf_raw.empty:
            log.error(f"No data for {args.district}")
            sys.exit(1)
        gdf = clean_and_enrich(gdf_raw, args.district)
    else:
        gdf = download_all_districts(TN_DISTRICTS)

    gdf = remove_duplicates(gdf)

    if args.type:
        gdf = gdf[gdf["campus_type"] == args.type]
        log.info(f"Filtered to type '{args.type}': {len(gdf)} campuses")

    save_all(gdf)
    print_summary(gdf)

    elapsed = (time.time() - start) / 60
    log.info(f"\nTotal time: {elapsed:.1f} minutes")


if __name__ == "__main__":
    main()
