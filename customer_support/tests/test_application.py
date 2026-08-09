"""验证应用层会把短追问补全为可独立检索的问题，并保存会话历史。"""

from src.application import SupportApplication
from src.assistant import SupportAnswer
from src.conversation import History


class RecordingAssistant:
    """记录应用层最终交给底层助手的文本，避免测试依赖模型。"""

    def __init__(self):
        self.questions: list[str] = []

    def ask(self, question: str) -> SupportAnswer:
        self.questions.append(question)
        return SupportAnswer(f"回答：{question}", ("customer_faq.md",))


def test_application_keeps_history_and_expands_short_follow_up():
    assistant = RecordingAssistant()
    application = SupportApplication(assistant, History(max_turns=2))

    application.ask("退款多久到账？", session_id="session-1")
    result = application.ask("那多久？", session_id="session-1")

    assert assistant.questions == [
        "退款多久到账？",
        "上一个问题：退款多久到账？\n当前追问：那多久？",
    ]
    assert result.sources == ("customer_faq.md",)
    assert [turn.question for turn in application.history.get("session-1")] == [
        "退款多久到账？",
        "那多久？",
    ]
