from argparse import Namespace

from videt_app.cli import _read_words


def test_read_words_uses_packaged_default_list_when_no_override() -> None:
    words = _read_words(Namespace(words=None, words_file=None))

    assert "damn" in words
    assert "hell" in words


def test_read_words_uses_explicit_inputs_instead_of_default_list(tmp_path) -> None:
    words_file = tmp_path / "words.txt"
    words_file.write_text("dang\nheck\n", encoding="utf-8")

    words = _read_words(Namespace(words=None, words_file=words_file))

    assert words == {"dang", "heck"}
