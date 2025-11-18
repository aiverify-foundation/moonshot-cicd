# Alembic Database Migrations

## What is Alembic?

Alembic is a database migration tool for SQLAlchemy. Think of it as version control for your database schema. Just like Git tracks changes to your code, Alembic tracks changes to your database structure (tables, columns, indexes, etc.).

**Why use Alembic?**
- **Version control for database**: Track all schema changes over time
- **Reproducible deployments**: Ensure all environments (dev, staging, production) have the same database structure
- **Team collaboration**: Multiple developers can work on schema changes without conflicts
- **Rollback capability**: Safely revert database changes if needed

**Challenges of Moonshot**
- **Upgrading/Downgrading of Moonshot**: Users may upgrade/downgrade existing version of Moonshot toto a specific version, will need to ensure DB Table Schema of SQLite DB at user's device has to be compatible to that version of Moonshot. Provide easy upgrade/downgrade path of schema regardless of which version of Moonshot user is currently using.
- **Schema Drift**: Detection of schema drift due to unintended manual modification of schema by user, as SQLite DB is accessible by user for modification. 
- **Maintainability**: Instead of keeping DDL of table schema for each version of Moonshot, schema versioning provide progressive schema changes required for specific version of Moonshot. 

## How Alembic Works in This Project

In the moonshot-cicd project, Alembic is used to manage the SQLite database schema located at `moonshot_core/data/database/moonshot.db`.

### Automatic Migration on Startup

**Important**: Migrations are automatically applied when the application starts!

The `SQLiteAdapter` class (in `moonshot_core/src/application/services/sqlite_adapter.py`) automatically runs all pending migrations when it's initialized. This means:

- When you start the application, any new migrations are automatically applied
- You typically don't need to manually run migrations in development
- The database schema stays up-to-date automatically

## File Structure

```
moonshot_core/
├── alembic.ini                    # Alembic configuration file
└── data/database/
    ├── moonshot.db                # SQLite database file
    └── alembic/
        ├── env.py                 # Migration environment setup
        ├── script.py.mako         # Template for new migration files
        ├── README                 # This file
        └── versions/              # Migration files (one per schema change)
            └── 2bf4af1172bc_add_llm_provider_and_config.py
            └── ...
```

### Key Files Explained

- **`alembic.ini`**: Main configuration file. Defines where migration scripts are located and database connection settings.
- **`env.py`**: Python script that sets up the migration environment. This is where Alembic connects to your database.
- **`versions/`**: Directory containing all migration files. Each file represents one schema change.
- **`script.py.mako`**: Template used when generating new migration files.

## Setup and Installation

Before working with Alembic migrations, you need to set up your development environment with the required dependencies.

### Prerequisites

- Python 3.12 or higher
- Poetry (Python dependency management tool)

### Installing Dependencies, run Moonshot to auto create SQLite database file and upgrade to latest schema version

This project uses Poetry for dependency management. Alembic and SQLAlchemy are included in the project dependencies defined in `pyproject.toml`.

   ```bash
   cd moonshot_core

   # Activate virtual environment on macOS/Linux
   source .venv/bin/activate

   # Install all dependencies including Alembic and SQLAlchemy
   poetry lock
   poetry install --with dev

   # Run Moonshot to create SQLite database file and upgrade to the latest schema version
   python run_api.py
   ```

## Common Alembic Commands

All Alembic commands should be run from the `moonshot_core/` directory (where `alembic.ini` is located).

### Check Migration Status

See which migrations have been applied and which are pending:

```bash
alembic current
```

View the full migration history:

```bash
alembic history
```

### View Current Database Revision

Check what version your database is currently at:

```bash
alembic current
```

### Apply Migrations Manually

While migrations run automatically on startup, you can also apply them manually:

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Apply one migration at a time
alembic upgrade +1
```

### Rollback Migrations

Revert to a previous database version (use with caution!):

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

## Creating New Migrations

When you need to change the database schema (add a table, modify a column, etc.), you create a migration file.

### Step-by-Step Guide

1. **Generate a new migration**:
   ```bash
   cd moonshot_core
   alembic revision -m "description_of_your_change"
   ```
   
   This creates a new file in `data/database/alembic/versions/` with a name like:
   `{revision_id}_{description_of_your_change}.py`

2. **Edit the migration file** to define your changes:
   - The `upgrade()` function defines what happens when applying the migration
   - The `downgrade()` function defines how to rollback the migration

3. **Test your migration**:
   ```bash
   # Apply the migration
   alembic upgrade head
   
   # Test rollback (optional)
   alembic downgrade -1
   alembic upgrade head
   ```

## Troubleshooting

### Migration Fails on Startup

If you see migration errors when the application starts:

1. Check the error message - it usually indicates what went wrong
2. Verify your migration file syntax is correct
3. Check that the `down_revision` in your migration matches the previous migration's `revision` ID
4. Ensure the database file exists and is writable

### Database Out of Sync

If your database schema doesn't match your migrations:

```bash
# Check current state
alembic current

# View migration history
alembic history

# Apply pending migrations
alembic upgrade head
```

### Need to Start Fresh

If you need to reset the database (⚠️ **WARNING**: This deletes all data, backup moonshot.db if required!):

```bash
cd moonshot_core

# Delete the database file
rm data/database/moonshot.db

# Restart the application - migrations will run automatically
python run_api.py
```

## Best Practices

1. **Always provide downgrade functions**: Every `upgrade()` should have a corresponding `downgrade()` to allow rollbacks. In Moonshot context, ensure downgrade do not remove any columns, tables to prevent data lost on users' side as they may temporary downgrade Moonshot and eventually upgrade back to latest version. 

2. **Always add and not remove column/table in new schema version**: Same reason as point 1, not removing existing column/table to ensure compatibility of all versions of Moonshot. Do DML data migration if required in the same migration version. 

3. **Test migrations**: Test both upgrade and downgrade paths before committing.

4. **One migration per release**: Consolidate all changes into one migration per release. Once a migration has been applied to production (released Moonshot), don't modify it. Create a new migration instead.

5. **SQLite DB limitation on alter table**: Some operations in SQLAlchemy may not be supported by SQLite DB such as ALTER statement on modifying column.
