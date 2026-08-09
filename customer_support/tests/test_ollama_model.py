"""验证本地 Ollama 适配器发送的请求结构。"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.ollama_model import OllamaChatModel


class FakeResponse:
    """模仿 httpx 响应中适配器会用到的最小字段。"""

    is_error = False
    status_code = 200
    text = ""

    def json(self):
        return {"message": {"content": "本地回答"}}


def test_ollama_request_omits_empty_tools(monkeypatch):
    # monkeypatch 在测试期间替换网络函数，结束后 pytest 会自动还原它。
    captured = {}

    def fake_post(url, **kwargs):
        # 不发真实 HTTP 请求，只保存请求参数供后续断言。
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("src.ollama_model.httpx.post", fake_post)
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
