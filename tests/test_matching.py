from videt_app.matching import build_match_windows, load_word_list, normalize_word
from videt_app.models import WordToken


def test_normalize_word_strips_case_and_punctuation() -> None:
    assert normalize_word("Shit!!") == "shit"
    assert normalize_word("'Damn'") == "damn"


def test_load_word_list_discards_empty_values() -> None:
    assert load_word_list([" damn ", "", "!!", "hell"]) == {"damn", "hell"}


def test_build_match_windows_applies_padding_and_merges_overlap() -> None:
    words = [
        WordToken(text="hello", start=0.0, end=0.3),
        WordToken(text="damn", start=1.0, end=1.2),
        WordToken(text="damn!", start=1.22, end=1.4),
        WordToken(text="bye", start=2.0, end=2.2),
    ]

    windows = build_match_windows(
        words,
        targets={"damn"},
        lead_padding_ms=80,
        tail_padding_ms=50,
    )

    assert len(windows) == 1
    assert windows[0].start == 0.92
    assert windows[0].end == 1.45
    assert windows[0].word == "damn,damn"
