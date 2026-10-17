"""Run explicitly with STT_TEST_MEDIA and pytest -m integration."""

import json
import os
from pathlib import Path

import pytest

from stt_services.cli import main


@pytest.mark.integration
def test_real_model_transcribes_media(tmp_path):
    media = os.environ.get("STT_TEST_MEDIA")
    if not media:
        pytest.skip("Set STT_TEST_MEDIA to a supported recording")
    source = Path(media)
    output = tmp_path / "result"
    assert main(["transcribe", str(source), "--output-dir", str(output), "--approved-only"]) == 0
    result = json.loads((output / "transcript.json").read_text(encoding="utf-8"))
    assert result["duration_seconds"] > 0
    assert result["segments"]
    assert all(
        0 <= s["start"] <= s["end"] <= result["duration_seconds"] + 0.1 for s in result["segments"]
    )
