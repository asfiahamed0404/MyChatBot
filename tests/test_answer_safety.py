import unittest

from answer_safety import sanitize_answer_markdown


class AnswerSafetyTests(unittest.TestCase):
    def test_normalizes_inline_and_standalone_display_latex(self):
        answer = r"""A parametric curve is \(x=f(t),\ y=g(t)\) [Page 1].

\[
\frac{dx}{dt} \leq 2\pi
\]
"""
        expected = r"""A parametric curve is $x=f(t),\ y=g(t)$ [Page 1].

$$
\frac{dx}{dt} \leq 2\pi
$$
"""

        self.assertEqual(
            sanitize_answer_markdown(answer, [1, 6]),
            expected,
        )

    def test_preserves_existing_dollar_math_and_literal_backslashes(self):
        answer = (
            r"Keep $x \leq \pi$, $ \(spaced\) $, $$y \leq 2\pi$$, "
            r"\$5, \\(literal\\), and C:\temp."
        )

        self.assertEqual(sanitize_answer_markdown(answer), answer)

    def test_code_spans_and_fenced_code_are_unchanged(self):
        answer = r"""Outside \(x=f(t)\).

`inline \(y \leq \pi\)`

``code ` \(z\)``

```tex
\[
x \leq \pi
\]
```

~~~text
\(w\)
~~~
"""
        expected = answer.replace(
            r"Outside \(x=f(t)\).",
            r"Outside $x=f(t)$.",
            1,
        )

        self.assertEqual(sanitize_answer_markdown(answer), expected)

    def test_nested_fences_and_indented_code_are_not_normalized(self):
        answer = r"""> ~~~tex
> \(quoted\)
> ~~~

    \(indented\)
	\(tabbed\)
"""

        self.assertEqual(sanitize_answer_markdown(answer), answer)

    def test_markdown_link_destinations_are_not_normalized(self):
        answer = r"See [example](https://example.invalid/\(section\)). \(x=f(t)\)"

        self.assertEqual(
            sanitize_answer_markdown(answer),
            r"See [example](https://example.invalid/\(section\)). $x=f(t)$",
        )

    def test_unclosed_fence_protects_the_rest_of_the_answer(self):
        answer = "Before \\(x\\).\n```tex\n\\(y\\)\n"
        expected = "Before $x$.\n```tex\n\\(y\\)\n"

        self.assertEqual(sanitize_answer_markdown(answer), expected)

    def test_ambiguous_or_untrusted_legacy_math_stays_raw(self):
        answers = (
            r"Unmatched \(x",
            r"Empty \(\)",
            r"Nested \(outer \(inner\)",
            r"Embedded \[x \leq \pi\] stays raw.",
            "\\[\nouter\n\\[\ninner\n\\]\n",
            r"Unsafe \(\href{javascript:alert(1)}{click}\).",
            r"""Unsafe display:
\[
\includegraphics{https://example.invalid/plot.png}
\]""",
        )

        for answer in answers:
            with self.subTest(answer=answer):
                self.assertEqual(sanitize_answer_markdown(answer), answer)

    def test_raw_html_and_trust_gated_latex_are_not_promoted(self):
        answer = (
            r'<img src="x" onerror="alert(1)"> '
            r"\(\htmlClass{danger}{x}\) "
            r"\(\url{javascript:alert(1)}\)"
        )

        sanitized = sanitize_answer_markdown(answer)

        self.assertEqual(sanitized, answer)
        self.assertNotIn(r"$\htmlClass", sanitized)
        self.assertNotIn(r"$\url", sanitized)

    def test_crlf_and_indentation_survive_display_normalization(self):
        answer = "  \\[\r\n  x \\leq \\pi\r\n  \\]\r\n"
        expected = "  $$\r\n  x \\leq \\pi\r\n  $$\r\n"

        self.assertEqual(sanitize_answer_markdown(answer), expected)

    def test_whole_line_display_math_normalizes_without_code_ticks(self):
        answer = r"\[ x=f(t),\quad t \leq \pi \]"
        sanitized = sanitize_answer_markdown(answer)

        self.assertEqual(
            sanitized,
            "$$\n x=f(t),\\quad t \\leq \\pi \n$$",
        )
        self.assertNotIn("`", sanitized)

    def test_all_common_markdown_image_forms_are_neutralized(self):
        answer = """Inline ![one](https://example.invalid/one.png)
Full reference ![two][image-two]
Collapsed reference ![three][]
Shortcut reference ![four]
Nested ![![track]][outer]

[image-two]: https://example.invalid/two.png
[three]: https://example.invalid/three.png
[four]: https://example.invalid/four.png
[track]: https://example.invalid/track.png
[outer]: https://example.invalid/outer.png
"""

        sanitized = sanitize_answer_markdown(answer)

        self.assertNotIn("![", sanitized)
        self.assertNotIn("https://example.invalid/one.png", sanitized)
        for label in ("one", "two", "three", "four"):
            self.assertIn(f"[External image omitted: {label}]", sanitized)

    def test_thinking_and_unsupported_page_citations_are_removed(self):
        answer = (
            "<think>Private reasoning [Page 99]</think>"
            r"Grounded \(x=f(t)\) [Page 1] [Page 99]"
        )

        sanitized = sanitize_answer_markdown(answer, [1, 6])

        self.assertEqual(sanitized, "Grounded $x=f(t)$ [Page 1] ")
        self.assertNotIn("Private reasoning", sanitized)

    def test_removed_citation_cannot_create_unbalanced_math(self):
        sanitized = sanitize_answer_markdown(
            r"\([Page 99]\) tail",
            [1],
        )

        self.assertEqual(sanitized, r"\(\) tail")
        self.assertNotIn("[Page 99]", sanitized)
        self.assertNotIn("$", sanitized)

    def test_unclosed_thinking_block_fails_closed(self):
        sanitized = sanitize_answer_markdown(
            "Visible answer.<think>Unclosed private reasoning",
            [1],
        )

        self.assertEqual(sanitized, "Visible answer.")


if __name__ == "__main__":
    unittest.main()
