#!/usr/bin/env python3
"""
Migration rollback script for containerized deployments.
Provides safe rollback functionality with validation.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
import sqlalchemy as sa
from backend.app.database import get_database_url

def get_alembic_config():
    """Get Alembic configuration."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", get_database_url())
    return config

def get_current_revision():
    """Get current database revision."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)

    with sa.create_engine(get_database_url()).connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        return current_rev

def rollback_migration(revision="head:-1"):
    """
    Rollback to specified revision.

    Args:
        revision: Target revision (default: one step back from head)
    """
    try:
        print(f"Rolling back to revision: {revision}")
        config = get_alembic_config()
        command.downgrade(config, revision)
        print("Rollback completed successfully")

        # Verify rollback
        current = get_current_revision()
        print(f"Current revision after rollback: {current}")

    except Exception as e:
        print(f"Rollback failed: {e}")
        sys.exit(1)

def list_migrations():
    """List available migrations."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)

    print("Available migrations:")
    for rev in script.walk_revisions():
        print(f"  {rev.revision}: {rev.doc}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migration_rollback.py <command> [revision]")
        print("Commands:")
        print("  rollback [revision]  - Rollback to revision (default: head:-1)")
        print("  current             - Show current revision")
        print("  list                - List available migrations")
        sys.exit(1)

    command = sys.argv[1]

    if command == "rollback":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head:-1"
        rollback_migration(revision)
    elif command == "current":
        current = get_current_revision()
        print(f"Current revision: {current}")
    elif command == "list":
        list_migrations()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)