# Persisted data and ownership

## Storage owner

`STT_DATA_DIR` owns service-managed SQLite state, API uploads, published service results, worker/lease markers, and their retention. Its default is external to the repository (`[private local path]` on Windows; `~/.local/share/ai-stt` elsewhere). `config.py` resolves configured paths. CLI input and caller-selected CLI output remain user-owned and are never expired by service cleanup.

## SQLite entities

`src/stt_services/infrastructure/sqlite_job_repository.py` creates and upgrades the schema transactionally. SQLite WAL is used for concurrent API/worker access. The adapter maps internal typed `Job` entities from `src/stt_services/domain/job_entity.py` to persistence rows; the repository contract lives in `src/stt_services/application/job_repository.py`.

| Table | Fields/invariants | Purpose and lifecycle |
| --- | --- | --- |
| `jobs` | `id`, `status`, `suffix`, `created_at`, `started_at`, `finished_at`, `error`, `progress_percent`; index on `(status, created_at)`. Status transitions are queued → running → succeeded/failed; recovery converts prior running jobs to failed/interrupted. Progress is an integer, 0 for queued, capped at 99 while running, and 100 only after publication and success commit. | Durable queue and safe client-visible status; IDs are generated 32-character lowercase hex. Queue admission and FIFO claim use transactions. No automatic retry. |
| `worker` | Singleton row with owner, heartbeat, and status. | Worker readiness/ownership. An OS-backed `worker.lock` prevents concurrent workers for the same data directory; heartbeat remains independent of slow inference and cleanup. |

Service files live under `jobs/<job_id>/input.<extension>` and `jobs/<job_id>/result/`; upload and result staging are private sibling directories. Fixed lock buckets and `worker.lock` are filesystem coordination markers, not relational entities. SQLite and filesystem publication are coordinated by ordering and recovery, not one cross-resource transaction.

## Retention and migrations

- Successful service inputs expire after 24 hours; results and status expire after seven days.
- Failed inputs, artifacts, and status expire after 24 hours.
- Queued/running jobs and active downloads are excluded from cleanup; filesystem failures are retried on a later sweep.
- CLI sources/results, caches, environment files, and external references are outside managed cleanup.
- Schema upgrades run transactionally and preserve existing jobs. The progress migration initializes old succeeded rows to 100 and other old rows to 0 because prior progress was not recorded.

The MVP architecture/spec and the implementation in `infrastructure/sqlite_job_repository.py`, `workers/job_worker.py`, and `config.py` own details. For a schema change, document migration/rollback behavior, update the upgrade tests, preserve old jobs unless an accepted decision says otherwise, and verify cleanup against an isolated data directory. Never point cleanup or test fixtures at production/user data.
