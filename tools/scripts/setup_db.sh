#!/bin/bash
# Setup PostgreSQL database for Angel-X

set -e

echo "📦 Setting up PostgreSQL database..."

# Database credentials
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-angelx_ml}"
DB_USER="${DB_USER:-angelx}"
DB_PASSWORD="${DB_PASSWORD:-angelx_secure_2026}"

# Create database and user
echo "Creating database '$DB_NAME' and user '$DB_USER'..."

# Connect to PostgreSQL
psql -h "$DB_HOST" -U postgres -d postgres << EOF
-- Create user if not exists
DO \$do\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
  END IF;
END \$do\$;

-- Create database
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

echo "✅ Database setup complete"
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
