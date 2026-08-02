COUNT_MATVIEWS_SQL = """
    SELECT count(*) 
    FROM pg_catalog.pg_matviews 
    WHERE matviewname ILIKE %s;
"""

LIST_MATVIEWS_SQL = """
    SELECT matviewname, schemaname 
    FROM pg_catalog.pg_matviews 
    WHERE matviewname ILIKE %s;
"""

TERMINATE_MATVIEW_CONNECTIONS_SQL = """
DO $$
DECLARE
    backend RECORD;
BEGIN
    FOR backend IN
        SELECT pg_stat_activity.pid AS pid, pg_locks.relation::regclass AS locked_relation
        FROM pg_stat_activity
        JOIN pg_locks ON pg_stat_activity.pid = pg_locks.pid
        WHERE pg_locks.relation::regclass::text ILIKE '{pattern}'
            AND pg_stat_activity.pid <> pg_backend_pid()
    LOOP
        EXECUTE format('SELECT pg_terminate_backend(%s)', backend.pid);
        RAISE NOTICE 'Terminated connection to matview % with PID %', backend.locked_relation, backend.pid;
    END LOOP;
END;
$$;
"""

DROP_MATVIEWS_CASCADE_SQL = """
DO $$
DECLARE
    view_record RECORD;
BEGIN
    FOR view_record IN
        SELECT schemaname, matviewname
        FROM pg_matviews
        WHERE matviewname ILIKE '{pattern}'
    LOOP
        EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS '
                || quote_ident(view_record.schemaname) || '.'
                || quote_ident(view_record.matviewname)
                || ' CASCADE';
    END LOOP;
END;
$$;
"""