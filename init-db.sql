-- ============================================================================
-- PostgreSQL Database Initialization Script
-- Sets up the database for Insurance RAG Application
-- ============================================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE NOTICE 'pgvector extension successfully installed';
    ELSE
        RAISE EXCEPTION 'Failed to install pgvector extension';
    END IF;
END $$;

-- Create schema for application tables (optional, for organization)
CREATE SCHEMA IF NOT EXISTS insurance;

-- Set search path to include the new schema
SET search_path TO insurance, public;

-- Grant necessary permissions to postgres user
GRANT ALL PRIVILEGES ON SCHEMA insurance TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA insurance TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA insurance TO postgres;

-- Create index for better performance (tables will be created by the app)
-- This is a placeholder - actual indexes will be created when tables are created

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
    RAISE NOTICE 'pgvector version: %', (SELECT extversion FROM pg_extension WHERE extname = 'vector');
END $$;

-- ============================================================================
-- Optional: Create utility functions for debugging
-- ============================================================================

-- Function to check vector dimensions
CREATE OR REPLACE FUNCTION check_vector_dimension(vec vector)
RETURNS INTEGER AS $$
BEGIN
    RETURN array_length(vec::text::float[], 1);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate cosine similarity (redundant with <=> operator but useful for reference)
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Performance tuning for PostgreSQL with pgvector
-- ============================================================================

-- Adjust shared buffers (will be set in postgresql.conf for production)
-- These are hints; actual tuning should be done in PostgreSQL configuration

-- Log completion
SELECT 'Database initialization script completed at ' || NOW() AS completion_time;
