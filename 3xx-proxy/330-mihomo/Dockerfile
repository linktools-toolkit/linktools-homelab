FROM metacubex/mihomo:{{ MIHOMO_TAG }}

RUN apk add --no-cache curl yq

COPY scripts/entrypoint.sh /docker-entrypoint.sh
COPY scripts/crond.sh /docker-entrypoint.d/00-crond.sh
COPY scripts/subscribe.sh /docker-entrypoint.d/01-subscribe.sh
COPY scripts/update-subscription.sh /etc/periodic/hourly/update-subscription

RUN chmod +x \
    /docker-entrypoint.sh \
    /docker-entrypoint.d/00-crond.sh \
    /docker-entrypoint.d/01-subscribe.sh \
    /etc/periodic/hourly/update-subscription

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/mihomo", "-d", "/root/.config/mihomo"]
