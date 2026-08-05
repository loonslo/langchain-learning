"""验证本地 Ollama 适配器发送的请求结构。"""

from langchain_core.messages import HumanMessage, SystemMessage

from customer_support.ollama_model import OllamaChatModel


class FakeResponse:
    is_error = False
    status_code = 200
    text = ""

    def json(self):
        return {"message": {"content": "本地回答"}}


def test_ollama_request_omits_empty_tools(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("customer_support.ollama_model.httpx.post", fake_post)
    model = OllamaChatModel("qwen3.5:9b", "http://localhost:11434")

    response = model.invoke(
        [SystemMessage(content="只按证据回答"), HumanMessage(content="退款多久到账？")]
    )

    assert response.content == "本地回答"
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert "tools" not in captured["json"]
    assert captured["json"]["think"] is False
    assert captured["json"]["messages"] == [
        {"role": "system", "content": "只按证据回答"},
        {"role": "user", "content": "退款多久到账？"},
    ]
