"""客服助手主程序：启动后直接连续接收用户问题。"""

from __future__ import annotations

from collections.abc import Callable
import sys
from pathlib import Path
from typing import TYPE_CHECKING


# 兼容 `python src/customer_support/app.py` 这种直接启动方式。
# 正常用 `python -m customer_support.app` 启动时，Python 已经知道包的位置，
# 这里不会改变现有行为；直接运行时则把项目的 src 目录加入搜索路径。
if __package__ in (None, ""):
    src_dir = str(Path(__file__).resolve().parents[1])
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

if TYPE_CHECKING:
    from .assistant import CustomerSupportAssistant, SupportAnswer

EXIT_COMMANDS = {"exit", "quit", "q", "退出"}


def build_product_assistant() -> CustomerSupportAssistant:
    """首次真实提问时再加载较重的 LangChain 与模型依赖。"""

    if __package__:
        from .bootstrap import build_assistant
    else:
        from customer_support.bootstrap import build_assistant

    return build_assistant()


def print_answer(result: SupportAnswer, output: Callable[[str], None] = print) -> None:
    output(f"回答：{result.text}")
    output("来源：" + ("、".join(result.sources) if result.sources else "无"))


def run_interactive(
    assistant: CustomerSupportAssistant | None = None,
    *,
    read: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    factory: Callable[[], CustomerSupportAssistant] = build_product_assistant,
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
