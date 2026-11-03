#!/bin/sh
set -eu

: "${GUACAMOLE_ADMIN_USERNAME:?}"
psql -v ON_ERROR_STOP=1 -v admin_username="$GUACAMOLE_ADMIN_USERNAME" --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" <<'SQL'
BEGIN;
INSERT INTO guacamole_entity (name, type)
VALUES (:'admin_username', 'USER');

-- Header authentication supplies the identity. No known JDBC password is created.
INSERT INTO guacamole_user (entity_id, password_hash, password_salt, password_date)
SELECT entity_id,
       decode(replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''), 'hex'),
       decode(replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''), 'hex'),
       CURRENT_TIMESTAMP
FROM guacamole_entity
WHERE name = :'admin_username' AND type = 'USER';

INSERT INTO guacamole_system_permission (entity_id, permission)
SELECT e.entity_id, p.permission::guacamole_system_permission_type
FROM guacamole_entity e
CROSS JOIN (VALUES ('CREATE_CONNECTION'), ('CREATE_CONNECTION_GROUP'),
                   ('CREATE_SHARING_PROFILE'), ('CREATE_USER'),
                   ('CREATE_USER_GROUP'), ('ADMINISTER')) AS p(permission)
WHERE e.name = :'admin_username' AND e.type = 'USER';

INSERT INTO guacamole_user_permission (entity_id, affected_user_id, permission)
SELECT e.entity_id, u.user_id, p.permission::guacamole_object_permission_type
FROM guacamole_entity e
JOIN guacamole_user u ON u.entity_id = e.entity_id
CROSS JOIN (VALUES ('READ'), ('UPDATE'), ('ADMINISTER')) AS p(permission)
WHERE e.name = :'admin_username' AND e.type = 'USER';
COMMIT;
SQL
