"""
capstone/connector.py · 真实数据接入 + 增量同步（Day54）
==========================================================
企业知识库不是建一次就完事：文档天天增删改。全量重建又慢又贵。
增量同步 = 只处理变化的文件：新增的入库、改过的先删旧块再入新块、删掉的从库里清掉。

怎么判断"变了"：记每个文件的内容 hash 到状态文件，
本次扫描和上次比对——hash 变了就是改过，文件没了就是删了。

这里以"本地文件夹"作为数据源（最常见）。换 Notion / 数据库只需替换 _scan_source()，
增量比对和向量库增删的逻辑完全复用。
==========================================================
"""

import json
import hashlib
from pathlib import Path

import config as C
from knowledge_base import _load_one, KnowledgeBase
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

STATE_PATH = C.HERE / "data" / "sync_state.json"   # 记录每个文件上次的 hash


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _scan_source() -> dict[str, str]:
    """扫描数据源，返回 {文件名: 内容hash}。换数据源只改这个函数。"""
    return {p.name: _file_hash(p) for p in sorted(C.DOCS_DIR.glob("*"))
            if p.suffix.lower() in (".txt", ".md", ".pdf")}


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _diff(old: dict, new: dict):
    """对比新旧 hash，分出三类变化。"""
    added = [f for f in new if f not in old]
    deleted = [f for f in old if f not in new]
    updated = [f for f in new if f in old and new[f] != old[f]]
    return added, updated, deleted


def _chunks_of(filename: str):
    docs = _load_one(C.DOCS_DIR / filename)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=C.CHUNK_SIZE, chunk_overlap=C.CHUNK_OVERLAP, separators=C.ZH_SEPARATORS)
    return splitter.split_documents(docs)


def sync() -> dict:
    """执行一次增量同步，返回本次处理的变化统计。"""
    store = Chroma(persist_directory=C.CHROMA_DIR, embedding_function=C.get_embeddings())
    old, new = _load_state(), _scan_source()
    added, updated, deleted = _diff(old, new)

    # 删除 + 更新：先按 source 把旧块从向量库清掉（关键：不留孤儿块）
    for f in deleted + updated:
        store.delete(where={"source": f})   # Chroma 按 metadata 删

    # 新增 + 更新：把新内容切块写回
    for f in added + updated:
        chunks = _chunks_of(f)
        if chunks:
            store.add_documents(chunks)

    _save_state(new)
    stats = {"新增": len(added), "更新": len(updated), "删除": len(deleted)}
    print(f"增量同步完成：{stats}")
    return stats


if __name__ == "__main__":
    # 演示：先确保已 build 过一次（python capstone/main.py build）
    print("当前同步状态文件：", STATE_PATH)
    print("改一个 docs/ 里的文件再跑本脚本，检索结果会跟着变；删掉文件它就不再被检索到。")
    sync()
