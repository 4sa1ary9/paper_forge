import json

import pytest

from paperforge.llm_client import (
    LlmConfig,
    LlmConfigError,
    OpenAICompatibleChatClient,
    load_dotenv_file,
    load_llm_config,
)


def test_load_llm_config_uses_task_specific_models(monkeypatch):
    monkeypatch.setenv("PAPERFORGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("PAPERFORGE_LLM_API_KEY", "sk-test-secret")
    monkeypatch.setenv("PAPERFORGE_QUERY_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("PAPERFORGE_READER_MODEL", "deepseek-v4-pro")

    query_config = load_llm_config("query")
    reader_config = load_llm_config("reader")

    assert query_config.base_url == "https://api.deepseek.com"
    assert query_config.model == "deepseek-v4-flash"
    assert reader_config.model == "deepseek-v4-pro"


def test_llm_config_repr_does_not_expose_api_key():
    config = LlmConfig(base_url="https://api.deepseek.com", api_key="sk-test-secret", model="deepseek-v4-flash")

    rendered = repr(config)

    assert "sk-test-secret" not in rendered
    assert "api_key='***'" in rendered


def test_load_llm_config_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.setattr("paperforge.llm_client.get_project_root", lambda: tmp_path)
    monkeypatch.setenv("PAPERFORGE_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.delenv("PAPERFORGE_LLM_API_KEY", raising=False)
    monkeypatch.setenv("PAPERFORGE_QUERY_MODEL", "deepseek-v4-flash")

    with pytest.raises(LlmConfigError, match="PAPERFORGE_LLM_API_KEY"):
        load_llm_config("query")


def test_load_dotenv_file_reads_comments_quotes_and_unquoted_values(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "# local LLM settings",
                'PAPERFORGE_LLM_BASE_URL="https://api.deepseek.com"',
                "PAPERFORGE_LLM_API_KEY='sk-test-secret'",
                "PAPERFORGE_QUERY_MODEL=deepseek-v4-flash",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("PAPERFORGE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("PAPERFORGE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("PAPERFORGE_QUERY_MODEL", raising=False)

    load_dotenv_file(dotenv_path)

    assert load_llm_config("query") == LlmConfig(
        base_url="https://api.deepseek.com",
        api_key="sk-test-secret",
        model="deepseek-v4-flash",
    )


def test_process_environment_overrides_dotenv_file(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "PAPERFORGE_LLM_BASE_URL=https://api.deepseek.com",
                "PAPERFORGE_LLM_API_KEY=sk-from-dotenv",
                "PAPERFORGE_READER_MODEL=deepseek-v4-pro",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PAPERFORGE_LLM_API_KEY", "sk-from-env")
    monkeypatch.delenv("PAPERFORGE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("PAPERFORGE_READER_MODEL", raising=False)

    load_dotenv_file(dotenv_path)

    config = load_llm_config("reader")
    assert config.api_key == "sk-from-env"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-v4-pro"


def test_load_llm_config_loads_project_dotenv(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "PAPERFORGE_LLM_BASE_URL=https://api.deepseek.com",
                "PAPERFORGE_LLM_API_KEY=sk-from-project-dotenv",
                "PAPERFORGE_QUERY_MODEL=deepseek-v4-flash",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("paperforge.llm_client.get_project_root", lambda: tmp_path)
    monkeypatch.delenv("PAPERFORGE_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("PAPERFORGE_LLM_API_KEY", raising=False)
    monkeypatch.delenv("PAPERFORGE_QUERY_MODEL", raising=False)

    config = load_llm_config("query")

    assert config.api_key == "sk-from-project-dotenv"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-v4-flash"


def test_openai_compatible_client_posts_chat_completion_request():
    captured = {}

    def fake_transport(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "{\"canonical_title\":\"Attention Is All You Need\"}",
                        }
                    }
                ]
            }
        )

    config = LlmConfig(base_url="https://api.deepseek.com", api_key="sk-test-secret", model="deepseek-v4-flash")
    client = OpenAICompatibleChatClient(config, transport=fake_transport)

    content = client.chat([{"role": "user", "content": "Plan this query"}])

    assert content == "{\"canonical_title\":\"Attention Is All You Need\"}"
    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["timeout"] == 60
    assert captured["headers"]["Authorization"] == "Bearer sk-test-secret"
    assert captured["body"]["model"] == "deepseek-v4-flash"
    assert captured["body"]["messages"] == [{"role": "user", "content": "Plan this query"}]
    assert captured["body"]["temperature"] == 0.2


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")
