"""Environment-backed settings; model/cache storage stays outside the checkout."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="STT_", extra="ignore")

    data_dir: Path = Path("D:/ai-stt") if os.name == "nt" else Path.home() / ".local/share/ai-stt"
    model: str = "turbo"
    cpu_threads: int = Field(default=4, ge=1, le=64)
    max_bytes: int = Field(default=1024**3, ge=1, le=1024**3)
    max_duration_seconds: float = Field(default=7200, gt=0, le=7200)
    max_queued: int = Field(default=10, ge=1, le=10)
    poll_seconds: float = Field(default=1, gt=0)
    heartbeat_seconds: float = Field(default=5, gt=0)
    heartbeat_timeout_seconds: float = Field(default=30, gt=0)

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
