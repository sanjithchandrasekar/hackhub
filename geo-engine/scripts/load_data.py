"""
GeoEngine – Sample Data Loader
================================
Reads processed CSV exports from data/exports/ and inserts them
into PostgreSQL (PostGIS required).

Usage:
    python scripts/load_data.py [--roads] [--addresses] [--all]

Environment variables (or .env file):
    DB_HOST      default: localhost
    DB_PORT      default: 5432
    DB_NAME      default: geoengine
    DB_USER      default: postgres
    DB_PASSWORD  default: postgres
"""

import argparse
import os
import sys
import csv
import json
import time

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("[ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "geoengine"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "exports")
BATCH_SIZE  = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def connect():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.OperationalError as exc:
        sys.exit(f"[ERROR] Cannot connect to database: {exc}")


def load_roads(conn):
    path = os.path.join(EXPORTS_DIR, "tamilnadu_roads.csv")
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    print(f"[ROADS] Loading {path} …")
    cur  = conn.cursor()
    rows = 0

    upsert_sql = """
        INSERT INTO roads (osmid, name, highway, oneway, length_m, distance,
                           maxspeed, lanes, geometry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakeLine(
                    ST_MakePoint(%s, %s),
                    ST_MakePoint(%s, %s)
                ), 4326))
        ON CONFLICT DO NOTHING
    """

    batch = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                batch.append((
                    row.get("osmid") or None,
                    row.get("name") or None,
                    row.get("highway") or None,
                    row.get("oneway", "False").lower() in ("true", "1", "yes"),
                    float(row["length_m"]) if row.get("length_m") else None,
                    float(row["distance"]) if row.get("distance") else None,
                    row.get("maxspeed") or None,
                    int(row["lanes"]) if row.get("lanes") and row["lanes"].isdigit() else None,
                    float(row["start_lon"]), float(row["start_lat"]),
                    float(row["end_lon"]),   float(row["end_lat"]),
                ))
            except (KeyError, ValueError):
                continue

            if len(batch) >= BATCH_SIZE:
                psycopg2.extras.execute_batch(cur, upsert_sql, batch)
                rows += len(batch)
                batch = []
                print(f"  … {rows} rows inserted", end="\r")

    if batch:
        psycopg2.extras.execute_batch(cur, upsert_sql, batch)
        rows += len(batch)

    conn.commit()
    print(f"[ROADS] Done — {rows} segments inserted.")


def load_addresses(conn):
    path = os.path.join(EXPORTS_DIR, "tamilnadu_addresses.csv")
    if not os.path.exists(path):
        print(f"[SKIP] {path} not found")
        return

    print(f"[ADDRESSES] Loading {path} …")
    cur  = conn.cursor()
    rows = 0

    upsert_sql = """
        INSERT INTO addresses (house_number, street, city, district, postcode,
                               latitude, longitude, geometry)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        ON CONFLICT DO NOTHING
    """

    batch = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (KeyError, ValueError):
                continue

            batch.append((
                row.get("house_number") or None,
                row.get("street") or row.get("name") or None,
                row.get("city") or None,
                row.get("district") or None,
                row.get("postcode") or None,
                lat, lon,
                lon, lat,
            ))

            if len(batch) >= BATCH_SIZE:
                psycopg2.extras.execute_batch(cur, upsert_sql, batch)
                rows += len(batch)
                batch = []
                print(f"  … {rows} rows inserted", end="\r")

    if batch:
        psycopg2.extras.execute_batch(cur, upsert_sql, batch)
        rows += len(batch)

    conn.commit()
    print(f"[ADDRESSES] Done — {rows} records inserted.")


def load_sample_geofence_events(conn):
    """Insert a handful of synthetic geofence events for demo purposes."""
    print("[GEOFENCE] Inserting sample events …")
    cur = conn.cursor()

    events = [
        ("asset_001", "IIT_Madras",    "ENTRY", 13.0070, 80.2340),
        ("asset_001", "IIT_Madras",    "EXIT",  13.0030, 80.2290),
        ("asset_002", "Tidel_Park",    "ENTRY", 12.9900, 80.2250),
        ("asset_003", "NIT_Trichy",    "ENTRY", 10.7600, 78.8180),
        ("asset_004", "Anna_University","ENTRY", 13.0085, 80.2370),
    ]

    sql = """
        INSERT INTO geofence_events
            (asset_id, campus_name, event_type, latitude, longitude,
             geometry, event_time)
        VALUES (%s, %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                NOW() - (RANDOM() * INTERVAL '7 days'))
        ON CONFLICT DO NOTHING
    """

    cur.executemany(sql, [
        (asset, campus, ev, lat, lon, lon, lat)
        for asset, campus, ev, lat, lon in events
    ])
    conn.commit()
    print(f"[GEOFENCE] {len(events)} sample events inserted.")


def load_sample_ml_predictions(conn):
    """Insert synthetic ML prediction records for the analytics dashboard."""
    import random
    from datetime import datetime, timedelta

    print("[ML] Inserting sample predictions …")
    cur  = conn.cursor()
    now  = datetime.utcnow()
    rows = []

    labels_congestion = ["Low Traffic", "Moderate", "High Congestion", "Severe", "Free Flow"]
    labels_eta        = ["On Time", "Slight Delay", "Heavy Delay"]

    for i in range(200):
        ts   = now - timedelta(hours=random.randint(0, 72))
        hour = ts.hour
        dist = round(random.uniform(2, 80), 2)
        pred_type = random.choice(["eta", "congestion", "safety"])

        if pred_type == "eta":
            val   = round(dist * random.uniform(1.5, 3.5), 1)
            label = random.choice(labels_eta)
            lo, hi = round(val * 0.85, 1), round(val * 1.15, 1)
        elif pred_type == "congestion":
            val   = round(random.uniform(0, 1), 3)
            label = random.choice(labels_congestion)
            lo, hi = None, None
        else:
            val   = round(random.uniform(4, 10), 2)
            label = "Safe" if val >= 7 else ("Moderate Risk" if val >= 4 else "High Risk")
            lo, hi = None, None

        rows.append((
            pred_type, dist, hour,
            ts.weekday(), bool(random.getrandbits(1)), bool(random.getrandbits(1)),
            val, label, "ml_model" if random.random() > 0.2 else "heuristic",
            lo, hi, ts,
        ))

    sql = """
        INSERT INTO ml_predictions
            (prediction_type, distance_km, hour, day_of_week, is_highway, is_rain,
             predicted_value, label, source, confidence_low, confidence_high, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    psycopg2.extras.execute_batch(cur, sql, rows)
    conn.commit()
    print(f"[ML] {len(rows)} sample predictions inserted.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="GeoEngine data loader")
    parser.add_argument("--roads",      action="store_true", help="Load road segments")
    parser.add_argument("--addresses",  action="store_true", help="Load address points")
    parser.add_argument("--samples",    action="store_true", help="Load sample demo data")
    parser.add_argument("--all",        action="store_true", help="Load everything")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    conn = connect()
    t0   = time.time()

    try:
        if args.all or args.roads:
            load_roads(conn)
        if args.all or args.addresses:
            load_addresses(conn)
        if args.all or args.samples:
            load_sample_geofence_events(conn)
            load_sample_ml_predictions(conn)
    finally:
        conn.close()

    elapsed = round(time.time() - t0, 1)
    print(f"\n✓ All done in {elapsed}s")


if __name__ == "__main__":
    main()
