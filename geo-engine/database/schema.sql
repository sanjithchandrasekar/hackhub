-- =============================================================
-- GeoEngine Database Schema
-- Region: Tamil Nadu, India
-- Requires: PostgreSQL 14+ with PostGIS 3+
-- =============================================================

-- STEP 1: Enable PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;        -- for geocoding fuzzy match
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder; -- optional US geocoder (safe to skip)

-- =============================================================
-- CLEAN SLATE (drop if rebuilding)
-- =============================================================
DROP TABLE IF EXISTS geofence_events CASCADE;
DROP TABLE IF EXISTS route_cache     CASCADE;
DROP TABLE IF EXISTS addresses       CASCADE;
DROP TABLE IF EXISTS campuses        CASCADE;
DROP TABLE IF EXISTS roads           CASCADE;
DROP TABLE IF EXISTS nodes           CASCADE;

-- =============================================================
-- TABLE: nodes
-- Every OSM intersection or road junction point
-- =============================================================
CREATE TABLE nodes (
    id          BIGINT PRIMARY KEY,          -- OSM node ID
    osmid       BIGINT,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    highway     VARCHAR(100),               -- junction type if any
    ref         VARCHAR(100),               -- road reference number
    street_count INTEGER DEFAULT 0,        -- how many roads meet here
    geometry    GEOMETRY(POINT, 4326) NOT NULL
);

CREATE INDEX idx_nodes_geometry  ON nodes USING GIST(geometry);
CREATE INDEX idx_nodes_osmid     ON nodes(osmid);
CREATE INDEX idx_nodes_lat_lon   ON nodes(latitude, longitude);

-- =============================================================
-- TABLE: roads
-- Every drivable road segment (OSM edge)
-- =============================================================
CREATE TABLE roads (
    id           SERIAL PRIMARY KEY,
    source_node  BIGINT          NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_node  BIGINT          NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    osmid        BIGINT,
    name         VARCHAR(255),
    highway      VARCHAR(100),              -- motorway, trunk, primary, secondary...
    oneway       BOOLEAN         DEFAULT FALSE,
    length_m     DOUBLE PRECISION,          -- length in metres (from OSM)
    distance     DOUBLE PRECISION,          -- length in km (computed)
    maxspeed     VARCHAR(50),               -- raw OSM tag value
    maxspeed_kph INTEGER,                   -- parsed numeric value
    lanes        INTEGER,
    bridge       BOOLEAN         DEFAULT FALSE,
    tunnel       BOOLEAN         DEFAULT FALSE,
    geometry     GEOMETRY(LINESTRING, 4326) NOT NULL
);

CREATE INDEX idx_roads_geometry   ON roads USING GIST(geometry);
CREATE INDEX idx_roads_source     ON roads(source_node);
CREATE INDEX idx_roads_target     ON roads(target_node);
CREATE INDEX idx_roads_highway    ON roads(highway);
CREATE INDEX idx_roads_osmid      ON roads(osmid);

-- =============================================================
-- TABLE: campuses
-- University / college / school campus polygons
-- =============================================================
CREATE TABLE campuses (
    id           SERIAL PRIMARY KEY,
    campus_name  VARCHAR(255)    NOT NULL,
    campus_type  VARCHAR(100),              -- university | college | school | research
    amenity      VARCHAR(100),              -- OSM amenity tag
    operator     VARCHAR(255),             -- operator name
    website      VARCHAR(500),
    osmid        BIGINT,
    district     VARCHAR(100),
    city         VARCHAR(100),
    state        VARCHAR(100)   DEFAULT 'Tamil Nadu',
    country      VARCHAR(100)   DEFAULT 'India',
    area_sqm     DOUBLE PRECISION,          -- computed area in sq metres
    boundary     GEOMETRY(MULTIPOLYGON, 4326)
);

CREATE INDEX idx_campuses_boundary ON campuses USING GIST(boundary);
CREATE INDEX idx_campuses_name     ON campuses(campus_name);
CREATE INDEX idx_campuses_type     ON campuses(campus_type);
CREATE INDEX idx_campuses_district ON campuses(district);

-- =============================================================
-- TABLE: addresses
-- Address points for geocoding and reverse geocoding
-- =============================================================
CREATE TABLE addresses (
    id           SERIAL PRIMARY KEY,
    house_number VARCHAR(50),
    street       VARCHAR(255),
    city         VARCHAR(100),
    district     VARCHAR(100),
    state        VARCHAR(100)   DEFAULT 'Tamil Nadu',
    country      VARCHAR(100)   DEFAULT 'India',
    postcode     VARCHAR(20),
    latitude     DOUBLE PRECISION,
    longitude    DOUBLE PRECISION,
    geometry     GEOMETRY(POINT, 4326)
);

CREATE INDEX idx_addresses_geometry ON addresses USING GIST(geometry);
CREATE INDEX idx_addresses_city      ON addresses(city);
CREATE INDEX idx_addresses_district  ON addresses(district);
CREATE INDEX idx_addresses_postcode  ON addresses(postcode);
CREATE INDEX idx_addresses_street    ON addresses(street);

-- Full-text search index on street + city
CREATE INDEX idx_addresses_fts ON addresses
    USING GIN(to_tsvector('english', COALESCE(street,'') || ' ' || COALESCE(city,'')));

-- =============================================================
-- TABLE: geofence_events
-- Real-time entry/exit events when assets cross campus boundaries
-- =============================================================
CREATE TABLE geofence_events (
    id          SERIAL PRIMARY KEY,
    asset_id    VARCHAR(100)    NOT NULL,
    campus_id   INTEGER         REFERENCES campuses(id) ON DELETE SET NULL,
    campus_name VARCHAR(255),
    event_type  VARCHAR(20)     CHECK (event_type IN ('ENTRY','EXIT','DWELLING')),
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    event_time  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    geometry    GEOMETRY(POINT, 4326)
);

CREATE INDEX idx_geofence_asset     ON geofence_events(asset_id);
CREATE INDEX idx_geofence_campus    ON geofence_events(campus_id);
CREATE INDEX idx_geofence_type      ON geofence_events(event_type);
CREATE INDEX idx_geofence_time      ON geofence_events(event_time);
CREATE INDEX idx_geofence_geometry  ON geofence_events USING GIST(geometry);

-- =============================================================
-- TABLE: route_cache
-- Cached computed routes to avoid re-computing expensive paths
-- =============================================================
CREATE TABLE route_cache (
    id              SERIAL PRIMARY KEY,
    start_lat       DOUBLE PRECISION,
    start_lon       DOUBLE PRECISION,
    end_lat         DOUBLE PRECISION,
    end_lon         DOUBLE PRECISION,
    distance_km     DOUBLE PRECISION,
    duration_min    DOUBLE PRECISION,
    mode            VARCHAR(50) DEFAULT 'fastest',
    route_geometry  GEOMETRY(LINESTRING, 4326),
    node_sequence   BIGINT[],               -- ordered OSM node IDs
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    hit_count       INTEGER DEFAULT 0
);

CREATE INDEX idx_route_cache_geom    ON route_cache USING GIST(route_geometry);
CREATE INDEX idx_route_cache_coords  ON route_cache(start_lat, start_lon, end_lat, end_lon);
CREATE INDEX idx_route_cache_time    ON route_cache(created_at);

-- =============================================================
-- USEFUL VIEWS
-- =============================================================

-- View: campus_summary — quick stats per campus type
CREATE OR REPLACE VIEW campus_summary AS
SELECT
    campus_type,
    district,
    COUNT(*)                             AS total,
    ROUND(AVG(area_sqm)::NUMERIC, 2)    AS avg_area_sqm
FROM campuses
GROUP BY campus_type, district
ORDER BY district, campus_type;

-- View: road_stats — road length per highway class
CREATE OR REPLACE VIEW road_stats AS
SELECT
    highway,
    COUNT(*)                                    AS segment_count,
    ROUND(SUM(length_m / 1000)::NUMERIC, 2)    AS total_km
FROM roads
GROUP BY highway
ORDER BY total_km DESC;

-- =============================================================
-- HELPER FUNCTIONS
-- =============================================================

-- Function: find campuses within N km of a point
CREATE OR REPLACE FUNCTION campuses_near(
    p_lat  DOUBLE PRECISION,
    p_lon  DOUBLE PRECISION,
    p_km   DOUBLE PRECISION DEFAULT 5.0
)
RETURNS TABLE (
    id          INTEGER,
    campus_name VARCHAR,
    campus_type VARCHAR,
    district    VARCHAR,
    distance_km DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.campus_name,
        c.campus_type,
        c.district,
        ROUND(
            (ST_Distance(
                c.boundary::GEOGRAPHY,
                ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY
            ) / 1000)::NUMERIC, 3
        )::DOUBLE PRECISION AS distance_km
    FROM campuses c
    WHERE ST_DWithin(
        c.boundary::GEOGRAPHY,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY,
        p_km * 1000
    )
    ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;

-- Function: check if point is inside any campus (geofence check)
CREATE OR REPLACE FUNCTION check_geofence(
    p_lat DOUBLE PRECISION,
    p_lon DOUBLE PRECISION
)
RETURNS TABLE (
    campus_id   INTEGER,
    campus_name VARCHAR,
    campus_type VARCHAR,
    inside      BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.campus_name,
        c.campus_type,
        ST_Contains(
            c.boundary,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)
        ) AS inside
    FROM campuses c
    WHERE ST_DWithin(
        c.boundary::GEOGRAPHY,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY,
        2000   -- pre-filter: only check campuses within 2 km
    );
END;
$$ LANGUAGE plpgsql;

-- Function: nearest road node to a lat/lon point
CREATE OR REPLACE FUNCTION nearest_node(
    p_lat DOUBLE PRECISION,
    p_lon DOUBLE PRECISION
)
RETURNS TABLE (
    node_id    BIGINT,
    latitude   DOUBLE PRECISION,
    longitude  DOUBLE PRECISION,
    distance_m DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id,
        n.latitude,
        n.longitude,
        ST_Distance(
            n.geometry::GEOGRAPHY,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY
        ) AS distance_m
    FROM nodes n
    ORDER BY n.geometry <-> ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- =============================================================
-- TABLE: ml_predictions
-- Persisted ETA / congestion predictions for analytics
-- =============================================================
DROP TABLE IF EXISTS ml_predictions CASCADE;
CREATE TABLE ml_predictions (
    id               SERIAL PRIMARY KEY,
    prediction_type  VARCHAR(50)  NOT NULL,  -- 'eta' | 'congestion' | 'safety'
    distance_km      DOUBLE PRECISION,
    hour             INTEGER,
    day_of_week      INTEGER,
    is_highway       BOOLEAN DEFAULT FALSE,
    is_rain          BOOLEAN DEFAULT FALSE,
    predicted_value  DOUBLE PRECISION,       -- eta_min / congestion_score / safety_score
    label            VARCHAR(50),            -- "Low Traffic", "High Congestion", etc.
    source           VARCHAR(50),            -- 'ml_model' | 'heuristic'
    confidence_low   DOUBLE PRECISION,
    confidence_high  DOUBLE PRECISION,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ml_pred_type ON ml_predictions(prediction_type);
CREATE INDEX idx_ml_pred_time ON ml_predictions(created_at);
CREATE INDEX idx_ml_pred_hour ON ml_predictions(hour);

-- =============================================================
-- TABLE: anomaly_log
-- Detected traffic anomalies from IsolationForest model
-- =============================================================
DROP TABLE IF EXISTS anomaly_log CASCADE;
CREATE TABLE anomaly_log (
    id          SERIAL PRIMARY KEY,
    asset_id    VARCHAR(100),
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    speed_kmh   DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,         -- IsolationForest decision score
    reason      VARCHAR(255),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    geometry    GEOMETRY(POINT, 4326)
);

CREATE INDEX idx_anomaly_asset    ON anomaly_log(asset_id);
CREATE INDEX idx_anomaly_time     ON anomaly_log(detected_at);
CREATE INDEX idx_anomaly_geometry ON anomaly_log USING GIST(geometry);

-- =============================================================
-- TABLE: traffic_heatmap_cache
-- ML-generated traffic density points (refreshed periodically)
-- =============================================================
DROP TABLE IF EXISTS traffic_heatmap_cache CASCADE;
CREATE TABLE traffic_heatmap_cache (
    id              SERIAL PRIMARY KEY,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    intensity       DOUBLE PRECISION,        -- 0 – 1 normalised
    speed_kmh       DOUBLE PRECISION,
    congestion_label VARCHAR(50),
    city            VARCHAR(100),
    generated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    geometry        GEOMETRY(POINT, 4326)
);

CREATE INDEX idx_heatmap_geometry  ON traffic_heatmap_cache USING GIST(geometry);
CREATE INDEX idx_heatmap_generated ON traffic_heatmap_cache(generated_at);
CREATE INDEX idx_heatmap_city      ON traffic_heatmap_cache(city);

-- =============================================================
-- VIEW: recent_anomalies — last 24 h anomaly list
-- =============================================================
CREATE OR REPLACE VIEW recent_anomalies AS
SELECT  id, asset_id, latitude, longitude, speed_kmh, reason, detected_at
FROM    anomaly_log
WHERE   detected_at > NOW() - INTERVAL '24 hours'
ORDER BY detected_at DESC;

-- =============================================================
-- GRANTS (adjust username as needed)
-- =============================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA public TO geo_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO geo_user;
-- GRANT EXECUTE ON ALL FUNCTIONS        IN SCHEMA public TO geo_user;
