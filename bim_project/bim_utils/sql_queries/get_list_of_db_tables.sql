SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' and table_name ilike %(name)s;
