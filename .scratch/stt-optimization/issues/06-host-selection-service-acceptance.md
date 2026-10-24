# 06: Homelab CPU portfolio acceptance

What to build: Verify that the CPU-only transcription workflow completes on the owner's homelab and produce concise, honest evidence suitable for testing or a portfolio.
Blocked by: OPT-01 and any conditional OPT-02/04/05 disposition.
Status: In progress.
Ready for agent: Yes; owner re-authorized homelab acceptance on 2026-10-24.
Triage label: ready-for-agent after blockers.

## Problem

Development-host measurements cannot prove that the workflow completes on the i7-4770K homelab. The portfolio needs a real end-to-end result and clear resource/timing evidence, without production service-level claims.

## Solution

Run both approved full recordings on the homelab with the CPU INT8 baseline or a justified CPU candidate. Demonstrate the existing CLI and persistent API/worker paths across the two recordings and publish complete canonical outputs. Report actual settings, runtime, memory, reference state, and limitations. Retain the baseline when no candidate is demonstrably better. Do not deploy or expose the service publicly.

## User stories

1. As the owner, I want the full approved recordings to finish on the target homelab CPU, so that the project is demonstrably runnable on its intended machine.
2. As a portfolio reviewer, I want complete JSON/TXT/SRT artifacts and measured resource use, so that I can see what the implementation actually does.
3. As the operator, I want the same selected CPU profile used by CLI and worker, so that the showcased paths behave consistently.

## Implementation decisions

Use only Formal Words and Conversation with Kob. Run one through CLI and the other through the existing API/worker flow, so both entry paths and both authorized sources are demonstrated without repeating every recording through every entry point. Use CPU INT8 unless OPT-02 proves a needed candidate; use the same effective profile for both paths. Confirm each call finishes and publishes all outputs without an out-of-memory or partial-success result.

Record host CPU/RAM, software/model revision, effective profile, external wall time through artifact publication and retrieval, RTFx, and peak process and system memory. For API/worker, record upload, queue, processing, and download separately. Start process-memory observation before worker model preload and continue through job completion so the reported peak includes the loaded model. One complete call per recording is sufficient for portfolio completion. Use the existing repeated-comparison workflow only when claiming a repeatable speed improvement. No RTFx threshold, GPU comparison, second host, batch matrix, production availability, or production SLA is part of acceptance.

Use reviewed references to compare the completed outputs. Do not claim an accuracy gain while reference review is pending. If a candidate is selected, retain it only if it fixes a reference-confirmed error without a material quality, time, or memory regression; otherwise use the baseline.

## Testing

Use existing ordinary fake-inference coverage for validation, profile propagation, publication, worker readiness, and job isolation. For real-model acceptance, run the two full originals only on the homelab with new external destinations. Preserve source and existing output files. No extra real-recording test, Docker deployment, or production exposure is authorized by this ticket.

## Acceptance criteria

- [ ] Both approved full recordings complete on the homelab CPU with the selected baseline or candidate and produce complete JSON/TXT/SRT bundles.
- [ ] One recording is demonstrated through CLI and the other through the local API/persistent worker; outputs identify the same effective CPU profile and preserve source-timeline behavior.
- [ ] The runs complete within available system memory without a partial success; host, runtime, model revision, settings, external wall time, RTFx, peak process memory including worker preload, and peak system memory are recorded. API upload, queue, worker processing, and artifact download times are kept distinct.
- [ ] Reviewed references are used for both outputs, or accuracy is clearly labeled pending if review is incomplete. Any promoted candidate fixes an identified error without material regression; otherwise the baseline is retained.
- [ ] The portfolio summary states that these two recordings and this homelab run do not establish production reliability, real-time service levels, or broad accuracy generalization.
- [x] Existing fake-inference worker isolation and lifecycle evidence is recorded in the [optimization verification report](../../../docs/optimization-verification-20261018.md); it does not substitute for the homelab real-model runs.

## Out of scope

GPU execution; development-host comparison; production deployment/SLA; broad tuning sweeps; additional or derived real recordings; model/backend replacement; new endpoints.

## Further notes

The owner re-authorized homelab acceptance on 2026-10-24. Complete this ticket only after all required host runs and evidence exist. See the [active scope](../spec.md#active-milestone-update-24-october-2026-owner-re-authorization) and the current progress report.

## Local-first evidence (23 October 2026)

Per owner direction, both approved full originals now complete on the current Windows workstation through the CLI and API/worker paths. The detailed local-only measurements, complete result bundles, source bindings, and limitations are in the [23 October progress report](../../../docs/optimization-progress-20261023.md) and `[private local path]`. The workstation is not the i7-4770K homelab, and reference review remains pending, so every homelab acceptance criterion above stays unchecked. Docker remains deferred until after local verification.

The owner clarified that Docker is the planned deployment method and should be handled at the end, after the workflow is usable on this computer. The owner later identified a configured SSH alias as the homelab, but clarified that work should stay in this project for now. No connection or remote command has occurred or is authorized yet. Keep this ticket open until target-host acceptance evidence is collected. Docker deployment remains last.

Local setup review found that `.env.local.example` explicitly set `STT_BATCH_SIZE=1`, although the current environment-backed configuration rejects that value when it is supplied as a string. The example now leaves the setting unset and relies on sequential mode's batch-size-one default. This resolves a local setup inconsistency only; it does not satisfy any homelab acceptance criterion.

The local Docker preflight on 23 October found no Dockerfile, Compose file, or `.dockerignore`, and PowerShell could not resolve the `docker` command. No image build or deployment was attempted. Docker remains the final phase, and this preflight does not change any OPT acceptance status.

The 24 October SSH preflight found four non-wildcard host stanzas in the user's SSH config, with one duplicate. The owner identified a configured alias as the i7-4770K homelab, then asked to keep work in the project for now. No connection or remote command has run; explicit authorization is still required before any homelab access.
