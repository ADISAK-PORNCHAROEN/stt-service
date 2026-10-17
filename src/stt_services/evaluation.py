"""Explicit, content-bound evaluation of the owner's two approved recordings."""

import hashlib
import json
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import psutil
from pydantic import BaseModel, ConfigDict, Field

from stt_services.benchmark import hardware_report
from stt_services.config import Settings
from stt_services.pipeline import EngineFactory, Pipeline
from stt_services.references import (
    SpokenReference,
    parse_publisher_subtitles,
    score_reference,
    summarize_quality,
)


@dataclass(frozen=True)
class ApprovedRecording:
    id: str
    title: str
    source_sha256: str
    reference_sha256: str
    role: Literal["tuning", "final"]


APPROVED_RECORDINGS = (
    ApprovedRecording(
        "aC-QbxZB7RU",
        "Formal Words",
        "a76b7d7f787bb43912f5b1880f84ba8a301f41648583903f5364e49638d636ee",
        "c2722da771b40d9964ec7cdb0fd1ca369609e85bfb9de5c6e95b9477b9ef2231",
        "tuning",
    ),
    ApprovedRecording(
        "8qcinxUA4YA",
        "Conversation with Kob",
        "556a18e23be94d3122478d86b9a19b4afc99d1c3a573fdd78718fa3ea8a54181",
        "819b8a647b64f081f5156822e22a0645e374d0be628e7fa5f96d9d2d47fd7306",
        "final",
    ),
)


class ManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    source: str
    reference: str
    role: Literal["tuning", "final"]
    reviewed_reference: str | None = None


class EvaluationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    recordings: list[ManifestEntry] = Field(min_length=1, max_length=2)


def file_sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def file_stamp(path: Path) -> tuple[int, int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


@dataclass(frozen=True)
class AuthorizedMedia:
    source: Path
    approved: ApprovedRecording
    stamp: tuple[int, int, int, int, int]

    def assert_unchanged(self) -> None:
        if file_stamp(self.source) != self.stamp:
            raise ValueError("Authorized source changed after preflight")


def authorize_media(
    source: Path, catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS
) -> AuthorizedMedia:
    source = source.resolve(strict=True)
    stamp = file_stamp(source)
    digest = file_sha256(source)
    approved = next((item for item in catalog if item.source_sha256 == digest), None)
    if approved is None:
        raise ValueError("Real-model source is not authorized for this evaluation")
    media = AuthorizedMedia(source, approved, stamp)
    media.assert_unchanged()
    return media


@dataclass(frozen=True)
class VerifiedRecording:
    approved: ApprovedRecording
    source: Path
    reference: Path
    source_stamp: tuple[int, int, int, int, int]
    reference_stamp: tuple[int, int, int, int, int]
    reviewed_reference: Path | None
    reviewed_stamp: tuple[int, int, int, int, int] | None = None

    def assert_unchanged(self) -> None:
        if (
            file_stamp(self.source) != self.source_stamp
            or file_stamp(self.reference) != self.reference_stamp
            or (
                self.reviewed_reference is not None
                and file_stamp(self.reviewed_reference) != self.reviewed_stamp
            )
        ):
            raise ValueError(f"Approved recording or reference changed: {self.approved.id}")


def load_manifest(
    path: Path, catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS
) -> list[VerifiedRecording]:
    manifest = EvaluationManifest.model_validate_json(path.read_bytes())
    approved = {item.id: item for item in catalog}
    identities = [item.id for item in manifest.recordings]
    for identity in identities:
        if identity not in approved:
            raise ValueError(f"Recording is not authorized: {identity}")
    if len(set(identities)) != len(identities):
        raise ValueError("Duplicate recording identity in evaluation manifest")
    if set(identities) != set(approved):
        raise ValueError("Evaluation manifest must explicitly contain both authorized recordings")
    verified = []
    for entry in manifest.recordings:
        item = approved[entry.id]
        if entry.role != item.role:
            raise ValueError(f"Recording role does not match authorization: {entry.id}")
        if any(char in value for value in (entry.source, entry.reference) for char in "*?[]"):
            raise ValueError("Evaluation inputs must be explicit files, not wildcard selections")
        source = (path.parent / entry.source).resolve(strict=True)
        reference = (path.parent / entry.reference).resolve(strict=True)
        source_stamp, reference_stamp = file_stamp(source), file_stamp(reference)
        if file_sha256(source) != item.source_sha256:
            raise ValueError(f"Source hash does not match authorization: {entry.id}")
        if file_sha256(reference) != item.reference_sha256:
            raise ValueError(f"Publisher reference hash does not match authorization: {entry.id}")
        reviewed = (
            (path.parent / entry.reviewed_reference).resolve(strict=True)
            if entry.reviewed_reference
            else None
        )
        record = VerifiedRecording(
            item,
            source,
            reference,
            source_stamp,
            reference_stamp,
            reviewed,
            file_stamp(reviewed) if reviewed else None,
        )
        record.assert_unchanged()
        verified.append(record)
    return sorted(verified, key=lambda record: record.approved.role != "tuning")


def evaluate(
    manifest: Path,
    output_dir: Path,
    settings: Settings,
    engine_factory: EngineFactory,
    *,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
    warm_runs: int = 3,
    recording_id: str | None = None,
) -> None:
    evaluation_started = time.perf_counter()
    if not 1 <= warm_runs <= 20:
        raise ValueError("Warm-run count must be between one and twenty")
    recordings = load_manifest(manifest, catalog)
    if recording_id is not None:
        if recording_id not in {recording.approved.id for recording in recordings}:
            raise ValueError(f"Selected recording is not authorized: {recording_id}")
        recordings = [
            recording for recording in recordings if recording.approved.id == recording_id
        ]
    references = {}
    for recording in recordings:
        reference = None
        if recording.reviewed_reference:
            reference = SpokenReference.model_validate_json(
                recording.reviewed_reference.read_bytes()
            )
            if (
                reference.recording_id != recording.approved.id
                or reference.source_sha256 != recording.approved.source_sha256
                or reference.publisher_sha256 != recording.approved.reference_sha256
            ):
                raise ValueError("Reviewed reference identity does not match its recording")
            publisher_cues = parse_publisher_subtitles(
                recording.reference.read_text(encoding="utf-8-sig")
            )
            if [(cue.id, cue.publisher_lines) for cue in reference.cues] != [
                (cue.id, cue.publisher_lines) for cue in publisher_cues
            ]:
                raise ValueError(
                    "Reviewed reference must retain every publisher cue and original lines; "
                    "keep unreviewed or uncertain cues explicitly instead of removing them"
                )
        recording.assert_unchanged()
        references[recording.approved.id] = reference
    preflight_seconds = time.perf_counter() - evaluation_started
    if output_dir.exists():
        raise ValueError("Evaluation output directory already exists; choose a new directory")
    output_dir.mkdir(parents=True)
    reports: list[dict[str, object]] = []
    for recording in recordings:
        pipeline = Pipeline(settings, engine_factory)
        runs: list[dict[str, object]] = []
        quality_reports: list[dict[str, object]] = []
        warm: list[float] = []
        for index in range(warm_runs + 1):
            recording.assert_unchanged()
            label = ("cold" if not reports else "model_load") if index == 0 else "warm"
            run_dir = output_dir / recording.approved.id / f"{index:02d}-{label}"
            cpu_before = psutil.cpu_times()
            process_before = psutil.Process().cpu_times()
            started = time.perf_counter()
            result = pipeline.run(
                recording.source, run_dir, source_guard=recording.assert_unchanged
            )
            elapsed = time.perf_counter() - started
            process_after = psutil.Process().cpu_times()
            cpu_after = psutil.cpu_times()
            busy_delta = sum(
                max(0.0, after - before)
                for field, before, after in zip(
                    cpu_before._fields, cpu_before, cpu_after, strict=True
                )
                if field not in {"idle", "iowait", "guest", "guest_nice"}
            )
            process_delta = (
                process_after.user
                + process_after.system
                - process_before.user
                - process_before.system
            )
            if index:
                warm.append(elapsed)
            recording.assert_unchanged()
            quality = score_reference(
                references[recording.approved.id],
                str(result.to_dict()["text"]),
                result.duration_seconds,
            )
            quality_reports.append(quality)
            runs.append(
                {
                    "kind": label,
                    "wall_seconds": elapsed,
                    "rtfx_total": result.duration_seconds / elapsed,
                    "configuration": result.configuration,
                    "versions": result.versions,
                    "metrics": result.to_dict()["metrics"],
                    "quality": quality,
                    "process_cpu_seconds": process_delta,
                    "observed_other_cpu_seconds": max(0.0, busy_delta - process_delta),
                }
            )
            print(f"{recording.approved.id} {index:02d}-{label}: {elapsed:.3f}s", flush=True)
        reports.append(
            {
                "recording_id": recording.approved.id,
                "source_sha256": recording.approved.source_sha256,
                "publisher_reference_sha256": recording.approved.reference_sha256,
                "reviewed_reference_sha256": file_sha256(recording.reviewed_reference)
                if recording.reviewed_reference
                else None,
                "role": recording.approved.role,
                "duration_seconds": result.duration_seconds,
                "runs": runs,
                "warm_median_seconds": statistics.median(warm),
                "warm_range_seconds": [min(warm), max(warm)],
                "warm_rtfx_total": result.duration_seconds / statistics.median(warm),
                "real_time_target_met": statistics.median(warm) <= result.duration_seconds,
                "quality": summarize_quality(quality_reports),
                "quality_aggregation": "Per-measure worst observed error across cold/model-load "
                "and warm runs; consult individual runs for the associated transcript. "
                "Manual candidate error and timing review remains pending.",
            }
        )
    (output_dir / "evaluation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "hardware": hardware_report(),
                "preflight_seconds": preflight_seconds,
                "evaluation_seconds": time.perf_counter() - evaluation_started,
                "timing_scope": "Per-run wall_seconds includes media validation, model load "
                "if needed, inference, final bundle publication and caller return. Authorization "
                "hashing/reference preflight and quality scoring are reported separately; "
                "CLI evaluation has no queue wait. Other-CPU counters are approximate "
                "system busy time minus this process; they are not proof of isolation.",
                "cold_definition": "cold identifies the first engine load in this evaluation "
                "process; invoke a fresh CLI process with --recording for each recording's "
                "cold measurement. Later instance loads in one process are model_load, not "
                "independent cold runs. Downloads and OS cache conditions must be disclosed.",
                "recordings": reports,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def prepare_references(
    manifest: Path,
    output_dir: Path,
    *,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
) -> None:
    recordings = load_manifest(manifest, catalog)
    if output_dir.exists():
        raise ValueError("Reference destination already exists; choose a new directory")
    drafts = []
    for recording in recordings:
        recording.assert_unchanged()
        draft = SpokenReference(
            recording_id=recording.approved.id,
            source_sha256=recording.approved.source_sha256,
            publisher_sha256=recording.approved.reference_sha256,
            cues=parse_publisher_subtitles(recording.reference.read_text(encoding="utf-8-sig")),
        )
        recording.assert_unchanged()
        drafts.append((recording, draft))
    for recording in recordings:
        recording.assert_unchanged()
    output_dir.mkdir(parents=True)
    entries = []
    for recording, draft in drafts:
        recording.assert_unchanged()
        destination = output_dir / f"{recording.approved.id}.reference.json"
        destination.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
        review_lines = [
            f"# {recording.approved.title}: reference review draft",
            "",
            "Not reviewed. Check every proposed speech line against the original recording.",
            "Keep spoken English; remove only unspoken translations and romanization.",
            "Edit the companion JSON, mark checked cues reviewed, and record reviewer/date.",
            "Subtitle timing and important-error review are separate checks.",
            "",
        ]
        for cue in draft.cues:
            review_lines.extend(
                [
                    f"## Cue {cue.id}: {cue.start:.3f} - {cue.end:.3f} seconds",
                    "",
                    f"Proposed speech: {cue.text}",
                    "",
                    "Publisher lines:",
                    *[f"- {line}" for line in cue.publisher_lines],
                    "",
                    cue.notes,
                    "",
                ]
            )
        (output_dir / f"{recording.approved.id}.review.md").write_text(
            "\n".join(review_lines), encoding="utf-8"
        )
        entries.append(
            {
                "id": recording.approved.id,
                "source": str(recording.source),
                "reference": str(recording.reference),
                "reviewed_reference": str(destination.resolve()),
                "role": recording.approved.role,
            }
        )
    (output_dir / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "recordings": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
