# Migrations

Plain, hand-written SQL migrations for the `distributed_inference` MySQL database.
Numbered in the order they must be applied — always run in order, never skip one.

| File | Purpose |
|---|---|
| `001_init.sql` | Creates the database and the four core tables: `workers`, `tasks`, `task_worker_map`, `activity_log`. |
| `002_add_worker_type_and_task_requeued.sql` | Adds `workers.worker_type` (gpu / apple_silicon / cpu_high / cpu_standard) and the `task_requeued` activity event, used by the failed-node task reclaim logic. |
| `003_add_blob_urls.sql` | Adds `tasks.input_url`, `tasks.result_url`, `tasks.result_mimetype` for image/video/pdf task inputs and outputs stored in object storage (Google Drive). |
| `004_add_node_name.sql` | Adds `workers.node_name`, a human-friendly label for each node (from its `NODE_NAME` env var) shown alongside its `worker_id` in Master's logs. |

## Applying

Fresh database:

```bash
mysql -u root -p < 001_init.sql
mysql -u root -p < 002_add_worker_type_and_task_requeued.sql
mysql -u root -p < 003_add_blob_urls.sql
mysql -u root -p < 004_add_node_name.sql
```

Or from an interactive shell:

```sql
SOURCE 001_init.sql;
SOURCE 002_add_worker_type_and_task_requeued.sql;
SOURCE 003_add_blob_urls.sql;
SOURCE 004_add_node_name.sql;
```

If `Master/backend/app.py` already ran once against a fresh database, `Base.metadata.create_all()`
will have created `001_init.sql`'s tables for you automatically — in that case only
the later numbered migrations need to be applied manually, since SQLAlchemy's
`create_all` never alters existing tables.

## Adding a new migration

Create the next-numbered file (`005_*.sql`), write forward-only SQL (no down-migrations
for this MVP), and add a row to the table above describing what it does.
