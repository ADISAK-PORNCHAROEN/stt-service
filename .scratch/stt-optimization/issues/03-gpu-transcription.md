# 03: Transcribe and measure with the existing GPU explicitly

What to build: An operator can request Turbo GPU transcription on the development PC, obtain a complete result bundle identifying its actual device/precision, and compare its controlled outcomes against the same-host CPU baseline.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; explicit CUDA profile/runtime checks are implemented, but controlled GPU experiments remain blocked by OPT-02 evidence.
Triage label: ready-for-agent.

## Problem

The development PC has a six-GiB GPU, but current inference is CPU-only. Hardware inventory does not establish CUDA compatibility or whether an equivalent GPU configuration improves this workload.

## Solution

Extend the shared startup configuration and existing engine boundary with explicit GPU execution. Validate runtime/device/precision compatibility, expose failures clearly, preserve result formats, and measure the two authorized originals against a same-host CPU baseline.

## User stories

1. As the operator, I want explicit device selection, so that successful GPU results cannot silently come from CPU fallback.
2. As the reviewer, I want host RAM, GPU memory, and effective precision identified, so that resource comparisons are meaningful.
3. As the CPU user, I want the existing CPU configuration to remain usable without GPU dependencies being required for CPU inference.

## Implementation decisions

Use the existing Turbo/faster-whisper/CTranslate2 boundary and the installed GPU. Document compatible GPU runtime setup while preserving pinned-environment and existing media-decoder constraints. Trial supported FP16 and mixed INT8/FP16 configurations only if supported by the actual device/runtime. No automatic device or precision fallback occurs on incompatibility or memory failure.

Establish an equivalent sequential GPU baseline before additional precision tuning. Record real effective settings, cached revision, host/device memory methods, cold loading, and isolated warm turnaround through publication. Freeze settings from Formal Words before final evaluation on Conversation with Kob. Keep the approved recording guard at every real-model entry point.

Verify the exact installed locked runtime rather than prescribing dependencies from inconsistent generic documentation. Separate GPU discovery/advertised compute support, successful model loading, and complete transcription. Begin with sequential execution within available memory; record requested and actual compute representations, and disclose device-wide memory attribution limits.

## Testing

Use public commands with a fake capability/engine boundary for missing GPU, unsupported precision, memory failures, metadata, and source/output preservation. Opt-in compatibility and measurements use only the two full originals. Existing persistent-worker readiness behavior should handle startup failure and must never advertise an unloaded model as ready.

## Acceptance criteria

- [ ] Explicit GPU selection produces complete Turbo JSON/TXT/SRT bundles on compatible installed hardware, and metadata identifies actual device, precision, revision, and effective decoding settings.
- [ ] Incompatible runtime/device/precision and resource failures produce actionable errors without silent CPU fallback or partial successful bundles.
- [ ] CPU selection remains usable and reproducible on a host without GPU runtime availability.
- [ ] A guarded same-host comparison records both originals, sequential CPU/GPU settings, cold loading, repeated warm full-call time, host RAM/device-memory observations, and reviewed quality/timing outcomes.
- [ ] Evidence separates raw GPU acceleration from precision/decoding changes and does not infer a home-server result.
- [ ] Runtime setup evidence identifies the installed wheel/library versions and distinguishes capability discovery from successful loading/inference; dependency changes or large demonstration batch sizes are not assumed necessary or safe from hardware presence alone.
- [ ] Existing model reuse, readiness, original timestamps, and publication contracts remain valid for a GPU-configured persistent worker.
- [x] Fake capability/engine and configuration checks pass; full ordinary suite, lint, formatting, and types pass, with commands in the [implementation evidence](../../../docs/optimization-verification-20261018.md). Runtime capability discovery exists, but no GPU model-load or transcription acceptance run was performed.

## Out of scope

Additional real recordings or derived test media; new GPU purchases; remote services; multi-GPU/multiple workers; batching; final service-profile promotion.

## Further notes

The explicit CUDA path, supported-compute checks, no-fallback behavior, and bounded device-memory observations are implemented. Prior CTranslate2 inventory reported one RTX 3050 and supported CUDA types, but that is capability discovery only; no model load or GPU transcription result exists. The ticket remains Blocked pending OPT-02-controlled evidence. See [implementation evidence](../../../docs/optimization-verification-20261018.md).
