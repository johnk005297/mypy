select datname as name from pg_database
where datname like %(name)s;
