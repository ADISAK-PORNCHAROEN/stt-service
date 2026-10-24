"""Public evaluation behavior uses generated fixtures, never extra recordings."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from stt_services.cli import main
from stt_services.evaluation import ApprovedRecording
from stt_services.schemas import Segment


@pytest.fixture
def evaluation_inputs(tmp_path, wav_bytes):
    entries = []
    catalog = []
    for identity, role in (("fixture-tuning", "tuning"), ("fixture-final", "final")):
        source = tmp_path / f"{identity}.wav"
        reference = tmp_path / f"{identity}.txt"
        source.write_bytes(wav_bytes)
        reference.write_text(
            "1\n00:00:00,125 --> 00:00:00,875\nHello Apple\nสวัสดี Apple\nsa-wat-dee Apple\n",
            encoding="utf-8",
        )
        catalog.append(
            ApprovedRecording(
                identity,
                identity,
                hashlib.sha256(wav_bytes).hexdigest(),
                hashlib.sha256(reference.read_bytes()).hexdigest(),
                role,
            )
        )
        entries.append(
            {"id": identity, "role": role, "source": str(source), "reference": str(reference)}
        )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": 1, "recordings": entries}), encoding="utf-8")
    return manifest, tuple(catalog)


def test_evaluation_rejects_unknown_recording_before_engine_or_output(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "recordings": [
                    {
                        "id": "not-authorized",
                        "source": "does-not-exist.mp4",
                        "reference": "does-not-exist.txt",
                        "role": "tuning",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "result"

    def forbidden_engine(settings):
        raise AssertionError("Rejected inputs must not construct inference")

    assert (
        main(
            ["evaluate", "--manifest", str(manifest), "--output-dir", str(output)],
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "not authorized" in capsys.readouterr().err.lower()
    assert not output.exists()


def test_evaluation_publishes_cold_and_three_warm_bundles_without_accuracy_claim(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    output = tmp_path / "evaluation"

    class FakeEngine:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "สวัสดี Apple")]

    assert (
        main(
            ["evaluate", "--manifest", str(manifest), "--output-dir", str(output)],
            recording_catalog=catalog,
            engine_factory=lambda configured: FakeEngine(),
        )
        == 0
    )
    report = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
    plan = json.loads((output / "experiment-plan.json").read_text(encoding="utf-8"))
    review_template = json.loads((output / "review-template.json").read_text(encoding="utf-8"))
    assert report["plan_id"] == plan["plan_id"]
    assert report["profile_id"] == plan["profile_id"]
    assert len(review_template["reviews"]) == 8
    assert all(not review["important_errors_reviewed"] for review in review_template["reviews"])
    assert all(not review["timing_reviewed"] for review in review_template["reviews"])
    assert len(report["recordings"]) == 2
    assert report["hardware"]["physical_cpus"] >= 1
    assert report["hardware"]["logical_cpus"] >= report["hardware"]["physical_cpus"]
    assert report["preflight_seconds"] >= 0
    assert "publication" in report["timing_scope"]
    for position, recording in enumerate(report["recordings"]):
        assert [run["kind"] for run in recording["runs"]] == [
            "cold" if position == 0 else "model_load",
            "warm",
            "warm",
            "warm",
        ]
        assert all(run["source_sha256"] == recording["source_sha256"] for run in recording["runs"])
        assert all(run["profile_id"] == report["profile_id"] for run in recording["runs"])
        assert all(run["result_json_sha256"] for run in recording["runs"])
        assert recording["runs"][0]["text_diff_from_previous_run"] is None
        assert "full_call_through_publication_seconds" in recording["runs"][0]["stage_timings"]
        assert recording["quality"] == {
            "status": "pending_review",
            "thai_cer": None,
            "english_wer": None,
        }
        bundle = output / recording["recording_id"] / "03-warm"
        assert (bundle / "transcript.txt").read_text(encoding="utf-8") == "สวัสดี Apple\n"
        assert "00:00:00,125 --> 00:00:00,875" in (bundle / "transcript.srt").read_text(
            encoding="utf-8"
        )
        transcript = json.loads((bundle / "transcript.json").read_text(encoding="utf-8"))
        assert transcript["text"] == "สวัสดี Apple"
        assert recording["publisher_reference_sha256"]
        assert recording["duration_seconds"] == 1
        assert isinstance(recording["real_time_target_met"], bool)
        assert recording["runs"][0]["observed_other_cpu_seconds"] >= 0


def test_evaluation_invalidates_source_changed_during_model_loading(
    tmp_path, evaluation_inputs, settings, capsys
):
    manifest, catalog = evaluation_inputs
    source = tmp_path / "fixture-tuning.wav"

    class ForbiddenEngine:
        def transcribe(self, path):
            raise AssertionError("Changed input must not reach inference")

    def change_source(configured):
        source.write_bytes(b"replaced after preflight")
        return ForbiddenEngine()

    output = tmp_path / "evaluation"
    assert (
        main(
            ["evaluate", "--manifest", str(manifest), "--output-dir", str(output)],
            recording_catalog=catalog,
            engine_factory=change_source,
        )
        == 1
    )
    assert "changed" in capsys.readouterr().err.lower()
    assert not (output / "evaluation.json").exists()
    assert not list(output.rglob("transcript.json"))


def test_reference_preparation_preserves_spoken_english_without_claiming_human_review(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    output = tmp_path / "references"

    def forbidden_engine(configured):
        raise AssertionError("Reference preparation must not load inference")

    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(output),
                "--prepare-references",
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 0
    )
    reference = json.loads((output / "fixture-tuning.reference.json").read_text(encoding="utf-8"))
    assert reference["cues"][0]["text"] == "สวัสดี Apple"
    assert reference["cues"][0]["publisher_lines"] == [
        "Hello Apple",
        "สวัสดี Apple",
        "sa-wat-dee Apple",
    ]
    assert reference["cues"][0]["reviewed"] is False
    assert reference["reviewed_by"] is None
    assert reference["source_sha256"] == catalog[0].source_sha256


def test_evaluation_scores_reviewed_reference_preserving_thai_tone_marks(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    references = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(references),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    for path in references.glob("*.reference.json"):
        reference = json.loads(path.read_text(encoding="utf-8"))
        reference["reviewed_by"] = "Fixture reviewer"
        reference["reviewed_at"] = "2026-10-18T00:00:00+00:00"
        reference["cues"][0].update(text="ก้า Apple 12", reviewed=True, uncertain=False)
        path.write_text(json.dumps(reference, ensure_ascii=False), encoding="utf-8")

    class FakeEngine:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "ก่า apple 12")]

    output = tmp_path / "scored"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(references / "manifest.json"),
                "--output-dir",
                str(output),
            ],
            recording_catalog=catalog,
            engine_factory=lambda configured: FakeEngine(),
        )
        == 0
    )
    report = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
    for recording in report["recordings"]:
        quality = recording["quality"]
        assert quality["status"] == "scored"
        assert quality["thai_cer"] == pytest.approx(1 / 3)
        assert quality["english_wer"] == 0
        assert quality["thai"]["reference_units"] == 3
        assert quality["english"]["reference_units"] == 1
        assert quality["raw_full_cer"] > quality["normalized_full_cer"]
        assert quality["important_error_review"] == "pending"


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("source", "source hash"),
        ("publisher", "reference hash"),
        ("duplicate", "duplicate"),
        ("missing", "all authorized"),
        ("role", "role"),
        ("wildcard", "wildcard"),
    ],
)
def test_evaluation_preflight_rejects_invalid_selection_without_processing(
    tmp_path, evaluation_inputs, settings, capsys, case, error
):
    manifest, catalog = evaluation_inputs
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if case == "source":
        (tmp_path / "fixture-tuning.wav").write_bytes(b"replacement")
    elif case == "publisher":
        (tmp_path / "fixture-tuning.txt").write_text("wrong reference", encoding="utf-8")
    elif case == "duplicate":
        data["recordings"][1] = data["recordings"][0]
    elif case == "missing":
        data["recordings"] = data["recordings"][:1]
    elif case == "role":
        data["recordings"][0]["role"] = "final"
    else:
        data["recordings"][0]["source"] = "*.wav"
    manifest.write_text(json.dumps(data), encoding="utf-8")

    def forbidden_engine(configured):
        raise AssertionError("Preflight failure must not load inference")

    output = tmp_path / "rejected"
    assert (
        main(
            ["evaluate", "--manifest", str(manifest), "--output-dir", str(output)],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert error in capsys.readouterr().err.lower()
    assert not output.exists()


def test_reference_preparation_keeps_english_only_cues_pending_audio_confirmation(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    publisher = tmp_path / "fixture-tuning.txt"
    publisher.write_text(
        "1\n00:00:00,125 --> 00:00:00,875\nThis is spoken English.\n", encoding="utf-8"
    )
    catalog = (
        replace(catalog[0], reference_sha256=hashlib.sha256(publisher.read_bytes()).hexdigest()),
        catalog[1],
    )
    output = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(output),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    reference = json.loads((output / "fixture-tuning.reference.json").read_text(encoding="utf-8"))
    assert reference["cues"][0]["text"] == "This is spoken English."
    assert reference["cues"][0]["uncertain"] is True
    assert reference["cues"][0]["reviewed"] is False


def test_evaluation_can_select_one_approved_original_for_a_fresh_process_cold_run(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    output = tmp_path / "selected"

    class FakeEngine:
        def transcribe(self, path):
            return [Segment(0.125, 0.875, "สวัสดี Apple")]

    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(output),
                "--recording",
                "fixture-final",
            ],
            recording_catalog=catalog,
            engine_factory=lambda configured: FakeEngine(),
        )
        == 0
    )
    report = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
    assert [recording["recording_id"] for recording in report["recordings"]] == ["fixture-final"]
    assert report["recordings"][0]["runs"][0]["kind"] == "cold"
    assert not (output / "fixture-tuning").exists()
    assert "fresh" in report["cold_definition"]


def test_real_model_cli_guard_rejects_unknown_media_before_decoding(tmp_path, settings, capsys):
    source = tmp_path / "not-a-real-recording.mp4"
    source.write_bytes(b"an inert denied-input fixture, not decodable media")
    output = tmp_path / "result"

    def forbidden_engine(configured):
        raise AssertionError("Denied media must not construct inference")

    assert (
        main(
            ["transcribe", str(source), "--output-dir", str(output), "--approved-only"],
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "not authorized" in capsys.readouterr().err.lower()
    assert not output.exists()


def test_reviewed_reference_cannot_drop_publisher_cues_and_claim_complete_coverage(
    tmp_path, evaluation_inputs, settings, capsys
):
    manifest, catalog = evaluation_inputs
    publisher = tmp_path / "fixture-tuning.txt"
    publisher.write_text(
        publisher.read_text(encoding="utf-8")
        + "\n2\n00:00:00,875 --> 00:00:00,950\nSpoken English.\n",
        encoding="utf-8",
    )
    catalog = (
        replace(catalog[0], reference_sha256=hashlib.sha256(publisher.read_bytes()).hexdigest()),
        catalog[1],
    )
    references = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(references),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    path = references / "fixture-tuning.reference.json"
    reference = json.loads(path.read_text(encoding="utf-8"))
    reference["cues"] = reference["cues"][:1]
    reference["reviewed_by"] = "Fixture reviewer"
    reference["reviewed_at"] = "2026-10-18T00:00:00+00:00"
    reference["cues"][0].update(reviewed=True, uncertain=False)
    path.write_text(json.dumps(reference), encoding="utf-8")

    def forbidden_engine(configured):
        raise AssertionError("Incomplete reference inventory must fail before inference")

    output = tmp_path / "incomplete"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(references / "manifest.json"),
                "--output-dir",
                str(output),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "publisher cue" in capsys.readouterr().err.lower()
    assert not output.exists()


@pytest.mark.parametrize("command", ["transcribe", "benchmark"])
def test_approved_cli_consumes_the_bound_source_after_working_directory_changes(
    tmp_path, evaluation_inputs, settings, monkeypatch, command
):
    _, catalog = evaluation_inputs
    authorized = tmp_path / "fixture-tuning.wav"
    other_directory = tmp_path / "other"
    other_directory.mkdir()
    (other_directory / authorized.name).write_bytes(b"unapproved inert input")
    monkeypatch.chdir(tmp_path)

    class FakeEngine:
        def transcribe(self, path):
            assert path.resolve() == authorized
            return [Segment(0.125, 0.875, "สวัสดี Apple")]

    def change_directory(configured):
        monkeypatch.chdir(other_directory)
        return FakeEngine()

    output = tmp_path / "bound-result"
    assert (
        main(
            [command, authorized.name, "--output-dir", str(output), "--approved-only"],
            recording_catalog=catalog,
            engine_factory=change_directory,
        )
        == 0
    )
    bundle = output / "warm" if command == "benchmark" else output
    assert (bundle / "transcript.txt").read_text(encoding="utf-8") == "สวัสดี Apple\n"


def test_reference_preparation_rejects_publisher_changed_while_reading(
    tmp_path, evaluation_inputs, settings, monkeypatch, capsys
):
    manifest, catalog = evaluation_inputs
    publisher = tmp_path / "fixture-tuning.txt"
    original_read = Path.read_text

    def read_and_replace(path, *args, **kwargs):
        content = original_read(path, *args, **kwargs)
        if path == publisher:
            path.write_text("changed publisher content", encoding="utf-8")
        return content

    monkeypatch.setattr(Path, "read_text", read_and_replace)
    output = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(output),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 1
    )
    assert "changed" in capsys.readouterr().err.lower()
    assert not output.exists()


def test_evaluation_requires_timezone_in_reference_review_provenance(
    tmp_path, evaluation_inputs, settings, capsys
):
    manifest, catalog = evaluation_inputs
    references = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(references),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    path = references / "fixture-tuning.reference.json"
    reference = json.loads(path.read_text(encoding="utf-8"))
    reference["reviewed_by"] = "Fixture reviewer"
    reference["reviewed_at"] = "2026-10-18T00:00:00"
    reference["cues"][0].update(reviewed=True, uncertain=False)
    path.write_text(json.dumps(reference), encoding="utf-8")

    def forbidden_engine(configured):
        raise AssertionError("Invalid review provenance must fail before inference")

    output = tmp_path / "invalid-review"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(references / "manifest.json"),
                "--output-dir",
                str(output),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "timezone" in capsys.readouterr().err.lower()
    assert not output.exists()


def test_evaluation_quality_summary_keeps_a_regression_from_an_earlier_warm_run(
    tmp_path, evaluation_inputs, settings
):
    manifest, catalog = evaluation_inputs
    references = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(references),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    for path in references.glob("*.reference.json"):
        reference = json.loads(path.read_text(encoding="utf-8"))
        reference.update(reviewed_by="Fixture reviewer", reviewed_at="2026-10-18T00:00:00Z")
        reference["cues"][0].update(text="ก้า Apple", reviewed=True, uncertain=False)
        path.write_text(json.dumps(reference), encoding="utf-8")

    class VaryingEngine:
        def __init__(self):
            self.calls = 0

        def transcribe(self, path):
            self.calls += 1
            text = "ก่า Banana" if self.calls == 2 else "ก้า Apple"
            return [Segment(0.125, 0.875, text)]

    output = tmp_path / "varying-quality"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(references / "manifest.json"),
                "--output-dir",
                str(output),
            ],
            recording_catalog=catalog,
            engine_factory=lambda configured: VaryingEngine(),
        )
        == 0
    )
    report = json.loads((output / "evaluation.json").read_text(encoding="utf-8"))
    for recording in report["recordings"]:
        assert recording["runs"][-1]["quality"]["thai_cer"] == 0
        assert recording["quality"]["thai_cer"] == pytest.approx(1 / 3)
        assert recording["quality"]["english_wer"] == 1
        assert "worst" in recording["quality_aggregation"]


def test_saved_results_can_be_rescored_without_constructing_inference(
    tmp_path, evaluation_inputs, capsys
):
    manifest, catalog = evaluation_inputs
    references = tmp_path / "references"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(references),
                "--prepare-references",
            ],
            recording_catalog=catalog,
        )
        == 0
    )
    prepared_manifest = references / "manifest.json"
    for reference_path in references.glob("*.reference.json"):
        reference = json.loads(reference_path.read_text(encoding="utf-8"))
        reference["reviewed_by"] = "Fixture reviewer"
        reference["reviewed_at"] = "2026-10-18T00:00:00Z"
        for cue in reference["cues"]:
            cue.update(text="Hello Apple สวัสดี Apple", reviewed=True, uncertain=False)
        reference_path.write_text(json.dumps(reference, ensure_ascii=False), encoding="utf-8")

    class FakeEngine:
        def transcribe(self, path):
            return [
                Segment(0.125, 0.4, "Hello Apple"),
                Segment(0.5, 0.875, "สวัสดี Apple"),
            ]

    saved_results = tmp_path / "saved-results"
    assert (
        main(
            ["evaluate", "--manifest", str(prepared_manifest), "--output-dir", str(saved_results)],
            recording_catalog=catalog,
            engine_factory=lambda configured: FakeEngine(),
        )
        == 0
    )
    bindings_path = saved_results / "evaluation.json"
    legacy_bindings_path = tmp_path / "saved-result-bindings.json"
    legacy_bindings_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "results": [
                    {
                        "recording_id": recording_id,
                        "source_sha256": approved.source_sha256,
                        "transcript_json": str(
                            saved_results / recording_id / "03-warm" / "transcript.json"
                        ),
                    }
                    for recording_id, approved in zip(
                        (item.id for item in catalog), catalog, strict=True
                    )
                ],
            }
        ),
        encoding="utf-8",
    )

    def forbidden_engine(configured):
        raise AssertionError("Offline rescoring must not construct an inference engine")

    rescored = tmp_path / "rescored"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(prepared_manifest),
                "--rescore-results",
                str(bindings_path),
                "--output-dir",
                str(rescored),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 0
    )
    report = json.loads((rescored / "comparison.json").read_text(encoding="utf-8"))
    assert report["binding_format"] == "evaluation_run_records"
    assert len(report["results"]) == 8
    assert all(item["quality"]["status"] == "scored" for item in report["results"])
    assert all(item["source_binding"] == "transcript_source_sha256" for item in report["results"])
    assert all(item["plan_id"] for item in report["results"])
    bundle = saved_results / catalog[0].id / "03-warm"
    assert (bundle / "transcript.json").is_file()
    saved_transcript = json.loads((bundle / "transcript.json").read_text(encoding="utf-8"))
    assert saved_transcript["source_sha256"] == catalog[0].source_sha256
    assert len(saved_transcript["segments"]) == 2

    invalid_bindings = json.loads(legacy_bindings_path.read_text(encoding="utf-8"))
    invalid_bindings["results"][0]["source_sha256"] = "0" * 64
    mismatched_binding = tmp_path / "mismatched-binding.json"
    mismatched_binding.write_text(json.dumps(invalid_bindings), encoding="utf-8")
    rejected = tmp_path / "mismatched-rescore"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(prepared_manifest),
                "--rescore-results",
                str(mismatched_binding),
                "--output-dir",
                str(rejected),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "source hash" in capsys.readouterr().err.lower()
    assert not rejected.exists()

    with (bundle / "transcript.txt").open("a", encoding="utf-8") as saved_text:
        saved_text.write("tampered\n")
    rejected_bundle = tmp_path / "mismatched-bundle"
    assert (
        main(
            [
                "evaluate",
                "--manifest",
                str(prepared_manifest),
                "--rescore-results",
                str(bindings_path),
                "--output-dir",
                str(rejected_bundle),
            ],
            recording_catalog=catalog,
            engine_factory=forbidden_engine,
        )
        == 1
    )
    assert "does not match" in capsys.readouterr().err.lower()
    assert not rejected_bundle.exists()
