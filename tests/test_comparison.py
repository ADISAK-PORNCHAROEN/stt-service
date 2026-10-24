"""Recorded experiment comparison never constructs a recognizer or touches media."""

import hashlib
import json
from pathlib import Path

from stt_services.cli import main
from stt_services.config import Settings
from stt_services.evaluation.evaluation_service import APPROVED_RECORDINGS


def _write_report(root, catalog_item, profile, profile_id, warm_seconds, cer):
    root.mkdir()
    result_records = []
    for index in range(4):
        kind = "cold" if index == 0 else "warm"
        bundle = root / catalog_item.id / f"{index:02d}-{kind}"
        bundle.mkdir(parents=True)
        transcript = bundle / "transcript.json"
        canonical_text = "fixture transcript"
        transcript.write_text(
            json.dumps(
                {
                    "fixture_run": index,
                    "source_sha256": catalog_item.source_sha256,
                    "text": canonical_text,
                    "configuration": {"profile_id": profile_id},
                }
            ),
            encoding="utf-8",
        )
        result_records.append(
            {
                "kind": kind,
                "recording_id": catalog_item.id,
                "role": catalog_item.role,
                "source_sha256": catalog_item.source_sha256,
                "publisher_reference_sha256": catalog_item.reference_sha256,
                "reviewed_reference_sha256": "f" * 64,
                "profile_id": profile_id,
                "plan_id": "a" * 64,
                "result_json": transcript.relative_to(root).as_posix(),
                "result_json_sha256": hashlib.sha256(transcript.read_bytes()).hexdigest(),
                "canonical_text_sha256": hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
                "wall_seconds": 10.0 if index == 0 else warm_seconds,
                "rtfx_total": 10.0 / warm_seconds,
                "observed_other_cpu_seconds": 0.0,
                "metrics": {"peak_ram_bytes": 1_000_000},
                "configuration": {
                    "profile_id": profile_id,
                    "requested": profile,
                    "effective": {"device": "cpu", "compute_type": "int8"},
                    "observations": {"gpu_memory": {"status": "not_applicable_cpu"}},
                },
                "versions": {"model_revision": "turbo-revision-test"},
                "quality": {
                    "status": "scored",
                    "scoring_policy_id": "nfc-casefold-projections-v1",
                    "thai_cer": cer,
                    "english_wer": 0.0,
                    "raw_full_cer": cer,
                    "normalized_full_cer": cer,
                    "coverage": {"cue_fraction": 1.0},
                    "reference_important_error_review": "reviewed",
                    "reference_timing_review": "reviewed",
                    "thai": {"reference_units": 10},
                    "english": {"reference_units": 4},
                    "numeric_tokens": {"reference_units": 1},
                },
            }
        )
    report = {
        "schema_version": 1,
        "hardware": {
            "os": "Test Windows",
            "processor": "Test CPU",
            "physical_cpus": 4,
            "logical_cpus": 8,
            "ram_bytes": 16_000_000_000,
            "gpus": {"status": "not_detected"},
        },
        "profile_id": profile_id,
        "plan_id": "a" * 64,
        "recordings": [
            {
                "recording_id": catalog_item.id,
                "source_sha256": catalog_item.source_sha256,
                "publisher_reference_sha256": catalog_item.reference_sha256,
                "reviewed_reference_sha256": "f" * 64,
                "role": catalog_item.role,
                "duration_seconds": 10.0,
                "quality": result_records[-1]["quality"],
                "runs": result_records,
            }
        ],
    }
    (root / "evaluation.json").write_text(json.dumps(report), encoding="utf-8")
    return root / "evaluation.json", result_records


def _write_review(path: Path, item, profile_id, result_records):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "plan_id": "a" * 64,
                "profile_id": profile_id,
                "reviews": [
                    {
                        "recording_id": item.id,
                        "role": item.role,
                        "source_sha256": item.source_sha256,
                        "run_kind": run["kind"],
                        "result_json": run["result_json"],
                        "result_json_sha256": run["result_json_sha256"],
                        "canonical_text_sha256": run["canonical_text_sha256"],
                        "reviewed_by": "Fixture reviewer",
                        "reviewed_at": "2026-10-18T00:00:00Z",
                        "important_errors_reviewed": True,
                        "new_important_errors": False,
                        "error_categories": [],
                        "important_error_notes": "Checked against the generated fixture contract.",
                        "timing_reviewed": True,
                        "new_timing_boundary_regressions": False,
                        "timing_notes": "Checked against the generated fixture contract.",
                        "host_isolation_reviewed": True,
                        "host_interference_observed": False,
                        "host_isolation_notes": (
                            "No competing CPU workload was present in this fixture."
                        ),
                    }
                    for run in result_records
                ],
            }
        ),
        encoding="utf-8",
    )


def test_cli_comparison_requires_reviews_and_reports_speedup_without_inference(tmp_path):
    catalog = APPROVED_RECORDINGS
    item = catalog[0]
    baseline_profile = Settings().resolve_profile()
    candidate_profile = Settings(beam_size=3).resolve_profile()
    baseline, baseline_runs = _write_report(
        tmp_path / "baseline",
        item,
        baseline_profile.public_configuration,
        baseline_profile.profile_id,
        warm_seconds=6.0,
        cer=0.2,
    )
    candidate, candidate_runs = _write_report(
        tmp_path / "candidate",
        item,
        candidate_profile.public_configuration,
        candidate_profile.profile_id,
        warm_seconds=4.0,
        cer=0.2,
    )

    def forbidden_engine(configured):
        raise AssertionError("Comparison must not construct inference")

    pending_output = tmp_path / "comparison-pending"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--output-dir",
                str(pending_output),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 0
    )
    pending = json.loads((pending_output / "comparison.json").read_text(encoding="utf-8"))
    row = pending["comparisons"][0]
    assert row["disposition"] == "host_activity_review_pending"
    assert row["candidate_warm_median_seconds"] == 4.0
    assert row["baseline_warm_median_seconds"] == 6.0

    baseline_review = tmp_path / "baseline-review.json"
    candidate_review = tmp_path / "candidate-review.json"
    _write_review(baseline_review, item, baseline_profile.profile_id, baseline_runs)
    _write_review(candidate_review, item, candidate_profile.profile_id, candidate_runs)
    reviewed_output = tmp_path / "comparison-reviewed"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--review",
                str(baseline_review),
                "--review",
                str(candidate_review),
                "--output-dir",
                str(reviewed_output),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 0
    )
    reviewed = json.loads((reviewed_output / "comparison.json").read_text(encoding="utf-8"))
    result = reviewed["comparisons"][0]
    assert result["disposition"] == "equal_quality_speedup"
    assert result["candidate_warm_rtfx"] == 2.5
    assert result["real_time_target_met"] is True
    assert result["result_identity"] == {
        "source_hash_verified": True,
        "canonical_text_hash_verified": True,
    }
    assert result["quality"]["measures"]["thai_cer"] == {
        "baseline": 0.2,
        "candidate": 0.2,
    }
    assert result["quality"]["reference_units"]["english"] == {
        "baseline": 4,
        "candidate": 4,
    }
    assert result["host_activity"]["baseline_observed_other_cpu_seconds"] == [0.0, 0.0, 0.0]
    assert result["host_activity"]["candidate_observed_other_cpu_seconds"] == [0.0, 0.0, 0.0]
    assert (reviewed_output / "comparison.md").is_file()


def test_repetition_limited_candidate_cannot_be_supplied_as_cpu_baseline(tmp_path, capsys):
    item = APPROVED_RECORDINGS[0]
    baseline_profile = Settings(no_repeat_ngram_size=8).resolve_profile()
    candidate_profile = Settings(beam_size=3).resolve_profile()
    baseline, _ = _write_report(
        tmp_path / "baseline",
        item,
        baseline_profile.public_configuration,
        baseline_profile.profile_id,
        20.0,
        0.1,
    )
    candidate, _ = _write_report(
        tmp_path / "candidate",
        item,
        candidate_profile.public_configuration,
        candidate_profile.profile_id,
        10.0,
        0.1,
    )
    output = tmp_path / "comparison"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--output-dir",
                str(output),
            ]
        )
        == 1
    )
    assert "baseline" in capsys.readouterr().err.lower()
    assert not output.exists()


def test_duplicate_report_or_run_cannot_fake_independent_warm_runs(tmp_path, capsys):
    item = APPROVED_RECORDINGS[0]
    baseline_profile = Settings().resolve_profile()
    candidate_profile = Settings(beam_size=3).resolve_profile()
    baseline, _ = _write_report(
        tmp_path / "baseline",
        item,
        baseline_profile.public_configuration,
        baseline_profile.profile_id,
        warm_seconds=6.0,
        cer=0.2,
    )
    candidate, candidate_runs = _write_report(
        tmp_path / "candidate",
        item,
        candidate_profile.public_configuration,
        candidate_profile.profile_id,
        warm_seconds=4.0,
        cer=0.2,
    )
    output = tmp_path / "duplicate-report"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--output-dir",
                str(output),
            ],
            recording_catalog=APPROVED_RECORDINGS,
        )
        == 1
    )
    assert "Duplicate evaluation report" in capsys.readouterr().err
    assert not output.exists()

    payload = json.loads(candidate.read_text(encoding="utf-8"))
    payload["recordings"][0]["runs"].append(candidate_runs[-1])
    candidate.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "duplicate-run"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--output-dir",
                str(output),
            ],
            recording_catalog=APPROVED_RECORDINGS,
        )
        == 1
    )
    assert "Duplicate transcript result" in capsys.readouterr().err
    assert not output.exists()


def test_host_contention_blocks_acceptance(tmp_path):
    item = APPROVED_RECORDINGS[0]
    baseline_profile = Settings().resolve_profile()
    candidate_profile = Settings(beam_size=3).resolve_profile()
    baseline, baseline_runs = _write_report(
        tmp_path / "baseline",
        item,
        baseline_profile.public_configuration,
        baseline_profile.profile_id,
        warm_seconds=6.0,
        cer=0.2,
    )
    candidate, candidate_runs = _write_report(
        tmp_path / "candidate",
        item,
        candidate_profile.public_configuration,
        candidate_profile.profile_id,
        warm_seconds=4.0,
        cer=0.2,
    )
    baseline_review, candidate_review = tmp_path / "base-review.json", tmp_path / "cand-review.json"
    _write_review(baseline_review, item, baseline_profile.profile_id, baseline_runs)
    _write_review(candidate_review, item, candidate_profile.profile_id, candidate_runs)
    candidate_doc = json.loads(candidate_review.read_text(encoding="utf-8"))
    candidate_doc["reviews"][1]["host_interference_observed"] = True
    candidate_doc["reviews"][1]["host_isolation_notes"] = (
        "Another CPU workload ran during this call."
    )
    candidate_review.write_text(json.dumps(candidate_doc), encoding="utf-8")

    output = tmp_path / "contended-comparison"
    assert (
        main(
            [
                "compare",
                "--baseline",
                str(baseline),
                "--candidate",
                str(candidate),
                "--review",
                str(baseline_review),
                "--review",
                str(candidate_review),
                "--output-dir",
                str(output),
            ],
            recording_catalog=APPROVED_RECORDINGS,
        )
        == 0
    )
    row = json.loads((output / "comparison.json").read_text(encoding="utf-8"))["comparisons"][0]
    assert row["disposition"] == "host_activity_confounded"
    assert row["host_activity"]["contention_observed"] is True
