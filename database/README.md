# Database

- `migrations/`: ordered, immutable database migrations.
- `seed/`: deterministic local/demo seed data.

PostgreSQL and PostGIS are the intended persistence layer. Never edit an applied migration; add a new migration instead.
