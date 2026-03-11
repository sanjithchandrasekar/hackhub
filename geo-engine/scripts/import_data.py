"""
import_data.py
=============
Reads all downloaded datasets and imports them into PostgreSQL (with PostGIS).

What it imports:
  1. Road nodes + edges from tamilnadu_roads.graphml  -> tables: nodes, roads
  2. Campus polygons from tamilnadu_campuses.geojson  -> table: campuses
  3. Address CSV from tamilnadu_addresses.csv          -> table: addresses

Prerequisites:
  1. PostgreSQL running with PostGIS enabled
  2. Database 'geo_engine' created
  3. Schema applied: psql -d geo_engine -f database/schema.sql
  4. .env file (or env vars) with DB credentials

Usage:
    python scripts/import_data.py                 # import everything
    python scripts/import_data.py --table roads   # import only roads
    python scripts/import_data.py --table campuses
    python scripts/import_data.py --table addresses
    python scripts/import_data.py --dry-run       # validate without inserting
"""

import os
import sys
import argparse
import logging
import time
from typing import Generator

import psycopg2
import psycopg2.extras
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import Point, LineString, MultiPolygon, Polygon
from shapely.wkb import dumps as wkb_dumps

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("import_data.log")]
)
log = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPHML_PATH = os.path.join(BASE_DIR, "data", "osm",    "tamilnadu_roads.graphml")
CAMPUS_PATH  = os.path.join(BASE_DIR, "data", "campus", "tamilnadu_campuses.geojson")
ADDRESS_PATH = os.path.join(BASE_DIR, "data", "address","tamilnadu_addresses.csv")

# ── Database configuration (reads from environment or .env) ─────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
except ImportError:
    pass

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME",     "geo_engine"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

BATCH_SIZE = 500   # rows per INSERT batch


# =============================================================================
# Database helpers
# =============================================================================

def get_connection():
    """Open a psycopg2 connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        log.error(f"Cannot connect to PostgreSQL: {e}")
        log.error("Check DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD env vars.")
        sys.exit(1)


def execute_sql(conn, sql: str, values=None):
    with conn.cursor() as cur:
        cur.execute(sql, values)


def batched(iterable, n: int) -> Generator:
    """Yield successive n-sized chunks."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch


def geom_to_wkb_hex(geom) -> str | None:
    """Convert Shapely geometry to hex-encoded WKB with SRID=4326."""
    if geom is None or geom.is_empty:
        return None
    try:
        return wkb_dumps(geom, hex=True, srid=4326, include_srid=True)
    except Exception:
        return None


# =============================================================================
# 1. IMPORT ROADS (nodes + edges from GraphML)
# =============================================================================

def import_roads(conn, dry_run: bool = False):
    """Load tamilnadu_roads.graphml into tables: nodes, roads."""

    if not os.path.exists(GRAPHML_PATH):
        log.error(f"GraphML file not found: {GRAPHML_PATH}")
        log.error("Run: python scripts/download_roads.py first.")
        return

    log.info("=" * 55)
    log.info("IMPORTING ROAD NETWORK")
    log.info("=" * 55)
    log.info(f"Loading GraphML: {GRAPHML_PATH}")

    start = time.time()
    G = ox.load_graphml(GRAPHML_PATH)

    total_nodes = len(G.nodes)
    total_edges = len(G.edges)
    log.info(f"Loaded graph: {total_nodes:,} nodes, {total_edges:,} edges")

    if dry_run:
        log.info("[DRY RUN] Road import validated. No data written.")
        return

    with conn.cursor() as cur:
        # ── Truncate existing data ──────────────────────────────────────────
        log.info("Truncating existing roads/nodes tables...")
        cur.execute("TRUNCATE TABLE geofence_events, route_cache, roads, nodes RESTART IDENTITY CASCADE")
        conn.commit()

        # ── Insert NODES ───────────────────────────────────────────────────
        log.info(f"Inserting {total_nodes:,} nodes...")
        node_sql = """
            INSERT INTO nodes (id, osmid, latitude, longitude, highway, ref, geometry)
            VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromWKB(decode(%s,'hex')))
            ON CONFLICT (id) DO NOTHING
        """
        node_rows = []
        for node_id, data in G.nodes(data=True):
            lat = data.get("y")
            lon = data.get("x")
            if lat is None or lon is None:
                continue
            geom_hex = geom_to_wkb_hex(Point(lon, lat))
            node_rows.append((
                node_id,
                data.get("osmid", node_id),
                lat,
                lon,
                data.get("highway"),
                data.get("ref"),
                geom_hex,
            ))

        inserted_nodes = 0
        for batch in batched(node_rows, BATCH_SIZE):
            psycopg2.extras.execute_batch(cur, node_sql, batch, page_size=BATCH_SIZE)
            inserted_nodes += len(batch)
            if inserted_nodes % 10000 == 0:
                log.info(f"  Nodes: {inserted_nodes:,}/{total_nodes:,}")
        conn.commit()
        log.info(f"  Nodes inserted: {inserted_nodes:,}")

        # ── Insert ROADS (edges) ────────────────────────────────────────────
        log.info(f"Inserting {total_edges:,} road segments...")
        road_sql = """
            INSERT INTO roads
              (source_node, target_node, osmid, name, highway, oneway,
               length_m, distance, maxspeed, lanes, geometry)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    ST_GeomFromWKB(decode(%s,'hex')))
        """
        road_rows = []
        for u, v, data in G.edges(data=True):
            # Build LineString from geometry or from node coordinates
            try:
                if "geometry" in data:
                    geom = data["geometry"]
                    if not isinstance(geom, LineString):
                        coords = list(geom.coords)
                        geom = LineString(coords)
                else:
                    n_u = G.nodes[u]
                    n_v = G.nodes[v]
                    geom = LineString([(n_u["x"], n_u["y"]), (n_v["x"], n_v["y"])])
            except Exception:
                continue

            geom_hex = geom_to_wkb_hex(geom)
            if geom_hex is None:
                continue

            length_m = data.get("length", 0)
            road_rows.append((
                int(u),
                int(v),
                data.get("osmid"),
                str(data.get("name", ""))[:255] if data.get("name") else None,
                data.get("highway"),
                bool(data.get("oneway", False)),
                float(length_m),
                round(float(length_m) / 1000, 4),
                str(data.get("maxspeed", ""))[:50] if data.get("maxspeed") else None,
                int(data["lanes"]) if str(data.get("lanes", "")).isdigit() else None,
                geom_hex,
            ))

        inserted_roads = 0
        for batch in batched(road_rows, BATCH_SIZE):
            psycopg2.extras.execute_batch(cur, road_sql, batch, page_size=BATCH_SIZE)
            inserted_roads += len(batch)
            if inserted_roads % 10000 == 0:
                log.info(f"  Roads: {inserted_roads:,}/{total_edges:,}")
        conn.commit()
        log.info(f"  Roads inserted: {inserted_roads:,}")

    elapsed = time.time() - start
    log.info(f"Road import complete in {elapsed:.1f}s")


# =============================================================================
# 2. IMPORT CAMPUSES
# =============================================================================

def to_multipolygon(geom) -> MultiPolygon | None:
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, MultiPolygon):
        return geom
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return None


def import_campuses(conn, dry_run: bool = False):
    """Load tamilnadu_campuses.geojson into table: campuses."""

    if not os.path.exists(CAMPUS_PATH):
        log.error(f"Campus file not found: {CAMPUS_PATH}")
        log.error("Run: python scripts/download_campus.py first.")
        return

    log.info("=" * 55)
    log.info("IMPORTING CAMPUS BOUNDARIES")
    log.info("=" * 55)

    gdf = gpd.read_file(CAMPUS_PATH)
    gdf = gdf.to_crs("EPSG:4326")

    log.info(f"Loaded {len(gdf)} campus features")

    if dry_run:
        log.info("[DRY RUN] Campus import validated. No data written.")
        return

    campus_sql = """
        INSERT INTO campuses
          (campus_name, campus_type, amenity, operator, website,
           district, area_sqm, boundary)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                ST_GeomFromWKB(decode(%s,'hex')))
    """

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE geofence_events, campuses RESTART IDENTITY CASCADE")
        conn.commit()

        campus_rows = []
        skipped = 0

        for _, row in gdf.iterrows():
            geom = to_multipolygon(row.geometry)
            if geom is None:
                skipped += 1
                continue

            geom_hex = geom_to_wkb_hex(geom)
            if geom_hex is None:
                skipped += 1
                continue

            campus_rows.append((
                str(row.get("campus_name", "Unknown"))[:255],
                str(row.get("campus_type", "campus"))[:100],
                str(row.get("amenity",     ""))[:100]  or None,
                str(row.get("operator",    ""))[:255]  or None,
                str(row.get("website",     ""))[:500]  or None,
                str(row.get("district",    ""))[:100]  or None,
                float(row.get("area_sqm",  0) or 0),
                geom_hex,
            ))

        for batch in batched(campus_rows, BATCH_SIZE):
            psycopg2.extras.execute_batch(cur, campus_sql, batch, page_size=BATCH_SIZE)
        conn.commit()

    log.info(f"  Campuses inserted: {len(campus_rows)}")
    if skipped:
        log.warning(f"  Skipped (invalid geometry): {skipped}")


# =============================================================================
# 3. IMPORT ADDRESSES
# =============================================================================

def import_addresses(conn, dry_run: bool = False):
    """Load tamilnadu_addresses.csv into table: addresses."""

    if not os.path.exists(ADDRESS_PATH):
        log.error(f"Address CSV not found: {ADDRESS_PATH}")
        log.error("Run: python scripts/load_address_dataset.py first.")
        return

    log.info("=" * 55)
    log.info("IMPORTING ADDRESSES")
    log.info("=" * 55)

    df = pd.read_csv(ADDRESS_PATH, dtype=str)
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    log.info(f"Loaded {len(df):,} address records")

    if dry_run:
        log.info("[DRY RUN] Address import validated. No data written.")
        return

    addr_sql = """
        INSERT INTO addresses
          (house_number, street, city, district, state, country,
           postcode, latitude, longitude, geometry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                ST_GeomFromWKB(decode(%s,'hex')))
    """

    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE addresses RESTART IDENTITY")
        conn.commit()

        addr_rows = []
        for _, row in df.iterrows():
            geom_hex = geom_to_wkb_hex(Point(row["longitude"], row["latitude"]))
            addr_rows.append((
                str(row.get("house_number", ""))[:50]  or None,
                str(row.get("street",       ""))[:255] or None,
                str(row.get("city",         ""))[:100] or None,
                str(row.get("district",     ""))[:100] or None,
                str(row.get("state",        "Tamil Nadu"))[:100],
                str(row.get("country",      "India"))[:100],
                str(row.get("postcode",     ""))[:20]  or None,
                float(row["latitude"]),
                float(row["longitude"]),
                geom_hex,
            ))

        inserted = 0
        for batch in batched(addr_rows, BATCH_SIZE):
            psycopg2.extras.execute_batch(cur, addr_sql, batch, page_size=BATCH_SIZE)
            inserted += len(batch)
            if inserted % 5000 == 0:
                log.info(f"  Addresses: {inserted:,}/{len(addr_rows):,}")
        conn.commit()

    log.info(f"  Addresses inserted: {inserted:,}")


# =============================================================================
# VERIFY
# =============================================================================

def verify_import(conn):
    """Print row counts for all tables."""
    tables = ["nodes", "roads", "campuses", "addresses"]
    log.info("\n" + "=" * 55)
    log.info("  DATABASE IMPORT VERIFICATION")
    log.info("=" * 55)
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            log.info(f"  {table:<20}: {count:>10,} rows")
    log.info("=" * 55)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Import Tamil Nadu data into PostgreSQL")
    parser.add_argument("--table", choices=["roads", "campuses", "addresses", "all"],
                        default="all", help="Which table to import")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate only, do not write to database")
    args = parser.parse_args()

    if args.dry_run:
        log.info("DRY RUN mode: validating files without writing to database.")

    conn = get_connection()
    log.info(f"Connected to PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}"
             f" / {DB_CONFIG['database']}")

    try:
        start = time.time()

        if args.table in ("roads",    "all"):
            import_roads(conn,    dry_run=args.dry_run)
        if args.table in ("campuses", "all"):
            import_campuses(conn, dry_run=args.dry_run)
        if args.table in ("addresses","all"):
            import_addresses(conn,dry_run=args.dry_run)

        if not args.dry_run:
            verify_import(conn)

        elapsed = (time.time() - start) / 60
        log.info(f"\nAll imports completed in {elapsed:.1f} minutes.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
