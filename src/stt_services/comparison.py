"""Offline comparison of recorded optimization runs; performs no inference."""

import hashlib
import json
import math
import shutil
import statistics
import tempfile
from pathlib import Path
from typing import Literal, cast

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from stt_services.evaluation import APPROVED_RECORDINGS, ApprovedRecording


class RunReview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    recording_id: str
    role: Literal["tuning", "final"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_kind: str
    result_json: str
    result_json_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_by: str | None = None
    reviewed_at: AwareDatetime | None = None
    important_errors_reviewed: bool = False
    new_important_errors: bool | None = None
    error_categories: list[str] = Field(default_factory=list)
    important_error_notes: str = ""
    timing_reviewed: bool = False
    new_timing_boundary_regressions: bool | None = None
    timing_notes: str = ""
    host_isolation_reviewed: bool = False
    host_interference_observed: bool | None = None
    host_isolation_notes: str = ""

    @model_validator(mode="after")
    def reviewed_fields_have_provenance(self) -> "RunReview":
        if self.important_errors_reviewed and (
            not self.reviewed_by or self.reviewed_at is None or self.new_important_errors is None
        ):
            raise ValueError("Important-error review needs reviewer, time, and regression outcome")
        if self.timing_reviewed and (
            not self.reviewed_by
            or self.reviewed_at is None
            or self.new_timing_boundary_regressions is None
        ):
            raise ValueError("Timing review needs reviewer, time, and boundary outcome")
        if self.host_isolation_reviewed and (
            not self.reviewed_by
            or self.reviewed_at is None
            or self.host_interference_observed is None
        ):
            raise ValueError("Host-isolation review needs reviewer, time, and interference outcome")
        return self


class ReviewDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    plan_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_id: str
    instructions: str | None = None
    reviews: list[RunReview] = Field(min_length=1)


def compare_evaluations(
    baseline_paths: list[Path],
    candidate_paths: list[Path],
    review_paths: list[Path],
    output_dir: Path,
    *,
    catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
) -> None:
    """Write one host/profile comparison summary from existing evaluation reports."""
    if not baseline_paths or not candidate_paths:
        raise ValueError("At least one baseline report and one candidate report are required")
    if output_dir.exists():
        raise ValueError("Comparison output directory already exists; choose a new directory")

    reviews = _load_reviews(review_paths)
    baseline_runs, baseline_profiles = _load_reports(baseline_paths, catalog)
    candidate_runs, candidate_profiles = _load_reports(candidate_paths, catalog)
    baseline_result_hashes = {str(row["result_json_sha256"]) for row in baseline_runs}
    candidate_result_hashes = {str(row["result_json_sha256"]) for row in candidate_runs}
    if baseline_result_hashes & candidate_result_hashes:
        raise ValueError("A saved transcript result cannot serve as both baseline and candidate")
    baselines: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in baseline_runs:
        profile = cast(dict[str, object], row["profile"])
        if not _is_cpu_baseline(profile):
            raise ValueError(
                "Baseline reports must use the approved Turbo CPU INT8 default profile"
            )
        key = (str(row["host_id"]), str(row["recording_id"]), str(row["model_revision"]))
        if key not in baselines:
            baselines[key] = _group_row(row)
        else:
            _merge_group(baselines[key], _group_row(row))

    candidate_groups: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in candidate_runs:
        profile_id = str(row["profile_id"])
        candidate_key = (
            str(row["host_id"]),
            profile_id,
            str(row["recording_id"]),
            str(row["model_revision"]),
        )
        if candidate_key not in candidate_groups:
            candidate_groups[candidate_key] = _group_row(row)
        else:
            _merge_group(candidate_groups[candidate_key], _group_row(row))

    comparisons = []
    for candidate in candidate_groups.values():
        baseline_key = (
            str(candidate["host_id"]),
            str(candidate["recording_id"]),
            str(candidate["model_revision"]),
        )
        baseline = baselines.get(baseline_key)
        if baseline is None:
            comparisons.append(
                {
                    "host_id": candidate["host_id"],
                    "recording_id": candidate["recording_id"],
                    "profile_id": candidate["profile_id"],
                    "model_revision": candidate["model_revision"],
                    "disposition": "no_same_host_baseline",
                    "reason": "No baseline report with matching host and model revision "
                    "was supplied.",
                }
            )
            continue
        comparisons.append(_compare_group(baseline, candidate, reviews))

    report = {
        "schema_version": 1,
        "mode": "offline_profile_comparison",
        "inference_performed": False,
        "baselines": baseline_profiles,
        "candidates": candidate_profiles,
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "promotion": "owner_decision_required",
        "limitations": [
            "Only the two owner-authorized recordings are accepted by identity and content hash.",
            "The previously inspected Conversation with Kob results remain disclosed "
            "prior exposure; "
            "this is not an independent holdout estimate.",
            "Missing reviewed text, candidate error review, timing review, same-host baseline, "
            "or repeat measurements remain pending rather than passing.",
        ],
    }
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".stt-compare-", dir=output_dir.parent))
    try:
        (staging / "comparison.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (staging / "comparison.md").write_text(_render_markdown(report), encoding="utf-8")
        staging.rename(output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _load_reports(
    paths: list[Path], catalog: tuple[ApprovedRecording, ...]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    approved = {recording.id: recording for recording in catalog}
    rows: list[dict[str, object]] = []
    identities: list[dict[str, object]] = []
    seen_report_hashes: set[str] = set()
    seen_result_hashes: set[str] = set()
    for report_path in paths:
        report_path = report_path.resolve(strict=True)
        raw_bytes = report_path.read_bytes()
        payload = json.loads(raw_bytes)
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ValueError(f"Unsupported evaluation report: {report_path}")
        hardware = payload.get("hardware")
        recordings = payload.get("recordings")
        if not isinstance(hardware, dict) or not isinstance(recordings, list):
            raise ValueError(f"Evaluation report lacks hardware or recording runs: {report_path}")
        host_id = _host_id(hardware)
        report_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        if report_sha256 in seen_report_hashes:
            raise ValueError(f"Duplicate evaluation report supplied: {report_path}")
        seen_report_hashes.add(report_sha256)
        identities.append(
            {
                "path": str(report_path),
                "sha256": report_sha256,
                "host_id": host_id,
                "profile_id": payload.get("profile_id"),
                "plan_id": payload.get("plan_id"),
            }
        )
        for recording in recordings:
            if not isinstance(recording, dict):
                raise ValueError("Evaluation report contains an invalid recording entry")
            recording_id = recording.get("recording_id")
            source_sha256 = recording.get("source_sha256")
            if not isinstance(recording_id, str) or not isinstance(source_sha256, str):
                raise ValueError("Evaluation report contains an invalid recording identity")
            approved_recording = approved.get(recording_id)
            if approved_recording is None or source_sha256 != approved_recording.source_sha256:
                raise ValueError(
                    f"Evaluation report contains an unauthorized source: {recording_id}"
                )
            if (
                recording.get("role") != approved_recording.role
                or recording.get("publisher_reference_sha256")
                != approved_recording.reference_sha256
            ):
                raise ValueError(
                    f"Evaluation report identity does not match authorization: {recording_id}"
                )
            runs = recording.get("runs")
            if not isinstance(runs, list) or not runs:
                raise ValueError(f"Evaluation report has no runs for {recording_id}")
            duration_seconds = _as_float(recording.get("duration_seconds"), "duration_seconds")
            if duration_seconds <= 0:
                raise ValueError(f"Evaluation report has invalid duration for {recording_id}")
            for run in runs:
                if not isinstance(run, dict):
                    raise ValueError("Evaluation report contains an invalid run")
                configuration = run.get("configuration")
                requested = (
                    configuration.get("requested") if isinstance(configuration, dict) else None
                )
                if not isinstance(requested, dict):
                    raise ValueError("Evaluation run lacks its resolved startup profile")
                if run.get("source_sha256", source_sha256) != source_sha256:
                    raise ValueError(f"Per-run source identity mismatch: {recording_id}")
                if run.get("publisher_reference_sha256", approved_recording.reference_sha256) != (
                    approved_recording.reference_sha256
                ):
                    raise ValueError(f"Per-run publisher reference mismatch: {recording_id}")
                result_relative = run.get("result_json")
                result_hash = run.get("result_json_sha256")
                if not isinstance(result_relative, str) or not isinstance(result_hash, str):
                    raise ValueError(f"Evaluation run has no saved result binding: {recording_id}")
                if result_hash in seen_result_hashes:
                    raise ValueError(f"Duplicate transcript result supplied: {result_hash}")
                seen_result_hashes.add(result_hash)
                result_path = (report_path.parent / result_relative).resolve(strict=True)
                transcript_bytes = result_path.read_bytes()
                if hashlib.sha256(transcript_bytes).hexdigest() != result_hash:
                    raise ValueError(
                        f"Saved result hash does not match evaluation report: {result_path}"
                    )
                transcript = json.loads(transcript_bytes)
                if not isinstance(transcript, dict):
                    raise ValueError(f"Saved result is not a transcript object: {result_path}")
                embedded_source = transcript.get("source_sha256")
                if embedded_source is not None and embedded_source != source_sha256:
                    raise ValueError(f"Saved result source identity mismatch: {result_path}")
                result_configuration = transcript.get("configuration")
                embedded_profile_id = (
                    result_configuration.get("profile_id")
                    if isinstance(result_configuration, dict)
                    else None
                )
                profile_id = run.get("profile_id", payload.get("profile_id"))
                if embedded_profile_id is not None and embedded_profile_id != profile_id:
                    raise ValueError(f"Saved result profile identity mismatch: {result_path}")
                canonical_text = transcript.get("text")
                text_hash = (
                    hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
                    if isinstance(canonical_text, str)
                    else None
                )
                reported_text_hash = run.get("canonical_text_sha256")
                if reported_text_hash is not None and text_hash != reported_text_hash:
                    raise ValueError(f"Saved result text identity mismatch: {result_path}")
                wall_seconds = _as_float(run.get("wall_seconds"), "wall_seconds")
                rtfx_total = _as_float(run.get("rtfx_total"), "rtfx_total")
                other_cpu_value = run.get("observed_other_cpu_seconds")
                observed_other_cpu_seconds = (
                    _as_float(other_cpu_value, "observed_other_cpu_seconds")
                    if other_cpu_value is not None
                    else None
                )
                if wall_seconds <= 0 or run.get("kind") not in {"cold", "warm"}:
                    raise ValueError(f"Evaluation run has invalid timing or kind: {recording_id}")
                if observed_other_cpu_seconds is not None and observed_other_cpu_seconds < 0:
                    raise ValueError(
                        f"Evaluation run has invalid host activity measurement: {recording_id}"
                    )
                rows.append(
                    {
                        "report_path": str(report_path),
                        "report_sha256": report_sha256,
                        "host_id": host_id,
                        "hardware": hardware,
                        "recording_id": recording_id,
                        "source_sha256": source_sha256,
                        "publisher_reference_sha256": approved_recording.reference_sha256,
                        "reviewed_reference_sha256": recording.get("reviewed_reference_sha256"),
                        "role": approved_recording.role,
                        "duration_seconds": duration_seconds,
                        "quality": recording.get("quality"),
                        "profile": requested,
                        "profile_id": profile_id,
                        "plan_id": run.get("plan_id", payload.get("plan_id")),
                        "model_revision": str(
                            run.get("versions", {}).get("model_revision", "unreported")
                            if isinstance(run.get("versions"), dict)
                            else "unreported"
                        ),
                        "result_path": str(result_path),
                        "result_json_sha256": result_hash,
                        "canonical_text_sha256": run.get("canonical_text_sha256"),
                        "source_binding_verified": embedded_source == source_sha256,
                        "text_binding_verified": text_hash is not None
                        and reported_text_hash == text_hash,
                        "kind": run.get("kind"),
                        "wall_seconds": wall_seconds,
                        "rtfx_total": rtfx_total,
                        "observed_other_cpu_seconds": observed_other_cpu_seconds,
                        "metrics": run.get("metrics", {}),
                        "configuration": configuration,
                    }
                )
    return rows, identities


def _load_reviews(
    paths: list[Path],
) -> dict[tuple[str, str], tuple[RunReview, str, str]]:
    reviews: dict[tuple[str, str], tuple[RunReview, str, str]] = {}
    for path in paths:
        path = path.resolve(strict=True)
        document = ReviewDocument.model_validate_json(path.read_bytes())
        for review in document.reviews:
            key = (review.recording_id, review.result_json_sha256)
            if key in reviews:
                raise ValueError(f"Duplicate review for result: {review.recording_id}")
            reviews[key] = (review, document.plan_id, document.profile_id)
    return reviews


def _host_id(hardware: dict[str, object]) -> str:
    fields = {
        key: hardware.get(key)
        for key in ("os", "processor", "physical_cpus", "logical_cpus", "ram_bytes", "gpus")
    }
    return hashlib.sha256(
        json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:20]


def _is_cpu_baseline(profile: dict[str, object]) -> bool:
    expected: dict[str, object] = {
        "model": "turbo",
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": 4,
        "beam_size": 5,
        "mode": "sequential",
        "batch_size": 1,
        "language_mode": "auto",
        "condition_on_previous_text": True,
        "temperature_zero": False,
        "vad_enabled": True,
        "vad_threshold": 0.5,
        "vad_min_silence_duration_ms": 2000,
        "vad_speech_pad_ms": 400,
        "initial_prompt_sha256": None,
        "hotwords_sha256": None,
        "model_window_seconds": 30,
    }
    return profile.get("no_repeat_ngram_size", 0) == 0 and all(
        profile.get(key) == value for key, value in expected.items()
    )


def _merge_group(target: dict[str, object], additional: dict[str, object]) -> None:
    if (
        target["source_sha256"] != additional["source_sha256"]
        or target["publisher_reference_sha256"] != additional["publisher_reference_sha256"]
        or target["reviewed_reference_sha256"] != additional["reviewed_reference_sha256"]
        or target["profile_id"] != additional["profile_id"]
        or target["model_revision"] != additional["model_revision"]
    ):
        raise ValueError("Evaluation reports cannot be combined across identities or revisions")
    cast(list[dict[str, object]], target["runs"]).extend(
        cast(list[dict[str, object]], additional["runs"])
    )
    cast(list[str], target["report_hashes"]).extend(cast(list[str], additional["report_hashes"]))
    cast(list[object], target["quality_reports"]).extend(
        cast(list[object], additional["quality_reports"])
    )


def _group_row(row: dict[str, object]) -> dict[str, object]:
    return {
        **row,
        "runs": [row],
        "report_hashes": [str(row["report_sha256"])],
        "quality_reports": [row.get("quality")],
    }


def _aggregate_quality(reports: list[object]) -> dict[str, object]:
    valid = [report for report in reports if isinstance(report, dict)]
    if not valid or any(report.get("status") != "scored" for report in valid):
        return {"status": "pending_review"}
    result = dict(valid[0])
    for metric in ("thai_cer", "english_wer", "raw_full_cer", "normalized_full_cer"):
        values = [
            cast(float, report[metric])
            for report in valid
            if isinstance(report.get(metric), (int, float))
        ]
        result[metric] = max(values) if values else None
    return result


def _compare_group(
    baseline: dict[str, object],
    candidate: dict[str, object],
    reviews: dict[tuple[str, str], tuple[RunReview, str, str]],
) -> dict[str, object]:
    base_warm = [
        run for run in cast(list[dict[str, object]], baseline["runs"]) if run["kind"] == "warm"
    ]
    candidate_warm = [
        run for run in cast(list[dict[str, object]], candidate["runs"]) if run["kind"] == "warm"
    ]
    base_median = (
        statistics.median(_as_float(run.get("wall_seconds"), "wall_seconds") for run in base_warm)
        if base_warm
        else None
    )
    candidate_median = (
        statistics.median(
            _as_float(run.get("wall_seconds"), "wall_seconds") for run in candidate_warm
        )
        if candidate_warm
        else None
    )
    base_quality = _aggregate_quality(cast(list[object], baseline["quality_reports"]))
    candidate_quality = _aggregate_quality(cast(list[object], candidate["quality_reports"]))
    quality_comparable = _quality_comparable(baseline, candidate, base_quality, candidate_quality)
    quality_result = (
        _quality_comparison(base_quality, candidate_quality)
        if quality_comparable
        else {"status": "pending_or_revision_mismatch"}
    )
    baseline_reviews = _reviews_for_runs(base_warm, baseline, reviews)
    candidate_reviews = _reviews_for_runs(candidate_warm, candidate, reviews)
    all_reviews_complete = bool(base_warm and candidate_warm) and all(
        item["important_errors_reviewed"]
        and item["timing_reviewed"]
        and item["host_isolation_reviewed"]
        and item["host_interference_observed"] is not None
        for item in baseline_reviews + candidate_reviews
    )
    host_activity_available = bool(base_warm and candidate_warm) and all(
        run.get("observed_other_cpu_seconds") is not None for run in base_warm + candidate_warm
    )
    host_interference = any(
        item.get("host_interference_observed") is True
        for item in baseline_reviews + candidate_reviews
    )
    host_isolation_reviewed = bool(base_warm and candidate_warm) and all(
        item.get("host_isolation_reviewed") is True for item in baseline_reviews + candidate_reviews
    )
    important_regression = any(
        item.get("new_important_errors") is True for item in candidate_reviews
    )
    timing_regression = any(
        item.get("new_timing_boundary_regressions") is True for item in candidate_reviews
    )
    speed_improved = (
        base_median is not None and candidate_median is not None and candidate_median < base_median
    )
    target_met = (
        candidate_median is not None
        and _as_float(candidate.get("duration_seconds"), "duration_seconds") / candidate_median >= 1
    )
    enough_runs = len(base_warm) >= 3 and len(candidate_warm) >= 3
    quality_nonregression = quality_result.get("non_regression") is True
    quality_improvement = quality_result.get("improvement") is True
    source_identity_verified = all(
        run.get("source_binding_verified") is True for run in base_warm + candidate_warm
    )
    text_identity_verified = all(
        run.get("text_binding_verified") is True for run in base_warm + candidate_warm
    )
    if not enough_runs:
        disposition = "insufficient_warm_runs"
    elif not source_identity_verified or not text_identity_verified:
        disposition = "result_identity_pending"
    elif host_interference:
        disposition = "host_activity_confounded"
    elif not host_activity_available or not host_isolation_reviewed:
        disposition = "host_activity_review_pending"
    elif not speed_improved:
        disposition = "no_warm_speed_improvement"
    elif not target_met:
        disposition = "performance_target_unmet"
    elif not quality_comparable or not all_reviews_complete:
        disposition = "quality_or_human_review_pending"
    elif important_regression or timing_regression or not quality_nonregression:
        disposition = "quality_or_timing_regression"
    elif quality_improvement:
        disposition = "quality_improvement_with_speedup"
    else:
        disposition = "equal_quality_speedup"
    base_profile = cast(dict[str, object], baseline["profile"])
    candidate_profile = cast(dict[str, object], candidate["profile"])
    changed_settings = sorted(
        key
        for key in set(base_profile) | set(candidate_profile)
        if base_profile.get(key) != candidate_profile.get(key)
    )
    return {
        "host_id": candidate["host_id"],
        "hardware": candidate["hardware"],
        "recording_id": candidate["recording_id"],
        "role": candidate["role"],
        "source_sha256": candidate["source_sha256"],
        "publisher_reference_sha256": candidate["publisher_reference_sha256"],
        "reviewed_reference_sha256": candidate["reviewed_reference_sha256"],
        "model_revision": candidate["model_revision"],
        "baseline_profile_id": baseline["profile_id"],
        "candidate_profile_id": candidate["profile_id"],
        "changed_settings": changed_settings,
        "change_count": len(changed_settings),
        "baseline_warm_run_count": len(base_warm),
        "candidate_warm_run_count": len(candidate_warm),
        "baseline_warm_median_seconds": base_median,
        "baseline_warm_range_seconds": _range(base_warm),
        "candidate_warm_median_seconds": candidate_median,
        "candidate_warm_range_seconds": _range(candidate_warm),
        "host_activity": {
            "baseline_observed_other_cpu_seconds": [
                run.get("observed_other_cpu_seconds") for run in base_warm
            ],
            "candidate_observed_other_cpu_seconds": [
                run.get("observed_other_cpu_seconds") for run in candidate_warm
            ],
            "measurements_available": host_activity_available,
            "isolation_reviewed": host_isolation_reviewed,
            "contention_observed": host_interference if host_isolation_reviewed else None,
            "review_status": "complete" if host_isolation_reviewed else "pending",
        },
        "baseline_warm_rtfx": (
            _as_float(baseline.get("duration_seconds"), "duration_seconds") / base_median
            if base_median
            else None
        ),
        "candidate_warm_rtfx": (
            _as_float(candidate.get("duration_seconds"), "duration_seconds") / candidate_median
            if candidate_median
            else None
        ),
        "real_time_target_met": target_met,
        "baseline_peak_rss_bytes": _peak_rss(base_warm),
        "candidate_peak_rss_bytes": _peak_rss(candidate_warm),
        "candidate_gpu_sampled_max_mib": _peak_gpu_memory(candidate_warm),
        "quality": quality_result,
        "human_review": {
            "status": "complete" if all_reviews_complete else "pending",
            "baseline_runs_reviewed": len(baseline_reviews),
            "candidate_runs_reviewed": len(candidate_reviews),
            "new_important_errors": important_regression if all_reviews_complete else None,
            "new_timing_boundary_regressions": timing_regression if all_reviews_complete else None,
            "host_isolation_reviewed": host_isolation_reviewed,
            "host_interference_observed": (host_interference if host_isolation_reviewed else None),
            "error_categories": sorted(
                {
                    category
                    for item in candidate_reviews
                    for category in cast(list[str], item.get("error_categories", []))
                }
            ),
        },
        "result_identity": {
            "source_hash_verified": source_identity_verified,
            "canonical_text_hash_verified": text_identity_verified,
        },
        "baseline_result_hashes": [run["result_json_sha256"] for run in base_warm],
        "candidate_result_hashes": [run["result_json_sha256"] for run in candidate_warm],
        "baseline_text_variants": len({run.get("canonical_text_sha256") for run in base_warm}),
        "candidate_text_variants": len(
            {run.get("canonical_text_sha256") for run in candidate_warm}
        ),
        "disposition": disposition,
        "promotion": "owner_decision_required",
    }


def _quality_comparable(
    baseline: dict[str, object],
    candidate: dict[str, object],
    baseline_quality: object,
    candidate_quality: object,
) -> bool:
    if not isinstance(baseline_quality, dict) or not isinstance(candidate_quality, dict):
        return False
    baseline_coverage = baseline_quality.get("coverage")
    candidate_coverage = candidate_quality.get("coverage")
    if not isinstance(baseline_coverage, dict) or not isinstance(candidate_coverage, dict):
        return False
    return bool(
        baseline_quality.get("status") == "scored"
        and candidate_quality.get("status") == "scored"
        and baseline_quality.get("reference_important_error_review") == "reviewed"
        and candidate_quality.get("reference_important_error_review") == "reviewed"
        and baseline_quality.get("reference_timing_review") == "reviewed"
        and candidate_quality.get("reference_timing_review") == "reviewed"
        and baseline["reviewed_reference_sha256"]
        and baseline["reviewed_reference_sha256"] == candidate["reviewed_reference_sha256"]
        and baseline_quality.get("scoring_policy_id") == candidate_quality.get("scoring_policy_id")
        and baseline_coverage.get("cue_fraction") == 1
        and candidate_coverage.get("cue_fraction") == 1
    )


def _quality_comparison(baseline: object, candidate: object) -> dict[str, object]:
    assert isinstance(baseline, dict) and isinstance(candidate, dict)
    measures = ("thai_cer", "english_wer", "raw_full_cer", "normalized_full_cer")
    pairs: dict[str, tuple[float, float]] = {}
    for name in measures:
        old, new = baseline.get(name), candidate.get(name)
        if (
            isinstance(old, (int, float))
            and not isinstance(old, bool)
            and isinstance(new, (int, float))
            and not isinstance(new, bool)
        ):
            pairs[name] = (float(old), float(new))
    if not pairs:
        return {"status": "no_comparable_reviewed_measure"}
    non_regression = all(new <= old for old, new in pairs.values())
    improvement = any(new < old for old, new in pairs.values())
    return {
        "status": "scored",
        "measures": {
            name: {"baseline": old, "candidate": new} for name, (old, new) in pairs.items()
        },
        "reference_units": {
            name: _unit_counts(baseline, candidate, name)
            for name in (
                "thai",
                "english",
                "numeric_tokens",
                "raw_full_text",
                "normalized_full_text",
            )
        },
        "non_regression": non_regression,
        "improvement": improvement,
        "aggregation": "per-measure worst observed error in each evaluation report",
    }


def _unit_counts(
    baseline: dict[str, object], candidate: dict[str, object], measure: str
) -> dict[str, object]:
    baseline_value, candidate_value = baseline.get(measure), candidate.get(measure)
    return {
        "baseline": baseline_value.get("reference_units")
        if isinstance(baseline_value, dict)
        else None,
        "candidate": candidate_value.get("reference_units")
        if isinstance(candidate_value, dict)
        else None,
    }


def _reviews_for_runs(
    runs: list[dict[str, object]],
    group: dict[str, object],
    reviews: dict[tuple[str, str], tuple[RunReview, str, str]],
) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for run in runs:
        review_record = reviews.get((str(group["recording_id"]), str(run["result_json_sha256"])))
        if review_record is None:
            found.append(
                {
                    "important_errors_reviewed": False,
                    "timing_reviewed": False,
                    "host_isolation_reviewed": False,
                    "host_interference_observed": None,
                }
            )
            continue
        review, reviewed_plan_id, reviewed_profile_id = review_record
        if reviewed_plan_id != run.get("plan_id") or reviewed_profile_id != run.get("profile_id"):
            raise ValueError("Human review plan/profile does not match the compared result")
        if review.source_sha256 != group["source_sha256"] or review.role != group["role"]:
            raise ValueError("Human review identity does not match the compared run")
        if review.canonical_text_sha256 != run.get("canonical_text_sha256"):
            raise ValueError("Human review transcript hash does not match the compared run")
        found.append(review.model_dump(mode="json"))
    return found


def _range(runs: list[dict[str, object]]) -> list[float] | None:
    values = [_as_float(run.get("wall_seconds"), "wall_seconds") for run in runs]
    return [min(values), max(values)] if values else None


def _peak_rss(runs: list[dict[str, object]]) -> int | None:
    values: list[int] = []
    for run in runs:
        metrics = run.get("metrics")
        peak = metrics.get("peak_ram_bytes") if isinstance(metrics, dict) else None
        if isinstance(peak, int) and not isinstance(peak, bool):
            values.append(peak)
    return max(values) if values else None


def _peak_gpu_memory(runs: list[dict[str, object]]) -> int | None:
    values: list[int] = []
    for run in runs:
        configuration = run.get("configuration")
        observations = (
            configuration.get("observations") if isinstance(configuration, dict) else None
        )
        gpu = observations.get("gpu_memory") if isinstance(observations, dict) else None
        peak = gpu.get("sampled_max_used_mib") if isinstance(gpu, dict) else None
        if isinstance(peak, int) and not isinstance(peak, bool):
            values.append(peak)
    return max(values) if values else None


def _render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# STT profile comparison",
        "",
        "Offline summary from recorded evaluation runs; no inference was performed.",
        "",
        "| Recording | Host | Baseline → candidate RTFx | Host activity review | Disposition |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in cast(list[dict[str, object]], report["comparisons"]):
        if row.get("disposition") == "no_same_host_baseline":
            rtfx = "—"
        else:
            rtfx = f"{row.get('baseline_warm_rtfx')} → {row.get('candidate_warm_rtfx')}"
        host_activity = cast(dict[str, object], row["host_activity"])
        lines.append(
            f"| {row['recording_id']} | {str(row['host_id'])[:10]} | {rtfx} | "
            f"{host_activity['review_status']} | "
            f"{row['disposition']} |"
        )
    lines.extend(
        [
            "",
            "Review the JSON for ranges, quality, memory, text variability, and pending evidence.",
            "No candidate is promoted automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def _as_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Evaluation report has invalid numeric field: {field}")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"Evaluation report has non-finite numeric field: {field}")
    return converted
