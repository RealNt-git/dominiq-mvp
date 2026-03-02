#!/bin/bash
# 01-create-langflow-db.sh
# Создаёт базу данных langflow, если она ещё не существует.

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE langflow' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langflow')\gexec
EOSQL