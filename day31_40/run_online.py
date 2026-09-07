"""旧在线入口的兼容转发层。

真实实现已经合并到 ``production_graph.py``。保留这个文件是为了让旧教程中的
``python -m day31_40.run_online ...`` 命令继续可用；新代码建议直接使用：
``python day31_40/production_graph.py run ...``。
"""

from __future__ import annotations

import sys

from .production_graph import main as production_main
from .production_graph import run_online

__all__ = ["run_online"]


def main() -> None:
    """把旧的“直接跟问题”命令转换为新的 ``run`` 子命令。"""

    if len(sys.argv) == 1 or sys.argv[1] != "run":
        sys.argv.insert(1, "run")
    production_main()


if __name__ == "__main__":
    main()
