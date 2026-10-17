"""Command-line entry point; injectable inference is the test seam."""

import argparse
import logging
import sys
from pathlib import Path

from stt_services.benchmark import benchmark
from stt_services.config import Settings
from stt_services.engines.whisper import WhisperEngine
from stt_services.pipeline import EngineFactory, Pipeline


def main(argv: list[str] | None = None, *, engine_factory: EngineFactory = WhisperEngine) -> int:
    parser = argparse.ArgumentParser(prog="stt")
    commands = parser.add_subparsers(dest="command", required=True)
    transcribe = commands.add_parser("transcribe", help="Transcribe a local audio/video file")
    transcribe.add_argument("file", type=Path)
    transcribe.add_argument("--output-dir", type=Path, required=True)
    bench = commands.add_parser("benchmark", help="Run cold/warm transcription and record metrics")
    bench.add_argument("file", type=Path)
    bench.add_argument("--output-dir", type=Path, required=True)
    serve = commands.add_parser("serve", help="Serve the job API on 127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    commands.add_parser("worker", help="Run the single persistent inference worker")
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        if args.command == "serve":
            import uvicorn

            from stt_services.api import create_app

            uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port)
            return 0
        if args.command == "worker":
            from stt_services.worker import Worker

            logging.basicConfig(level=logging.INFO)
            with Worker(settings, engine_factory) as worker:
                worker.run_forever()
            return 0
        if args.command == "benchmark":
            _validate_output(args.output_dir, settings)
            benchmark(args.file, args.output_dir, Pipeline(settings, engine_factory))
            return 0
        _validate_output(args.output_dir, settings)
        transcript = Pipeline(settings, engine_factory).run(args.file, args.output_dir)
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
