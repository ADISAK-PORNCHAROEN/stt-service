"""Environment-backed settings; model/cache storage stays outside the checkout."""

import hashlib
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STT_", extra="ignore", frozen=True)

    data_dir: Path = Path("D:/ai-stt") if os.name == "nt" else Path.home() / ".local/share/ai-stt"
    model: str = "turbo"
    cpu_threads: int = Field(default=4, ge=1, le=64)
    beam_size: int = Field(default=5, ge=1, le=10)
    device: Literal["cpu", "cuda"] = "cpu"
    device_index: int = Field(default=0, ge=0, le=15)
    compute_type: Literal["int8", "float16", "int8_float16"] | None = None
    mode: Literal["sequential", "batched"] = "sequential"
    batch_size: Literal[1, 2, 4] = 1
    language_mode: Literal["auto", "th", "multilingual_per_window"] = "auto"
    condition_on_previous_text: bool = True
    temperature_zero: bool = False
    no_repeat_ngram_size: int = Field(default=0, ge=0, le=20)
    vad_enabled: bool = True
    vad_threshold: float = Field(default=0.5, gt=0, lt=1)
    vad_min_silence_duration_ms: int = Field(default=2000, ge=0, le=30000)
    vad_speech_pad_ms: int = Field(default=400, ge=0, le=5000)
    initial_prompt: str | None = Field(default=None, max_length=1000)
    hotwords: str | None = Field(default=None, max_length=1000)
    max_bytes: int = Field(default=1024**3, ge=1, le=1024**3)
    max_duration_seconds: float = Field(default=7200, gt=0, le=7200)
    max_queued: int = Field(default=10, ge=1, le=10)
    poll_seconds: float = Field(default=1, gt=0)
    heartbeat_seconds: float = Field(default=5, gt=0)
    heartbeat_timeout_seconds: float = Field(default=30, gt=0)

    def resolve_profile(self) -> "ResolvedProfile":
        return ResolvedProfile(
            schema_version=2 if self.no_repeat_ngram_size else 1,
            model=self.model,
            device=self.device,
            device_index=self.device_index,
            compute_type=self.compute_type or ("int8" if self.device == "cpu" else "float16"),
            cpu_threads=self.cpu_threads,
            beam_size=self.beam_size,
            mode=self.mode,
            batch_size=self.batch_size,
            language_mode=self.language_mode,
            condition_on_previous_text=self.condition_on_previous_text,
            temperature_zero=self.temperature_zero,
            no_repeat_ngram_size=self.no_repeat_ngram_size,
            vad_enabled=self.vad_enabled,
            vad_threshold=self.vad_threshold,
            vad_min_silence_duration_ms=self.vad_min_silence_duration_ms,
            vad_speech_pad_ms=self.vad_speech_pad_ms,
            initial_prompt=self.initial_prompt,
            hotwords=self.hotwords,
        )

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def database(self) -> Path:
        return self.data_dir / "jobs.sqlite3"

    def prepare(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self.data_dir / "cache/huggingface"))
        os.environ.setdefault("UV_CACHE_DIR", str(self.data_dir / "cache/uv"))


class ResolvedProfile(BaseModel):
    """Versioned immutable startup configuration shared by every inference path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1, 2] = 1
    model: str
    device: Literal["cpu", "cuda"]
    device_index: int
    compute_type: Literal["int8", "float16", "int8_float16"]
    cpu_threads: int
    beam_size: int
    mode: Literal["sequential", "batched"]
    batch_size: Literal[1, 2, 4]
    language_mode: Literal["auto", "th", "multilingual_per_window"]
    condition_on_previous_text: bool
    temperature_zero: bool
    no_repeat_ngram_size: int = Field(default=0, ge=0, le=20)
    vad_enabled: bool
    vad_threshold: float
    vad_min_silence_duration_ms: int
    vad_speech_pad_ms: int
    initial_prompt: str | None = None
    hotwords: str | None = None
    model_window_seconds: Literal[30] = 30

    @model_validator(mode="after")
    def valid_profile_combinations(self) -> "ResolvedProfile":
        if self.schema_version == 1 and self.no_repeat_ngram_size:
            raise ValueError("A nonzero repetition limit requires profile schema version 2")
        if self.mode == "sequential" and self.batch_size != 1:
            raise ValueError("Sequential mode requires batch size 1")
        if self.mode == "batched" and not self.vad_enabled:
            raise ValueError(
                "Batched mode currently requires VAD; the pinned runtime requires explicit "
                "clip timestamps when VAD is disabled"
            )
        if self.device == "cpu" and self.compute_type != "int8":
            raise ValueError("CPU transcription supports the configured int8 baseline only")
        if self.device == "cuda" and self.compute_type not in {"float16", "int8_float16"}:
            raise ValueError("CUDA transcription requires float16 or int8_float16 compute")
        if self.initial_prompt and self.hotwords:
            raise ValueError("Initial prompt and hotwords must be evaluated separately")
        return self

    @property
    def temperature_schedule(self) -> list[float]:
        return [0.0] if self.temperature_zero else [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    @property
    def vad_parameters(self) -> dict[str, int | float]:
        return {
            "threshold": self.vad_threshold,
            "min_silence_duration_ms": self.vad_min_silence_duration_ms,
            "speech_pad_ms": self.vad_speech_pad_ms,
            "max_speech_duration_s": self.model_window_seconds,
        }

    @property
    def public_configuration(self) -> dict[str, object]:
        result = self.model_dump(exclude={"initial_prompt", "hotwords"})
        if self.schema_version == 1:
            # Preserve existing baseline and candidate identities byte for byte.
            result.pop("no_repeat_ngram_size")
        result["initial_prompt_sha256"] = _private_value_hash(self.initial_prompt)
        result["hotwords_sha256"] = _private_value_hash(self.hotwords)
        return result

    @property
    def profile_id(self) -> str:
        encoded = json.dumps(self.public_configuration, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:20]
        return f"whisper-profile-v{self.schema_version}-{digest}"


def _private_value_hash(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
