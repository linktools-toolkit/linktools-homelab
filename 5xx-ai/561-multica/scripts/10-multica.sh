#!/bin/sh
set -eu

# code-server waits for ENTRYPOINTD scripts, so run Multica in the background.
if [ "${1:-}" != "--run" ]; then
    set +e
    nohup "$0" --run </dev/null &
    exit 0
fi

: "${MULTICA_APP_URL:?MULTICA_APP_URL is required}"
: "${MULTICA_SERVER_URL:?MULTICA_SERVER_URL is required}"
: "${MULTICA_DAEMON_ID:?MULTICA_DAEMON_ID is required}"

pat_file="${MULTICA_PAT_FILE:-/run/secrets/multica/multica_pat}"
bin_dir="/workspace/.local/bin"
multica_cli="$bin_dir/multica"
installer_url="https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh"

mkdir -p "$bin_dir" /workspace/.multica
export PATH="$bin_dir:$PATH"

install_multica() {
    if ! curl -fsSL --retry 2 --connect-timeout 10 --max-time 120 "$installer_url" \
        | MULTICA_BIN_DIR="$bin_dir" bash; then
        echo "Multica's official installer failed" >&2
    fi
    [ -x "$multica_cli" ]
}

until install_multica; do
    echo "Multica CLI is unavailable; retrying..." >&2
    sleep 30
done

while :; do
    if [ ! -r "$pat_file" ]; then
        echo "Multica PAT file is missing or unreadable: $pat_file" >&2
    elif ! "$multica_cli" config set server_url "$MULTICA_SERVER_URL" \
        || ! "$multica_cli" config set app_url "$MULTICA_APP_URL"; then
        echo "Could not configure Multica; retrying..." >&2
    else
        pat="$(tr -d '\r\n' < "$pat_file")"
        if [ -z "$pat" ]; then
            echo "Multica PAT file is empty; retrying..." >&2
        elif "$multica_cli" login --token "$pat"; then
            unset pat
            "$multica_cli" daemon start --foreground --daemon-id "$MULTICA_DAEMON_ID" || true
            echo "Multica daemon exited; retrying..." >&2
        else
            unset pat
            echo "Multica login failed; retrying..." >&2
        fi
    fi
    sleep 5
done
