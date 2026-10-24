"""Publisher subtitle parsing and explicit human-review provenance."""

import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from typing import Literal, Self, cast

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from rapidfuzz.distance import Levenshtein

SCORING_POLICY_ID = "nfc-casefold-projections-v1"
SCORING_POLICY_DESCRIPTION = (
    "NFC; case-fold; normalize curly apostrophe; replace other punctuation/symbols with "
    "spaces; collapse whitespace; Thai CER counts Thai-script code points including marks; "
    "English WER counts ASCII words with internal apostrophes; numeric tokens are separate."
)


class ReferenceCue(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: int = Field(ge=1)
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(ge=0, allow_inf_nan=False)
    text: str
    publisher_lines: list[str]
    reviewed: bool = False
    uncertain: bool = False
    timing_reviewed: bool = False
    notes: str = ""

    @model_validator(mode="after")
    def ordered_times(self) -> Self:
        if self.end < self.start:
            raise ValueError("Reference cue end precedes its start")
        return self


class SpokenReference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1] = 1
    recording_id: str
    source_sha256: str
    publisher_sha256: str
    normalization: Literal["nfc-casefold-projections-v1"] = "nfc-casefold-projections-v1"
    reviewed_by: str | None = None
    reviewed_at: AwareDatetime | None = None
    cues: list[ReferenceCue] = Field(min_length=1, max_length=10000)
    important_errors_reviewed: bool = False
    important_error_notes: str = ""

    @model_validator(mode="after")
    def ordered_cues(self) -> Self:
        if len({cue.id for cue in self.cues}) != len(self.cues):
            raise ValueError("Duplicate reference cue identity")
        if any(a.start > b.start for a, b in zip(self.cues, self.cues[1:], strict=False)):
            raise ValueError("Reference cue starts must be chronological")
        if self.reviewed_by is not None and not self.reviewed_by.strip():
            raise ValueError("Reference reviewer must have a nonempty identity")
        return self


_TIMED_HEADER = re.compile(
    r"(?m)^\s*(\d+)\s*\n"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})[^\n]*\n"
)


def parse_publisher_subtitles(text: str) -> list[ReferenceCue]:
    """Suggest speech lines but never infer a human review from a suggestion."""
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    headers = list(_TIMED_HEADER.finditer(text))
    if not headers:
        raise ValueError("Publisher reference contains no supported timed cues")
    cues = []
    for index, header in enumerate(headers):
        stop = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        lines = [line.strip() for line in text[header.end() : stop].splitlines() if line.strip()]
        if not lines:
            raise ValueError("Publisher reference has an empty subtitle cue")
        thai = next((line for line in lines if re.search(r"[\u0e00-\u0e7f]", line)), None)
        values = [int(value) for value in header.groups()]
        if any(value > 59 for value in (values[2], values[3], values[6], values[7])):
            raise ValueError("Publisher reference timestamp has an invalid minute or second")
        cues.append(
            ReferenceCue(
                id=values[0],
                start=values[1] * 3600 + values[2] * 60 + values[3] + values[4] / 1000,
                end=values[5] * 3600 + values[6] * 60 + values[7] + values[8] / 1000,
                text=thai or lines[0],
                publisher_lines=lines,
                uncertain=thai is None,
                notes="Confirm English-only cue against the audio; do not discard it."
                if thai is None
                else "Check actual speech; translation/romanization selection is provisional.",
            )
        )
    return cues


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold().replace("’", "'")
    return " ".join(
        "".join(
            " " if unicodedata.category(char)[0] in {"P", "S"} and char != "'" else char
            for char in text
        ).split()
    )


def error_measure(reference: Sequence[str], hypothesis: Sequence[str]) -> dict[str, object]:
    operations = Counter(operation.tag for operation in Levenshtein.editops(reference, hypothesis))
    errors = sum(operations.values())
    return {
        "errors": errors,
        "substitutions": operations["replace"],
        "deletions": operations["delete"],
        "insertions": operations["insert"],
        "reference_units": len(reference),
        "rate": errors / len(reference) if reference else None,
    }


def score_reference(
    reference: SpokenReference | None, hypothesis: str, duration_seconds: float
) -> dict[str, object]:
    pending: dict[str, object] = {"status": "pending_review", "thai_cer": None, "english_wer": None}
    if reference is None:
        return pending
    if any(cue.end > duration_seconds for cue in reference.cues):
        raise ValueError("Reviewed reference cue exceeds the original recording duration")
    reviewed = [cue for cue in reference.cues if cue.reviewed and not cue.uncertain]
    coverage = {
        "reviewed_cues": len(reviewed),
        "total_cues": len(reference.cues),
        "cue_fraction": len(reviewed) / len(reference.cues),
        "uncertain_cue_ids": [cue.id for cue in reference.cues if cue.uncertain],
    }
    if (
        len(reviewed) != len(reference.cues)
        or not reference.reviewed_by
        or not reference.reviewed_at
    ):
        return {**pending, "coverage": coverage}
    spoken = " ".join(cue.text for cue in reference.cues)
    normalized_reference = normalize_text(spoken)
    normalized_hypothesis = normalize_text(hypothesis)
    thai = error_measure(
        re.findall(r"[\u0e00-\u0e7f]", normalized_reference),
        re.findall(r"[\u0e00-\u0e7f]", normalized_hypothesis),
    )
    english = error_measure(
        re.findall(r"[a-z]+(?:'[a-z]+)*", normalized_reference),
        re.findall(r"[a-z]+(?:'[a-z]+)*", normalized_hypothesis),
    )
    return {
        "status": "scored",
        "scoring_policy_id": SCORING_POLICY_ID,
        "normalization": reference.normalization,
        "thai_cer": thai["rate"],
        "english_wer": english["rate"],
        "thai": thai,
        "english": english,
        "raw_full_cer": error_measure(spoken, hypothesis)["rate"],
        "raw_full_text": error_measure(list(spoken), list(hypothesis)),
        "normalized_full_cer": error_measure(
            list(normalized_reference), list(normalized_hypothesis)
        )["rate"],
        "normalized_full_text": error_measure(
            list(normalized_reference), list(normalized_hypothesis)
        ),
        "numeric_tokens": error_measure(
            re.findall(r"\d+(?:\.\d+)?", normalized_reference),
            re.findall(r"\d+(?:\.\d+)?", normalized_hypothesis),
        ),
        "coverage": coverage,
        "reviewed_by": reference.reviewed_by,
        "reviewed_at": reference.reviewed_at.isoformat(),
        "important_error_review": "pending",
        "timing_review": "pending",
        "reference_important_error_review": "reviewed"
        if reference.important_errors_reviewed
        else "pending",
        "reference_timing_review": "reviewed"
        if all(cue.timing_reviewed for cue in reference.cues)
        else "pending",
        "limitations": "Thai-character and English-word projections; numeric tokens reported "
        "separately. Full-text error and manual important-error review are required to detect "
        "cross-language ordering errors. No standalone English-only accuracy claim.",
    }


def summarize_quality(reports: Sequence[dict[str, object]]) -> dict[str, object]:
    """Retain the worst observed measure; this is not a single-run transcript."""
    summary = dict(reports[0])
    if any(report["status"] != "scored" for report in reports):
        return summary
    for measure in ("thai_cer", "english_wer", "raw_full_cer", "normalized_full_cer"):
        values = [cast(float, report[measure]) for report in reports if report[measure] is not None]
        summary[measure] = max(values) if values else None
    for measure in ("thai", "english", "numeric_tokens"):
        summary[measure] = max(
            (cast(dict[str, object], report[measure]) for report in reports),
            key=lambda item: cast(int, item["errors"]),
        )
    for measure in ("raw_full_text", "normalized_full_text"):
        summary[measure] = max(
            (cast(dict[str, object], report[measure]) for report in reports),
            key=lambda item: cast(int, item["errors"]),
        )
    return summary
