"""Explicit, content-bound evaluation of the owner's approved recording."""

import difflib
import hashlib
import json
import math
import shutil
import statistics
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import psutil
from pydantic import BaseModel, ConfigDict, Field

from stt_services.config import Settings
from stt_services.evaluation.benchmark_service import hardware_report
from stt_services.evaluation.reference_review import (
    SCORING_POLICY_DESCRIPTION,
    SCORING_POLICY_ID,
    SpokenReference,
    parse_publisher_subtitles,
    score_reference,
    summarize_quality,
)
from stt_services.transcription.pipeline import EngineFactory, Pipeline


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


class SavedResultBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    recording_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    transcript_json: str = Field(min_length=1)
    expected_result_json_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    profile_id: str | None = None
    plan_id: str | None = None
    run_kind: str | None = None


class SavedResultBindings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    results: list[SavedResultBinding] = Field(min_length=1, max_length=40)


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
    path: Path,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
    *,
    recording_id: str | None = None,
) -> list[VerifiedRecording]:
    manifest = EvaluationManifest.model_validate_json(path.read_bytes())
    approved = {item.id: item for item in catalog}
    identities = [item.id for item in manifest.recordings]
    if recording_id is not None:
        item = approved.get(recording_id)
        if item is None:
            raise ValueError(f"Recording is not authorized: {recording_id}")
        if len(manifest.recordings) != 1:
            raise ValueError("Selected-recording manifest must contain exactly one recording")
        entry = manifest.recordings[0]
        if entry.id != recording_id:
            raise ValueError(
                f"Evaluation manifest does not match selected recording: {recording_id}"
            )
        approved = {recording_id: item}
    else:
        for identity in identities:
            if identity not in approved:
                raise ValueError(f"Recording is not authorized: {identity}")
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate recording identity in evaluation manifest")
        if set(identities) != set(approved):
            raise ValueError(
                "Evaluation manifest must explicitly contain all authorized recordings"
            )
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
    recordings = load_manifest(manifest, catalog, recording_id=recording_id)
    references: dict[str, SpokenReference | None] = {}
    for recording in recordings:
        reference = _load_reviewed_reference(recording)
        recording.assert_unchanged()
        references[recording.approved.id] = reference
    preflight_seconds = time.perf_counter() - evaluation_started
    if output_dir.exists():
        raise ValueError("Evaluation output directory already exists; choose a new directory")
    output_dir.mkdir(parents=True)
    profile = settings.resolve_profile()
    plan: dict[str, object] = {
        "schema_version": 1,
        "profile_id": profile.profile_id,
        "profile": profile.public_configuration,
        "scoring_policy": {
            "id": SCORING_POLICY_ID,
            "description": SCORING_POLICY_DESCRIPTION,
            "sha256": hashlib.sha256(SCORING_POLICY_DESCRIPTION.encode("utf-8")).hexdigest(),
        },
        "recordings": [
            {
                "recording_id": recording.approved.id,
                "role": recording.approved.role,
                "source_sha256": recording.approved.source_sha256,
                "publisher_reference_sha256": recording.approved.reference_sha256,
                "reviewed_reference_sha256": file_sha256(recording.reviewed_reference)
                if recording.reviewed_reference
                else None,
            }
            for recording in recordings
        ],
    }
    plan_content = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    plan_id = hashlib.sha256(plan_content.encode("utf-8")).hexdigest()
    plan["plan_id"] = plan_id
    (output_dir / "experiment-plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    reports: list[dict[str, object]] = []
    for recording in recordings:
        pipeline = Pipeline(settings, engine_factory)
        runs: list[dict[str, object]] = []
        quality_reports: list[dict[str, object]] = []
        warm: list[float] = []
        previous_text: str | None = None
        for index in range(warm_runs + 1):
            recording.assert_unchanged()
            label = ("cold" if not reports else "model_load") if index == 0 else "warm"
            run_dir = output_dir / recording.approved.id / f"{index:02d}-{label}"
            cpu_before = psutil.cpu_times()
            process_before = psutil.Process().cpu_times()
            started = time.perf_counter()
            result = pipeline.run(
                recording.source,
                run_dir,
                source_guard=recording.assert_unchanged,
                source_sha256=recording.approved.source_sha256,
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
            canonical_text = str(result.to_dict()["text"])
            text_diff = (
                list(
                    difflib.unified_diff(
                        previous_text.splitlines(),
                        canonical_text.splitlines(),
                        fromfile="previous-run",
                        tofile=f"{index:02d}-{label}",
                        lineterm="",
                    )
                )
                if previous_text is not None
                else None
            )
            transcript_path = run_dir / "transcript.json"
            runs.append(
                {
                    "kind": label,
                    "recording_id": recording.approved.id,
                    "role": recording.approved.role,
                    "source_sha256": recording.approved.source_sha256,
                    "publisher_reference_sha256": recording.approved.reference_sha256,
                    "reviewed_reference_sha256": file_sha256(recording.reviewed_reference)
                    if recording.reviewed_reference
                    else None,
                    "profile_id": profile.profile_id,
                    "plan_id": plan_id,
                    "wall_seconds": elapsed,
                    "rtfx_total": result.duration_seconds / elapsed,
                    "configuration": result.configuration,
                    "versions": result.versions,
                    "metrics": result.to_dict()["metrics"],
                    "stage_timings": {
                        "media_validation_seconds": result.metrics.validation_seconds,
                        "engine_processing_seconds": result.metrics.inference_seconds,
                        "artifact_preparation_seconds": result.metrics.publication_seconds,
                        "full_call_through_publication_seconds": elapsed,
                        "artifact_preparation_scope": "JSON/TXT/SRT export creation before final "
                        "metrics JSON serialization and atomic directory rename; full publication "
                        "is included in full_call_through_publication_seconds",
                    },
                    "result_json": transcript_path.relative_to(output_dir).as_posix(),
                    "result_json_sha256": file_sha256(transcript_path),
                    "canonical_text_sha256": hashlib.sha256(
                        canonical_text.encode("utf-8")
                    ).hexdigest(),
                    "text_diff_from_previous_run": text_diff,
                    "quality": quality,
                    "process_cpu_seconds": process_delta,
                    "observed_other_cpu_seconds": max(0.0, busy_delta - process_delta),
                }
            )
            previous_text = canonical_text
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
                "plan_id": plan_id,
                "profile_id": profile.profile_id,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    review_template = {
        "schema_version": 1,
        "plan_id": plan_id,
        "profile_id": profile.profile_id,
        "instructions": "Review each saved output against the authorized original. "
        "For a candidate, "
        "compare important errors and audible segment boundaries with the same-host baseline. "
        "Review the per-run other-CPU activity measurement and your run-time host records; "
        "mark host isolation reviewed only when you checked that evidence. Record whether a "
        "competing workload was present. Do not mark other fields reviewed unless you checked "
        "the matching full recording.",
        "reviews": [
            {
                "recording_id": recording["recording_id"],
                "role": recording["role"],
                "source_sha256": recording["source_sha256"],
                "run_kind": run["kind"],
                "result_json": run["result_json"],
                "result_json_sha256": run["result_json_sha256"],
                "canonical_text_sha256": run["canonical_text_sha256"],
                "reviewed_by": None,
                "reviewed_at": None,
                "important_errors_reviewed": False,
                "new_important_errors": None,
                "error_categories": [],
                "important_error_notes": "",
                "timing_reviewed": False,
                "new_timing_boundary_regressions": None,
                "timing_notes": "",
                "host_isolation_reviewed": False,
                "host_interference_observed": None,
                "host_isolation_notes": "",
            }
            for recording in reports
            for run in cast(list[dict[str, object]], recording["runs"])
        ],
    }
    (output_dir / "review-template.json").write_text(
        json.dumps(review_template, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def prepare_references(
    manifest: Path,
    output_dir: Path,
    *,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
    recording_id: str | None = None,
) -> None:
    recordings = load_manifest(manifest, catalog, recording_id=recording_id)
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


def rescore_saved_results(
    manifest: Path,
    bindings_path: Path,
    output_dir: Path,
    *,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
    recording_id: str | None = None,
) -> None:
    """Compare explicitly bound, existing result bundles without loading inference."""
    recordings = load_manifest(manifest, catalog, recording_id=recording_id)
    authorized = {recording.approved.id: recording for recording in recordings}
    raw_bindings = json.loads(bindings_path.read_bytes())
    bindings, binding_source = _parse_saved_result_bindings(raw_bindings)
    if output_dir.exists():
        raise ValueError("Comparison output directory already exists; choose a new directory")

    references: dict[str, SpokenReference | None] = {}
    for recording in recordings:
        reference = _load_reviewed_reference(recording)
        references[recording.approved.id] = reference

    results: list[dict[str, object]] = []
    seen_paths: set[Path] = set()
    for binding in bindings.results:
        bound_recording = authorized.get(binding.recording_id)
        if bound_recording is None:
            raise ValueError(
                f"Saved result is not bound to an authorized recording: {binding.recording_id}"
            )
        if binding.source_sha256 != bound_recording.approved.source_sha256:
            raise ValueError(
                f"Saved result source hash does not match authorization: {binding.recording_id}"
            )
        if any(char in binding.transcript_json for char in "*?[]"):
            raise ValueError("Saved result paths must identify explicit files, not wildcards")
        transcript_path = (bindings_path.parent / binding.transcript_json).resolve(strict=True)
        if transcript_path in seen_paths:
            raise ValueError("A saved transcript bundle may be bound only once")
        seen_paths.add(transcript_path)
        bundle = transcript_path.parent
        json_bytes, json_stamp, json_sha256 = _read_stable_file(transcript_path)
        if (
            binding.expected_result_json_sha256 is not None
            and json_sha256 != binding.expected_result_json_sha256
        ):
            raise ValueError(
                f"Saved result hash does not match its run record: {binding.recording_id}"
            )
        try:
            payload = json.loads(json_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Saved transcript is not valid UTF-8 JSON: {transcript_path}"
            ) from exc
        text, other_artifact_hashes, other_artifact_stamps = _validate_saved_bundle(payload, bundle)
        embedded_source = payload.get("source_sha256")
        if embedded_source is not None and embedded_source != binding.source_sha256:
            raise ValueError(
                f"Saved transcript source identity does not match binding: {binding.recording_id}"
            )
        source_binding = (
            "transcript_source_sha256"
            if embedded_source is not None
            else "explicit_operator_binding_legacy_result"
        )
        reference = references[binding.recording_id]
        quality = score_reference(reference, text, float(payload["duration_seconds"]))
        if (
            file_stamp(transcript_path) != json_stamp
            or file_sha256(transcript_path) != json_sha256
            or any(file_stamp(path) != stamp for path, stamp in other_artifact_stamps.items())
        ):
            raise ValueError(f"Saved result changed during offline scoring: {transcript_path}")
        bound_recording.assert_unchanged()
        results.append(
            {
                "recording_id": binding.recording_id,
                "role": bound_recording.approved.role,
                "source_sha256": binding.source_sha256,
                "source_binding": source_binding,
                "run_kind": binding.run_kind,
                "profile_id": binding.profile_id,
                "plan_id": binding.plan_id,
                "result_json": str(transcript_path),
                "result_json_sha256": json_sha256,
                "result_artifact_sha256": {
                    "transcript.json": json_sha256,
                    **other_artifact_hashes,
                },
                "canonical_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "reviewed_reference_sha256": (
                    file_sha256(recording.reviewed_reference)
                    if recording.reviewed_reference is not None
                    else None
                ),
                "scoring_policy": (
                    reference.normalization if reference is not None else "unavailable_unreviewed"
                ),
                "scoring_policy_sha256": hashlib.sha256(
                    SCORING_POLICY_DESCRIPTION.encode("utf-8")
                ).hexdigest()
                if reference is not None
                else None,
                "quality": quality,
                "acceptance_note": (
                    "Legacy transcript has no embedded source hash; its explicit operator binding "
                    "is recorded and does not independently prove inference provenance."
                    if embedded_source is None
                    else "Result source hash matches the authorized source identity."
                ),
            }
        )

    for recording in recordings:
        recording.assert_unchanged()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".stt-rescore-", dir=output_dir.parent))
    try:
        (staging / "comparison.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "mode": "offline_rescore",
                    "inference_performed": False,
                    "manifest": str(manifest.resolve()),
                    "bindings": str(bindings_path.resolve()),
                    "binding_format": binding_source,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        staging.rename(output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _parse_saved_result_bindings(
    payload: object,
) -> tuple[SavedResultBindings, str]:
    if isinstance(payload, dict) and "results" in payload:
        return SavedResultBindings.model_validate(payload), "explicit_result_bindings"
    if isinstance(payload, dict) and isinstance(payload.get("recordings"), list):
        results = []
        for recording in payload["recordings"]:
            if not isinstance(recording, dict) or not isinstance(recording.get("runs"), list):
                raise ValueError("Evaluation report contains an invalid recording run list")
            for run in recording["runs"]:
                if not isinstance(run, dict) or not isinstance(run.get("result_json"), str):
                    raise ValueError("Evaluation report lacks a bound result path")
                results.append(
                    {
                        "recording_id": run.get("recording_id", recording.get("recording_id")),
                        "source_sha256": run.get("source_sha256", recording.get("source_sha256")),
                        "transcript_json": run["result_json"],
                        "expected_result_json_sha256": run.get("result_json_sha256"),
                        "profile_id": run.get("profile_id"),
                        "plan_id": run.get("plan_id", payload.get("plan_id")),
                        "run_kind": run.get("kind"),
                    }
                )
        return (
            SavedResultBindings.model_validate({"schema_version": 1, "results": results}),
            "evaluation_run_records",
        )
    raise ValueError("Saved result input must be a binding manifest or evaluation report")


def _load_reviewed_reference(recording: VerifiedRecording) -> SpokenReference | None:
    if recording.reviewed_reference is None:
        return None
    reference = SpokenReference.model_validate_json(recording.reviewed_reference.read_bytes())
    if (
        reference.recording_id != recording.approved.id
        or reference.source_sha256 != recording.approved.source_sha256
        or reference.publisher_sha256 != recording.approved.reference_sha256
    ):
        raise ValueError("Reviewed reference identity does not match its recording")
    publisher_cues = parse_publisher_subtitles(recording.reference.read_text(encoding="utf-8-sig"))
    if [(cue.id, cue.publisher_lines) for cue in reference.cues] != [
        (cue.id, cue.publisher_lines) for cue in publisher_cues
    ]:
        raise ValueError(
            "Reviewed reference must retain every publisher cue and original lines; "
            "keep unreviewed or uncertain cues explicitly instead of removing them"
        )
    return reference


def _read_stable_file(path: Path) -> tuple[bytes, tuple[int, int, int, int, int], str]:
    before = file_stamp(path)
    content = path.read_bytes()
    after = file_stamp(path)
    if before != after:
        raise ValueError(f"Saved result changed while being read: {path}")
    return content, after, hashlib.sha256(content).hexdigest()


def _validate_saved_bundle(
    payload: object, bundle: Path
) -> tuple[str, dict[str, str], dict[Path, tuple[int, int, int, int, int]]]:
    if not isinstance(payload, dict):
        raise ValueError("Saved transcript JSON must contain an object")
    if payload.get("schema_version") != 1:
        raise ValueError("Saved transcript schema is unsupported")
    segments = payload.get("segments")
    if not isinstance(segments, list):
        raise ValueError("Saved transcript segments are missing")
    duration = payload.get("duration_seconds")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration < 0
    ):
        raise ValueError("Saved transcript duration is invalid")
    normalized_segments = []
    srt_lines = []
    previous_start = 0.0
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict) or not isinstance(segment.get("text"), str):
            raise ValueError("Saved transcript contains an invalid segment")
        try:
            start, end = float(segment["start"]), float(segment["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Saved transcript contains invalid segment times") from exc
        if (
            not math.isfinite(start)
            or not math.isfinite(end)
            or start < 0
            or end < start
            or end > duration
            or start < previous_start
        ):
            raise ValueError("Saved transcript contains times outside its ordered source timeline")
        previous_start = start
        value = segment["text"].strip()
        normalized_segments.append(value)
        srt_lines.extend([str(index), f"{_srt_time(start)} --> {_srt_time(end)}", value, ""])
    text = "\n".join(normalized_segments)
    if payload.get("text") != text:
        raise ValueError("Saved transcript text does not match its canonical segments")
    txt_path, srt_path = bundle / "transcript.txt", bundle / "transcript.srt"
    if not txt_path.is_file() or not srt_path.is_file():
        raise ValueError("Saved result bundle must contain JSON, TXT, and SRT artifacts")
    txt_bytes, txt_stamp, txt_sha256 = _read_stable_file(txt_path)
    srt_bytes, srt_stamp, srt_sha256 = _read_stable_file(srt_path)
    expected_txt = "".join(value + "\n" for value in normalized_segments)
    if txt_bytes.decode("utf-8") != expected_txt:
        raise ValueError("Saved TXT does not match the canonical transcript segments")
    if srt_bytes.decode("utf-8") != "\n".join(srt_lines) + "\n":
        raise ValueError("Saved SRT does not match the canonical transcript segments")
    return (
        text,
        {"transcript.txt": txt_sha256, "transcript.srt": srt_sha256},
        {txt_path: txt_stamp, srt_path: srt_stamp},
    )


def _srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"
