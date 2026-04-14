from __future__ import annotations

import threading
from pathlib import Path

from videt_app.models import TranscriptionConfig, WordToken


class FasterWhisperTranscriber:
    _thread_local = threading.local()

    def __init__(self, config: TranscriptionConfig) -> None:
        self.config = config

    def _get_model(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is required for local transcription. "
                "Run `uv sync --dev` first."
            ) from exc

        cache = getattr(self._thread_local, "model_cache", None)
        if cache is None:
            cache = {}
            self._thread_local.model_cache = cache

        cache_key = (
            self.config.model_size,
            str(self.config.model_dir) if self.config.model_dir else None,
            self.config.device,
            self.config.compute_type,
            self.config.cpu_threads,
            self.config.num_workers,
        )
        model = cache.get(cache_key)
        if model is not None:
            return model

        model_kwargs = {
            "device": self.config.device,
            "compute_type": self.config.compute_type,
            "cpu_threads": self.config.cpu_threads,
            "num_workers": self.config.num_workers,
        }
        if self.config.model_dir:
            model_kwargs["download_root"] = str(self.config.model_dir)

        model = WhisperModel(self.config.model_size, **model_kwargs)
        cache[cache_key] = model
        return model

    def transcribe(self, media_path: Path) -> list[WordToken]:
        model = self._get_model()
        segments, _ = model.transcribe(
            str(media_path),
            language=self.config.language,
            beam_size=self.config.beam_size,
            word_timestamps=True,
            vad_filter=True,
        )

        words: list[WordToken] = []
        for segment in segments:
            for word in segment.words or []:
                if word.start is None or word.end is None:
                    continue
                words.append(
                    WordToken(
                        text=word.word,
                        start=float(word.start),
                        end=float(word.end),
                    )
                )
        return words
