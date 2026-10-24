# Local transcription

Language for transcribing Thai/English recordings and tracking locally submitted work.

## Language

**Recording**:
The original audio timeline to which all transcript timestamps refer, including when the source is a video containing audio.
_Avoid_: Chunk timeline, processed timeline

**Source**:
The user-owned file supplied for transcription.
_Avoid_: Upload, temporary input

**Upload**:
A service-owned copy of a submitted source, retained for processing and a limited period afterward.
_Avoid_: Source, permanent archive

**Transcript**:
The canonical account of recognized text and its ordered timed segments for one recording.
_Avoid_: Subtitle file, export

**Reviewed reference**:
Text checked by a human against a recording and used to assess transcription errors for that recording.
_Avoid_: Unreviewed model output, assumed ground truth

**Segment**:
A span of recognized text with start and end times on the original recording.
_Avoid_: Word timestamp, speaker turn

**Model timing**:
Segment boundaries estimated by the transcription model, without a claim of manual alignment.
_Avoid_: Verified alignment, word alignment

**Export**:
A representation of a transcript for reading or subtitles, derived without transcribing the recording again.
_Avoid_: New transcription

**Result bundle**:
The complete set of transcript artifacts published together for one transcription.
_Avoid_: Partial result, individual working file

**Job**:
A service-accepted request to transcribe one recording, with an identity and lifecycle state.
_Avoid_: CLI invocation, upload

**Queued job**:
An accepted job waiting to begin transcription.
_Avoid_: Running job, all unfinished jobs

**Running job**:
A job claimed for transcription whose outcome has not yet been recorded.
_Avoid_: Queued job

**Succeeded job**:
A job with a complete published result bundle and a recorded successful outcome.
_Avoid_: Finished inference, staged result

**Failed job**:
A job with a recorded unsuccessful outcome, including work interrupted by a worker restart.
_Avoid_: Retrying job, expired job

**Active job**:
A queued or running job whose data is still needed for processing.
_Avoid_: Retained terminal job

**Interrupted job**:
A formerly running job whose processing ended before an outcome was recorded and is classified as failed during recovery.
_Avoid_: Automatically retried job

**Expired job**:
A terminal job whose retention period has elapsed and whose status and results are no longer available to clients.
_Avoid_: Failed job, interrupted job

**Cold run**:
A measurement beginning with an unloaded transcription model in a fresh process; download and cache conditions are stated separately.
_Avoid_: First download

**Warm run**:
A measurement that reuses an already loaded transcription model.
_Avoid_: Second CLI invocation, cached download

**RTFx**:
Recording duration divided by a stated processing duration; the denominator identifies inference time or total time.
_Avoid_: Unqualified speed multiplier
