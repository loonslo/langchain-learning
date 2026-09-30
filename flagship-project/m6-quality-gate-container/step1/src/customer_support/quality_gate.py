"""把评测报告变成 CI 退出条件；缺失指标也必须失败关闭。"""

THRESHOLDS = {"pass_rate": 0.9, "citation_rate": 1.0, "refusal_rate": 0.9}


def check(metrics):
    """返回不达标或缺失的指标说明，空列表表示通过；缺失的指标同样算失败（失败关闭）。"""
    return [
        f"缺少 {name}" if name not in metrics else f"{name} 低于阈值"
        for name, required in THRESHOLDS.items()
        if name not in metrics or metrics[name] < required
    ]
