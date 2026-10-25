from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr


class TranscriptSegmentEditDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: StrictInt
    text: StrictStr


class TranscriptUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    segments: list[TranscriptSegmentEditDTO]


class TranscriptSavedDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["saved"] = "saved"
