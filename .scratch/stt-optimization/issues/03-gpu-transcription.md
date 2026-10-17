# 03: Transcribe and measure with the existing GPU explicitly

What to build: An operator can request Turbo GPU transcription on the development PC, obtain a complete result bundle identifying its actual device/precision, and compare its controlled outcomes against the same-host CPU baseline.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; approved; waiting for ticket 02.
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

## Testing

Use public commands with a fake capability/engine boundary for missing GPU, unsupported precision, memory failures, metadata, and source/output preservation. Opt-in compatibility and measurements use only the two full originals. Existing persistent-worker readiness behavior should handle startup failure and must never advertise an unloaded model as ready.

## Acceptance criteria

- [ ] Explicit GPU selection produces complete Turbo JSON/TXT/SRT bundles on compatible installed hardware, and metadata identifies actual device, precision, revision, and effective decoding settings.
- [ ] Incompatible runtime/device/precision and resource failures produce actionable errors without silent CPU fallback or partial successful bundles.
- [ ] CPU selection remains usable and reproducible on a host without GPU runtime availability.
- [ ] A guarded same-host comparison records both originals, sequential CPU/GPU settings, cold loading, repeated warm full-call time, host RAM/device-memory observations, and reviewed quality/timing outcomes.
- [ ] Evidence separates raw GPU acceleration from precision/decoding changes and does not infer a home-server result.
- [ ] Existing model reuse, readiness, original timestamps, and publication contracts remain valid for a GPU-configured persistent worker.
- [ ] Relevant fake-engine, configuration, and configured quality checks pass, with actual commands and evidence recorded; unavailable GPU capability is reported as pending/unsupported rather than a passing acceptance result.

## Out of scope

Additional real recordings or derived test media; new GPU purchases; remote services; multi-GPU/multiple workers; batching; final service-profile promotion.

## Further notes

This depends on ticket 02's shared configuration/reporting contract, not on a CPU speedup having been achieved. Validation evidence: Pending implementation.
