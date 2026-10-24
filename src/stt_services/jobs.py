"""Durable, transactionally bounded FIFO jobs on a local SQLite database."""

import hashlib
import shutil
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

from stt_services.config import Settings

DAY = 86400


def terminal_retention(status: str) -> int:
    return 7 * DAY if status == "succeeded" else DAY


class QueueFull(ValueError):
    pass


class JobStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        settings.prepare()
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, status TEXT NOT NULL,
                    suffix TEXT NOT NULL, created_at REAL NOT NULL,
                    started_at REAL, finished_at REAL, error TEXT
                );
                CREATE INDEX IF NOT EXISTS jobs_status_created ON jobs(status, created_at);
                CREATE TABLE IF NOT EXISTS worker (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    owner TEXT NOT NULL, heartbeat_at REAL NOT NULL, status TEXT NOT NULL
                );
            """)
            # Serialize schema upgrades across API and worker startup on existing stores.
            db.execute("BEGIN IMMEDIATE")
            columns = {row["name"] for row in db.execute("PRAGMA table_info(jobs)")}
            if "progress_percent" not in columns:
                db.execute(
                    "ALTER TABLE jobs ADD COLUMN progress_percent INTEGER NOT NULL DEFAULT 0"
                )
                db.execute("UPDATE jobs SET progress_percent=100 WHERE status='succeeded'")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.settings.database, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self, job_id: str, suffix: str, staging: Path) -> None:
        destination = self.settings.jobs_dir / job_id
        moved = False
        try:
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                count = db.execute("SELECT count(*) FROM jobs WHERE status='queued'").fetchone()[0]
                if count >= self.settings.max_queued:
                    raise QueueFull("Queue is full; try again after a job starts")
                staging.rename(destination)
                moved = True
                db.execute(
                    "INSERT INTO jobs(id,status,suffix,created_at) VALUES(?,?,?,?)",
                    (job_id, "queued", suffix, time.time()),
                )
        except BaseException:
            if moved:
                shutil.rmtree(destination, ignore_errors=True)
            raise

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None

    def claim(self) -> dict[str, Any] | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            started_at = time.time()
            db.execute(
                "UPDATE jobs SET status='running',started_at=? WHERE id=?", (started_at, row["id"])
            )
            return {**dict(row), "status": "running", "started_at": started_at}

    def update_progress(self, job_id: str, percent: int) -> None:
        """Persist increasing estimates only for running jobs; success owns 100%."""
        percent = min(99, max(0, percent))
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET progress_percent=? "
                "WHERE id=? AND status='running' AND progress_percent<?",
                (percent, job_id, percent),
            )

    def finish(self, job_id: str, error: str | None = None) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET status=?,finished_at=?,error=?,"
                "progress_percent=CASE WHEN ? IS NULL THEN 100 ELSE progress_percent END "
                "WHERE id=?",
                ("failed" if error else "succeeded", time.time(), error, error, job_id),
            )

    def recover(self) -> None:
        # Only the process holding the worker file lock may call this.
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET status='failed',error='interrupted',finished_at=? "
                "WHERE status='running'",
                (time.time(),),
            )

    def heartbeat(self, owner: str, status: str) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO worker VALUES(1,?,?,?) ON CONFLICT(singleton) DO UPDATE SET "
                "owner=excluded.owner,heartbeat_at=excluded.heartbeat_at,status=excluded.status",
                (owner, time.time(), status),
            )

    def health(self) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute("SELECT heartbeat_at,status FROM worker WHERE singleton=1").fetchone()
        ready = bool(
            row
            and row["status"] == "ready"
            and time.time() - row["heartbeat_at"] < self.settings.heartbeat_timeout_seconds
        )
        return {
            "ready": ready,
            "api": "ready",
            "worker": "ready" if ready else "unavailable",
            "model_ready": ready,
            "heartbeat_at": row["heartbeat_at"] if row else None,
            "heartbeat_age_seconds": max(0, time.time() - row["heartbeat_at"]) if row else None,
        }

    def cleanup(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM jobs WHERE status IN ('succeeded','failed')"
            ).fetchall()
        for row in rows:
            age = now - row["finished_at"]
            directory = self.settings.jobs_dir / row["id"]
            try:
                with self.result_lock(row["id"]):
                    if age >= terminal_retention(row["status"]):
                        self._remove(directory)
                        with self.connect() as db:
                            db.execute(
                                "DELETE FROM jobs WHERE id=? AND status IN ('succeeded','failed')",
                                (row["id"],),
                            )
                    elif age >= DAY:
                        (directory / f"input{row['suffix']}").unlink(missing_ok=True)
            except (OSError, Timeout):
                continue  # Retry later if a download or filesystem error prevents deletion.
        # Remove stale uploads/crash artifacts, never active/tracked directories.
        with self.connect() as db:
            tracked = {row[0] for row in db.execute("SELECT id FROM jobs")}
        for directory in self.settings.jobs_dir.iterdir():
            try:
                if directory.name not in tracked and now - directory.stat().st_mtime >= DAY:
                    job_id = directory.name.removeprefix(".upload-")
                    with self.result_lock(job_id):
                        # Admission may have committed after the earlier inventory query.
                        if self.get(job_id) is None:
                            self._remove(directory)
            except (OSError, Timeout):
                continue

    def result_lock(self, job_id: str) -> FileLock:
        locks = self.settings.data_dir / "locks"
        locks.mkdir(exist_ok=True)
        # Fixed stripes bound lock metadata even for unlimited rejected uploads on Unix,
        # where flock lock files remain after release. Never unlink a live lock inode.
        bucket = int.from_bytes(hashlib.sha256(job_id.encode()).digest()[:2], "big") % 1024
        return FileLock(locks / f"bucket-{bucket:04}.lock", timeout=0, thread_local=False)

    def _remove(self, path: Path) -> None:
        root = self.settings.jobs_dir.resolve()
        if path.is_symlink():
            path.unlink()
        elif path.resolve().is_relative_to(root) and path.resolve() != root:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
