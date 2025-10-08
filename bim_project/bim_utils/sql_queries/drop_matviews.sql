DO $$
DECLARE
    view_record RECORD;
BEGIN
    FOR view_record IN
        SELECT schemaname, matviewname
        FROM pg_matviews
        WHERE matviewname ilike '{0}'
    LOOP
        EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS '
                || quote_ident(view_record.schemaname) || '.'
                || quote_ident(view_record.matviewname)
                || ' CASCADE';
    END LOOP;
END;
$$;