from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from paperforge.storage import get_project_root


DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TEMPERATURE = 0.2


class LlmConfigError(RuntimeError):
    pass


@dataclass(frozen=True, repr=False)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    def __repr__(self) -> str:
        return (
            "LlmConfig("
            f"base_url={self.base_url!r}, "
            "api_key='***', "
            f"model={self.model!r}, "
            f"timeout_seconds={self.timeout_seconds!r}"
            ")"
        )


class ChatClient(Protocol):
    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """Return the text content from an OpenAI-compatible chat completion."""


Transport = Callable[[urllib.request.Request, int], Any]


class OpenAICompatibleChatClient:
    def __init__(self, config: LlmConfig, transport: Transport | None = None) -> None:
        self.config = config
        self._transport = transport or urllib.request.urlopen

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature,
        }
        request = urllib.request.Request(
            _chat_completions_url(self.config.base_url),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with self._transport(request, self.config.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        return _message_content(data)


class QueryPlannerLlmClient:
    def __init__(self, chat_client: ChatClient, model: str) -> None:
        self.chat_client = chat_client
        self.model = model

    def plan_query(self, raw_input: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You plan academic paper search queries. Return JSON only with keys: "
                    "canonical_title, search_query, author_hint, year_hint, rationale, confidence. "
                    "Do not rewrite arXiv IDs, arXiv URLs, or PDF URLs."
                ),
            },
            {
                "role": "user",
                "content": f"Raw paper input: {raw_input}",
            },
        ]
        return self.chat_client.chat(messages, model=self.model, temperature=0.0)


def load_llm_config(task: str) -> LlmConfig:
    load_project_dotenv()
    base_url = _required_env("PAPERFORGE_LLM_BASE_URL")
    api_key = _required_env("PAPERFORGE_LLM_API_KEY")
    model_env = _model_env_name(task)
    model = _required_env(model_env)
    return LlmConfig(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=_timeout_seconds(),
    )


def load_project_dotenv() -> None:
    load_dotenv_file(get_project_root() / ".env")


def load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        key_value = _parse_dotenv_line(raw_line)
        if key_value is None:
            continue
        key, value = key_value
        os.environ.setdefault(key, value)


def query_planner_client_from_env() -> QueryPlannerLlmClient | None:
    try:
        config = load_llm_config("query")
    except LlmConfigError:
        return None
    return QueryPlannerLlmClient(OpenAICompatibleChatClient(config), config.model)


def reader_chat_client_from_env() -> tuple[ChatClient, str]:
    config = load_llm_config("reader")
    return OpenAICompatibleChatClient(config), config.model


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise LlmConfigError(f"Missing required LLM environment variable: {name}")
    return value


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None

    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].lstrip()

    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return key, value


def _model_env_name(task: str) -> str:
    if task == "query":
        return "PAPERFORGE_QUERY_MODEL"
    if task == "reader":
        return "PAPERFORGE_READER_MODEL"
    raise LlmConfigError(f"Unknown LLM task: {task}")


def _timeout_seconds() -> int:
    raw_value = os.getenv("PAPERFORGE_LLM_TIMEOUT_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return int(raw_value)
    except ValueError as error:
        raise LlmConfigError("PAPERFORGE_LLM_TIMEOUT_SECONDS must be an integer") from error


def _chat_completions_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def _message_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("LLM response did not include choices[0].message.content") from error
    if not isinstance(content, str):
        raise RuntimeError("LLM message content must be a string")
    return content
