# 05: Compare language and vocabulary hints for mixed speech

What to build: An operator can select language/context and short vocabulary hints through the same transcription workflow, obtain complete bundles identifying the effective choices, and compare reviewed Thai/English errors against the frozen baseline.
Blocked by: 02 - Compare configurable CPU decoding through complete result bundles.
Status: Blocked.
Ready for agent: No; approved; waiting for ticket 02.
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

Compare automatic language, an explicit Thai hint, and per-window multilingual mode where supported. Test a short relevant initial prompt or vocabulary hint independently, and compare previous-text conditioning as a separate factor. Record effective settings and hint identities without exposing private hint text in sanitized metadata.

Build vocabulary only from permitted tuning knowledge, never final-evaluation reference content. Preserve spoken English-only cues when preparing references. Watch for inserted glossary words, unwanted translation/transliteration, names/numbers, omissions, repetition, and silence errors. Per-window language detection is not a guarantee of within-sentence language-switch accuracy.

Keep baseline VAD/fallback initially. An evidence-justified VAD/fallback case must be separately labeled and retain quiet-speech and timestamp checks; it is not a blanket speed shortcut. No automatic LLM text repair is introduced.

## Testing

Use public commands and existing fake-engine seams to verify option validation, effective metadata, Unicode preservation, and exporters. Use hand-authored text fixtures for reference cleaning, spoken English-only cues, and scoring. Restrict all real inference/quality comparisons to Formal Words and Conversation with Kob, with the agreed tuning/final-evaluation roles.

## Acceptance criteria

- [ ] Supported language/context/hint choices reach actual inference through shared configuration and are described truthfully in complete result bundles.
- [ ] Unsupported combinations or ignored options fail clearly or are explicitly reported without claiming their application.
- [ ] Separate controlled cases compare baseline with language, context, and short vocabulary hints, with all other effective options held fixed.
- [ ] Frozen Thai/English scoring, important-name/number review, speech coverage, hallucination/repetition checks, and timing observations show which cases improve, regress, or remain inconclusive.
- [ ] Hints do not consume final-evaluation answer text, and reference preparation preserves spoken English while excluding translations/romanization.
- [ ] Any VAD/fallback change is justified by observed evidence and assessed separately for retained quiet speech, retries, and original-time subtitle behavior.
- [ ] Relevant public behavior and configured implementation-quality checks pass, with actual commands and sanitized evidence recorded.

## Out of scope

Additional real recordings or derived media; English-only or noise accuracy certification unsupported by these two originals; training; another model; automatic transcript rewriting; final default promotion.

## Further notes

No hint is assumed to improve every recording, and a numerical accuracy pass requires reviewed reference coverage. Validation evidence: Pending implementation.
