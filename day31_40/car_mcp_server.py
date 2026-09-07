"""兼容入口：MCP Server 的实现已经合并到 ``production_graph.py``。

旧的 MCP 配置可能仍然启动这个路径，因此保留转发文件。新的在线 Graph 会
直接启动 ``production_graph.py --mcp-server``，避免把计算工具维护两份。
"""

from __future__ import annotations

import sys
from pathlib import Path


# ``python -m day31_40.car_mcp_server`` 有包上下文；
# ``python day31_40/car_mcp_server.py`` 没有包上下文，需要补充项目根目录。
if __package__:
    from .production_graph import (
        _run_mcp_server,
        calculate_annual_energy_cost,
        calculate_budget_ratio,
        calculate_five_year_tco,
        calculate_monthly_payment,
        secure_ping,
    )
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from day31_40.production_graph import (  # noqa: E402
        _run_mcp_server,
        calculate_annual_energy_cost,
        calculate_budget_ratio,
        calculate_five_year_tco,
        calculate_monthly_payment,
        secure_ping,
    )


if __name__ == "__main__":
    _run_mcp_server()
