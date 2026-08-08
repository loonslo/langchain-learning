"""客服助手主程序：启动后直接连续接收用户问题。"""

from __future__ import annotations

import sys
from collections.abc import Callable
import io
from pathlib import Path
from typing import TYPE_CHECKING

# 修复 Windows 控制台（PowerShell/CMD）下的中文乱码：强制 stdout/stderr 使用 UTF-8。
# 默认代码页（如 GBK）会把程序输出的 UTF-8 字节错误解码成乱码。
if sys.stdout.encoding.lower() not in ("utf-8", "utf8", "utf_8"):
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    except (AttributeError, ValueError):
        pass
if sys.stderr.encoding.lower() not in ("utf-8", "utf8", "utf_8"):
    try:
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except (AttributeError, ValueError):
        pass
if hasattr(sys.stdin, "buffer") and sys.stdin.encoding.lower() not in (
    "utf-8",
    "utf8",
    "utf_8",
):
    try:
        sys.stdin = io.TextIOWrapper(
            sys.stdin.buffer, encoding="utf-8", errors="replace"
        )
    except (AttributeError, ValueError):
        pass


def _is_interactive() -> bool:
    """判断是否在可交互终端中运行（能接收键盘输入）。

    IDE 的 Run/Debug 输出面板通常不是 tty，无法用 input() 接收输入，
    这种情况下应明确提示用户改用真正的终端，而不是卡死。
    """
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


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
        try:
            print_answer(assistant.ask(question), output)
        except Exception as exc:  # noqa: BLE001 - 交互循环不应因单次提问失败而退出
            output(f"处理问题时出错（{type(exc).__name__}）：{exc}")
            output("本次回答失败，可重新输入问题，或输入 exit / 退出结束会话。")


def main() -> int:
    if _is_interactive():
        # 真正的终端：直接用 input() 进行无限交互循环。
        run_interactive()
        return 0

    # 非交互环境（如管道 / 重定向 / 某些 Runner）：
    # 逐行读取 stdin，支持 `echo "问题" | python app.py` 这类用法，
    # 遇到 EOF（管道关闭）即结束，不会卡死等待键盘输入。
    output = print
    output("客服知识助手已启动（非交互模式：从标准输入逐行读取问题，EOF 结束）。")
    assistant: CustomerSupportAssistant | None = None
    asked_anything = False
    try:
        for raw_line in sys.stdin:
            question = raw_line.strip()
            if not question:
                continue
            asked_anything = True
            if question.lower() in EXIT_COMMANDS:
                break
            if assistant is None:
                output("正在加载知识库和模型，请稍候……")
                assistant = build_product_assistant()
            try:
                print_answer(assistant.ask(question), output)
            except Exception as exc:  # noqa: BLE001
                output(f"处理问题时出错（{type(exc).__name__}）：{exc}")
    except (EOFError, KeyboardInterrupt):
        pass

    if not asked_anything:
        print(
            "未检测到可交互终端，也没有从标准输入读到任何问题。\n"
            "若需要键盘交互，请在系统终端（PowerShell / CMD）或 IDE 的 Terminal "
            "标签页中运行：\n"
            "    python src/customer_support/app.py\n"
            "或在 Code Runner 设置中开启 `code-runner.runInTerminal`。",
            file=sys.stderr,
        )
        return 1
    output("会话已结束。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
