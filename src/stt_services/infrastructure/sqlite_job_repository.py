import hashlib
import shutil
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from stt_services.application.job_errors import JobQueueFull
from stt_services.application.job_policy import DAY, terminal_retention
from stt_services.application.job_repository import Lease
from stt_services.config import Settings
from stt_services.domain.job_entity import Job, JobFailure, JobStatus, WorkerState


class SQLiteJobRepository:
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

    def enqueue(self, job_id: str, suffix: str, staging: Path) -> Job:
        destination = self.settings.jobs_dir / job_id
        moved = False
        created_at = time.time()
        try:
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                count = db.execute("SELECT count(*) FROM jobs WHERE status='queued'").fetchone()[0]
                if count >= self.settings.max_queued:
                    raise JobQueueFull("Queue is full; try again after a job starts")
                staging.rename(destination)
                moved = True
                db.execute(
                    "INSERT INTO jobs(id,status,suffix,created_at) VALUES(?,?,?,?)",
                    (job_id, JobStatus.QUEUED.value, suffix, created_at),
                )
        except BaseException:
            if moved:
                shutil.rmtree(destination, ignore_errors=True)
            raise
        return Job(
            id=job_id,
            status=JobStatus.QUEUED,
            suffix=suffix,
            created_at=created_at,
            started_at=None,
            finished_at=None,
            error=None,
            progress_percent=0,
        )

    def get(self, job_id: str) -> Job | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return self._job(row) if row else None

    def claim(self) -> Job | None:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            started_at = time.time()
            db.execute(
                "UPDATE jobs SET status='running',started_at=? WHERE id=?",
                (started_at, row["id"]),
            )
            return Job(
                id=row["id"],
                status=JobStatus.RUNNING,
                suffix=row["suffix"],
                created_at=row["created_at"],
                started_at=started_at,
                finished_at=row["finished_at"],
                error=JobFailure(row["error"]) if row["error"] else None,
                progress_percent=row["progress_percent"],
            )

    def update_progress(self, job_id: str, percent: int) -> None:
        percent = min(99, max(0, percent))
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET progress_percent=? "
                "WHERE id=? AND status='running' AND progress_percent<?",
                (percent, job_id, percent),
            )

    def finish(self, job_id: str, error: JobFailure | None = None) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET status=?,finished_at=?,error=?,"
                "progress_percent=CASE WHEN ? IS NULL THEN 100 ELSE progress_percent END "
                "WHERE id=?",
                (
                    (JobStatus.FAILED if error else JobStatus.SUCCEEDED).value,
                    time.time(),
                    error.value if error else None,
                    error.value if error else None,
                    job_id,
                ),
            )

    def fail_interrupted_jobs(self) -> None:
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET status='failed',error=?,finished_at=? WHERE status='running'",
                (JobFailure.INTERRUPTED.value, time.time()),
            )

    def heartbeat(self, owner: str, status: str) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO worker VALUES(1,?,?,?) ON CONFLICT(singleton) DO UPDATE SET "
                "owner=excluded.owner,heartbeat_at=excluded.heartbeat_at,status=excluded.status",
                (owner, time.time(), status),
            )

    def worker_state(self) -> WorkerState | None:
        with self.connect() as db:
            row = db.execute("SELECT heartbeat_at,status FROM worker WHERE singleton=1").fetchone()
        return WorkerState(row["status"], row["heartbeat_at"]) if row else None

    def cleanup(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM jobs WHERE status IN ('succeeded','failed')"
            ).fetchall()
        for row in rows:
            age = now - row["finished_at"]
            directory = self.settings.jobs_dir / row["id"]
            lease = self.try_acquire_lease(row["id"])
            if lease is None:
                continue
            try:
                if age >= terminal_retention(JobStatus(row["status"])):
                    self._remove(directory)
                    with self.connect() as db:
                        db.execute(
                            "DELETE FROM jobs WHERE id=? AND status IN ('succeeded','failed')",
                            (row["id"],),
                        )
                elif age >= DAY:
                    (directory / f"input{row['suffix']}").unlink(missing_ok=True)
            except OSError:
                continue
            finally:
                lease.release()
        with self.connect() as db:
            tracked = {row[0] for row in db.execute("SELECT id FROM jobs")}
        for directory in self.settings.jobs_dir.iterdir():
            try:
                if directory.name not in tracked and now - directory.stat().st_mtime >= DAY:
                    job_id = directory.name.removeprefix(".upload-")
                    lease = self.try_acquire_lease(job_id)
                    if lease is None:
                        continue
                    try:
                        if self.get(job_id) is None:
                            self._remove(directory)
                    finally:
                        lease.release()
            except OSError:
                continue

    def try_acquire_lease(self, job_id: str) -> Lease | None:
        locks = self.settings.data_dir / "locks"
        locks.mkdir(parents=True, exist_ok=True)
        bucket = int.from_bytes(hashlib.sha256(job_id.encode()).digest()[:2], "big") % 1024
        lease = FileLock(locks / f"bucket-{bucket:04}.lock", timeout=0, thread_local=False)
        try:
            lease.acquire()
        except Timeout:
            return None
        return lease

    def result_path(self, job_id: str, suffix: str) -> Path:
        return self.settings.jobs_dir / job_id / "result" / f"transcript.{suffix}"

    def _job(self, row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"],
            status=JobStatus(row["status"]),
            suffix=row["suffix"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            error=JobFailure(row["error"]) if row["error"] else None,
            progress_percent=row["progress_percent"],
        )

    def _remove(self, path: Path) -> None:
        root = self.settings.jobs_dir.resolve()
        if path.is_symlink():
            path.unlink()
        elif path.resolve().is_relative_to(root) and path.resolve() != root:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
