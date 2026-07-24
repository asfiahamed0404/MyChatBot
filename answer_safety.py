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
FENCE_START_PATTERN = re.compile(
    r"^(?: {0,3}>[ \t]?)*"
    r"(?: {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+)?"
    r" {0,3}(?P<fence>`{3,}|~{3,})"
)
TRUST_GATED_LATEX_COMMAND_PATTERN = re.compile(
    r"\\(?:href|url|includegraphics|html(?:class|id|style|data))\b",
    flags=re.IGNORECASE,
)
# This guard only prevents the compatibility transform from activating these
# commands. Existing dollar-delimited math remains byte-for-byte unchanged.


def _image_omission(match: re.Match[str]) -> str:
    """Return inert text without preserving nested Markdown image markers."""
    label = re.sub(r"[!\[\]<>`]", "", match.group(1)).strip()
    return f"[External image omitted: {label or 'image'}]"


def _is_unescaped(text: str, index: int) -> bool:
    """Return whether the character at index has an even backslash prefix."""
    backslash_count = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslash_count += 1
        cursor -= 1
    return backslash_count % 2 == 0


def _find_unescaped(
    text: str,
    token: str,
    start: int,
    end: Optional[int] = None,
) -> int:
    search_end = len(text) if end is None else end
    cursor = start
    while cursor < search_end:
        match_index = text.find(token, cursor, search_end)
        if match_index < 0:
            return -1
        if _is_unescaped(text, match_index):
            return match_index
        cursor = match_index + 1
    return -1


def _find_inline_code_end(text: str, start: int, run_length: int) -> int:
    delimiter = "`" * run_length
    cursor = start
    while cursor < len(text):
        match_index = text.find(delimiter, cursor)
        if match_index < 0:
            return -1
        before_is_tick = match_index > 0 and text[match_index - 1] == "`"
        after_index = match_index + run_length
        after_is_tick = (
            after_index < len(text) and text[after_index] == "`"
        )
        if not before_is_tick and not after_is_tick:
            return after_index
        cursor = after_index
    return -1


def _find_link_destination_end(text: str, start: int) -> int:
    """Return the end of a balanced Markdown link destination."""
    depth = 1
    cursor = start
    while cursor < len(text) and text[cursor] not in "\r\n":
        if text[cursor] == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if text[cursor] == "(":
            depth += 1
        elif text[cursor] == ")":
            depth -= 1
            if depth == 0:
                return cursor + 1
        cursor += 1
    return -1


def _find_standalone_display_close(text: str, start: int) -> int:
    """Find the start of a standalone display-math closing delimiter."""
    cursor = start
    while cursor < len(text):
        line_end = text.find("\n", cursor)
        if line_end < 0:
            line_end = len(text)
        content_end = (
            line_end - 1
            if line_end > cursor and text[line_end - 1] == "\r"
            else line_end
        )
        line = text[cursor:content_end]
        stripped = line.strip(" \t")
        if stripped == r"\]":
            return cursor + line.index("\\")
        cursor = line_end + 1
    return -1


def _standalone_display_close(text: str, opening_index: int) -> int:
    """Return the paired standalone display closer, or -1."""
    line_start = text.rfind("\n", 0, opening_index) + 1
    if text[line_start:opening_index].strip(" \t"):
        return -1

    line_end = text.find("\n", opening_index)
    if line_end < 0:
        line_end = len(text)
    content_end = (
        line_end - 1
        if line_end > opening_index and text[line_end - 1] == "\r"
        else line_end
    )

    same_line_close = _find_unescaped(
        text,
        r"\]",
        opening_index + 2,
        content_end,
    )
    if (
        same_line_close >= 0
        and not text[same_line_close + 2:content_end].strip(" \t")
    ):
        return same_line_close

    if text[opening_index + 2:content_end].strip(" \t"):
        return -1
    if line_end == len(text):
        return -1

    return _find_standalone_display_close(text, line_end + 1)


def _safe_latex_body(body: str) -> bool:
    return bool(
        body.strip()
        and not TRUST_GATED_LATEX_COMMAND_PATTERN.search(body)
        and not INLINE_PAGE_CITATION_PATTERN.search(body)
        and _find_unescaped(body, "$", 0) < 0
        and all(
            _find_unescaped(body, delimiter, 0) < 0
            for delimiter in (r"\(", r"\)", r"\[", r"\]")
        )
        and "`" not in body
    )


def _copy_existing_dollar_math(text: str, start: int) -> int:
    """Return the end of paired existing dollar math, or -1."""
    if text.startswith("$$", start):
        closing_index = _find_unescaped(text, "$$", start + 2)
        return closing_index + 2 if closing_index >= 0 else -1

    if start + 1 >= len(text):
        return -1
    line_end = text.find("\n", start + 1)
    if line_end < 0:
        line_end = len(text)
    closing_index = _find_unescaped(text, "$", start + 1, line_end)
    return closing_index + 1 if closing_index > start + 1 else -1


def _normalize_non_fenced_latex(text: str) -> str:
    normalized: list[str] = []
    cursor = 0

    while cursor < len(text):
        if text[cursor] == "`" and _is_unescaped(text, cursor):
            run_end = cursor + 1
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            code_end = _find_inline_code_end(
                text,
                run_end,
                run_end - cursor,
            )
            if code_end < 0:
                normalized.append(text[cursor:])
                break
            normalized.append(text[cursor:code_end])
            cursor = code_end
            continue

        if text[cursor] == "$" and _is_unescaped(text, cursor):
            math_end = _copy_existing_dollar_math(text, cursor)
            if math_end >= 0:
                normalized.append(text[cursor:math_end])
                cursor = math_end
                continue

        if text.startswith("](", cursor):
            destination_end = _find_link_destination_end(text, cursor + 2)
            if destination_end >= 0:
                normalized.append(text[cursor:destination_end])
                cursor = destination_end
                continue

        if text.startswith(r"\(", cursor) and _is_unescaped(text, cursor):
            line_end = text.find("\n", cursor + 2)
            if line_end < 0:
                line_end = len(text)
            closing_index = _find_unescaped(
                text,
                r"\)",
                cursor + 2,
                line_end,
            )
            if closing_index >= 0:
                body = text[cursor + 2:closing_index]
                pair_end = closing_index + 2
                if _safe_latex_body(body):
                    normalized.extend(("$", body, "$"))
                else:
                    normalized.append(text[cursor:pair_end])
                cursor = pair_end
                continue

        if text.startswith(r"\[", cursor) and _is_unescaped(text, cursor):
            closing_index = _standalone_display_close(text, cursor)
            if closing_index >= 0:
                body = text[cursor + 2:closing_index]
                pair_end = closing_index + 2
                if _safe_latex_body(body):
                    if "\n" not in body and "\r" not in body:
                        line_start = text.rfind("\n", 0, cursor) + 1
                        indentation = text[line_start:cursor]
                        line_break = (
                            "\r\n"
                            if text.startswith("\r\n", pair_end)
                            else "\n"
                        )
                        normalized.extend(
                            (
                                "$$",
                                line_break,
                                body,
                                line_break,
                                indentation,
                                "$$",
                            )
                        )
                    else:
                        normalized.extend(("$$", body, "$$"))
                else:
                    normalized.append(text[cursor:pair_end])
                cursor = pair_end
                continue

        normalized.append(text[cursor])
        cursor += 1

    return "".join(normalized)


def _normalize_latex_delimiters(markdown: str) -> str:
    """Normalize safe legacy LaTeX delimiters outside Markdown code."""
    normalized: list[str] = []
    plain_lines: list[str] = []
    closing_fence_pattern: Optional[re.Pattern[str]] = None

    def flush_plain_lines() -> None:
        if plain_lines:
            normalized.append(
                _normalize_non_fenced_latex("".join(plain_lines))
            )
            plain_lines.clear()

    for line in markdown.splitlines(keepends=True):
        line_without_ending = line.rstrip("\r\n")
        if closing_fence_pattern:
            normalized.append(line)
            if closing_fence_pattern.fullmatch(line_without_ending):
                closing_fence_pattern = None
            continue

        if line.startswith(("    ", "\t")):
            flush_plain_lines()
            normalized.append(line)
            continue

        fence_match = FENCE_START_PATTERN.match(line_without_ending)
        if fence_match:
            flush_plain_lines()
            fence = fence_match.group("fence")
            closing_fence_pattern = re.compile(
                rf"^(?: {{0,3}}>[ \t]?)*"
                rf" {{0,3}}{re.escape(fence[0])}"
                rf"{{{len(fence)},}}[ \t]*$"
            )
            normalized.append(line)
        else:
            plain_lines.append(line)

    flush_plain_lines()
    return "".join(normalized)


def sanitize_answer_markdown(
    answer: str,
    valid_source_pages: Optional[Sequence[int]] = None,
) -> str:
    """Normalize safe math and remove unsafe or unsupported model output."""
    sanitized_answer = MODEL_THINKING_PATTERN.sub("", answer)
    sanitized_answer = MARKDOWN_IMAGE_PATTERN.sub(
        _image_omission,
        sanitized_answer,
    )
    # A nested or malformed image can leave a second marker outside the first
    # regex match. Removing its leading bang keeps it inert in Markdown.
    sanitized_answer = sanitized_answer.replace("![", "[")
    if valid_source_pages is not None:
        valid_pages = set(valid_source_pages)
        sanitized_answer = INLINE_PAGE_CITATION_PATTERN.sub(
            lambda match: (
                match.group(0)
                if int(match.group(1)) in valid_pages
                else ""
            ),
            sanitized_answer,
        )
    return _normalize_latex_delimiters(sanitized_answer)


__all__ = ["sanitize_answer_markdown"]
