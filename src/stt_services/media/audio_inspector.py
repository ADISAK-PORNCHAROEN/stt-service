import math
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import av

from stt_services.config import Settings

SUPPORTED_SUFFIXES = frozenset({".wav", ".mp3", ".m4a", ".flac", ".mp4"})
DEMUXERS = {".wav": "wav", ".mp3": "mp3", ".m4a": "mov", ".mp4": "mov", ".flac": "flac"}
MAX_TIMELINE_SPANS = 16_384


class InvalidMedia(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TimelineSpan:
    decoded_start: float
    decoded_end: float
    source_start: float
    source_end: float


@dataclass(frozen=True)
class AudioInfo:
    duration_seconds: float
    sample_rate: int
    channels: int
    decoded_seconds: float
    spans: tuple[TimelineSpan, ...]
    decoded_ends: tuple[float, ...]

    def source_time(self, seconds: float, *, end: bool = False) -> float:
        # Resampling to 16 kHz can round the decoded tail up by one sample.
        if seconds > self.decoded_seconds + 1 / 16000 + 1e-9:
            raise ValueError("Engine returned timestamps beyond decoded audio")
        point = min(seconds, self.decoded_seconds)
        position = (bisect_left if end else bisect_right)(self.decoded_ends, point)
        span = self.spans[min(position, len(self.spans) - 1)]
        return min(span.source_end, span.source_start + max(0, point - span.decoded_start))


def inspect_audio(path: Path, settings: Settings) -> AudioInfo:
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise InvalidMedia("Supported formats: WAV, MP3, M4A, FLAC, MP4")
    if not path.is_file():
        raise InvalidMedia("Input file does not exist")
    size = path.stat().st_size
    if size == 0 or size > settings.max_bytes:
        raise InvalidMedia("Input is empty or exceeds the upload size limit")
    try:
        # Force a supported container: sniffing arbitrary content could accept a playlist
        # that fetches remote URLs or local references before audio validation.
        with av.open(
            str(path),
            format=DEMUXERS[path.suffix.lower()],
            options={"protocol_whitelist": "file,pipe"},
        ) as container:
            if not container.streams.audio:
                raise InvalidMedia("Input has no audio stream")
            stream = container.streams.audio[0]
            duration = (
                float(stream.duration * stream.time_base)
                if stream.duration is not None and stream.time_base is not None
                else float(container.duration / av.time_base)
                if container.duration
                else 0
            )
            if not math.isfinite(duration) or duration <= 0:
                raise InvalidMedia("Audio duration is unknown or invalid")
            if duration > settings.max_duration_seconds:
                raise InvalidMedia("Audio exceeds the duration limit (maximum 2 hours)")
            decoded_seconds = Fraction(0)
            origin = float(container.start_time / av.time_base) if container.start_time else 0.0
            spans: list[TimelineSpan] = []
            for frame in container.decode(audio=0):
                if frame.is_corrupt or not frame.sample_rate:
                    raise InvalidMedia("Audio contains corrupt frames")
                frame_seconds = Fraction(frame.samples, frame.sample_rate)
                source_start = (
                    float(frame.pts * frame.time_base) - origin
                    if frame.pts is not None and frame.time_base is not None
                    else spans[-1].source_end
                    if spans
                    else 0.0
                )
                if source_start < -1 / frame.sample_rate:
                    raise InvalidMedia("Audio starts before the recording timeline")
                source_start = max(0.0, source_start)
                source_end = source_start + float(frame_seconds)
                if spans and source_start < spans[-1].source_end - 1 / frame.sample_rate:
                    raise InvalidMedia("Audio contains overlapping source timestamps")
                span = TimelineSpan(
                    float(decoded_seconds),
                    float(decoded_seconds + frame_seconds),
                    source_start,
                    source_end,
                )
                if spans and abs(source_start - spans[-1].source_end) < 1 / frame.sample_rate:
                    previous = spans[-1]
                    spans[-1] = TimelineSpan(
                        previous.decoded_start, span.decoded_end, previous.source_start, source_end
                    )
                else:
                    if len(spans) >= MAX_TIMELINE_SPANS:
                        raise InvalidMedia("Audio timeline is excessively fragmented")
                    spans.append(span)
                decoded_seconds += frame_seconds
                if decoded_seconds > settings.max_duration_seconds:
                    raise InvalidMedia("Audio exceeds the duration limit (maximum 2 hours)")
                if source_end > settings.max_duration_seconds:
                    raise InvalidMedia("Recording timeline exceeds the duration limit")
            if decoded_seconds <= 0:
                raise InvalidMedia("Audio stream cannot be decoded")
            recording_duration = max(
                spans[-1].source_end,
                float(container.duration / av.time_base) if container.duration else 0,
            )
            if recording_duration > settings.max_duration_seconds:
                raise InvalidMedia("Recording timeline exceeds the duration limit")
            timeline_spans = tuple(spans)
            return AudioInfo(
                recording_duration,
                stream.codec_context.sample_rate,
                stream.codec_context.channels,
                float(decoded_seconds),
                timeline_spans,
                tuple(span.decoded_end for span in timeline_spans),
            )
    except InvalidMedia:
        raise
    except (av.error.FFmpegError, OSError, ValueError, OverflowError) as exc:
        raise InvalidMedia("Cannot decode input audio") from exc
