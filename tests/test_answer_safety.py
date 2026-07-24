import unittest

from answer_safety import sanitize_answer_markdown


class AnswerSafetyTests(unittest.TestCase):
    def test_all_common_markdown_image_forms_are_neutralized(self):
        answer = """Inline ![one](https://example.invalid/one.png)
Full reference ![two][image-two]
Collapsed reference ![three][]
Shortcut reference ![four]

[image-two]: https://example.invalid/two.png
[three]: https://example.invalid/three.png
[four]: https://example.invalid/four.png
"""

        sanitized = sanitize_answer_markdown(answer)

        self.assertNotIn("![", sanitized)
        for label in ("one", "two", "three", "four"):
            self.assertIn(f"[External image omitted: {label}]", sanitized)

    def test_thinking_and_unsupported_page_citations_are_removed(self):
        answer = (
            "<think>Private reasoning [Page 99]</think>"
            "Grounded answer [Page 1] [Page 99]"
        )

        sanitized = sanitize_answer_markdown(answer, [1, 6])

        self.assertEqual(sanitized, "Grounded answer [Page 1] ")
        self.assertNotIn("Private reasoning", sanitized)

    def test_unclosed_thinking_block_fails_closed(self):
        sanitized = sanitize_answer_markdown(
            "Visible answer.<think>Unclosed private reasoning",
            [1],
        )

        self.assertEqual(sanitized, "Visible answer.")


if __name__ == "__main__":
    unittest.main()
