#!/bin/sh
set -eu

# code-server waits for ENTRYPOINTD scripts, so run CloudCLI in the background.
if [ "${1:-}" != "--run" ]; then
    set +e
    nohup "$0" --run </dev/null &
    exit 0
fi

# Install into NPM_CONFIG_PREFIX when the environment provides one (VS Code's
# /workspace/.node_modules), otherwise into CloudCLI's own volume. A cloudcli
# already resolvable on PATH is used as-is. Node 24's npm blocks dependency
# install scripts by default; persist the allowlist into npm's global config
# so both this install and any later manual npm operations keep working.
install_prefix="${NPM_CONFIG_PREFIX:-/workspace/.cloudcli/app}"

install_cloudcli() {
    command -v cloudcli >/dev/null 2>&1 && return 0
    npm config set allow-scripts=@cloudcli-ai/cloudcli,bcrypt,better-sqlite3,node-pty --location=global
    PATH="$install_prefix/bin:$PATH" \
        npm install -g --omit=dev @cloudcli-ai/cloudcli@latest || return 1
    command -v cloudcli >/dev/null 2>&1
}

until install_cloudcli; do
    echo "CloudCLI install failed; retrying..." >&2
    sleep 30
done

# Keep these variables local to CloudCLI, without changing code-server's env.
export HOST=0.0.0.0
export SERVER_PORT=3001
export DATABASE_PATH=/workspace/.cloudcli/auth/cloudcli.db

while :; do
    cloudcli start || true
    echo "CloudCLI exited; retrying..." >&2
    sleep 30
done
