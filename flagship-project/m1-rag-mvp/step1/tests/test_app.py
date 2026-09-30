from customer_support.app import run_interactive
from customer_support.assistant import SupportAnswer


class RecordingAssistant:
    def __init__(self):
        self.questions = []

    def ask(self, question):
        self.questions.append(question)
        return SupportAnswer(f"已收到：{question}", ("customer_faq.md",))


def test_main_program_accepts_multiple_user_questions():
    answers = iter(["我可以自己输入吗？", "订单发货后怎么办？", "退出"])
    output = []
    assistant = RecordingAssistant()

    run_interactive(assistant, read=lambda _prompt: next(answers), output=output.append)

    assert assistant.questions == ["我可以自己输入吗？", "订单发货后怎么办？"]
    assert any("已收到：我可以自己输入吗？" in line for line in output)
    assert output[-1] == "会话已结束。"


def test_main_program_can_start_and_exit_without_loading_model():
    output = []

    def should_not_build():
        raise AssertionError("退出前不应该加载模型")

    run_interactive(
        read=lambda _prompt: "退出",
        output=output.append,
        factory=should_not_build,
    )

    assert output[-1] == "会话已结束。"
