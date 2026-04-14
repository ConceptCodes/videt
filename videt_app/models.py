from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WordToken:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class MatchWindow:
    word: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class ProcessingConfig:
    words: set[str]
    lead_padding_ms: int = 220
    tail_padding_ms: int = 180
    mode: str = "beep"
    beep_frequency: int = 920
    beep_volume: float = 0.55


@dataclass(frozen=True)
class TranscriptionConfig:
    model_size: str = "small.en"
    model_dir: Path | None = None
    device: str = "auto"
    compute_type: str = "auto"
    language: str = "en"
    beam_size: int = 1
    cpu_threads: int = 4
    num_workers: int = 1


@dataclass(frozen=True)
class JobResult:
    input_path: Path
    output_path: Path
    windows: list[MatchWindow]
    transcript_word_count: int
    dry_run: bool
