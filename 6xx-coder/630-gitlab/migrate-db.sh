#!/bin/sh
set -eu
umask 077

case "$1" in
    dump) test -s "$PGDATA/PG_VERSION" ;;
    restore) test -s /backup/cluster.sql ;;
    *) exit 2 ;;
esac

# The temporary database has no network access; clients use its local socket.
echo "[migrate-db] Starting PostgreSQL for $1..."
/usr/local/bin/docker-entrypoint.sh postgres -c listen_addresses= &
server_pid=$!
cleanup() {
    kill -INT "$server_pid" 2>/dev/null || true
    wait "$server_pid" || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Wait for the final server, not the temporary server used during initdb.
attempt=0
until [ "$(head -n 1 "$PGDATA/postmaster.pid" 2>/dev/null || true)" = "$server_pid" ] &&
      pg_isready -q -U "${POSTGRES_USER:-$DB_USER}" -d postgres; do
    kill -0 "$server_pid" 2>/dev/null || { echo 'PostgreSQL exited' >&2; exit 1; }
    attempt=$((attempt + 1))
    [ "$attempt" -lt 300 ] || { echo 'PostgreSQL startup timed out' >&2; exit 1; }
    sleep 1
done

if [ "$1" = dump ]; then
    echo '[migrate-db] Exporting all databases and roles...'
    pg_dumpall -U "$DB_USER" > /backup/cluster.sql
    echo "[migrate-db] Export complete: $(wc -c < /backup/cluster.sql) bytes"
else
    echo '[migrate-db] Restoring all databases and roles (large databases may take a while)...'
    psql -X -q -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 < /backup/cluster.sql
    echo '[migrate-db] Restore complete. Updating database statistics...'
    vacuumdb -U "$POSTGRES_USER" --all --analyze-in-stages
    psql -X -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 \
        -c "ALTER ROLE \"$POSTGRES_USER\" NOLOGIN"
    echo '[migrate-db] Restore and analysis complete.'
fi
