FROM guacamole/guacamole:{{ GUACAMOLE_TAG }} AS schema

FROM postgres:16-alpine

# Copy only the schema; upstream 002-create-admin-user.sql creates guacadmin.
COPY --from=schema /opt/guacamole/extensions/guacamole-auth-jdbc/postgresql/schema/001-create-schema.sql /docker-entrypoint-initdb.d/001-create-schema.sql
