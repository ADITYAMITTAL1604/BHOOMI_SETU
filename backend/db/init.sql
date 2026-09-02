-- =============================================================================
-- BhoomiSetu — PostgreSQL + PostGIS bootstrap
-- Runs once on first container start via docker-entrypoint-initdb.d/
-- =============================================================================

-- PostGIS geometry + raster support
CREATE EXTENSION IF NOT EXISTS postgis;

-- PostGIS topology (needed for certain geometry ops)
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- UUID generation helper
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm for fuzzy text search on parcel/owner names
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify extensions installed
DO $$
BEGIN
  RAISE NOTICE 'PostGIS version: %', PostGIS_Full_Version();
END;
$$;
