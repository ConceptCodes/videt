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
) -> str:
    if not windows:
        return "[0:a]anull[aout]"

    parts: list[str] = []
    muted = "[0:a]"
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
) -> None:
    filter_complex = build_filter_complex(
        windows=windows,
        mode=mode,
        beep_frequency=beep_frequency,
        beep_volume=beep_volume,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[aout]",
        "-c:a",
        "aac",
    ]
    if has_video_stream(input_path):
        command.extend(["-map", "0:v:0", "-c:v", "copy", "-movflags", "+faststart"])
    command.append(str(output_path))
    subprocess.run(command, check=True)
