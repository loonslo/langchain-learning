"""历史遗留的 Ollama 适配器，仅供对照学习，当前产品入口不会加载它。

适配器的作用像插头转换器：项目其余部分只认识 ``invoke(messages)``，而本模块
把这种统一调用翻译成 Ollama HTTP API 所需的 JSON 请求。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from langchain_core.messages import AIMessage


# LangChain 的角色名称和 Ollama API 的角色名称并不完全一样，此表完成对应转换。
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
        """把 LangChain 消息转换为 Ollama 请求，并转回标准 ``AIMessage``。"""
        ollama_messages: list[dict[str, str]] = []
        for message in messages:
            # getattr 在属性不存在时返回默认值，兼容测试中的简单消息对象。
            message_type = getattr(message, "type", "human")
            role = ROLE_BY_MESSAGE_TYPE.get(message_type, "user")
            ollama_messages.append(
                {
                    "role": role,
                    "content": str(getattr(message, "content", message)),
                }
            )

        # HTTP POST 表示“向服务发送一份数据并请求处理”。``json=`` 会自动编码为 JSON。
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

        # HTTP 状态码为 4xx/5xx 时，Ollama 没有成功处理请求；转换成更易读的异常。
        if response.is_error:
            detail = response.text.strip()
            suffix = f"：{detail}" if detail else ""
            raise RuntimeError(f"Ollama 请求失败（HTTP {response.status_code}）{suffix}")

        # API 返回的 JSON 大致形如 {"message": {"content": "回答"}}。
        data = response.json()
        content = data.get("message", {}).get("content", "")
        return AIMessage(content=str(content))
