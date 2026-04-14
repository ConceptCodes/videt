from videt_app.ffmpeg import build_filter_complex
from videt_app.models import MatchWindow


def test_build_filter_complex_for_mute_mode() -> None:
    filter_complex = build_filter_complex(
        windows=[MatchWindow(word="damn", start=1.0, end=1.5)],
        mode="mute",
        beep_frequency=1000,
        beep_volume=0.35,
    )

    assert "volume=enable='between(t,1.000,1.500)':volume=0" in filter_complex
    assert filter_complex.endswith("[aout]")


def test_build_filter_complex_for_beep_mode_mixes_generated_tones() -> None:
    filter_complex = build_filter_complex(
        windows=[
            MatchWindow(word="damn", start=1.0, end=1.5),
            MatchWindow(word="hell", start=3.0, end=3.4),
        ],
        mode="beep",
        beep_frequency=1200,
        beep_volume=0.2,
    )

    assert "sine=frequency=1200" in filter_complex
    assert "sine=frequency=2040" in filter_complex
    assert "adelay=1000|1000[tone0a]" in filter_complex
    assert "adelay=3000|3000[tone1b]" in filter_complex
    assert "[tone0a][tone0b]amix=inputs=2:normalize=0[beep0]" in filter_complex
    assert "amix=inputs=3:normalize=0[aout]" in filter_complex
