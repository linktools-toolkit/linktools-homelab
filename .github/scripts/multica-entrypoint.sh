#!/bin/sh
set -eu

: "${MULTICA_SERVER_URL:?MULTICA_SERVER_URL is required}"
: "${MULTICA_APP_URL:?MULTICA_APP_URL is required}"

pat_file="${MULTICA_PAT_FILE:-/run/secrets/multica_pat}"
if [ ! -r "$pat_file" ]; then
    echo "Multica PAT file is missing or unreadable: $pat_file" >&2
    exit 1
fi

pat="$(tr -d '\r\n' < "$pat_file")"
if [ -z "$pat" ]; then
    echo "Multica PAT file is empty" >&2
    exit 1
fi

until curl -fsS "${MULTICA_SERVER_URL%/}/health" >/dev/null; do
    echo "Waiting for Multica API at ${MULTICA_SERVER_URL}..."
    sleep 5
done

multica config set server_url "$MULTICA_SERVER_URL"
multica config set app_url "$MULTICA_APP_URL"
multica login --token "$pat"
unset pat

if [ -n "${MULTICA_DAEMON_ID:-}" ]; then
    set -- "$@" --daemon-id "$MULTICA_DAEMON_ID"
fi

exec multica "$@"
