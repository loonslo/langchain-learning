"""旧数据录入入口的兼容转发层。

数据表、写入函数和参数解析已经合并到 ``production_graph.py``。旧命令继续
可用，新代码可以直接使用 ``production_graph.py profile`` 或 ``car``。
"""

from __future__ import annotations

from .production_graph import main


if __name__ == "__main__":
    main()
