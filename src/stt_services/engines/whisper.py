from pathlib import Path

from stt_services.config import Settings
from stt_services.schemas import Segment


class WhisperEngine:
    def __init__(self, settings: Settings) -> None:
        settings.prepare()
        from faster_whisper import WhisperModel, download_model

        model_path = download_model(settings.model)
        self.revision = Path(model_path).name
        self.model = WhisperModel(
            model_path,
            device="cpu",
            compute_type="int8",
            cpu_threads=settings.cpu_threads,
        )

    def transcribe(self, path: Path) -> list[Segment]:
        segments, info = self.model.transcribe(
            str(path), task="transcribe", vad_filter=True, word_timestamps=False, beam_size=5
        )
        # Consuming the generator is part of inference, not model loading.
        return [
            Segment(min(s.start, info.duration), min(s.end, info.duration), s.text.strip())
            for s in segments
        ]
