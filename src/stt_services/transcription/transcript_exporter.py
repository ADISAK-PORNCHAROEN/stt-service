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
    (destination / "transcript.json").write_text(
        json.dumps(transcript.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (destination / "transcript.txt").write_text(
        "".join(s.text.strip() + "\n" for s in transcript.segments), encoding="utf-8", newline="\n"
    )
    (destination / "transcript.srt").write_text(
        "".join(
            f"{index}\n{srt_time(s.start)} --> {srt_time(s.end)}\n{s.text.strip()}\n\n"
            for index, s in enumerate(transcript.segments, start=1)
        ),
        encoding="utf-8",
        newline="\n",
    )
