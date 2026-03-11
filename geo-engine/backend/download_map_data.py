"""
Pre-download OpenStreetMap road network data for Bengaluru.
Run this ONCE before starting the server for the first time.
After this completes, routing will work instantly.
"""

import os
import pickle
import sys

# Set UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CACHE_DIR = "../data/osm_data"
CACHE_FILE = os.path.join(CACHE_DIR, "bengaluru_network.pkl")
BENGALURU_CENTER = (12.9716, 77.5946)
BENGALURU_DIST = 15000  # 15 km radius

def main():
    if os.path.exists(CACHE_FILE):
        size_mb = os.path.getsize(CACHE_FILE) / (1024 * 1024)
        print(f"[OK] Map data already cached ({size_mb:.1f} MB)")
        print(f"     Location: {CACHE_FILE}")
        print("     Routing is ready to use!")
        return

    print("=" * 55)
    print("  Downloading Bengaluru Road Network from OSM")
    print("=" * 55)
    print(f"  Center : {BENGALURU_CENTER}")
    print(f"  Radius : {BENGALURU_DIST / 1000:.0f} km")
    print("  This will take 5-15 minutes on first run.")
    print("  Requires internet connection.")
    print("=" * 55)

    try:
        import osmnx as ox
        print("\n[1/3] Connecting to OpenStreetMap...")

        G = ox.graph_from_point(
            BENGALURU_CENTER,
            dist=BENGALURU_DIST,
            network_type='drive'
        )

        print(f"[2/3] Downloaded: {len(G.nodes)} nodes, {len(G.edges)} road segments")

        os.makedirs(CACHE_DIR, exist_ok=True)
        print(f"[3/3] Saving cache to {CACHE_FILE} ...")

        with open(CACHE_FILE, "wb") as f:
            pickle.dump(G, f)

        size_mb = os.path.getsize(CACHE_FILE) / (1024 * 1024)
        print(f"\n[DONE] Map data saved ({size_mb:.1f} MB)")
        print("       Routing is now ready to use!")

    except ImportError:
        print("[ERROR] osmnx is not installed.")
        print("        Run: pip install osmnx")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        print("        Check your internet connection and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
