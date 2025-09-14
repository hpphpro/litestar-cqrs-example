DO $$
DECLARE
    replica_user text := current_setting('replica.user', TRUE);
    replica_pass text := current_setting('replica.pass', TRUE);
BEGIN
    IF replica_user IS NULL OR replica_user = '' OR replica_pass IS NULL OR replica_pass = '' THEN
        RAISE NOTICE 'replica.user/replica.pass not set; skipping replication role creation';
    ELSIF NOT EXISTS (
            SELECT
                1
            FROM
                pg_roles
            WHERE
                rolname = replica_user) THEN
        EXECUTE format('CREATE ROLE %I WITH REPLICATION LOGIN PASSWORD %L', replica_user, replica_pass);
    END IF;
END
$$;
