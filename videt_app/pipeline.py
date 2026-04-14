from __future__ import annotations

import json
from pathlib import Path

from videt_app.ffmpeg import render_output
from videt_app.matching import build_match_windows
from videt_app.models import JobResult, ProcessingConfig
from videt_app.transcription import FasterWhisperTranscriber


def process_media(
    input_path: Path,
    output_path: Path,
    transcriber: FasterWhisperTranscriber,
    processing: ProcessingConfig,
    dry_run: bool = False,
) -> JobResult:
    transcript_words = transcriber.transcribe(input_path)
    windows = build_match_windows(
        words=transcript_words,
        targets=processing.words,
        lead_padding_ms=processing.lead_padding_ms,
        tail_padding_ms=processing.tail_padding_ms,
    )

    if not dry_run:
        render_output(
            input_path=input_path,
            output_path=output_path,
            windows=windows,
            mode=processing.mode,
            beep_frequency=processing.beep_frequency,
            beep_volume=processing.beep_volume,
        )

    return JobResult(
        input_path=input_path,
        output_path=output_path,
        windows=windows,
        transcript_word_count=len(transcript_words),
        dry_run=dry_run,
    )


def write_report(result: JobResult, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "input": str(result.input_path),
        "output": str(result.output_path),
        "dry_run": result.dry_run,
        "transcript_word_count": result.transcript_word_count,
        "matches": [
            {"word": item.word, "start": item.start, "end": item.end}
            for item in result.windows
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
