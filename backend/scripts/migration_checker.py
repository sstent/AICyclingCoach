#!/usr/bin/env python3
"""
Migration compatibility and version checker for containerized deployments.
Validates migration integrity and compatibility before deployments.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from backend.app.database import get_database_url

class MigrationChecker:
    """Validates migration compatibility and integrity."""

    def __init__(self):
        self.config = self._get_alembic_config()
        self.script = ScriptDirectory.from_config(self.config)

    def _get_alembic_config(self):
        """Get Alembic configuration."""
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", get_database_url())
        return config

    def check_migration_files(self) -> Dict[str, bool]:
        """Check integrity of migration files."""
        results = {
            "files_exist": False,
            "proper_ordering": False,
            "no_duplicates": False,
            "valid_syntax": False
        }

        try:
            # Check if migration directory exists
            versions_dir = Path("alembic/versions")
            if not versions_dir.exists():
                print("❌ Migration versions directory not found")
                return results

            # Get all migration files
            migration_files = list(versions_dir.glob("*.py"))
            if not migration_files:
                print("⚠️  No migration files found")
                results["files_exist"] = True  # Empty is valid
                return results

            results["files_exist"] = True

            # Check for duplicate revision numbers
            revisions = []
            for file_path in migration_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Extract revision from file
                    if "revision = " in content:
                        rev_line = [line for line in content.split('\n') if "revision = " in line]
                        if rev_line:
                            rev = rev_line[0].split("'")[1]
                            if rev in revisions:
                                print(f"❌ Duplicate revision found: {rev}")
                                return results
                            revisions.append(rev)

            results["no_duplicates"] = True

            # Validate migration ordering
            try:
                # Get ordered revisions from script directory
                ordered_revisions = []
                for rev in self.script.walk_revisions():
                    ordered_revisions.append(rev.revision)

                # Check if our files match the ordering
                if set(revisions) == set(ordered_revisions):
                    results["proper_ordering"] = True
                else:
                    print("❌ Migration ordering mismatch")
                    return results

            except Exception as e:
                print(f"❌ Error checking migration ordering: {e}")
                return results

            # Basic syntax validation
            for file_path in migration_files:
                try:
                    compile(open(file_path).read(), file_path, 'exec')
                except SyntaxError as e:
                    print(f"❌ Syntax error in {file_path}: {e}")
                    return results

            results["valid_syntax"] = True
            print("✅ All migration files are valid")

        except Exception as e:
            print(f"❌ Error checking migration files: {e}")

        return results

    def check_database_state(self) -> Dict[str, any]:
        """Check current database migration state."""
        results = {
            "connected": False,
            "current_revision": None,
            "head_revision": None,
            "up_to_date": False,
            "pending_migrations": []
        }

        try:
            engine = create_engine(get_database_url())

            with engine.connect() as conn:
                results["connected"] = True

                # Get current revision
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()
                results["current_revision"] = current_rev

                # Get head revision
                head_rev = self.script.get_current_head()
                results["head_revision"] = head_rev

                # Check if up to date
                results["up_to_date"] = current_rev == head_rev

                # Get pending migrations
                if not results["up_to_date"]:
                    pending = []
                    for rev in self.script.walk_revisions():
                        if rev.revision > current_rev:
                            pending.append(rev.revision)
                    results["pending_migrations"] = pending

        except Exception as e:
            print(f"❌ Database connection error: {e}")

        return results

    def validate_deployment_readiness(self) -> bool:
        """Validate if deployment can proceed safely."""
        print("🔍 Checking deployment readiness...")

        # Check migration files
        file_checks = self.check_migration_files()
        all_files_good = all(file_checks.values())

        # Check database state
        db_checks = self.check_database_state()
        db_connected = db_checks["connected"]

        if not all_files_good:
            print("❌ Migration files have issues")
            return False

        if not db_connected:
            print("❌ Cannot connect to database")
            return False

        if not db_checks["up_to_date"]:
            print(f"⚠️  Database not up to date. Current: {db_checks['current_revision']}, Head: {db_checks['head_revision']}")
            print(f"Pending migrations: {db_checks['pending_migrations']}")

            # For deployment, we might want to allow this if migrations will be run
            print("ℹ️  This is acceptable if migrations will be run during deployment")
            return True

        print("✅ Deployment readiness check passed")
        return True

    def generate_migration_report(self) -> str:
        """Generate a detailed migration status report."""
        report = []
        report.append("# Migration Status Report")
        report.append("")

        # File checks
        report.append("## Migration Files")
        file_checks = self.check_migration_files()
        for check, status in file_checks.items():
            status_icon = "✅" if status else "❌"
            report.append(f"- {check}: {status_icon}")

        # Database state
        report.append("")
        report.append("## Database State")
        db_checks = self.check_database_state()
        for check, value in db_checks.items():
            if isinstance(value, list):
                value = ", ".join(value) if value else "None"
            report.append(f"- {check}: {value}")

        # Deployment readiness
        report.append("")
        report.append("## Deployment Readiness")
        ready = self.validate_deployment_readiness()
        readiness_icon = "✅" if ready else "❌"
        report.append(f"- Ready for deployment: {readiness_icon}")

        return "\n".join(report)

def main():
    if len(sys.argv) < 2:
        print("Usage: python migration_checker.py <command>")
        print("Commands:")
        print("  check-files     - Check migration file integrity")
        print("  check-db        - Check database migration state")
        print("  validate-deploy - Validate deployment readiness")
        print("  report          - Generate detailed migration report")
        sys.exit(1)

    checker = MigrationChecker()
    command = sys.argv[1]

    try:
        if command == "check-files":
            results = checker.check_migration_files()
            all_good = all(results.values())
            print("✅ Files OK" if all_good else "❌ Files have issues")
            sys.exit(0 if all_good else 1)

        elif command == "check-db":
            results = checker.check_database_state()
            print(f"Connected: {'✅' if results['connected'] else '❌'}")
            print(f"Up to date: {'✅' if results['up_to_date'] else '❌'}")
            print(f"Current: {results['current_revision']}")
            print(f"Head: {results['head_revision']}")

        elif command == "validate-deploy":
            ready = checker.validate_deployment_readiness()
            sys.exit(0 if ready else 1)

        elif command == "report":
            report = checker.generate_migration_report()
            print(report)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()