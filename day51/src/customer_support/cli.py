"""把 CustomerSupportAssistant 暴露成用户可以运行的命令行程序。

CLI 只处理参数和展示结果，不复制检索/回答规则。以后增加 FastAPI 时，HTTP 入口
也会调用同一个 assistant，而不是重新实现一遍业务逻辑。
"""

from __future__ import annotations

import argparse

from .bootstrap import build_assistant
from .knowledge import load_chunks
from .settings import Settings


def main(argv: list[str] | None = None) -> int:
    """解析命令行参数并执行数据检查或一次真实问答。"""

    parser = argparse.ArgumentParser(description="企业客服知识库助手 v0.1")
    parser.add_argument("--question", default="退款多久到账？", help="要咨询的客服问题")
    parser.add_argument(
        "--check-data",
        action="store_true",
        help="只检查资料加载和切块，不初始化 embedding 和聊天模型",
    )
    args = parser.parse_args(argv)

    # 配置只创建一次，再显式传给后续函数。
    settings = Settings.from_env()

    if args.check_data:
        # 这条路径不会创建模型，适合第一次检查目录和资料编码是否正确。
        chunks = load_chunks(settings.knowledge_path)
        print(f"知识库：{settings.knowledge_path}")
        print(f"切块数：{len(chunks)}")
        print(f"来源：{chunks[0].metadata['source']}")
        return 0
    # 正式路径会初始化 embedding、Chroma 和 LLM，然后调用唯一业务入口 ask()。
    assistant = build_assistant(settings)
    result = assistant.ask(args.question)
    print(f"回答：{result.text}")
    print("来源：" + ("、".join(result.sources) if result.sources else "无"))
    return 0


if __name__ == "__main__":
    # ``python -m customer_support.cli`` 执行这里；被其他模块 import 时不会自动运行。
    raise SystemExit(main())
