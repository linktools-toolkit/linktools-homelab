FROM guacamole/guacamole:{{ GUACAMOLE_TAG }} AS schema
RUN /opt/guacamole/bin/initdb.sh --postgresql > /tmp/guacamole.sql

FROM postgres:16-alpine

COPY --from=schema /tmp/guacamole.sql /docker-entrypoint-initdb.d/guacamole.sql
COPY scripts/admin.sql /docker-entrypoint-initdb.d/secure-admin.sql
