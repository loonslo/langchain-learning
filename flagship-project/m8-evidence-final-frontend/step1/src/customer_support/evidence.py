"""面试陈述只能引用仓库中真实存在的证据文件。"""

from pathlib import Path


def missing_evidence(root: Path, paths: list[str]) -> list[str]:
    """返回不存在的证据路径，空列表表示全部存在；只检查文件是否存在，不代表内容已验收。"""
    return [p for p in paths if not (root / p).exists()]
