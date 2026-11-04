-- Provision the single fixed identity used by the Nginx Header Auth route.
-- The random password hash prevents password-based login; access is through Authelia only.

INSERT INTO guacamole_entity (name, type)
VALUES ('guacadmin', 'USER')
ON CONFLICT (type, name) DO NOTHING;

INSERT INTO guacamole_user (entity_id, password_hash, password_salt, password_date)
SELECT
    entity_id,
    decode(
        replace(gen_random_uuid()::text, '-', '') ||
        replace(gen_random_uuid()::text, '-', ''),
        'hex'
    ),
    decode(
        replace(gen_random_uuid()::text, '-', '') ||
        replace(gen_random_uuid()::text, '-', ''),
        'hex'
    ),
    CURRENT_TIMESTAMP
FROM guacamole_entity
WHERE name = 'guacadmin' AND type = 'USER'
ON CONFLICT (entity_id) DO NOTHING;

INSERT INTO guacamole_system_permission (entity_id, permission)
SELECT e.entity_id, p.permission::guacamole_system_permission_type
FROM guacamole_entity AS e
CROSS JOIN (
    VALUES
        ('CREATE_CONNECTION'),
        ('CREATE_CONNECTION_GROUP'),
        ('CREATE_SHARING_PROFILE'),
        ('CREATE_USER'),
        ('CREATE_USER_GROUP'),
        ('ADMINISTER')
) AS p(permission)
WHERE e.name = 'guacadmin' AND e.type = 'USER'
ON CONFLICT DO NOTHING;

INSERT INTO guacamole_user_permission (entity_id, affected_user_id, permission)
SELECT e.entity_id, u.user_id, p.permission::guacamole_object_permission_type
FROM guacamole_entity AS e
JOIN guacamole_user AS u ON u.entity_id = e.entity_id
CROSS JOIN (
    VALUES ('READ'), ('UPDATE'), ('ADMINISTER')
) AS p(permission)
WHERE e.name = 'guacadmin' AND e.type = 'USER'
ON CONFLICT DO NOTHING;
