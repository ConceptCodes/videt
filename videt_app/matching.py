from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from videt_app.models import MatchWindow, WordToken

WORD_CLEAN_RE = re.compile(r"[^\w']+")


def normalize_word(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    normalized = WORD_CLEAN_RE.sub("", normalized)
    return normalized.strip("'")


def load_word_list(raw_words: Iterable[str]) -> set[str]:
    return {word for item in raw_words if (word := normalize_word(item))}


def build_match_windows(
    words: Iterable[WordToken],
    targets: set[str],
    lead_padding_ms: int,
    tail_padding_ms: int,
) -> list[MatchWindow]:
    lead_padding_s = max(0.0, lead_padding_ms / 1000)
    tail_padding_s = max(0.0, tail_padding_ms / 1000)
    merged: list[MatchWindow] = []

    for token in words:
        normalized = normalize_word(token.text)
        if normalized not in targets:
            continue
        start = max(0.0, token.start - lead_padding_s)
        end = max(start, token.end + tail_padding_s)
        current = MatchWindow(word=normalized, start=start, end=end)
        if merged and current.start <= merged[-1].end:
            last = merged[-1]
            merged[-1] = MatchWindow(
                word=f"{last.word},{current.word}",
                start=last.start,
                end=max(last.end, current.end),
            )
            continue
        merged.append(current)
    return merged
