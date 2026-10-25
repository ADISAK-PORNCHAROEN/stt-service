from typing import Any

from stt_services.application.job_errors import InvalidTranscript


def apply_reviewed_text(document: dict[str, Any], edits: list[tuple[int, str]]) -> dict[str, Any]:
    segments = document.get("segments")
    if not isinstance(segments, list):
        raise InvalidTranscript("Transcript segments are unavailable")

    segment_ids: list[int] = []
    for segment in segments:
        if not isinstance(segment, dict):
            raise InvalidTranscript("Transcript segments are unavailable")
        segment_id = segment.get("id")
        if type(segment_id) is not int:
            raise InvalidTranscript("Transcript segment IDs are invalid")
        segment_ids.append(segment_id)
    if len(set(segment_ids)) != len(segment_ids):
        raise InvalidTranscript("Transcript segment IDs are invalid")

    edit_ids = [segment_id for segment_id, _ in edits]
    if len(set(edit_ids)) != len(edit_ids) or set(edit_ids) != set(segment_ids):
        raise InvalidTranscript("Provide one text update for every transcript segment ID")

    replacements = dict(edits)
    for segment in segments:
        segment["text"] = replacements[segment["id"]]
    document["text"] = "\n".join(segment["text"].strip() for segment in segments)
    return document
