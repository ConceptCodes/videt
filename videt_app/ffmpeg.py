from __future__ import annotations

import json
import subprocess
from pathlib import Path

from videt_app.models import MatchWindow


def has_video_stream(input_path: Path) -> bool:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        str(input_path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout or "{}")
    return bool(payload.get("streams"))


def _escape_timestamp(value: float) -> str:
    return f"{value:.3f}"


def build_filter_complex(
    windows: list[MatchWindow],
    mode: str,
    beep_frequency: int,
    beep_volume: float,
    beep_file: Path | None = None,
    media_input_index: int = 0,
    beep_input_index: int | None = None,
) -> str:
    if not windows:
        return f"[{media_input_index}:a]anull[aout]"

    parts: list[str] = []
    muted = f"[{media_input_index}:a]"
    for idx, window in enumerate(windows):
        target = f"[mute{idx}]"
        parts.append(
            f"{muted}volume=enable='between(t,{_escape_timestamp(window.start)},"
            f"{_escape_timestamp(window.end)})':volume=0{target}"
        )
        muted = target

    if mode == "mute":
        parts.append(f"{muted}anull[aout]")
        return ";".join(parts)

    if beep_file is not None:
        beep_source_index = 0 if beep_input_index is None else beep_input_index
        source_labels: list[str] = []
        for idx, window in enumerate(windows):
            source = f"[beep{idx}src]"
            source_labels.append(source)
            parts.append(
                f"{source}atrim=duration={_escape_timestamp(window.duration)},"
                f"asetpts=PTS-STARTPTS,volume={beep_volume},adelay={int(window.start * 1000)}|{int(window.start * 1000)}"
                f"[beep{idx}]"
            )
        if source_labels:
            parts.insert(1, f"[{beep_source_index}:a]asplit={len(source_labels)}{''.join(source_labels)}")
        mix_inputs = "".join([muted, *[f"[beep{idx}]" for idx in range(len(windows))]])
        parts.append(f"{mix_inputs}amix=inputs={1 + len(windows)}:normalize=0[aout]")
        return ";".join(parts)

    beep_inputs: list[str] = []
    for idx, window in enumerate(windows):
        delay_ms = int(window.start * 1000)
        duration = _escape_timestamp(window.duration)
        tone_a = f"[tone{idx}a]"
        tone_b = f"[tone{idx}b]"
        label = f"[beep{idx}]"
        parts.append(
            "sine="
            f"frequency={beep_frequency}:sample_rate=48000:duration={duration},"
            f"volume={beep_volume},adelay={delay_ms}|{delay_ms}{tone_a}"
        )
        parts.append(
            "sine="
            f"frequency={int(beep_frequency * 1.7)}:sample_rate=48000:duration={duration},"
            f"volume={beep_volume * 0.75},adelay={delay_ms}|{delay_ms}{tone_b}"
        )
        parts.append(
            f"{tone_a}{tone_b}amix=inputs=2:normalize=0{label}"
        )
        beep_inputs.append(label)

    mix_inputs = "".join([muted, *beep_inputs])
    parts.append(f"{mix_inputs}amix=inputs={1 + len(beep_inputs)}:normalize=0[aout]")
    return ";".join(parts)


def render_output(
    input_path: Path,
    output_path: Path,
    windows: list[MatchWindow],
    mode: str,
    beep_frequency: int,
    beep_volume: float,
    beep_file: Path | None = None,
) -> None:
    filter_complex = build_filter_complex(
        windows=windows,
        mode=mode,
        beep_frequency=beep_frequency,
        beep_volume=beep_volume,
        beep_file=beep_file,
        media_input_index=1 if beep_file is not None else 0,
        beep_input_index=0 if beep_file is not None else None,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_render_command(
        input_path=input_path,
        output_path=output_path,
        filter_complex=filter_complex,
        beep_file=beep_file,
    )
    subprocess.run(command, check=True)


def build_render_command(
    input_path: Path,
    output_path: Path,
    filter_complex: str,
    beep_file: Path | None = None,
    has_video_stream_fn=has_video_stream,
) -> list[str]:
    command = ["ffmpeg", "-y"]
    media_input_index = 0
    if beep_file is not None:
        command.extend(["-stream_loop", "-1", "-i", str(beep_file)])
        media_input_index = 1
    command.extend(["-i", str(input_path), "-filter_complex", filter_complex, "-map", "[aout]", "-c:a", "aac"])
    if has_video_stream_fn(input_path):
        command.extend(
            ["-map", f"{media_input_index}:v:0", "-c:v", "copy", "-movflags", "+faststart"]
        )
    command.append(str(output_path))
    return command
