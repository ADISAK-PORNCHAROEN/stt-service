import io
import wave

import pytest

from stt_services.config import ResolvedProfile, Settings
from stt_services.schemas import Segment


@pytest.fixture(autouse=True)
def isolate_profile_environment(request, monkeypatch):
    # Ordinary cases choose their own profile; real opt-in checks inherit the
    # operator's selected profile so they still test actual service settings.
    if request.node.get_closest_marker("integration") is None:
        for name in Settings.model_fields.keys() & ResolvedProfile.model_fields.keys():
            monkeypatch.delenv(f"STT_{name.upper()}", raising=False)


@pytest.fixture
def wav_bytes():
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16000)
    return buffer.getvalue()


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("HF_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("STT_DATA_DIR", str(tmp_path / "data"))
    return Settings(data_dir=tmp_path / "data")


class FakeEngine:
    def transcribe(self, path):
        return [Segment(0.125, 0.875, "ทดสอบ Apple ราคาใหม่")]


@pytest.fixture
def engine_factory():
    return lambda settings: FakeEngine()
