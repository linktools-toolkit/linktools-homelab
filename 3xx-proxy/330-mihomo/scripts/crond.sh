#!/bin/sh

set -u

escape_env_value() {
  printf "%s" "$1" | sed "s/'/'\\\\\\\\''/g"
}

: > /etc/mihomo-subscribe.env
printf "CONFIG_FILE='%s'\n" "$(escape_env_value "${CONFIG_FILE:-config.yaml}")" >> /etc/mihomo-subscribe.env
printf "SUBSCRIBE_URL='%s'\n" "$(escape_env_value "${SUBSCRIBE_URL:-}")" >> /etc/mihomo-subscribe.env
printf "SUBSCRIBE_USER_AGENT='%s'\n" "$(escape_env_value "${SUBSCRIBE_USER_AGENT:-}")" >> /etc/mihomo-subscribe.env
printf "EXTERNAL_SECRET='%s'\n" "$(escape_env_value "${EXTERNAL_SECRET:-}")" >> /etc/mihomo-subscribe.env
printf "EXTERNAL_UI_NAME='%s'\n" "$(escape_env_value "${EXTERNAL_UI_NAME:-}")" >> /etc/mihomo-subscribe.env
printf "EXTERNAL_UI_URL='%s'\n" "$(escape_env_value "${EXTERNAL_UI_URL:-}")" >> /etc/mihomo-subscribe.env

crond -b
