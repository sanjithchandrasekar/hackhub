"""
download_roads.py
=================
Downloads the ENTIRE Tamil Nadu road network from OpenStreetMap using OSMNX.
Saves output as:
  - data/osm/tamilnadu_roads.graphml   (full graph for routing)
  - data/osm/tamilnadu_nodes.gpkg      (node GeoPackage)
  - data/osm/tamilnadu_edges.gpkg      (edge GeoPackage)

Strategy: Download district by district (38 districts) then merge.
This avoids timeout/memory issues with a single large query.

Usage:
    python scripts/download_roads.py                  # all 38 districts
    python scripts/download_roads.py --district Chennai  # single district
    python scripts/download_roads.py --full-state        # one query (slow)
"""

import os
import sys
import argparse
import time
import pickle
import logging

import osmnx as ox
import networkx as nx

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("download_roads.log")]
)
log = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OSM_DIR    = os.path.join(BASE_DIR, "data", "osm")
GRAPHML    = os.path.join(OSM_DIR, "tamilnadu_roads.graphml")
CACHE_PKL  = os.path.join(OSM_DIR, "tamilnadu_roads.pkl")
NODES_GPKG = os.path.join(OSM_DIR, "tamilnadu_nodes.gpkg")
EDGES_GPKG = os.path.join(OSM_DIR, "tamilnadu_edges.gpkg")

os.makedirs(OSM_DIR, exist_ok=True)

# ── All 38 Tamil Nadu Districts ──────────────────────────────────────────────
TN_DISTRICTS = [
    "Ariyalur, Tamil Nadu, India",
    "Chengalpattu, Tamil Nadu, India",
    "Chennai, Tamil Nadu, India",
    "Coimbatore, Tamil Nadu, India",
    "Cuddalore, Tamil Nadu, India",
    "Dharmapuri, Tamil Nadu, India",
    "Dindigul, Tamil Nadu, India",
    "Erode, Tamil Nadu, India",
    "Kallakurichi, Tamil Nadu, India",
    "Kancheepuram, Tamil Nadu, India",
    "Kanyakumari, Tamil Nadu, India",
    "Karur, Tamil Nadu, India",
    "Krishnagiri, Tamil Nadu, India",
    "Madurai, Tamil Nadu, India",
    "Mayiladuthurai, Tamil Nadu, India",
    "Nagapattinam, Tamil Nadu, India",
    "Namakkal, Tamil Nadu, India",
    "Nilgiris, Tamil Nadu, India",
    "Perambalur, Tamil Nadu, India",
    "Pudukkottai, Tamil Nadu, India",
    "Ramanathapuram, Tamil Nadu, India",
    "Ranipet, Tamil Nadu, India",
    "Salem, Tamil Nadu, India",
    "Sivaganga, Tamil Nadu, India",
    "Tenkasi, Tamil Nadu, India",
    "Thanjavur, Tamil Nadu, India",
    "Theni, Tamil Nadu, India",
    "Thoothukudi, Tamil Nadu, India",
    "Tiruchirappalli, Tamil Nadu, India",
    "Tirunelveli, Tamil Nadu, India",
    "Tirupattur, Tamil Nadu, India",
    "Tiruppur, Tamil Nadu, India",
    "Tiruvallur, Tamil Nadu, India",
    "Tiruvannamalai, Tamil Nadu, India",
    "Tiruvarur, Tamil Nadu, India",
    "Vellore, Tamil Nadu, India",
    "Villupuram, Tamil Nadu, India",
    "Virudhunagar, Tamil Nadu, India",
]

# Tamil Nadu bounding box (for full-state single-query mode)
TN_BBOX = {
    "north": 13.5,
    "south":  8.0,
    "east":  80.35,
    "west":  76.25,
}


def configure_osmnx():
    """Set OSMNX settings for large downloads."""
    ox.settings.use_cache = True
    ox.settings.cache_folder = os.path.join(BASE_DIR, "backend", "cache")
    ox.settings.timeout = 300          # 5-minute timeout per request
    ox.settings.max_query_area_size = 25e9   # allow large queries
    ox.settings.requests_timeout = 300
    os.makedirs(ox.settings.cache_folder, exist_ok=True)


def download_district(place_name: str, retry: int = 3) -> nx.MultiDiGraph | None:
    """Download road network for one district. Returns graph or None on failure."""
    for attempt in range(1, retry + 1):
        try:
            log.info(f"  Downloading: {place_name} (attempt {attempt}/{retry})")
            G = ox.graph_from_place(place_name, network_type="drive", simplify=True)
            nodes_count = len(G.nodes)
            edges_count = len(G.edges)
            log.info(f"  OK: {nodes_count} nodes, {edges_count} edges")
            return G
        except Exception as e:
            log.warning(f"  Attempt {attempt} failed: {e}")
            if attempt < retry:
                time.sleep(5 * attempt)
    log.error(f"  FAILED after {retry} attempts: {place_name}")
    return None


def download_by_district(districts: list[str]) -> nx.MultiDiGraph:
    """Download each district and compose into one graph."""
    combined = None
    failed = []

    for i, district in enumerate(districts, 1):
        log.info(f"\n[{i}/{len(districts)}] {district}")
        G = download_district(district)

        if G is None:
            failed.append(district)
            continue

        if combined is None:
            combined = G
        else:
            combined = nx.compose(combined, G)

        # Checkpoint every 5 districts
        if i % 5 == 0:
            _save_pickle(combined, CACHE_PKL)
            log.info(f"  Checkpoint saved ({len(combined.nodes)} nodes total)")

        time.sleep(1)   # be polite to OSM servers

    if failed:
        log.warning(f"\nFailed districts ({len(failed)}): {failed}")

    return combined


def download_full_state() -> nx.MultiDiGraph:
    """Download entire Tamil Nadu in one bbox query (faster but may fail)."""
    log.info("Downloading full Tamil Nadu state via bounding box...")
    log.info(f"  BBox: N={TN_BBOX['north']} S={TN_BBOX['south']} "
             f"E={TN_BBOX['east']} W={TN_BBOX['west']}")
    log.warning("  This may take 30-90 minutes and require 4+ GB RAM.")

    G = ox.graph_from_bbox(
        north=TN_BBOX["north"],
        south=TN_BBOX["south"],
        east=TN_BBOX["east"],
        west=TN_BBOX["west"],
        network_type="drive",
        simplify=True,
    )
    return G


def _save_pickle(G: nx.MultiDiGraph, path: str):
    with open(path, "wb") as f:
        pickle.dump(G, f)
    mb = os.path.getsize(path) / 1_048_576
    log.info(f"  Pickle saved: {path} ({mb:.1f} MB)")


def save_all(G: nx.MultiDiGraph):
    """Save graph as GraphML + GeoPackage files."""
    log.info("\nSaving outputs...")

    # 1. GraphML (for NetworkX / OSMNX routing)
    log.info(f"  Writing GraphML -> {GRAPHML}")
    ox.save_graphml(G, filepath=GRAPHML)
    mb = os.path.getsize(GRAPHML) / 1_048_576
    log.info(f"  GraphML saved ({mb:.1f} MB)")

    # 2. Pickle (fastest to reload)
    _save_pickle(G, CACHE_PKL)

    # 3. GeoDataFrames (for PostGIS import)
    log.info("  Converting to GeoDataFrames...")
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

    nodes_gdf.to_file(NODES_GPKG, driver="GPKG", layer="nodes")
    edges_gdf.to_file(EDGES_GPKG, driver="GPKG", layer="edges")
    log.info(f"  Nodes GeoPackage saved: {NODES_GPKG}")
    log.info(f"  Edges GeoPackage saved: {EDGES_GPKG}")


def print_summary(G: nx.MultiDiGraph):
    log.info("\n" + "=" * 55)
    log.info("  TAMIL NADU ROAD NETWORK - DOWNLOAD COMPLETE")
    log.info("=" * 55)
    log.info(f"  Total nodes (junctions) : {len(G.nodes):,}")
    log.info(f"  Total edges (road segs) : {len(G.edges):,}")
    log.info(f"  GraphML file : {GRAPHML}")
    log.info(f"  Pickle cache : {CACHE_PKL}")
    log.info(f"  Nodes GPKG   : {NODES_GPKG}")
    log.info(f"  Edges GPKG   : {EDGES_GPKG}")
    log.info("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="Download Tamil Nadu road network")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full-state",  action="store_true",
                      help="Download entire state in one bbox query")
    mode.add_argument("--district",    type=str,
                      help="Download a single district by name (e.g. Chennai)")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if GraphML already exists")
    args = parser.parse_args()

    if os.path.exists(GRAPHML) and not args.force:
        mb = os.path.getsize(GRAPHML) / 1_048_576
        log.info(f"Road network already downloaded ({mb:.1f} MB).")
        log.info("Use --force to re-download.")
        return

    configure_osmnx()

    start = time.time()

    if args.full_state:
        G = download_full_state()

    elif args.district:
        place = f"{args.district}, Tamil Nadu, India"
        G = download_district(place)
        if G is None:
            log.error("Download failed.")
            sys.exit(1)

    else:
        # Default: all 38 districts merged
        G = download_by_district(TN_DISTRICTS)

    if G is None or len(G.nodes) == 0:
        log.error("No data downloaded. Check internet connection.")
        sys.exit(1)

    save_all(G)
    print_summary(G)
    elapsed = (time.time() - start) / 60
    log.info(f"\nTotal time: {elapsed:.1f} minutes")


if __name__ == "__main__":
    main()
