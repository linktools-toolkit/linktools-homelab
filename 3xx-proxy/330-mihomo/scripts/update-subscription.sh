#!/bin/sh
set -u

CONFIG_DIR=/root/.config/mihomo
CONFIG_FILE=${CONFIG_FILE:-config.yaml}
CONFIG_PATH="$CONFIG_DIR/$CONFIG_FILE"

if [ -f /etc/mihomo-subscribe.env ]; then
  . /etc/mihomo-subscribe.env
  CONFIG_FILE=${CONFIG_FILE:-config.yaml}
  CONFIG_PATH="$CONFIG_DIR/$CONFIG_FILE"
fi

if [ -f "$CONFIG_PATH" ]; then
  OLD_SUM=$(cksum "$CONFIG_PATH" 2>/dev/null || true)
else
  OLD_SUM=
fi

/docker-entrypoint.d/01-subscribe.sh

if [ -f "$CONFIG_PATH" ]; then
  NEW_SUM=$(cksum "$CONFIG_PATH" 2>/dev/null || true)
else
  NEW_SUM=
fi

if [ "$OLD_SUM" = "$NEW_SUM" ]; then
  exit 0
fi

curl -sf -X PUT "http://localhost:9090/configs?force=true" \
  -H "Authorization: Bearer ${EXTERNAL_SECRET:-}" \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"$CONFIG_PATH\"}" >/dev/null
