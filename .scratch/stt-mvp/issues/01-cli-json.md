# 01 — Establish CLI transcription and canonical JSON

What to build: A local CLI baseline backed by a reusable transcription pipeline.
Blocked by: None.
Status: Complete.
Ready for agent: Completed; verified implementation and regression checks.

Triage label: ready-for-agent

## Problem

The workspace has no runnable transcription baseline. A measurable, reusable local path is needed before HTTP or queue infrastructure can be evaluated.

## Solution

Provide the approved CLI using the fixed Turbo CPU configuration and publish canonical JSON as one completed result bundle. Establish the engine boundary so service jobs can reuse the pipeline and ordinary tests can supply a fake engine.

## User stories

- As an operator, I can supply a supported recording and choose an external output directory, receive UTF-8 Thai/English JSON with original segment offsets, and retain my source unchanged. If the destination already exists or processing fails, the command fails visibly without overwriting existing work or publishing partial output.
- As a maintainer, I can invoke the public command with a fake engine during ordinary tests and later use the same pipeline from a worker. I can inspect effective model settings and timestamp provenance in the result without coupling inference to HTTP or persistence.

## Implementation decisions

Follow the [spec input, transcript, and CLI contracts](../spec.md). Use Python 3.12, uv, the root environment, faster-whisper Turbo CPU INT8 with four inference threads, and no PyTorch requirement. Configure external storage and the single HF cache before downloads. Generate and version the lockfile during implementation.

Keep configuration, schemas, orchestration, engine adaptation, and publication separate. Validate supported media and duration before inference. Publish JSON with model timing and restored original offsets using same-volume directory staging. Handle an empty-speech transcript as success. Choose and document a type checker and its invocation as part of scaffolding.

## Testing

Exercise the public CLI with a fake engine for valid Thai/English output, empty speech, original offsets, invalid media, byte/duration boundaries, destination collisions, and inference/publication failure. Confirm ordinary tests never load or download models. Run pytest, Ruff lint/format, and the configured type checker. Record outcomes rather than implying the scaffolding commands already exist. Keep actual model smoke checks opt-in.

## Acceptance criteria

- [x] The approved CLI invocation produces validated canonical JSON through the reusable pipeline.
- [x] Effective Turbo CPU/INT8/four-thread settings and `timing_source=model` are recorded.
- [x] UTF-8 and original timestamp invariants hold, including silence and empty speech.
- [x] Failures return a nonzero exit without partial publication, source deletion, or result overwrite.
- [x] Runtime storage/cache configuration, root environment, lockfile, and verification commands are documented and usable.
- [x] Public CLI fake-engine checks, lint, format, and type checking pass with recorded evidence.

## Out of scope

TXT/SRT, performance conclusions, HTTP, persistence, and service lifecycle work. Global MVP exclusions in the spec apply.

## Further notes

Tickets 02 and 03 depend on this baseline. This ticket's tests establish behavior without asserting real-model accuracy.

Validation evidence: See [verification report](../../../docs/verification-20261017.md). Public CLI/API fake-engine checks, all supported media types and scaled boundaries, concurrency/recovery/retention regressions, Ruff and mypy pass. Real-model CLI plus separate actual HTTP/worker process smoke tests passed on the 15-second excerpt. No accuracy claim is made.
