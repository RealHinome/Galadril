CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;

CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
