DO $$
DECLARE
    view_record RECORD;
BEGIN
    FOR view_record IN
        SELECT schemaname, matviewname
        FROM pg_matviews
        WHERE matviewname ILIKE '{0}'
    LOOP
        EXECUTE 'REFRESH MATERIALIZED VIEW '
                || quote_ident(view_record.schemaname) || '.'
                || quote_ident(view_record.matviewname);
    END LOOP;
END;
$$;
