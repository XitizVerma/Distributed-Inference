# Migrations

Schema for the `distributed_inference` MySQL database, kept as a single
hand-written SQL file.

| File | Purpose |
|---|---|
| `001_init.sql` | Full end-state schema: creates the database and all tables — `workers`, `tasks`, `task_worker_map`, `worker_metrics`, `models`, `model_commands`, `activity_log`. The previous incremental migrations (node name, worker type, blob URLs, worker metrics, model management) have all been folded into these `CREATE TABLE`s. |

## Applying

Fresh database:

```bash
mysql -u root -p < 001_init.sql
```

Or from an interactive shell:

```sql
SOURCE 001_init.sql;
```

If `Master/backend/app.py` already ran once against a fresh database,
`Base.metadata.create_all()` will have created these tables for you
automatically — SQLAlchemy's `create_all` creates any missing tables but never
alters existing ones, so this file is the source of truth for the exact column
definitions, enums, and indexes.

## Adding a new change

This project has no down-migrations. For a schema change, either update
`001_init.sql` in place (for a not-yet-deployed database) or add a new
next-numbered `002_*.sql` with forward-only SQL and document it in the table
above.
