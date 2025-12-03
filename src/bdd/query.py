"""
SQL query definitions for database operations.
"""

from sqlalchemy import text

ENABLE_PGCRYPTO = text("""
CREATE EXTENSION IF NOT EXISTS pgcrypto;
""")

CHECK_TABLES = text(
    """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
"""
)

CLEAR_ALL_TABLES = text(
    """
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('TRUNCATE TABLE public.%I RESTART IDENTITY CASCADE;', tabname);
    END LOOP;
END $$;
"""
)


DROP_ALL_TABLES = text(
"""
DO $$
DECLARE
    tabname text;
BEGIN
    FOR tabname IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE;', tabname);
    END LOOP;
END $$;
"""
)

POPULATE_TABLES = text("""
INSERT INTO exemple (id, name)
VALUES
    (gen_random_uuid(), 'exemple 1'),
    (gen_random_uuid(), 'exemple 2'),
    (gen_random_uuid(), 'exemple 3'),
    (gen_random_uuid(), 'exemple 4'),
    (gen_random_uuid(), 'exemple 5'));
""")
