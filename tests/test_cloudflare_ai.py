import io
import http.server
import json
import socket
import threading
import unittest
import urllib.error
from unittest import mock

import cloudflare_ai


ACCOUNT_ID = "0123456789abcdef0123456789abcdef"
API_TOKEN = "test-token-that-must-stay-secret"


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.read_limit = None
        self.closed = False

    def getcode(self):
        return self.status

    def read(self, limit=-1):
        self.read_limit = limit
        if limit is None or limit < 0:
            return self.payload
        return self.payload[:limit]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closed = True
        return False


class RecordingOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, request, **kwargs):
        self.calls.append((request, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


def encoded_response(payload):
    return json.dumps(payload).encode("utf-8")


class CloudflareAIClientTests(unittest.TestCase):
    def make_client(self, opener):
        return cloudflare_ai.CloudflareAIClient(
            ACCOUNT_ID,
            API_TOKEN,
            opener=opener,
        )

    def test_native_result_response_success(self):
        response = FakeResponse(
            encoded_response(
                {
                    "result": {"response": "  A grounded answer [Page 1].  "},
                    "success": True,
                    "errors": [],
                    "messages": [],
                }
            )
        )
        opener = RecordingOpener(response=response)

        answer = self.make_client(opener).answer(
            "What is the definition?",
            "[Page 1]\nThe definition is grounded.",
        )

        self.assertEqual(answer, "A grounded answer [Page 1].")
        self.assertTrue(response.closed)
        self.assertEqual(response.read_limit, cloudflare_ai.MAX_RESPONSE_BYTES + 1)
        self.assertEqual(len(opener.calls), 1)

    def test_nested_and_top_level_openai_shapes_return_only_final_content(self):
        payloads = (
            {
                "success": True,
                "result": {
                    "choices": [
                        {
                            "message": {
                                "content": "Nested final answer",
                                "reasoning_content": "private nested reasoning",
                            }
                        }
                    ]
                },
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "Top-level final answer",
                            "reasoning_content": "private top-level reasoning",
                        }
                    }
                ]
            },
        )
        expected_answers = ("Nested final answer", "Top-level final answer")

        for payload, expected_answer in zip(payloads, expected_answers):
            with self.subTest(expected_answer=expected_answer):
                opener = RecordingOpener(
                    response=FakeResponse(encoded_response(payload))
                )
                answer = self.make_client(opener).answer("Question", "Context")
                self.assertEqual(answer, expected_answer)
                self.assertNotIn("reasoning", answer)

    def test_request_uses_fixed_private_bounded_payload(self):
        opener = RecordingOpener(
            response=FakeResponse(
                encoded_response(
                    {"success": True, "result": {"response": "Answer"}}
                )
            )
        )
        client = self.make_client(opener)

        client.answer("QUESTION_SENTINEL", "CONTEXT_SENTINEL")

        request, request_kwargs = opener.calls[0]
        self.assertEqual(
            request.full_url,
            cloudflare_ai.CLOUDFLARE_ENDPOINT_TEMPLATE.format(
                account_id=ACCOUNT_ID
            ),
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            request_kwargs,
            {"timeout": cloudflare_ai.CLOUDFLARE_TIMEOUT_SECONDS},
        )
        self.assertEqual(
            request.get_header("Authorization"),
            f"Bearer {API_TOKEN}",
        )
        self.assertEqual(request.get_header("Content-type"), "application/json")
        payload_text = request.data.decode("utf-8")
        payload = json.loads(payload_text)
        self.assertEqual(
            set(payload),
            {"messages", "stream", "max_tokens", "temperature", "top_p"},
        )
        self.assertIs(payload["stream"], False)
        self.assertEqual(
            payload["max_tokens"],
            cloudflare_ai.CLOUDFLARE_MAX_OUTPUT_TOKENS,
        )
        self.assertEqual(payload["temperature"], 0.1)
        self.assertEqual(payload["top_p"], 0.9)
        self.assertEqual(payload["messages"][0]["role"], "system")
        system_prompt = payload["messages"][0]["content"].lower()
        self.assertIn("untrusted", system_prompt)
        self.assertIn("do not follow", system_prompt)
        self.assertEqual(payload["messages"][1]["role"], "user")
        self.assertIn("QUESTION_SENTINEL", payload["messages"][1]["content"])
        self.assertIn("CONTEXT_SENTINEL", payload["messages"][1]["content"])
        self.assertNotIn(API_TOKEN, payload_text)
        self.assertNotIn(API_TOKEN, request.full_url)
        self.assertNotIn(API_TOKEN, repr(client))
        self.assertIn("<redacted>", repr(client))

    def test_account_and_token_validation_happens_before_network(self):
        invalid_accounts = (
            "",
            "a" * 31,
            "a" * 33,
            "g" * 32,
            "../../" + "a" * 32,
            None,
        )
        for account_id in invalid_accounts:
            with self.subTest(account_id=account_id):
                opener = RecordingOpener()
                with self.assertRaises(
                    cloudflare_ai.CloudflareConfigurationError
                ):
                    cloudflare_ai.CloudflareAIClient(
                        account_id,
                        API_TOKEN,
                        opener=opener,
                    )
                self.assertEqual(opener.calls, [])

        for token in ("", "   ", "bad\r\ntoken", None):
            with self.subTest(token=token):
                opener = RecordingOpener()
                with self.assertRaises(
                    cloudflare_ai.CloudflareConfigurationError
                ) as raised:
                    cloudflare_ai.CloudflareAIClient(
                        ACCOUNT_ID,
                        token,
                        opener=opener,
                    )
                self.assertNotIn("bad", str(raised.exception))
                self.assertEqual(opener.calls, [])

    def test_input_bounds_and_blank_inputs_fail_before_network(self):
        invalid_inputs = (
            ("", "context", cloudflare_ai.CloudflareInputError),
            ("question", "   ", cloudflare_ai.CloudflareInputError),
            (
                "q" * (cloudflare_ai.MAX_QUESTION_CHARS + 1),
                "context",
                cloudflare_ai.CloudflareInputError,
            ),
            (
                "question",
                "c" * (cloudflare_ai.MAX_CONTEXT_CHARS + 1),
                cloudflare_ai.CloudflareInputError,
            ),
        )
        for question, context, expected_error in invalid_inputs:
            with self.subTest(question_length=len(question), context_length=len(context)):
                opener = RecordingOpener()
                with self.assertRaises(expected_error):
                    self.make_client(opener).answer(question, context)
                self.assertEqual(opener.calls, [])

    def test_http_statuses_map_to_safe_dedicated_errors_without_retry(self):
        mappings = (
            (302, cloudflare_ai.CloudflareUnexpectedStatusError),
            (400, cloudflare_ai.CloudflareBadRequestError),
            (401, cloudflare_ai.CloudflareAuthenticationError),
            (403, cloudflare_ai.CloudflarePermissionError),
            (408, cloudflare_ai.CloudflareTimeoutError),
            (413, cloudflare_ai.CloudflarePayloadTooLargeError),
            (429, cloudflare_ai.CloudflareRateLimitError),
            (500, cloudflare_ai.CloudflareServiceError),
            (503, cloudflare_ai.CloudflareServiceError),
            (418, cloudflare_ai.CloudflareUnexpectedStatusError),
        )
        sensitive_body = f"provider body contains {API_TOKEN}".encode("utf-8")
        for status, expected_error in mappings:
            with self.subTest(status=status):
                http_error = urllib.error.HTTPError(
                    "https://example.invalid",
                    status,
                    f"unsafe reason {API_TOKEN}",
                    {},
                    io.BytesIO(sensitive_body),
                )
                opener = RecordingOpener(error=http_error)
                with self.assertRaises(expected_error) as raised:
                    self.make_client(opener).answer("question", "context")
                safe_error = str(raised.exception)
                self.assertNotIn(API_TOKEN, safe_error)
                self.assertNotIn("provider body", safe_error)
                self.assertNotIn("unsafe reason", safe_error)
                self.assertEqual(len(opener.calls), 1)
                self.assertTrue(http_error.fp is None or http_error.fp.closed)

    def test_non_raising_http_status_is_also_mapped_without_reading_body(self):
        response = FakeResponse(
            f"unsafe {API_TOKEN}".encode("utf-8"),
            status=429,
        )
        opener = RecordingOpener(response=response)

        with self.assertRaises(cloudflare_ai.CloudflareRateLimitError):
            self.make_client(opener).answer("question", "context")

        self.assertIsNone(response.read_limit)
        self.assertTrue(response.closed)
        self.assertEqual(len(opener.calls), 1)

    def test_network_and_timeout_errors_are_safe(self):
        cases = (
            (
                TimeoutError(f"unsafe timeout {API_TOKEN}"),
                cloudflare_ai.CloudflareTimeoutError,
            ),
            (
                socket.timeout(f"unsafe timeout {API_TOKEN}"),
                cloudflare_ai.CloudflareTimeoutError,
            ),
            (
                urllib.error.URLError(
                    socket.timeout(f"unsafe wrapped timeout {API_TOKEN}")
                ),
                cloudflare_ai.CloudflareTimeoutError,
            ),
            (
                urllib.error.URLError(f"unsafe network {API_TOKEN}"),
                cloudflare_ai.CloudflareNetworkError,
            ),
            (
                OSError(f"unsafe operating-system error {API_TOKEN}"),
                cloudflare_ai.CloudflareNetworkError,
            ),
        )
        for source_error, expected_error in cases:
            with self.subTest(source_error=source_error.__class__.__name__):
                opener = RecordingOpener(error=source_error)
                with self.assertRaises(expected_error) as raised:
                    self.make_client(opener).answer("question", "context")
                self.assertNotIn(API_TOKEN, str(raised.exception))
                self.assertEqual(len(opener.calls), 1)

    def test_invalid_failed_and_empty_responses_are_safe(self):
        cases = (
            (
                b"not json",
                cloudflare_ai.CloudflareInvalidResponseError,
            ),
            (
                b"\xff",
                cloudflare_ai.CloudflareInvalidResponseError,
            ),
            (
                encoded_response({"success": False, "errors": [API_TOKEN]}),
                cloudflare_ai.CloudflareAPIResponseError,
            ),
            (
                encoded_response({"success": True, "result": {}}),
                cloudflare_ai.CloudflareInvalidResponseError,
            ),
            (
                encoded_response(
                    {"success": True, "result": {"response": "   "}}
                ),
                cloudflare_ai.CloudflareEmptyResponseError,
            ),
            (
                encoded_response(
                    {
                        "result": {
                            "choices": [
                                {
                                    "message": {
                                        "content": "",
                                        "reasoning_content": API_TOKEN,
                                    }
                                }
                            ]
                        }
                    }
                ),
                cloudflare_ai.CloudflareEmptyResponseError,
            ),
        )
        for response_body, expected_error in cases:
            with self.subTest(expected_error=expected_error.__name__):
                opener = RecordingOpener(
                    response=FakeResponse(response_body)
                )
                with self.assertRaises(expected_error) as raised:
                    self.make_client(opener).answer("question", "context")
                self.assertNotIn(API_TOKEN, str(raised.exception))

    def test_oversized_response_is_rejected_before_json_parsing(self):
        oversized_body = b"x" * (cloudflare_ai.MAX_RESPONSE_BYTES + 1)
        response = FakeResponse(oversized_body)
        opener = RecordingOpener(response=response)

        with self.assertRaises(
            cloudflare_ai.CloudflareResponseTooLargeError
        ):
            self.make_client(opener).answer("question", "context")

        self.assertEqual(response.read_limit, cloudflare_ai.MAX_RESPONSE_BYTES + 1)
        self.assertTrue(response.closed)

    def test_convenience_function_uses_the_same_client_contract(self):
        opener = RecordingOpener(
            response=FakeResponse(
                encoded_response(
                    {"success": True, "result": {"response": "Answer"}}
                )
            )
        )

        answer = cloudflare_ai.generate_cloudflare_answer(
            ACCOUNT_ID,
            API_TOKEN,
            "question",
            "context",
            opener=opener,
        )

        self.assertEqual(answer, "Answer")
        self.assertEqual(len(opener.calls), 1)

    def test_default_transport_refuses_redirect_without_forwarding_token(self):
        received_paths = []
        received_authorizations = []

        class RedirectHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                received_paths.append(self.path)
                received_authorizations.append(
                    self.headers.get("Authorization")
                )
                if self.path.startswith("/start/"):
                    self.send_response(302)
                    self.send_header(
                        "Location",
                        f"http://localhost:{self.server.server_port}/second-host",
                    )
                    self.end_headers()
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    encoded_response(
                        {"success": True, "result": {"response": "unsafe"}}
                    )
                )

            def log_message(self, format_string, *args):
                pass

        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0),
            RedirectHandler,
        )
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
        endpoint_template = (
            f"http://127.0.0.1:{server.server_port}/start/"
            "{account_id}"
        )
        try:
            with mock.patch.object(
                cloudflare_ai,
                "CLOUDFLARE_ENDPOINT_TEMPLATE",
                endpoint_template,
            ):
                with self.assertRaises(
                    cloudflare_ai.CloudflareUnexpectedStatusError
                ):
                    cloudflare_ai.CloudflareAIClient(
                        ACCOUNT_ID,
                        API_TOKEN,
                    ).answer("question", "context")
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        self.assertEqual(len(received_paths), 1)
        self.assertTrue(received_paths[0].startswith("/start/"))
        self.assertEqual(received_authorizations, [f"Bearer {API_TOKEN}"])

class MutableClock:
    def __init__(self):
        self.monotonic_value = 0.0
        self.utc_day_value = "2026-07-24"

    def monotonic(self):
        return self.monotonic_value

    def utc_day(self):
        return self.utc_day_value


class CloudflareUsageGuardTests(unittest.TestCase):
    def make_guard(self, clock, **overrides):
        settings = {
            "max_concurrent": 2,
            "max_requests_per_window": 2,
            "request_window_seconds": 10.0,
            "max_requests_per_utc_day": 3,
            "wait_seconds": 0.0,
            "monotonic_clock": clock.monotonic,
            "utc_day_clock": clock.utc_day,
        }
        settings.update(overrides)
        return cloudflare_ai.CloudflareUsageGuard(**settings)

    def test_attempts_include_failed_provider_work_and_window_expires(self):
        clock = MutableClock()
        guard = self.make_guard(clock)

        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            with guard.request_slot():
                raise RuntimeError("provider failed")
        with guard.request_slot():
            pass

        with self.assertRaises(cloudflare_ai.CloudflareLocalUsageLimitError):
            with guard.request_slot():
                pass

        clock.monotonic_value = 11.0
        with guard.request_slot():
            pass
        with self.assertRaises(cloudflare_ai.CloudflareLocalUsageLimitError):
            with guard.request_slot():
                pass

        clock.utc_day_value = "2026-07-25"
        clock.monotonic_value = 22.0
        with guard.request_slot():
            pass

    def test_concurrency_limit_is_released_after_context_exit(self):
        clock = MutableClock()
        guard = self.make_guard(
            clock,
            max_concurrent=1,
            max_requests_per_window=10,
            max_requests_per_utc_day=10,
        )
        entered = threading.Event()
        release = threading.Event()

        def hold_slot():
            with guard.request_slot():
                entered.set()
                release.wait(timeout=2)

        worker = threading.Thread(target=hold_slot)
        worker.start()
        self.assertTrue(entered.wait(timeout=1))
        with self.assertRaises(cloudflare_ai.CloudflareLocalBusyError):
            with guard.request_slot():
                pass
        release.set()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())

        with guard.request_slot():
            pass


if __name__ == "__main__":
    unittest.main()
