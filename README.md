# videt

`videt` is a local-first CLI for automatically bleeping selected words from audio or video files.

It ships with a packaged default profanity list derived from the English list in `soluvas/badwords-list`, which documents that list as being based on Google's old "what do you love" profanity list.

## Design

- Transcription uses `faster-whisper`, which runs locally and can use CPU or GPU.
- Word matching is rule-based and happens on word-level timestamps.
- Media rewriting uses `ffmpeg`, which keeps video untouched and replaces only the audio track.
- Batch processing is parallelized at the file level for bulk runs.

## Requirements

- Python 3.11+
- `uv`
- `ffmpeg` and `ffprobe` on `PATH`

## Install

Provision the local virtualenv with `uv`:

```bash
uv sync --dev
```

After that, use `just` for project commands. The `justfile` calls tools from `.venv/bin` directly; it does not shell out through `uv run`.

## Usage

Single file:

```bash
just single input.mp4 output.mp4
```

With explicit overrides:

```bash
just run input.mp4 output.mp4 --lead-padding-ms 260 --tail-padding-ms 220
```

Batch directory:

```bash
just batch ./incoming ./processed banned_words.txt 4
```

Dry run with reports:

```bash
just dry-run ./incoming ./processed banned_words.txt ./reports
```

CLI help:

```bash
just help
```

Run tests:

```bash
just test
```

Underlying `uv` command equivalents:

```bash
uv sync --dev
```

## Notes

- `--beam-size 1` is the fastest option and is the default here.
- The default censor timing is asymmetric: `220ms` lead-in and `180ms` tail padding so short profanities do not leak at the edges.
- If you do not pass `--words` or `--words-file`, the packaged default profanity list is used.
- For CPU-heavy bulk processing, `small.en` or `base.en` with `--compute-type int8` is the practical starting point.
- For better quality on difficult audio, move to `medium.en` and accept slower throughput.
- Matching is exact after normalization, so `shit!` matches `shit`.
