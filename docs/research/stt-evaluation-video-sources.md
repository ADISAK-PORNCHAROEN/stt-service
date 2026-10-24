# Videos paired with transcription references

Checked: 18 October 2026. These are research candidates, not an approved or scored test corpus. No media or complete transcript is reproduced here, and no STT benchmark was run.

## Current experiment authorization

The owner's later instruction permits only Formal Words and Conversation with Kob for experiments. The downloaded MIT lecture is not authorized for experiments, inference, benchmarks, real-model integration, excerpts, or scoring unless the owner explicitly authorizes it later. Its historical listing below documents research/download history only. Do not enumerate the whole download folder or reuse its three-recording manifest as an approved evaluation manifest. No further source may be added to compensate for English-only or noise coverage gaps under the current scope.

## Downloaded package

At the owner's request, Formal Words, Conversation with Kob, and the MIT lecture were downloaded with their source transcripts to `[private local path]`. The package README maps files; `manifest.json` records sizes, SHA-256, durations, reference-cue counts, and file verification. MIT includes VTT/PDF, Formal Words includes original timed TXT, and Kob includes timed text extracted from the creator page as SRT with all original languages retained. All three MP4 files have audio/video; complete audio decoding and one video frame per file succeeded. This establishes file readability, not human-reviewed text accuracy or timestamp alignment. The earlier YouTube-access limitations below describe research-tool access before these successful downloads.

## Recommended starting candidates

### Thai with English terms: Formal Words, Thai With Grace

- [Video](https://www.youtube.com/watch?v=aC-QbxZB7RU)
- [Creator transcript and download page](https://thaiwithgrace.com/formal-words-transcript/)
- [Timed transcript TXT](https://thaiwithgrace.com/wp-content/uploads/2022/12/formalwordstranscript.txt)
- Last subtitle ends at 04:41.366; this is not a verified full video duration.
- The creator describes her own subtitle preparation. The Thai transcript contains English terms and some English-only cues, making this a useful mixed-language candidate.
- The file includes translations and romanization. Select the words actually spoken cue by cue; do not concatenate all subtitle lines or discard all Latin-only lines. Spot-check against the audio before calling it a reviewed reference. Pedagogical language switching differs from a technical meeting.

### English technical speech: MIT 6.0001, Lecture 1, What is Computation?

- [Official video and transcript page](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/resources/lecture-1-what-is-computation/)
- [Timed English VTT](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/a746f6bc380f5e6d807ffff5f56cd877_nykOeWgQcHM.vtt)
- [Publisher transcript PDF](https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/904de062253d2fad3064ab5ca917883d_nykOeWgQcHM.pdf)
- [Video download linked by MIT](https://archive.org/download/MIT6.0001F16/MIT6_0001F16_Lecture_01_300k.mp4)
- Official page HTML pairs these resources. The VTT returned HTTP 200, 62,402 bytes and 887 timed cues; its final cue ends at 42:57.160. Full video transfer was not checked. Publisher provision establishes provenance, not independently audited verbatim accuracy or subtitle alignment.
- Useful for English technical terms, numbers, and sustained speech. Choose a short contiguous excerpt after preview and retain exactly corresponding reference cues; this does not establish real-world noise coverage.

### Conversational Thai: Listen and Speak Natural Thai, Learn Thai with Mod

- [Creator page with episode transcript and embedded video](https://learnthaiwithmod.com/2020/04/video-listen-and-speak-like-a-native-thai-speaker-advanced-listening/)
- [Video](https://www.youtube.com/watch?v=ijIaqeF6Vck)
- The creator publishes a Thai conversation with her brother and a transcript. Its reference includes names and English entertainment terms embedded in Thai.
- Reference is formatted with Thai, romanization, and English translations. Use only the spoken-text lines for the matching conversation; teaching commentary elsewhere in the video is not automatically covered. Excerpt boundaries and exact correspondence have not been verified by listening.

## Additional candidates

- [Conversation with Kob, Thai With Grace](https://thaiwithgrace.com/conversation-with-kob/), [video](https://www.youtube.com/watch?v=8qcinxUA4YA): creator's inline timed transcript ends at 09:55.733. Its download link currently points to another episode; use and verify the inline transcript. See [Thai candidate investigation](thai-video-reference-candidates.md).
- [What Do Thai People Read? Easy Thai 7](https://www.youtube.com/watch?v=eHnd-0A4_64): official Easy Languages description credits transcription/translation to Natee Sakornyutthadej and describes original-language plus English subtitles. Candidate for street-interview speech. A downloadable Thai text track, actual acoustic conditions, and transcript completeness were not verified; do not treat as a ready machine-scoring reference.

## Practical selection policy

Start by checking Formal Words for Thai/English switching and MIT for English. Add conversational Thai from another speaker/source. Current candidates do not yet establish the accepted background-music/noise subset. Do not fill that gap with an assumed label or score.

Existing transcripts reduce reference-preparation work but may edit filler words, spelling, or content. Keep source subtitles and any corrections distinct, document the scoring treatment of filler/non-speech text, and assess subtitle timing separately from text. Source timestamps are useful navigation, not verified word alignment.

Reserve independent recordings/speakers for final evaluation where possible. A time split within one video can leak speaker/topic/vocabulary information, so it is a pilot compromise rather than evidence of broad generalization. Do not derive glossaries from held-out reference text. Native Thai subtitles are appropriate for Thai speech; translated Thai subtitles for English speech are not an ASR reference. Ignore auto-generated captions as an authoritative answer.

TED is an optional English source with interactive transcripts, but specific track provenance must be checked: [TED's own transcript instructions](https://help.ted.com/hc/en-us/articles/360018572954-How-do-I-find-transcripts-for-TED-and-TEDx-talks) warn that YouTube can default to auto-generated text.

YouTube pages/embed playback were throttled in the research tool. Creator pages and the MIT VTT were accessible; successful playback/download of every linked video is not claimed. Preserve publisher URLs and obtain media through available source-provided options. Keep downloaded media and working references outside Git.
