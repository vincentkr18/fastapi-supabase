#!/bin/bash
# clean_reset.sh

# Remove alembic migrations
rm -rf alembic/versions/*

# Drop and recreate public schema in Supabase (run this SQL manually or via psql)
echo "Run this SQL in Supabase SQL Editor:"
echo "DROP SCHEMA public CASCADE;"
echo "CREATE SCHEMA public;"
echo "GRANT ALL ON SCHEMA public TO postgres;"
echo "GRANT ALL ON SCHEMA public TO public;"

# Wait for user confirmation
read -p "Press enter after running the SQL commands..."

# Create new migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head

echo "Reset complete!"