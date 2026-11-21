import unittest
from unittest.mock import Mock, patch

import requests

import main


class ConfigurationTests(unittest.TestCase):
    def test_empty_input_is_rejected(self):
        with self.assertRaises(main.EmptyInputError):
            main.capture_text(input_function=lambda: "")

    def test_missing_auth_credential_is_rejected(self):
        env = {
            "OLLAMA_HOST": "https://llm-internal.softex:9001",
            "OLLAMA_MODEL": "qwen3.5",
            "OLLAMA_REQUIRE_AUTH": "true",
            "OLLAMA_API_KEY": "",
        }
        with self.assertRaises(main.AuthenticationError):
            main.load_configuration(env)

    def test_invalid_host_is_rejected(self):
        env = {"OLLAMA_HOST": "llm-internal.softex:9001"}
        with self.assertRaises(main.ConfigurationError):
            main.load_configuration(env)


class AuthenticationAndResponseTests(unittest.TestCase):
    def setUp(self):
        self.config = main.Config(
            host="https://llm-internal.softex:9001",
            model="qwen3.5",
            api_key="simulated-key",
            require_auth=True,
            timeout_seconds=300,
        )

    @patch("main.requests.post")
    def test_invalid_credential_receives_401(self, post):
        response = Mock(status_code=401)
        post.return_value = response

        with self.assertRaises(main.AuthenticationError) as context:
            main.call_llm(self.config, {"model": "qwen3.5"})

        self.assertIn("credencial", str(context.exception).lower())

    @patch("main.requests.post")
    def test_timeout_has_readable_error(self, post):
        post.side_effect = requests.Timeout()

        with self.assertRaises(main.CommunicationError) as context:
            main.call_llm(self.config, {"model": "qwen3.5"})

        self.assertIn("demorou", str(context.exception).lower())

    @patch("main.requests.post")
    def test_unavailable_service_is_recognized(self, post):
        response = Mock(status_code=503)
        post.return_value = response

        with self.assertRaises(main.LLMUnavailableError) as context:
            main.call_llm(self.config, {"model": "qwen3.5"})

        self.assertIn("indisponível", str(context.exception).lower())

    def test_empty_model_response_is_rejected(self):
        with self.assertRaises(main.ResponseFormatError):
            main.parse_response({"message": {"content": ""}})

    def test_unexpected_response_format_is_rejected(self):
        with self.assertRaises(main.ResponseFormatError):
            main.parse_response({"unexpected": True})

    def test_valid_response_is_extracted(self):
        payload = {"message": {"content": "# Resumo Executivo\nTeste"}}
        self.assertEqual(
            main.parse_response(payload),
            "# Resumo Executivo\nTeste",
        )


if __name__ == "__main__":
    unittest.main()
