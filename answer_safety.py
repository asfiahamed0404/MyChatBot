"""Import-safe cleanup for model-generated Markdown answers."""

from __future__ import annotations

import re
from typing import Optional, Sequence


# The optional suffix covers inline, full-reference, collapsed-reference, and
# shortcut-reference image syntax. Removing the leading image marker prevents
# Markdown renderers from fetching any referenced image URL.
MARKDOWN_IMAGE_PATTERN = re.compile(
    r"!\[([^\]\n]*)\](?:\([^\n]*?\)|\[[^\]\n]*\])?",
    flags=re.IGNORECASE,
)
MODEL_THINKING_PATTERN = re.compile(
    r"<think\b[^>]*>.*?(?:</think\s*>|$)",
    flags=re.IGNORECASE | re.DOTALL,
)
INLINE_PAGE_CITATION_PATTERN = re.compile(
    r"\[Page\s+(\d+)\]",
    flags=re.IGNORECASE,
)


def sanitize_answer_markdown(
    answer: str,
    valid_source_pages: Optional[Sequence[int]] = None,
) -> str:
    """Remove model thinking/images and citations outside retrieved evidence."""
    sanitized_answer = MODEL_THINKING_PATTERN.sub("", answer)
    sanitized_answer = MARKDOWN_IMAGE_PATTERN.sub(
        lambda match: f"[External image omitted: {match.group(1) or 'image'}]",
        sanitized_answer,
    )
    if valid_source_pages is None:
        return sanitized_answer

    valid_pages = set(valid_source_pages)
    return INLINE_PAGE_CITATION_PATTERN.sub(
        lambda match: (
            match.group(0)
            if int(match.group(1)) in valid_pages
            else ""
        ),
        sanitized_answer,
    )


__all__ = ["sanitize_answer_markdown"]
