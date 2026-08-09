"""验证命令行交互流程，无需真的启动模型或读取知识库。"""

from src.app import CLI_SESSION_ID, run_interactive
from src.assistant import SupportAnswer


class RecordingAssistant:
    """测试替身：记录收到的问题，并返回可预测的固定结果。"""

    def __init__(self):
        self.questions = []
        self.session_ids = []

    def ask(self, question, *, session_id):
        self.questions.append(question)
        self.session_ids.append(session_id)
        return SupportAnswer(f"已收到：{question}", ("customer_faq.md",))


def test_main_program_accepts_multiple_user_questions():
    # iter 模拟用户依次输入的三行文字；每次调用 next 会取下一行。
    answers = iter(["我可以自己输入吗？", "订单发货后怎么办？", "退出"])
    output = []
    assistant = RecordingAssistant()

    # 不使用真实 input/print，而是把“输入”和“输出”替换为可观察的测试对象。
    run_interactive(assistant, read=lambda _prompt: next(answers), output=output.append)

    assert assistant.questions == ["我可以自己输入吗？", "订单发货后怎么办？"]
    assert assistant.session_ids == [CLI_SESSION_ID, CLI_SESSION_ID]
    assert any("已收到：我可以自己输入吗？" in line for line in output)
    assert output[-1] == "会话已结束。"


def test_main_program_can_start_and_exit_without_loading_model():
    output = []

    def should_not_build():
        # 若用户直接退出仍创建模型，测试会立刻失败，证明“延迟加载”被破坏。
        raise AssertionError("退出前不应该加载模型")

    run_interactive(
        read=lambda _prompt: "退出",
        output=output.append,
        factory=should_not_build,
    )

    assert output[-1] == "会话已结束。"
