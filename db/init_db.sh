#!/bin/bash

echo "Creating database $DJANGO_DB_NAME"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $DJANGO_DB_NAME;
EOSQL

echo "Creating user $DJANGO_DB_USER"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER $DJANGO_DB_USER WITH PASSWORD '$DJANGO_DB_PASSWORD';
EOSQL

echo "Granting privileges to user $DJANGO_DB_USER"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    GRANT ALL PRIVILEGES ON DATABASE $DJANGO_DB_NAME TO $DJANGO_DB_USER;
EOSQL

echo "Assigning ownership of database $DJANGO_DB_NAME to $DJANGO_DB_USER";
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    ALTER DATABASE $DJANGO_DB_NAME OWNER TO $DJANGO_DB_USER;
EOSQL

echo "Dumping database"
pg_dump -U postgres -h localhost -p 5432 search_engine > search_engine.sql