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

if [ -z "${SUBSCRIBE_URL:-}" ]; then
  echo "SUBSCRIBE_URL is required" >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR"

if [ -s "$CONFIG_PATH" ]; then
  NOW=$(date +%s)
  CONFIG_MTIME=$(stat -c %Y "$CONFIG_PATH")
  if [ $(( NOW - CONFIG_MTIME )) -lt 60 ]; then
    exit 0
  fi
fi

TMP_FILE=$(mktemp)

cleanup() {
  rm -f "$TMP_FILE"
}
trap cleanup EXIT

download_config() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --retry 3 --connect-timeout 15 -o "$TMP_FILE" "$SUBSCRIBE_URL"
  else
    wget -qO "$TMP_FILE" "$SUBSCRIBE_URL"
  fi
}

patch_config() {
  yq -i '
    .port = 7890 |
    .socks-port = 7891 |
    .mixed-port = 7892 |
    .external-controller = ":9090" |
    .external-ui = "ui" |
    .external-ui-name = strenv(EXTERNAL_UI_NAME) |
    .external-ui-url = strenv(EXTERNAL_UI_URL) |
    .secret = strenv(EXTERNAL_SECRET) |
    .sniffer.enable = true |
    .sniffer.sniff.HTTP.ports = [80, "8080-8880"] |
    .sniffer.sniff.HTTP.override-destination = true |
    .sniffer.sniff.TLS.ports = [443, 8443] |
    .sniffer.sniff.QUIC.ports = [443, 8443] |
    .sniffer.skip-domain = ["Mijia Cloud", "+.push.apple.com"]
  ' "$1"
}

if download_config && [ -s "$TMP_FILE" ]; then
  mv "$TMP_FILE" "$CONFIG_PATH"
  patch_config "$CONFIG_PATH"
  exit 0
fi

if [ -s "$CONFIG_PATH" ]; then
  echo "Download failed, keeping existing config: $CONFIG_PATH" >&2
  exit 0
fi

echo "Download failed and config does not exist: $CONFIG_PATH" >&2
exit 1
