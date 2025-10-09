#!/bin/bash
set -e

# Detect correct typedb binary path
if [ -x /opt/typedb-all-linux-arm64/typedb ]; then
  TYPEDB_BIN=/opt/typedb-all-linux-arm64/typedb
elif [ -x /opt/typedb-all-linux-x86_64/typedb ]; then
  TYPEDB_BIN=/opt/typedb-all-linux-x86_64/typedb
else
  echo "ERROR: Could not find typedb binary in /opt"
  exit 1
fi
echo "Using $TYPEDB_BIN"

# Paths
DATA_ARCHIVE="/data/knowledgeplatform-data.tar.gz"
IMPORT_DIR="/tmp/import_data"
SCHEMA_FILE="${IMPORT_DIR}/knowledgeplatform.typeql"
DATA_FILE="${IMPORT_DIR}/knowledgeplatform.typedb"

echo "Checking for data archive at ${DATA_ARCHIVE}..."
if [ -f "$DATA_ARCHIVE" ]; then
    echo "Data archive found. Unpacking into ${IMPORT_DIR}..."
    mkdir -p "$IMPORT_DIR"
    tar -xzvf "$DATA_ARCHIVE" -C "$IMPORT_DIR"
    echo "Unpacking complete."
else
    echo "Data archive not found. Starting with a fresh, empty database."
fi

echo "Starting TypeDB server in background..."
"$TYPEDB_BIN" server &
SERVER_PID=$!

echo "Waiting for TypeDB server to be ready..."
until "$TYPEDB_BIN" console --core=localhost:1729 --command="database list" &>/dev/null; do
  echo "Server not responsive yet. Retrying in 2 seconds..."
  sleep 2
done
echo "Server is ready."

if [ -f "$SCHEMA_FILE" ]; then
    if "$TYPEDB_BIN" console --core=localhost:1729 --command="database list" | grep -q "$DATABASE_NAME"; then
      echo "Database '$DATABASE_NAME' already exists. Skipping import."
    else
      echo "Importing database: $DATABASE_NAME"
      "$TYPEDB_BIN" server import --port=1729 --database="$DATABASE_NAME" --schema="$SCHEMA_FILE" --data="$DATA_FILE"
      echo "Import complete."
    fi
else
    echo "Schema file not found. No data will be imported."
fi

echo "TypeDB is running. Tailing logs to keep container alive."
wait $SERVER_PID