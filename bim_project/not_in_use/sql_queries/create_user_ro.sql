CREATE USER %(name)s WITH PASSWORD %(password)s IN ROLE pg_read_all_data;
GRANT pg_read_all_data TO %(name)s;
