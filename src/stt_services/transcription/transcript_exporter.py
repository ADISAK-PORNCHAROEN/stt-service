import json
from pathlib import Path

from stt_services.domain.transcript_entities import Transcript


def srt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def write_exports(transcript: Transcript, destination: Path) -> None:
    document = transcript.to_dict()
    for export_format in ("json", "txt", "srt"):
        write_transcript_export(
            document, export_format, destination / f"transcript.{export_format}"
        )


def write_transcript_export(
    document: dict[str, object], export_format: str, destination: Path
) -> None:
    segments = document.get("segments")
    if not isinstance(segments, list):
        raise ValueError("Transcript segments are unavailable")
    if export_format == "json":
        destination.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    if export_format == "txt":
        destination.write_text(
            "".join(f"{segment['text'].strip()}\n" for segment in segments),
            encoding="utf-8",
            newline="\n",
        )
        return
    if export_format != "srt":
        raise ValueError("Unsupported transcript export format")
    destination.write_text(
        "".join(
            f"{index}\n{srt_time(segment['start'])} --> {srt_time(segment['end'])}"
            f"\n{segment['text'].strip()}\n\n"
            for index, segment in enumerate(segments, start=1)
        ),
        encoding="utf-8",
        newline="\n",
    )
