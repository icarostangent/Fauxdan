-- Create database
CREATE DATABASE search_engine;

-- Create user
CREATE USER django WITH PASSWORD '$DJANGO_DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE search_engine TO django;

-- Set ownership
ALTER DATABASE search_engine OWNER TO django;
