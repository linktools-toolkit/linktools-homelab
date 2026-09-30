#!/usr/bin/env bash
set -Eeuo pipefail

export DISPLAY="${DISPLAY:-:99}"
width="${SCREEN_WIDTH:-1440}"
height="${SCREEN_HEIGHT:-900}"
if [[ ! "$width" =~ ^[1-9][0-9]*$ || ! "$height" =~ ^[1-9][0-9]*$ ]]; then
    echo 'SCREEN_WIDTH and SCREEN_HEIGHT must be positive integers' >&2
    exit 1
fi

pids=()
cleanup() {
    trap - EXIT TERM INT
    if ((${#pids[@]})); then
        kill "${pids[@]}" 2>/dev/null || true
        wait "${pids[@]}" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 0' TERM INT

wait_for() {
    local pid="$1"
    shift
    for ((attempt = 0; attempt < 150; attempt++)); do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "Service exited while waiting for: $*" >&2
            return 1
        fi
        if "$@" >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.2
    done
    echo "Timed out waiting for: $*" >&2
    return 1
}

mkdir -p /workspace/profile /workspace/output
# This profile belongs exclusively to this container; clear crash leftovers.
rm -f /workspace/profile/SingletonLock /workspace/profile/SingletonSocket /workspace/profile/SingletonCookie

Xvfb "$DISPLAY" -screen 0 "${width}x${height}x24" -ac -nolisten tcp &
pids+=("$!")
wait_for "$!" xdpyinfo -display "$DISPLAY"

openbox --sm-disable &
pids+=("$!")

# Raw VNC and CDP stay inside the container. noVNC is protected by nginx SSO.
x11vnc -display "$DISPLAY" -rfbport 5900 -localhost -forever -shared -nopw -xkb &
pids+=("$!")
websockify --web=/usr/share/novnc 6080 127.0.0.1:5900 &
pids+=("$!")

browser="$(node -p 'require("/opt/playwright/node_modules/playwright").chromium.executablePath()')"
# Mark this automated browser as a test session to suppress startup flag infobars.
# This only changes the UI; Chromium's sandbox remains disabled in this image.
"$browser" --test-type --no-sandbox --no-first-run --no-default-browser-check \
    --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 \
    --user-data-dir=/workspace/profile --window-size="${width},${height}" about:blank &
pids+=("$!")
wait_for "$!" curl --max-time 1 -fsS http://127.0.0.1:9222/json/version

/opt/playwright/node_modules/.bin/playwright-mcp \
    --host 0.0.0.0 --port 8931 --allowed-hosts '*' \
    --cdp-endpoint http://127.0.0.1:9222 --shared-browser-context \
    --output-dir /workspace/output &
pids+=("$!")

# Restart the entire stack if any of its processes exits, even with status zero.
status=0
wait -n "${pids[@]}" || status=$?
if ((status == 0)); then status=1; fi
exit "$status"
