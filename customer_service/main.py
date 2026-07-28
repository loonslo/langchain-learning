"""
customer_service/main.py · CLI 入口：chat 多轮对话 / eval 评估
==========================================================
python customer_service/main.py chat            # 交互式多轮对话
python customer_service/main.py eval            # 跑评估 + 出报告
==========================================================
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "chat"

    if cmd == "eval":
        import evaluation
        evaluation.run()
        return

    import config as C
    import graph
    sid = f"cli-{uuid.uuid4().hex[:8]}"
    print(f"智能客服（{'离线' if C.OFFLINE else '在线'}模式，会话 {sid}），输入 q 退出")
    while True:
        q = input("\n你: ").strip()
        if q.lower() in ("q", "quit", "exit"):
            break
        out = graph.chat(sid, q)
        tag = " [已转人工]" if out["escalated"] else ""
        print(f"客服[{out['intent']}]{tag}: {out['answer']}")


if __name__ == "__main__":
    main()
