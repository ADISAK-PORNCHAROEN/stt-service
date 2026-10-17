"""Engine-independent transcript contract."""

import math
from dataclasses import asdict, dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    timing_source: Literal["model"] = "model"

    def __post_init__(self) -> None:
        if not math.isfinite(self.start) or not math.isfinite(self.end):
            raise ValueError("Segment times must be finite")
        if self.start < 0 or self.end < self.start:
            raise ValueError("Invalid segment time range")


@dataclass(frozen=True)
class EngineResult:
    segments: list[Segment]
    effective_configuration: dict[str, object]
    observations: dict[str, object] = field(default_factory=dict)


@dataclass
class RunMetrics:
    validation_seconds: float = 0
    model_load_seconds: float = 0
    inference_seconds: float = 0
    publication_seconds: float = 0
    total_seconds: float = 0
    peak_ram_bytes: int = 0
    rtfx_total: float = 0
    rtfx_inference: float = 0


@dataclass
class Transcript:
    duration_seconds: float
    segments: list[Segment]
    metrics: RunMetrics
    model: str = "turbo"
    source_name: str = ""
    schema_version: int = 1
    engine: str = "faster-whisper"
    configuration: dict[str, object] = field(default_factory=dict)
    versions: dict[str, str] = field(default_factory=dict)
    source_sha256: str | None = None

    def to_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["text"] = "\n".join(segment.text.strip() for segment in self.segments)
        result["timing_source"] = "model"
        for index, segment in enumerate(result["segments"], start=1):
            segment["id"] = index
        return result
