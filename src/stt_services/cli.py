"""Command-line entry point; injectable inference is the test seam."""

import argparse
import logging
import sys
from pathlib import Path

from stt_services.benchmark import benchmark
from stt_services.comparison import compare_evaluations
from stt_services.config import Settings
from stt_services.engines.whisper import WhisperEngine
from stt_services.evaluation import (
    APPROVED_RECORDINGS,
    ApprovedRecording,
    authorize_media,
    evaluate,
    prepare_references,
    rescore_saved_results,
)
from stt_services.pipeline import EngineFactory, Pipeline


def main(
    argv: list[str] | None = None,
    *,
    engine_factory: EngineFactory = WhisperEngine,
    recording_catalog: tuple[ApprovedRecording, ...] = APPROVED_RECORDINGS,
) -> int:
    parser = argparse.ArgumentParser(prog="stt")
    commands = parser.add_subparsers(dest="command", required=True)
    transcribe = commands.add_parser("transcribe", help="Transcribe a local audio/video file")
    transcribe.add_argument("file", type=Path)
    transcribe.add_argument("--output-dir", type=Path, required=True)
    transcribe.add_argument("--approved-only", action="store_true")
    bench = commands.add_parser("benchmark", help="Run cold/warm transcription and record metrics")
    bench.add_argument("file", type=Path)
    bench.add_argument("--output-dir", type=Path, required=True)
    bench.add_argument("--approved-only", action="store_true")
    evaluation = commands.add_parser("evaluate", help="Evaluate the two authorized recordings")
    evaluation.add_argument("--manifest", type=Path, required=True)
    evaluation.add_argument("--output-dir", type=Path, required=True)
    evaluation.add_argument("--prepare-references", action="store_true")
    evaluation.add_argument(
        "--rescore-results",
        type=Path,
        help="Rescore explicitly bound saved transcript bundles without inference",
    )
    comparison = commands.add_parser(
        "compare", help="Compare recorded baseline/candidate evaluations without inference"
    )
    comparison.add_argument("--baseline", type=Path, action="append", required=True)
    comparison.add_argument("--candidate", type=Path, action="append", required=True)
    comparison.add_argument("--review", type=Path, action="append", default=[])
    comparison.add_argument("--output-dir", type=Path, required=True)
    evaluation.add_argument(
        "--recording", help="Select one authorized original; manifest stays explicit"
    )
    serve = commands.add_parser("serve", help="Serve the job API on 127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    commands.add_parser("worker", help="Run the single persistent inference worker")
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        if args.command == "evaluate":
            _validate_output(args.output_dir, settings)
            if args.prepare_references and args.rescore_results:
                raise ValueError(
                    "Reference preparation and offline rescoring are separate operations"
                )
            if args.prepare_references:
                prepare_references(args.manifest, args.output_dir, catalog=recording_catalog)
                return 0
            if args.rescore_results:
                rescore_saved_results(
                    args.manifest,
                    args.rescore_results,
                    args.output_dir,
                    catalog=recording_catalog,
                )
                return 0
            settings.resolve_profile()
            evaluate(
                args.manifest,
                args.output_dir,
                settings,
                engine_factory,
                catalog=recording_catalog,
                recording_id=args.recording,
            )
            return 0
        if args.command == "compare":
            _validate_output(args.output_dir, settings)
            compare_evaluations(
                args.baseline,
                args.candidate,
                args.review,
                args.output_dir,
                catalog=recording_catalog,
            )
            return 0
        if args.command == "serve":
            import uvicorn

            from stt_services.api import create_app

            uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port)
            return 0
        if args.command == "worker":
            from stt_services.worker import Worker

            settings.resolve_profile()
            logging.basicConfig(level=logging.INFO)
            with Worker(settings, engine_factory) as worker:
                worker.run_forever()
            return 0
        settings.resolve_profile()
        media = authorize_media(args.file, recording_catalog) if args.approved_only else None
        source = media.source if media else args.file
        if args.command == "benchmark":
            _validate_output(args.output_dir, settings)
            benchmark(
                source,
                args.output_dir,
                Pipeline(settings, engine_factory),
                source_guard=media.assert_unchanged if media else None,
                source_sha256=media.approved.source_sha256 if media else None,
                recording_id=media.approved.id if media else None,
                role=media.approved.role if media else None,
            )
            return 0
        _validate_output(args.output_dir, settings)
        transcript = Pipeline(settings, engine_factory).run(
            source,
            args.output_dir,
            source_guard=media.assert_unchanged if media else None,
            source_sha256=media.approved.source_sha256 if media else None,
        )
        print(f"Saved {len(transcript.segments)} segments to {args.output_dir}")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"stt: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


def _validate_output(output: Path, settings: Settings) -> None:
    for managed in (settings.jobs_dir, settings.data_dir / "cache", settings.data_dir / "locks"):
        if output.resolve().is_relative_to(managed.resolve()):
            raise ValueError("Choose an output directory outside managed jobs/cache/locks storage")


if __name__ == "__main__":
    raise SystemExit(main())
