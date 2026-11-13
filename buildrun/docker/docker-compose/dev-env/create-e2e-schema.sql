\set ON_ERROR_STOP on

BEGIN ISOLATION LEVEL REPEATABLE READ;
DROP SCHEMA IF EXISTS e2e_schema CASCADE;
CREATE SCHEMA e2e_schema;
DO
$$
    DECLARE
        public_table record;
    BEGIN
        FOR public_table IN SELECT tablename FROM pg_tables WHERE schemaname = 'public'
            LOOP
                EXECUTE format('CREATE TABLE e2e_schema.%I AS TABLE public.%I', public_table.tablename,
                               public_table.tablename);
            END LOOP;
    END
$$;
COMMIT;
