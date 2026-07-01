-- Runs ONCE at PostgreSQL first-init, BEFORE the application tables exist
-- (tables are created later by `alembic upgrade head`).
--
-- Therefore only table-independent, idempotent setup belongs here. Inserting
-- into users/categories here would fail because those tables don't exist yet.
-- The default admin user, categories and cases are seeded AFTER the migration
-- by `python -m app.db.seed` (see deploy.sh / start.sh).
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
