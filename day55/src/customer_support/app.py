"""客服主程序：所有用户问题都进入逐日累积的 SupportApplication。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from .assistant import SupportAnswer


class Application(Protocol):
    def ask(self, question: str, **kwargs) -> SupportAnswer: ...


EXIT_COMMANDS = {"exit", "quit", "q", "退出"}


def build_product_assistant() -> Application:
    from .bootstrap import build_application

    return build_application()


def print_answer(result: SupportAnswer, output: Callable[[str], None] = print) -> None:
    output(f"回答：{result.text}")
    output("来源：" + ("、".join(result.sources) if result.sources else "无"))


def run_interactive(
    assistant: Application | None = None,
    *,
    read: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    factory: Callable[[], Application] = build_product_assistant,
) -> None:
    output("客服知识助手已启动。输入问题开始咨询，输入 exit 或 退出结束。")
    while True:
        try:
            question = read("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            output("\n会话已结束。")
            return
        if question.lower() in EXIT_COMMANDS:
            output("会话已结束。")
            return
        if not question:
            output("问题不能为空，请重新输入。")
            continue
        if assistant is None:
            output("正在加载知识库和模型，请稍候……")
            assistant = factory()
        print_answer(assistant.ask(question), output)


def main() -> int:
    run_interactive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
