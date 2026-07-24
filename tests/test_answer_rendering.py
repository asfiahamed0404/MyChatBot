import ast
import unittest
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "asfi_notebot.py"


class AnswerRenderingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(APP_PATH))

    def streamlit_calls(self, method_name):
        return [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == method_name
        ]

    def source_for(self, node):
        return ast.get_source_segment(self.source, node)

    def test_assistant_answer_markdown_calls_explicitly_disable_html(self):
        expected_answer_expressions = {
            'message["content"]',
            "response",
        }
        answer_calls = [
            call
            for call in self.streamlit_calls("markdown")
            if call.args
            and self.source_for(call.args[0]) in expected_answer_expressions
        ]

        self.assertEqual(len(answer_calls), 2)
        self.assertEqual(
            {self.source_for(call.args[0]) for call in answer_calls},
            expected_answer_expressions,
        )
        for call in answer_calls:
            html_keywords = [
                keyword
                for keyword in call.keywords
                if keyword.arg == "unsafe_allow_html"
            ]
            self.assertEqual(len(html_keywords), 1)
            self.assertIsInstance(html_keywords[0].value, ast.Constant)
            self.assertIs(html_keywords[0].value.value, False)

    def test_full_answers_are_not_rendered_as_text_or_code(self):
        answer_expressions = {
            'message["content"]',
            "response",
        }
        unsafe_answer_paths = []
        for method_name in ("text", "code"):
            for call in self.streamlit_calls(method_name):
                if (
                    call.args
                    and self.source_for(call.args[0]) in answer_expressions
                ):
                    unsafe_answer_paths.append(
                        (method_name, self.source_for(call.args[0]))
                    )

        self.assertEqual(unsafe_answer_paths, [])


if __name__ == "__main__":
    unittest.main()
