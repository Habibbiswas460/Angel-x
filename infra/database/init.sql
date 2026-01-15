-- Initialize Angel-X database
-- This script runs when PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for common queries (will be created by SQLAlchemy too)
-- This is just a placeholder for any custom initialization

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Angel-X database initialized successfully';
END $$;
