# Whisper optimization design interview

Date: 18 October 2026.
Status: Owner requested specification and ticket synthesis. Recommendations for Q1-Q8 accepted, subject to the later two-recording restriction below. Draft test-seam and ticket-breakdown review is pending.

## Latest owner scope instruction

Only Formal Words and Conversation with Kob are authorized for real-recording evaluation. The owner expressly withheld permission to experiment on the downloaded MIT lecture or any other source; do not use it as a benchmark, integration input, excerpt, fallback source, or quality reference without a new explicit instruction. Do not include that lecture in the feature specification or tickets. Downloaded presence does not confer experiment authorization.

This instruction narrows the earlier corpus-breadth discussion. English-only and background-music/noise coverage must be reported as unverified where absent from the two allowed originals. The [draft specification](../../.scratch/stt-optimization/spec.md) and [review package](../../.scratch/stt-optimization/review.md) are the current synthesis; the historical discussion below is not broader permission.

## Objective

The owner wants faster transcription and better Thai/English text. Establish the target workload, deployment constraints, quality requirements, and evaluation evidence before selecting an implementation.

## Established facts

- Current approved runtime: Turbo, faster-whisper, CPU INT8, four threads, beam five, automatic language detection, VAD, segment timestamps, and one persistent worker. Model reuse already exists.
- The development baseline processed 400.684 seconds of audio in 820.607 seconds warm. Other work overlapped the measurement; repeat it in isolation before attributing gains to any change.
- The development host is an i3-12100F with about 15.84 GiB RAM. The home-server target mentioned in verification is an i7-4770K and remains unmeasured.
- Read-only hardware inspection during this interview returned NVIDIA GeForce RTX 3050, 6144 MiB VRAM, driver 610.88 from nvidia-smi. GPU inference compatibility and performance have not been tested.
- The speech benchmark has two reviewed phrase corrections, with no complete reviewed reference. A separate song reference does not establish spoken-recording quality.
- Previous MVP tickets are complete; Qwen tickets are cancelled. Optimization choices here are new decisions.

Sources: [baseline](../../benchmarks/reports/20261017-turbo-cpu.md), [verification](../verification-20261017.md), [specification](../../.scratch/stt-mvp/spec.md), and [primary-source research](whisper-turbo-optimization-20261018.md). Hardware inventory is an observation from this interview, not an inference benchmark.

## Decision tree

### Round one: accepted recommendations

The owner answered: "Q1-5 ตามที่แนะนำ" (accept the recommendations for Q1-Q5).

1. Support both home-server CPU execution and development-host GPU execution, with hardware-appropriate configurations. Each target needs its own evidence.
2. Optimize completion time for one recording first. An initial target is processing ten minutes of audio within ten minutes; this is an objective, not an established capability.
3. Evaluate Thai and English separately. Seek improvements without degrading either language; detailed metrics and important-error criteria remain to be agreed.
4. Thai speech mixed with English is the primary workload. The recommendation left additional categories conditional on actual needs, so English-only and music-backed speech still need explicit scope decisions. The example answer from the interview is not treated as approval of those categories.
5. Start with approximately ten minutes of human-reviewed reference audio/text. Review workflow and held-out allocation remain open.

### Round two: accepted recommendations and revised reference request

The owner accepted Q6-Q8 and requested videos with existing answer transcripts for Q9.

6. Include Thai/English mixed speech, English-only speech, and speech with background music/noise; report these categories separately. Singing is deferred.
7. Measure full processing through complete JSON/TXT/SRT publication, reporting queue wait and model loading separately. Compare each host against its own baseline and the real-time objective. Require separate Thai/English text checks, important name/number errors, omissions/repetition, and subtitle timing checks. Report an unmet CPU speed target explicitly.
8. Start with Turbo/faster-whisper and compare CPU/GPU, beam, threads, batching, and language/vocabulary hints one factor at a time. Consider selective conservative decoding or large-v3 after evidence of recurring difficult spans. Consider alternate backends after initial results.
9. Replace preparation of a new reference from scratch with finding videos paired with existing creator/publisher transcripts. This does not approve any particular source, a 6/4-minute split, or treating unchecked subtitles as reviewed references.

### Current frontier

- Select source videos and verify spoken-text correspondence, including removing translations and romanization without deleting spoken English.
- Decide tuning/evaluation allocation by independent recordings or speakers where practical; exact minutes remain open.
- Set normalization, text/timing gates, resource ceilings, hardware-selection behavior, experiment budget, and promotion criteria.

Source research: [video/reference candidates](stt-evaluation-video-sources.md).

## Documentation policy

Record agreed decisions as the interview progresses. Add domain terms to CONTEXT.md only once their meanings are resolved. Create an ADR only for a consequential architectural trade-off that is costly to reverse. Recommendations in the research note are hypotheses, not accepted decisions.
