CREATE MATERIALIZED VIEW IF NOT EXISTS mv_user_permissions AS
WITH user_roles AS (
    SELECT ur.user_id, r.id AS role_id, r.level, r.name
    FROM user_role ur
    JOIN role r ON r.id = ur.role_id
),
candidates AS (
    SELECT
        ur.user_id,
        ur.role_id,
        r.is_superuser,
        ur.level AS role_level,
        r.name AS role_name,
        p.id AS permission_id,
        p.resource,
        (p.action)::text AS action,
        p.operation,
        p.description,
        p.key AS permission_key,
        rp.scope::text AS scope
    FROM user_roles ur
    JOIN role_permission rp ON rp.role_id = ur.role_id
    JOIN permission p ON p.id = rp.permission_id
    JOIN "role" r ON r.id = ur.role_id
),
ranked AS (
    SELECT c.*,
            ROW_NUMBER() OVER (
            PARTITION BY user_id, permission_id
                ORDER BY
                    CASE WHEN c.is_superuser THEN 1 ELSE 0 END DESC,
                    c.role_level DESC,
                    c.role_id
            ) AS rn
    FROM candidates c
),
effective AS (
  SELECT * FROM ranked WHERE rn = 1
),
fields_raw AS (
    SELECT
        rpf.role_id,
        rpf.permission_id,
        pf.src::text AS src,
        rpf.effect::text AS effect,
        ARRAY_AGG(DISTINCT pf.name) AS names
    FROM role_permission_field rpf
    JOIN permission_field pf ON pf.id = rpf.field_id
    GROUP BY rpf.role_id, rpf.permission_id, pf.src, rpf.effect
),
fields_final AS (
    SELECT
        role_id,
        permission_id,
        JSONB_OBJECT_AGG(src, names) FILTER (WHERE effect = 'ALLOW') AS allow_fields,
        JSONB_OBJECT_AGG(src, names) FILTER (WHERE effect = 'DENY') AS deny_fields
    FROM fields_raw
    GROUP BY role_id, permission_id
)
SELECT
    e.user_id,
    e.role_id,
    e.role_name,
    e.role_level,
    e.permission_id,
    e.permission_key,
    e.resource,
    e.action,
    e.operation,
    e.description,
    e.scope,
    COALESCE(ff.allow_fields, '{}'::jsonb) AS allow_fields,
    COALESCE(ff.deny_fields, '{}'::jsonb) AS deny_fields
FROM effective e
LEFT JOIN fields_final ff
    ON ff.role_id = e.role_id AND ff.permission_id = e.permission_id
WITH DATA;

-- next --

DROP INDEX IF EXISTS mv_user_permissions_uid_key;

-- next --

CREATE UNIQUE INDEX IF NOT EXISTS mv_user_permissions_uid_key
    ON mv_user_permissions (user_id, permission_key);

-- next --

DROP INDEX IF EXISTS mv_user_permissions_user_id;

-- next --

CREATE INDEX IF NOT EXISTS mv_user_permissions_user_id
    ON mv_user_permissions (user_id);
