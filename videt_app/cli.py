from __future__ import annotations

import argparse
import concurrent.futures
from importlib import resources
from pathlib import Path

from videt_app.matching import load_word_list
from videt_app.models import ProcessingConfig, TranscriptionConfig
from videt_app.pipeline import process_media, write_report
from videt_app.transcription import FasterWhisperTranscriber

SUPPORTED_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".mp4", ".mov", ".mkv"}


def _default_word_file() -> Path:
    return Path(str(resources.files("videt_app.data").joinpath("default_words.txt")))


def _read_words(args: argparse.Namespace) -> set[str]:
    raw_words: list[str] = []
    if args.words:
        raw_words.extend(part.strip() for part in args.words.split(","))
    if args.words_file:
        raw_words.extend(args.words_file.read_text(encoding="utf-8").splitlines())
    if not raw_words:
        raw_words.extend(_default_word_file().read_text(encoding="utf-8").splitlines())
    words = load_word_list(raw_words)
    if not words:
        raise SystemExit("No target words were provided.")
    return words


def _iter_inputs(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path]
    pattern = "**/*" if recursive else "*"
    return sorted(
        item for item in path.glob(pattern) if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES
    )


def _output_path(input_path: Path, input_root: Path, output_root: Path) -> Path:
    if input_root.is_file():
        stem = input_path.stem
        return output_root if output_root.suffix else output_root / f"{stem}.bleeped{input_path.suffix}"
    relative = input_path.relative_to(input_root)
    return output_root / relative.with_name(f"{relative.stem}.bleeped{relative.suffix}")


def _report_path(input_path: Path, input_root: Path, report_root: Path) -> Path:
    if input_root.is_file():
        return report_root / f"{input_path.stem}.json"
    relative = input_path.relative_to(input_root)
    return report_root / relative.with_suffix(".json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-first profanity bleeping for audio and video.")
    parser.add_argument("input", type=Path, help="Input media file or directory.")
    parser.add_argument("output", type=Path, help="Output file or output directory.")
    parser.add_argument("--words", help="Comma-separated list of target words. Overrides the packaged default list.")
    parser.add_argument("--words-file", type=Path, help="Text file with one target word per line. Overrides the packaged default list.")
    parser.add_argument("--lead-padding-ms", type=int, default=220, help="Lead-in padding before a matched word.")
    parser.add_argument("--tail-padding-ms", type=int, default=180, help="Tail padding after a matched word.")
    parser.add_argument("--mode", choices=["beep", "mute"], default="beep", help="Replacement mode.")
    parser.add_argument("--beep-frequency", type=int, default=920, help="Base frequency for beep mode.")
    parser.add_argument("--beep-volume", type=float, default=0.55, help="Volume for beep mode.")
    parser.add_argument("--beep-file", type=Path, help="Optional custom audio file to use as the bleep sound.")
    parser.add_argument("--dry-run", action="store_true", help="Analyze and report matches without writing media.")
    parser.add_argument("--report-dir", type=Path, help="Write per-file JSON reports to this directory.")
    parser.add_argument("--recursive", action="store_true", help="Recursively scan an input directory.")
    parser.add_argument("--workers", type=int, default=1, help="Parallel files to process in batch mode.")
    parser.add_argument("--model-size", default="small.en", help="Whisper model name.")
    parser.add_argument("--model-dir", type=Path, help="Optional local model cache directory.")
    parser.add_argument("--device", default="auto", help="faster-whisper device: auto, cpu, cuda.")
    parser.add_argument("--compute-type", default="auto", help="faster-whisper compute type.")
    parser.add_argument("--language", default="en", help="Expected language for transcription.")
    parser.add_argument("--beam-size", type=int, default=1, help="Beam size. Lower is faster.")
    parser.add_argument("--cpu-threads", type=int, default=4, help="CPU threads for transcription.")
    parser.add_argument("--model-workers", type=int, default=1, help="Internal transcription workers.")
    return parser


def _process_one(
    media_path: Path,
    input_root: Path,
    output_root: Path,
    processing: ProcessingConfig,
    transcription: TranscriptionConfig,
    dry_run: bool,
    report_dir: Path | None,
) -> None:
    output_path = _output_path(media_path, input_root, output_root)
    transcriber = FasterWhisperTranscriber(transcription)
    result = process_media(
        input_path=media_path,
        output_path=output_path,
        transcriber=transcriber,
        processing=processing,
        dry_run=dry_run,
    )
    if report_dir:
        write_report(result, _report_path(media_path, input_root, report_dir))
    print(
        f"{media_path} -> {output_path} | transcript_words={result.transcript_word_count} "
        f"| matches={len(result.windows)} | dry_run={dry_run}"
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    words = _read_words(args)
    processing = ProcessingConfig(
        words=words,
        lead_padding_ms=args.lead_padding_ms,
        tail_padding_ms=args.tail_padding_ms,
        mode=args.mode,
        beep_frequency=args.beep_frequency,
        beep_volume=args.beep_volume,
        beep_file=args.beep_file,
    )
    transcription = TranscriptionConfig(
        model_size=args.model_size,
        model_dir=args.model_dir,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
        beam_size=args.beam_size,
        cpu_threads=args.cpu_threads,
        num_workers=args.model_workers,
    )

    inputs = _iter_inputs(args.input, recursive=args.recursive)
    if not inputs:
        raise SystemExit(f"No supported media found under {args.input}")

    if args.input.is_file() and len(inputs) == 1:
        _process_one(
            media_path=inputs[0],
            input_root=args.input,
            output_root=args.output,
            processing=processing,
            transcription=transcription,
            dry_run=args.dry_run,
            report_dir=args.report_dir,
        )
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = [
            executor.submit(
                _process_one,
                media_path=item,
                input_root=args.input,
                output_root=args.output,
                processing=processing,
                transcription=transcription,
                dry_run=args.dry_run,
                report_dir=args.report_dir,
            )
            for item in inputs
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return 0
