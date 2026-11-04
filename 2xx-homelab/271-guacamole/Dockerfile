FROM guacamole/guacamole:{{ GUACAMOLE_TAG }} AS schema

FROM postgres:16-alpine

# Copy the schema and idempotent single-user admin bootstrap.
COPY --from=schema /opt/guacamole/extensions/guacamole-auth-jdbc/postgresql/schema/001-create-schema.sql /docker-entrypoint-initdb.d/001-create-schema.sql
COPY scripts/002-create-admin-user.sql /docker-entrypoint-initdb.d/002-create-admin-user.sql
