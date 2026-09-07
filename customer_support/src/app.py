"""客服助手的命令行入口，可在 PyCharm 中直接运行本文件。

把这个文件理解成餐厅的“前台”：它只负责接收用户输入、显示结果和处理退出，
不负责检索资料或让大模型生成答案。真正的问答规则在 ``assistant.py``。
"""

from __future__ import annotations

import argparse
from collections.abc import Callable

# ``SupportAnswer`` 是问答结果的数据格式；``build_application`` 会把真实的模型、
# 知识库和业务规则装配起来。命令行界面只使用这两个对外能力。
from src.application import SupportApplication
from src.assistant import SupportAnswer
from src.bootstrap import build_application

# ``set``（集合）适合放“不重复的一组值”，用它判断退出词既直观又很快。
EXIT_COMMANDS = {"exit", "quit", "q", "退出"}
# 命令行是单个连续会话，因此每次启动使用同一个稳定会话编号。
CLI_SESSION_ID = "terminal"


def build_product_application() -> SupportApplication:
    """创建带会话历史和 LangGraph 工作流的真实客服应用。

    这个函数被单独保留，是为了让 ``run_interactive`` 可以延迟创建助手：用户一启动
    就退出时，无需加载向量模型和知识库，也便于测试时替换成轻量的假对象。
    """
    return build_application()


def print_answer(result: SupportAnswer, output: Callable[[str], None] = print) -> None:
    """将结构化结果转换为终端里的两行文字。

    ``output`` 默认是 Python 内置的 ``print``。测试可传入 ``list.append`` 来保存输出，
    因而不用真的向屏幕打印；这叫“依赖注入”，即把可替换的外部动作从参数传进来。
    """

    sources = "、".join(result.sources) if result.sources else "无"
    output(f"回答：{result.text}")
    output(f"来源：{sources}")


def run_interactive(
    assistant: SupportApplication | None = None,
    *,
    read: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    factory: Callable[[], SupportApplication] = build_product_application,
) -> None:
    """持续接收问题，直到用户主动退出。

    参数都有默认值，所以正式运行时可直接调用；测试时可替换 ``read``、``output`` 和
    ``factory``，以模拟用户输入且不加载真实模型。
    """

    output("客服知识助手已启动。输入问题开始咨询，输入 exit 或 退出结束。")

    while True:
        try:
            # ``strip`` 删除输入两侧的空格和换行，避免“只输入空格”被当成问题。
            question = read("\n你：").strip()
        except (EOFError, KeyboardInterrupt, StopIteration):
            output("\n会话已结束。")
            return

        # ``lower`` 将英文转为小写，因此 EXIT、Exit 和 exit 都能退出。
        if question.lower() in EXIT_COMMANDS:
            output("会话已结束。")
            return
        if not question:
            output("问题不能为空，请重新输入。")
            continue

        # 延迟初始化：只有第一条有效问题出现时，才加载较慢的知识库和模型。
        if assistant is None:
            output("正在加载知识库和模型，请稍候……")
            assistant = factory()

        try:
            # 传入稳定 session_id，让本次命令行会话的短追问能读取之前的对话。
            print_answer(assistant.ask(question, session_id=CLI_SESSION_ID), output)
        except Exception as exc:  # 单次提问失败时允许用户继续咨询
            output(f"处理问题时出错（{type(exc).__name__}）：{exc}")


def main(argv: list[str] | None = None) -> int:
    """提供给命令行脚本的统一入口；返回 0 表示正常结束。"""

    parser = argparse.ArgumentParser(description="企业客服知识库助手")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="以 HTTP 服务方式启动（FastAPI），默认监听 127.0.0.1:8000",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP 服务监听地址")
    parser.add_argument("--port", type=int, default=19100, help="HTTP 服务监听端口（8000/8080 常被 Hyper-V 占用）")
    args = parser.parse_args(argv)

    if args.serve:
        from src.server import main as serve_main

        serve_main(host=args.host, port=args.port)
        return 0

    run_interactive()
    return 0


if __name__ == "__main__":
    # 只有直接运行本文件时该条件才成立；被其他模块导入时不会自动启动聊天。
    raise SystemExit(main())
