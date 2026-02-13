#!/bin/sh

if [ $# != 1 ] ; then
    echo "USAGE: $0 <ssid>"
    echo " e.g.: $0 alibaba-guest"
    exit 1;
fi

log() {
    echo "[$(date +%Y-%m-%d" "%H:%M:%S)] $*"
}

number=0
while [ "$number" -lt 3 ]; do
    curl http://baidu.com >/dev/null 2>&1 && log "network is ok" && exit 0
    number=$((number + 1))
done

line=$(uci show | awk "/.ssid='$1'/")
iface=${line%%.ssid=*}

if [ -z "$line" ]
then
    log "can not find ssid $1"
    exit 1;
else
    log "find $iface"
fi

log set "$iface.disabled=1"
uci set "$iface.disabled=1"
uci commit
env -i /bin/ubus call network reload >/dev/null 2>/dev/null

sleep 10

log del "$iface.disabled"
uci del "$iface.disabled"
uci commit
env -i /bin/ubus call network reload >/dev/null 2>/dev/null
