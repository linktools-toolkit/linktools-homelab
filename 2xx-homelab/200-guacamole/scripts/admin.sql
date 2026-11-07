-- Replace the public guacadmin password created by upstream initdb.
UPDATE guacamole_user AS u
SET password_hash = decode(
        replace(gen_random_uuid()::text, '-', '') ||
        replace(gen_random_uuid()::text, '-', ''), 'hex'
    ),
    password_date = CURRENT_TIMESTAMP
FROM guacamole_entity AS e
WHERE u.entity_id = e.entity_id
  AND e.name = 'guacadmin'
  AND e.type = 'USER';
