select schemaname, matviewname, matviewowner 
from pg_catalog.pg_matviews
where matviewname  ilike %(name)s;
