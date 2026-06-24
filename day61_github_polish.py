"""
Day 61 · GitHub 打磨（主打作品成型）
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目收尾

陌生人照着 README 就能跑起来，才算作品。这天把仓库门面收拾干净。
非科班靠公开作品集补偿——README + 架构图 + 评测看板截图就是你的"作品证据"。
==========================================================
"""

README_CHECKLIST = [
    "一句话定位（带评测门禁、能回归、能上线的知识库 Agent，不是聊天框 demo）",
    "技术栈：LangChain + LangGraph + MCP + Chroma + FastAPI + pytest + GitHub Actions",
    "启动步骤：装依赖 → 配 .env → build → ask → eval → 起服务，陌生人能照着跑通",
    "架构图（capstone/README.md 已有 ASCII 版，可换成图）",
    "截图：问答带引用、评测看板 reports/dashboard.html、CI 红绿记录",
    "演示 GIF/视频：上传→问答→引用→评测 一条龙",
    ".env.example 列出所有需要的变量，且仓库里没有真实 key",
    "评测数字：拒答召回率/幻觉率，带计算方法（对应 reports/）",
]


if __name__ == "__main__":
    print("===== README / 仓库打磨清单 =====")
    for i, x in enumerate(README_CHECKLIST, 1):
        print(f"  [{i}] {x}")
    print("\n自检：git clone 到一个干净目录，照 README 从零跑一遍，卡住的地方就是要补的文档。")
    print("验收：陌生人照 README 能跑起来。【公开：主打作品成型】")
