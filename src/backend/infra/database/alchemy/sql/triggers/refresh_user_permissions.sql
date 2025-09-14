CREATE TABLE IF NOT EXISTS mv_user_permissions_refresh (
    id  boolean PRIMARY KEY DEFAULT true,
    dirty boolean NOT NULL    DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- next --
INSERT INTO mv_user_permissions_refresh (id, dirty)
VALUES (true, false)
ON CONFLICT (id) DO NOTHING;

-- next --
CREATE OR REPLACE FUNCTION mark_mv_user_permissions_dirty()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE mv_user_permissions_refresh
    SET dirty = true, updated_at = now()
    WHERE id = true;

    RETURN NULL;
END;
$$;

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_user_role ON user_role;
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_user_role
AFTER INSERT OR UPDATE OR DELETE ON user_role
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_role ON "role";
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_role
AFTER INSERT OR UPDATE OR DELETE ON "role"
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_permission ON permission;
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_permission
AFTER INSERT OR UPDATE OR DELETE ON permission
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_role_permission ON role_permission;
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_role_permission
AFTER INSERT OR UPDATE OR DELETE ON role_permission
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_role_permission_field ON role_permission_field;
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_role_permission_field
AFTER INSERT OR UPDATE OR DELETE ON role_permission_field
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
DROP TRIGGER IF EXISTS trg_mv_user_permissions_dirty_field ON permission_field;
-- next --
CREATE TRIGGER trg_mv_user_permissions_dirty_field
AFTER INSERT OR UPDATE OR DELETE ON permission_field
FOR EACH STATEMENT
EXECUTE FUNCTION mark_mv_user_permissions_dirty();

-- next --
CREATE OR REPLACE FUNCTION ensure_mv_user_permissions_refresh_job(
    p_schedule text DEFAULT '* * * * *',
    p_jobname  text DEFAULT 'mv_user_permissions_refresh_job'
) RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_jobid integer;
    v_cmd text := $cmd$
        DO $X$
        DECLARE v_dirty boolean;
        BEGIN
            SELECT dirty INTO v_dirty
            FROM mv_user_permissions_refresh
            WHERE id = true;

            IF v_dirty THEN
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_permissions;
                UPDATE mv_user_permissions_refresh
                SET dirty = false, updated_at = now()
                WHERE id = true;
            END IF;
        END
        $X$;
    $cmd$;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        EXECUTE 'CREATE EXTENSION pg_cron';
    END IF;

    INSERT INTO mv_user_permissions_refresh (id, dirty)
    VALUES (true, false)
    ON CONFLICT (id) DO NOTHING;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indrelid
        WHERE c.relkind = 'm'
        AND c.relname = 'mv_user_permissions'
        AND i.indisunique
    ) THEN
        RAISE EXCEPTION 'mv_user_permissions must have at least one UNIQUE index for CONCURRENTLY refresh';
    END IF;

    SELECT jobid
    INTO v_jobid
    FROM cron.job
    WHERE jobname = p_jobname
        AND database = current_database()
    ORDER BY jobid DESC
    LIMIT 1;

    IF v_jobid IS NULL THEN
        SELECT cron.schedule_in_database(
            p_jobname,
            p_schedule,
            v_cmd,
            current_database()
        )
        INTO v_jobid;
    ELSE
        PERFORM cron.alter_job(
            jobid => v_jobid,
            schedule => p_schedule,
            command => v_cmd,
            active => true
    );
    END IF;

    RETURN v_jobid;
END;
$$;

-- next --
REFRESH MATERIALIZED VIEW mv_user_permissions;

-- next --
SELECT ensure_mv_user_permissions_refresh_job('* * * * *');
