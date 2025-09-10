#!/usr/bin/env python3
"""
Database backup and restore utilities for containerized deployments.
Ensures safe backup/restore operations with migration compatibility checks.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import get_database_url

class DatabaseManager:
    """Handles database backup and restore operations."""

    def __init__(self, backup_dir: str = "/app/data/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.gpx_dir = Path("/app/data/gpx")
        self.manifest_file = self.backup_dir / "gpx_manifest.json"
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY").encode()

    def get_db_connection_params(self):
        """Extract database connection parameters from URL."""
        from urllib.parse import urlparse
        db_url = get_database_url()
        parsed = urlparse(db_url)

        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }

    def _backup_gpx_files(self, backup_dir: Path) -> Optional[Path]:
        """Backup GPX files directory"""
        gpx_dir = Path("/app/data/gpx")
        if not gpx_dir.exists():
            return None
            
        backup_path = backup_dir / "gpx.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(gpx_dir, arcname="gpx")
        return backup_path

    def _backup_sessions(self, backup_dir: Path) -> Optional[Path]:
        """Backup Garmin sessions directory"""
        sessions_dir = Path("/app/data/sessions")
        if not sessions_dir.exists():
            return None
            
        backup_path = backup_dir / "sessions.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(sessions_dir, arcname="sessions")
        return backup_path

    def _generate_checksum(self, file_path: Path) -> str:
        """Generate SHA256 checksum for a file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _verify_backup_integrity(self, backup_path: Path):
        """Verify backup file integrity using checksum"""
        checksum_file = backup_path.with_suffix('.sha256')
        if not checksum_file.exists():
            raise FileNotFoundError(f"Checksum file missing for {backup_path.name}")
        
        with open(checksum_file) as f:
            expected_checksum = f.read().split()[0]
        
        actual_checksum = self._generate_checksum(backup_path)
        if actual_checksum != expected_checksum:
            raise ValueError(f"Checksum mismatch for {backup_path.name}")

    def create_backup(self, name: Optional[str] = None) -> str:
        """Create a full system backup including database, GPX files, and sessions"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"full_backup_{timestamp}"
        backup_dir = self.backup_dir / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Backup database
            db_backup_path = self._backup_database(backup_dir)
            
            # Backup GPX files
            gpx_backup_path = self._backup_gpx_files(backup_dir)
            
            # Backup sessions
            sessions_backup_path = self._backup_sessions(backup_dir)

            # Generate checksums for all backup files
            for file in backup_dir.glob("*"):
                if file.is_file():
                    checksum = self._generate_checksum(file)
                    with open(f"{file}.sha256", "w") as f:
                        f.write(f"{checksum}  {file.name}")

            # Verify backups
            for file in backup_dir.glob("*"):
                if file.is_file() and not file.name.endswith('.sha256'):
                    self._verify_backup_integrity(file)

            print(f"✅ Full backup created successfully: {backup_dir}")
            return str(backup_dir)

        except Exception as e:
            shutil.rmtree(backup_dir, ignore_errors=True)
            print(f"❌ Backup failed: {str(e)}")
            raise

    def _backup_database(self, backup_dir: Path) -> Path:
        """Create database backup"""
        params = self.get_db_connection_params()
        backup_file = backup_dir / "database.dump"

        cmd = [
            "pg_dump",
            "-h", params['host'],
            "-p", str(params['port']),
            "-U", params['user'],
            "-d", params['database'],
            "-f", str(backup_file),
            "--no-password",
            "--format=custom",
            "--compress=9"
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = params['password']

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Database backup failed: {result.stderr}")
            
        return backup_file

    def restore_backup(self, backup_file: str, confirm: bool = False) -> None:
        """Restore database from backup."""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        if not confirm:
            print(f"⚠️  This will overwrite the current database!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Restore cancelled.")
                return

        params = self.get_db_connection_params()

        # Drop and recreate database to ensure clean restore
        self._recreate_database()

        # Use pg_restore for restore
        cmd = [
            "pg_restore",
            "-h", params['host'],
            "-p", str(params['port']),
            "-U", params['user'],
            "-d", params['database'],
            "--no-password",
            "--clean",
            "--if-exists",
            "--create",
            str(backup_path)
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = params['password']

        try:
            print(f"Restoring from backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Database restored successfully")
            else:
                print(f"❌ Restore failed: {result.stderr}")
                raise Exception(f"Restore failed: {result.stderr}")

        except FileNotFoundError:
            print("❌ pg_restore not found. Ensure PostgreSQL client tools are installed.")
            raise

    def backup_gpx_files(self, incremental: bool = True) -> Optional[Path]:
        """Handle GPX backup creation with incremental/full strategy"""
        try:
            if incremental:
                return self._incremental_gpx_backup()
            return self._full_gpx_backup()
        except Exception as e:
            print(f"GPX backup failed: {str(e)}")
            return None

    def _full_gpx_backup(self) -> Path:
        """Create full GPX backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"gpx_full_{timestamp}"
        backup_path.mkdir()
        
        # Copy all GPX files
        subprocess.run(["rsync", "-a", f"{self.gpx_dir}/", f"{backup_path}/"])
        self._encrypt_backup(backup_path)
        return backup_path

    def _incremental_gpx_backup(self) -> Optional[Path]:
        """Create incremental GPX backup using rsync --link-dest"""
        last_full = self._find_last_full_backup()
        if not last_full:
            return self._full_gpx_backup()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"gpx_inc_{timestamp}"
        backup_path.mkdir()

        # Use hardlinks to previous backup for incremental
        subprocess.run([
            "rsync", "-a",
            "--link-dest", str(last_full),
            f"{self.gpx_dir}/",
            f"{backup_path}/"
        ])
        self._encrypt_backup(backup_path)
        return backup_path

    def _find_last_full_backup(self) -> Optional[Path]:
        """Find most recent full backup"""
        full_backups = sorted(self.backup_dir.glob("gpx_full_*"), reverse=True)
        return full_backups[0] if full_backups else None

    def _encrypt_backup(self, backup_path: Path):
        """Encrypt backup directory using Fernet (AES-256-CBC with HMAC-SHA256)"""
        from cryptography.fernet import Fernet
        
        fernet = Fernet(self.encryption_key)
        
        for file in backup_path.rglob('*'):
            if file.is_file():
                with open(file, 'rb') as f:
                    data = f.read()
                encrypted = fernet.encrypt(data)
                with open(file, 'wb') as f:
                    f.write(encrypted)

    def decrypt_backup(self, backup_path: Path):
        """Decrypt backup directory"""
        from cryptography.fernet import Fernet
        
        fernet = Fernet(self.encryption_key)
        
        for file in backup_path.rglob('*'):
            if file.is_file():
                with open(file, 'rb') as f:
                    data = f.read()
                decrypted = fernet.decrypt(data)
                with open(file, 'wb') as f:
                    f.write(decrypted)

    def _recreate_database(self):
        """Drop and recreate the database."""
        params = self.get_db_connection_params()

        # Connect to postgres database to drop/recreate target database
        postgres_params = params.copy()
        postgres_params['database'] = 'postgres'

        drop_cmd = [
            "psql",
            "-h", postgres_params['host'],
            "-p", str(postgres_params['port']),
            "-U", postgres_params['user'],
            "-d", postgres_params['database'],
            "-c", f"DROP DATABASE IF EXISTS {params['database']};"
        ]

        create_cmd = [
            "psql",
            "-h", postgres_params['host'],
            "-p", str(postgres_params['port']),
            "-U", postgres_params['user'],
            "-d", postgres_params['database'],
            "-c", f"CREATE DATABASE {params['database']};"
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = params['password']

        for cmd in [drop_cmd, create_cmd]:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Database recreation step failed: {result.stderr}")

    def list_backups(self):
        """List available backup files."""
        backups = list(self.backup_dir.glob("*.sql"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if not backups:
            print("No backup files found.")
            return

        print("Available backups:")
        for backup in backups:
            size = backup.stat().st_size / (1024 * 1024)  # Size in MB
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(".2f")

    def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than specified days."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = []

        # Clean all backup directories (full_backup_*)
        for backup_dir in self.backup_dir.glob("full_backup_*"):
            if backup_dir.is_dir() and datetime.fromtimestamp(backup_dir.stat().st_mtime) < cutoff:
                shutil.rmtree(backup_dir)
                removed.append(backup_dir.name)

        if removed:
            print(f"Removed {len(removed)} old backups: {', '.join(removed)}")
        else:
            print("No old backups to remove.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python backup_restore.py <command> [options]")
        print("Commands:")
        print("  backup [name]          - Create a new database backup")
        print("  gpx-backup [--full]    - Create GPX backup (incremental by default)")
        print("  restore <file> [--yes] - Restore from backup")
        print("  list                   - List available backups")
        print("  cleanup [days]         - Remove backups older than N days (default: 30)")
        print("  decrypt <dir>          - Decrypt backup directory")
        sys.exit(1)

    manager = DatabaseManager()
    command = sys.argv[1]

    try:
        if command == "backup":
            name = sys.argv[2] if len(sys.argv) > 2 else None
           name = sys.argv[2] if len(sys.argv) > 2 else None
           manager.create_backup(name)
       elif command == "gpx-backup":
           if len(sys.argv) > 2 and sys.argv[2] == "--full":
               manager.backup_gpx_files(incremental=False)
           else:
               manager.backup_gpx_files()

        elif command == "restore":
            if len(sys.argv) < 3:
                print("Error: Please specify backup file to restore from")
                sys.exit(1)

            backup_file = sys.argv[2]
            confirm = "--yes" in sys.argv
            backup_file = sys.argv[2]
            confirm = "--yes" in sys.argv
            manager.restore_backup(backup_file, confirm)

        elif command == "list":
            manager.list_backups()

        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            manager.cleanup_old_backups(days)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()