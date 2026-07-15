"""Append-only SQLite execution ledger stored inside one AI run directory."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from buduunkhad.ai.contracts import (
    AIUsage,
    PromptIdentity,
    SchemaIdentity,
    TaskType,
    require_aware_datetime,
)
from buduunkhad.geospatial_ai.path_safety import StorageRoots


class JobLedgerError(RuntimeError):
    """Ledger record or transition is invalid."""


class LedgerStatus(StrEnum):
    PREPARED = "PREPARED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INGESTED = "INGESTED"
    PROCESSED = "PROCESSED"


class LedgerJobCreate(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    run_id: str
    phase_id: str
    task_type: TaskType
    request_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    package_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_assets: tuple[tuple[str, str], ...]
    prompt: PromptIdentity
    schema_identity: SchemaIdentity
    provider: str
    model: str
    created_at: datetime
    retry_number: int = Field(default=0, ge=0)

    @field_validator("created_at")
    @classmethod
    def _aware_creation_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "created_at")


class LedgerEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    sequence: int
    status: LedgerStatus
    occurred_at: datetime
    response_file: str | None = None
    response_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    usage: AIUsage | None = None
    estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    error_category: str | None = None

    @field_validator("occurred_at")
    @classmethod
    def _aware_event_time(cls, value: datetime) -> datetime:
        return require_aware_datetime(value, "occurred_at")


class LedgerJobView(BaseModel):
    model_config = ConfigDict(frozen=True)

    job: LedgerJobCreate
    status: LedgerStatus
    events: tuple[LedgerEvent, ...]

    @property
    def started_at(self) -> datetime | None:
        return next(
            (event.occurred_at for event in self.events if event.status is LedgerStatus.RUNNING),
            None,
        )

    @property
    def completed_at(self) -> datetime | None:
        return next(
            (
                event.occurred_at
                for event in reversed(self.events)
                if event.status
                in {LedgerStatus.SUCCEEDED, LedgerStatus.INGESTED, LedgerStatus.PROCESSED}
            ),
            None,
        )

    @property
    def failed_at(self) -> datetime | None:
        return next(
            (event.occurred_at for event in self.events if event.status is LedgerStatus.FAILED),
            None,
        )


_TRANSITIONS: dict[LedgerStatus, frozenset[LedgerStatus]] = {
    LedgerStatus.PREPARED: frozenset(
        {LedgerStatus.RUNNING, LedgerStatus.INGESTED, LedgerStatus.FAILED}
    ),
    LedgerStatus.RUNNING: frozenset({LedgerStatus.SUCCEEDED, LedgerStatus.FAILED}),
    LedgerStatus.SUCCEEDED: frozenset({LedgerStatus.INGESTED, LedgerStatus.PROCESSED}),
    LedgerStatus.INGESTED: frozenset({LedgerStatus.PROCESSED, LedgerStatus.FAILED}),
    LedgerStatus.FAILED: frozenset(),
    LedgerStatus.PROCESSED: frozenset(),
}


class AIJobLedger:
    """Transactionally append execution state without human-review semantics."""

    def __init__(self, path: Path, *, roots: StorageRoots, run_id: str) -> None:
        self.path = roots.assert_writable(path, run_id=run_id)
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def add_job(self, job: LedgerJobCreate) -> None:
        if job.run_id != self.run_id:
            raise JobLedgerError("ledger job run ID mismatch")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    INSERT INTO jobs (
                        job_id, run_id, phase_id, task_type, request_fingerprint,
                        package_manifest_sha256, source_assets_json, prompt_json, schema_json,
                        provider, model,
                        created_at, retry_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id,
                        job.run_id,
                        job.phase_id,
                        job.task_type.value,
                        job.request_fingerprint,
                        job.package_manifest_sha256,
                        json.dumps(job.source_assets, separators=(",", ":")),
                        job.prompt.model_dump_json(),
                        job.schema_identity.model_dump_json(),
                        job.provider,
                        job.model,
                        job.created_at.isoformat(),
                        job.retry_number,
                    ),
                )
                self._insert_event(
                    connection,
                    job_id=job.job_id,
                    status=LedgerStatus.PREPARED,
                    occurred_at=job.created_at,
                )
            except sqlite3.IntegrityError as exc:
                raise JobLedgerError(f"job already exists: {job.job_id}") from exc

    def transition(
        self,
        job_id: str,
        status: LedgerStatus,
        *,
        occurred_at: datetime | None = None,
        response_file: str | None = None,
        response_sha256: str | None = None,
        usage: AIUsage | None = None,
        estimated_cost_usd: Decimal | None = None,
        error_category: str | None = None,
        max_concurrency: int | None = None,
        max_requests: int | None = None,
        max_total_estimated_cost_usd: Decimal | None = None,
    ) -> LedgerJobView:
        timestamp = occurred_at or datetime.now(UTC)
        timestamp = require_aware_datetime(timestamp, "occurred_at")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current, previous_time = self._current_state(connection, job_id)
            if status not in _TRANSITIONS[current]:
                raise JobLedgerError(f"invalid job transition: {current.value} -> {status.value}")
            if max_concurrency is not None:
                if status is not LedgerStatus.RUNNING or max_concurrency < 1:
                    raise JobLedgerError("concurrency limit applies only to valid job starts")
                running = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM job_events AS candidate
                    WHERE candidate.status = ?
                      AND NOT EXISTS (
                        SELECT 1
                        FROM job_events AS later
                        WHERE later.job_id = candidate.job_id
                          AND later.sequence > candidate.sequence
                      )
                    """,
                    (LedgerStatus.RUNNING.value,),
                ).fetchone()
                if int(running["count"]) >= max_concurrency:
                    raise JobLedgerError("AI job concurrency limit would be exceeded")
            if max_requests is not None or max_total_estimated_cost_usd is not None:
                if status is not LedgerStatus.RUNNING:
                    raise JobLedgerError("request and cost limits apply only to job starts")
                if max_requests is not None:
                    if max_requests < 1:
                        raise JobLedgerError("maximum requests must be positive")
                    started = connection.execute(
                        "SELECT COUNT(DISTINCT job_id) AS count FROM job_events WHERE status = ?",
                        (LedgerStatus.RUNNING.value,),
                    ).fetchone()
                    if int(started["count"]) >= max_requests:
                        raise JobLedgerError("AI run request limit would be exceeded")
                if max_total_estimated_cost_usd is not None:
                    if max_total_estimated_cost_usd < 0 or estimated_cost_usd is None:
                        raise JobLedgerError(
                            "cost-limited job starts require a non-negative cost estimate"
                        )
                    committed_rows = connection.execute(
                        """
                        SELECT estimated_cost_usd
                        FROM job_events AS candidate
                        WHERE candidate.estimated_cost_usd IS NOT NULL
                          AND NOT EXISTS (
                            SELECT 1
                            FROM job_events AS later
                            WHERE later.job_id = candidate.job_id
                              AND later.estimated_cost_usd IS NOT NULL
                              AND later.sequence > candidate.sequence
                          )
                        """
                    ).fetchall()
                    committed = sum(
                        (Decimal(row["estimated_cost_usd"]) for row in committed_rows),
                        start=Decimal("0"),
                    )
                    if committed + estimated_cost_usd > max_total_estimated_cost_usd:
                        raise JobLedgerError("AI run estimated-cost limit would be exceeded")
            if timestamp < previous_time:
                raise JobLedgerError("job transition time precedes the current ledger state")
            if status is LedgerStatus.FAILED and not error_category:
                raise JobLedgerError("failed jobs require an error category")
            if status is not LedgerStatus.FAILED and error_category is not None:
                raise JobLedgerError("error category is valid only for failed jobs")
            if response_file is not None:
                relative = Path(response_file)
                if relative.is_absolute() or ".." in relative.parts:
                    raise JobLedgerError("response paths must remain relative to the run directory")
            if (response_file is None) != (response_sha256 is None):
                raise JobLedgerError(
                    "ledger file paths and SHA-256 values must be recorded together"
                )
            self._insert_event(
                connection,
                job_id=job_id,
                status=status,
                occurred_at=timestamp,
                response_file=response_file,
                response_sha256=response_sha256,
                usage=usage,
                estimated_cost_usd=estimated_cost_usd,
                error_category=error_category,
            )
        return self.inspect(job_id)

    def inspect(self, job_id: str) -> LedgerJobView:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if row is None:
                raise JobLedgerError(f"job not found: {job_id}")
            event_rows = connection.execute(
                "SELECT * FROM job_events WHERE job_id = ? ORDER BY sequence", (job_id,)
            ).fetchall()
        job = LedgerJobCreate(
            job_id=row["job_id"],
            run_id=row["run_id"],
            phase_id=row["phase_id"],
            task_type=row["task_type"],
            request_fingerprint=row["request_fingerprint"],
            package_manifest_sha256=row["package_manifest_sha256"],
            source_assets=tuple(tuple(item) for item in json.loads(row["source_assets_json"])),
            prompt=PromptIdentity.model_validate_json(row["prompt_json"]),
            schema_identity=SchemaIdentity.model_validate_json(row["schema_json"]),
            provider=row["provider"],
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]),
            retry_number=row["retry_number"],
        )
        events = tuple(_event_from_row(row) for row in event_rows)
        return LedgerJobView(job=job, status=events[-1].status, events=events)

    def count_jobs(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()
        return int(row["count"])

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    phase_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    request_fingerprint TEXT NOT NULL,
                    package_manifest_sha256 TEXT NOT NULL,
                    source_assets_json TEXT NOT NULL,
                    prompt_json TEXT NOT NULL,
                    schema_json TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retry_number INTEGER NOT NULL CHECK (retry_number >= 0)
                );
                CREATE TABLE IF NOT EXISTS job_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    status TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    response_file TEXT,
                    response_sha256 TEXT,
                    usage_json TEXT,
                    estimated_cost_usd TEXT,
                    error_category TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_job_events_job ON job_events(job_id, sequence);
                CREATE TRIGGER IF NOT EXISTS jobs_no_update
                BEFORE UPDATE ON jobs BEGIN
                    SELECT RAISE(ABORT, 'jobs are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS jobs_no_delete
                BEFORE DELETE ON jobs BEGIN
                    SELECT RAISE(ABORT, 'jobs are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS job_events_no_update
                BEFORE UPDATE ON job_events BEGIN
                    SELECT RAISE(ABORT, 'job events are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS job_events_no_delete
                BEFORE DELETE ON job_events BEGIN
                    SELECT RAISE(ABORT, 'job events are append-only');
                END;
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _current_state(
        connection: sqlite3.Connection, job_id: str
    ) -> tuple[LedgerStatus, datetime]:
        row = connection.execute(
            """
            SELECT status, occurred_at
            FROM job_events
            WHERE job_id = ?
            ORDER BY sequence DESC
            LIMIT 1
            """,
            (job_id,),
        ).fetchone()
        if row is None:
            raise JobLedgerError(f"job not found: {job_id}")
        return LedgerStatus(row["status"]), datetime.fromisoformat(row["occurred_at"])

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection,
        *,
        job_id: str,
        status: LedgerStatus,
        occurred_at: datetime,
        response_file: str | None = None,
        response_sha256: str | None = None,
        usage: AIUsage | None = None,
        estimated_cost_usd: Decimal | None = None,
        error_category: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO job_events (
                job_id, status, occurred_at, response_file, response_sha256, usage_json,
                estimated_cost_usd, error_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                status.value,
                occurred_at.isoformat(),
                response_file,
                response_sha256,
                usage.model_dump_json() if usage else None,
                str(estimated_cost_usd) if estimated_cost_usd is not None else None,
                error_category,
            ),
        )


def _event_from_row(row: sqlite3.Row) -> LedgerEvent:
    usage_json = row["usage_json"]
    cost = row["estimated_cost_usd"]
    return LedgerEvent(
        sequence=row["sequence"],
        status=row["status"],
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        response_file=row["response_file"],
        response_sha256=row["response_sha256"],
        usage=AIUsage.model_validate_json(usage_json) if usage_json else None,
        estimated_cost_usd=Decimal(cost) if cost is not None else None,
        error_category=row["error_category"],
    )
