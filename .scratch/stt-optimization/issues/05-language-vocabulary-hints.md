# 05: Compare language and vocabulary hints for mixed speech

What to build: Only after reference review identifies one specific spoken-word error in Formal Words, test at most one short hint and check it against the frozen baseline and Kob final result.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; wait for reviewed OPT-01/02 evidence. Record N/A if no specific error justifies a hint.
Triage label: ready-for-agent.

## Problem

Mixed Thai/English speech can lose names, English terms, or context. A glossary can also insert unspoken words, and a language hint does not prove better code-switch recognition.

## Solution

Expose controlled language, previous-text context, and vocabulary choices through shared startup configuration and compare them independently with actual spoken references. Preserve the default when evidence does not support a change.

## User stories

1. As a Thai/English user, I want English terms preserved during Thai speech, so that names and technical vocabulary remain recognizable.
2. As the reviewer, I want separate language/context/vocabulary cases, so that an improvement or regression has an attributable cause.
3. As the owner, I want held-out answer text protected from glossary construction, so that the final comparison is not optimized to its answer key.

## Implementation decisions

Do not sweep language, context, or hints. If one clear error in the Formal Words tuning reference meets the trigger, test one short relevant hint with all other settings unchanged. Record the effective profile and a hash of the private hint, never its text in sanitized output. Use Kob only as a final non-regression check; do not derive the hint from Kob's reference.

Build vocabulary only from permitted tuning knowledge, never final-evaluation reference content. Preserve spoken English-only cues when preparing references. Watch for inserted glossary words, unwanted translation/transliteration, names/numbers, omissions, repetition, and silence errors. Per-window language detection is not a guarantee of within-sentence language-switch accuracy.

Keep baseline VAD/fallback initially. An evidence-justified VAD/fallback case must be separately labeled and retain quiet-speech and timestamp checks; it is not a blanket speed shortcut. No automatic LLM text repair is introduced.

Use the earlier diagnostics to investigate actual language switches, English written phonetically in Thai, context-propagated errors, omissions, and inconsistent names/numbers. A writing-convention difference is not automatically a semantic recognition error; freeze that review/scoring policy before choosing a candidate. A separately justified temperature-zero comparison may investigate sampling variation, with unchanged baseline retained and no claim of guaranteed correctness or cross-device determinism. Returned segment temperature alone cannot count retries.

## Testing

Use public commands and existing fake-engine seams to verify option validation, effective metadata, Unicode preservation, and exporters. Use hand-authored text fixtures for reference cleaning, spoken English-only cues, and scoring. Restrict all real inference/quality comparisons to Formal Words and Conversation with Kob, with the agreed tuning/final-evaluation roles.

## Acceptance criteria

- [ ] Supported language/context/hint choices reach actual inference through shared configuration and are described truthfully in complete result bundles.
- [ ] Unsupported combinations or ignored options fail clearly or are explicitly reported without claiming their application.
- [ ] If the trigger is met, one hint case is compared to baseline with all other effective options held fixed; otherwise record N/A and the reviewed evidence that found no targeted error.
- [ ] Frozen Thai/English scoring, important-name/number review, speech coverage, hallucination/repetition checks, and timing observations show which cases improve, regress, or remain inconclusive.
- [ ] Reports distinguish reviewed language-switch/recognition errors, script/orthography differences, and reference mismatches; forced/detected language evidence is truthful and Kob answer text does not drive candidate selection.
- [ ] Hints do not consume final-evaluation answer text, and reference preparation preserves spoken English while excluding translations/romanization.
- [ ] Any VAD/fallback change is justified by observed evidence and assessed separately for retained quiet speech, retries, and original-time subtitle behavior.
- [x] Profile, option validation, fake-engine metadata, comparison, and worker-isolation checks pass; full ordinary suite, lint, formatting, and types pass, with commands in the [implementation evidence](../../../docs/optimization-verification-20261018.md). No reviewed real-recording comparison is claimed.

## Out of scope

Additional real recordings or derived media; more than one hint; broad language/context/hint sweeps; English-only or noise accuracy certification unsupported by these two originals; training; another model; automatic transcript rewriting; final default promotion.

## Further notes

Automatic/forced/per-window language modes, hashed prompt/hotword identities, scoring projections, and comparison fields are implemented. No hint/language/context trial has been run on the approved recordings, and no reviewed numerical accuracy comparison exists. Kob remains disclosed as prior exposure and cannot be treated as an independent untouched holdout. See [implementation evidence](../../../docs/optimization-verification-20261018.md).
