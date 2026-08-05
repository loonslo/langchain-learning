"""为本地 Ollama 提供最小的 LangChain 风格聊天模型适配器。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from langchain_core.messages import AIMessage


ROLE_BY_MESSAGE_TYPE = {
    "system": "system",
    "human": "user",
    "ai": "assistant",
}


@dataclass(frozen=True)
class OllamaChatModel:
    """调用本地 Ollama chat API，并保持 LangChain 风格的 invoke 接口。

    当前 Ollama Python 客户端会把没有工具的请求序列化为 ``tools: []``，
    qwen3.5 在本机 Ollama 版本下会因此返回 502。这里直接调用 HTTP API并省略
    本客服助手没有使用的 tools 字段。
    """

    model: str
    base_url: str
    temperature: float = 0
    timeout_seconds: float = 180

    def invoke(self, messages: list[Any]) -> AIMessage:
        ollama_messages: list[dict[str, str]] = []
        for message in messages:
            message_type = getattr(message, "type", "human")
            role = ROLE_BY_MESSAGE_TYPE.get(message_type, "user")
            ollama_messages.append(
                {
                    "role": role,
                    "content": str(getattr(message, "content", message)),
                }
            )

        response = httpx.post(
            f"{self.base_url.rstrip('/')}/api/chat",
            json={
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "think": False,
                "options": {"temperature": self.temperature},
            },
            timeout=self.timeout_seconds,
            trust_env=False,
        )

        if response.is_error:
            detail = response.text.strip()
            suffix = f"：{detail}" if detail else ""
            raise RuntimeError(f"Ollama 请求失败（HTTP {response.status_code}）{suffix}")

        data = response.json()
        content = data.get("message", {}).get("content", "")
        return AIMessage(content=str(content))
