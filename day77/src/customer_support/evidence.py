"""面试陈述只能引用仓库中真实存在的证据文件。"""

from pathlib import Path


def missing_evidence(root: Path, paths: list[str]) -> list[str]:
    return [p for p in paths if not (root / p).exists()]
