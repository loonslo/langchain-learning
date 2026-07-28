"""
test_day44.py · 数据层回归测试（护城河：测试背景的直接变现）
==========================================================
面试官问"你的测试经验怎么用在 AI 应用上"，这个文件就是答案之一：
数据层是整个应用最不能出错的一层，而且它【完全可测】—— 不依赖 LLM、
没有随机性、跑得飞快。写不写这套测试，是"会用 SQLite"和"敢把 SQLite
放进生产"的区别。

覆盖 6 类风险：
  1. SQL 注入      —— 参数化是否真的生效
  2. 迁移幂等      —— 重复启动服务不会把库跑坏
  3. 并发写        —— WAL + busy_timeout 是否真的扛住多线程
  4. 幂等落库      —— 重试不会写出重复记录
  5. 游标分页      —— 边写边翻页不漏不重
  6. 统计与导出    —— 成本聚合、评测集导出的正确性

运行：pytest test_day44.py -v
==========================================================
"""

import json
import sqlite3
import threading
import uuid

import pytest

import day44_sqlite_persistence as db


@pytest.fixture
def tmp_db(tmp_path):
    """每个用例一个独立库文件，互不污染。用完关连接。"""
    path = str(tmp_path / "test.db")
    db.migrate(path)
    yield path
    db.close_conn()


def _qa(tmp_db, user="u1", q="问题", a="答案", **kw):
    return db.save_qa(
        trace_id=kw.pop("trace_id", str(uuid.uuid4())),
        user_id=user, question=q, answer=a, db_path=tmp_db, **kw,
    )


# ============================================================
# 1. SQL 注入：安全红线
# ============================================================
def test_sql_injection_in_content(tmp_db):
    """把注入串当【内容】写进去：应该原样存下来，而不是被执行。"""
    payload = "'); DROP TABLE conversations; --"
    cid = _qa(tmp_db, q=payload, a=payload)

    rows = db.get_history("u1", db_path=tmp_db)
    assert rows[0]["question"] == payload      # 原样保存，没被当 SQL 解析
    assert rows[0]["id"] == cid
    # 表还在（没被 DROP）
    assert db.get_conn(tmp_db).execute(
        "SELECT count(*) FROM conversations").fetchone()[0] == 1


def test_sql_injection_in_user_id(tmp_db):
    """把注入串当【查询条件】传：应该查不到东西，而不是返回全表。"""
    _qa(tmp_db, user="u1")
    _qa(tmp_db, user="u2")
    assert db.get_history("u1' OR '1'='1", db_path=tmp_db) == []


# ============================================================
# 2. 迁移幂等：重复启动不炸
# ============================================================
def test_migrate_is_idempotent(tmp_db):
    for _ in range(5):
        assert db.migrate(tmp_db) == db.SCHEMA_VERSION
    tables = {
        r[0] for r in db.get_conn(tmp_db)
        .execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"conversations", "feedback"} <= tables


def test_migrate_from_legacy_v0_table(tmp_path):
    """真实事故回归：老库里有旧版 day44 的表，但 user_version=0。

    以前会炸 "no such column: session_id" —— 因为 CREATE TABLE IF NOT EXISTS
    看到表在就跳过了，接着建索引才发现结构对不上。
    正确行为：识别出老表，把数据搬进新结构，一条都不能丢。
    """
    path = str(tmp_path / "legacy.db")
    old = sqlite3.connect(path)
    old.execute("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL, question TEXT NOT NULL,
            answer TEXT NOT NULL, created_at TEXT NOT NULL)""")
    old.executemany(
        "INSERT INTO conversations (user_id,question,answer,created_at) VALUES (?,?,?,?)",
        [("u1", "RAG 是什么", "检索增强生成", "2026-07-20T10:00:00"),
         ("u1", "FAISS 干嘛的", "向量检索库", "2026-07-20T10:01:00")])
    old.commit()
    old.close()

    assert db.migrate(path) == db.SCHEMA_VERSION      # 不再抛异常

    rows = db.get_history("u1", db_path=path)
    assert [r["question"] for r in rows] == ["FAISS 干嘛的", "RAG 是什么"]   # 数据没丢
    assert rows[0]["trace_id"].startswith("legacy-")   # 补了唯一 trace_id
    assert rows[0]["session_id"] == "u1"               # 老数据没有会话概念，退化成按用户
    assert rows[0]["created_at"].endswith("+00:00")    # 补了时区后缀
    assert rows[0]["sources"] == []
    # 老表已清理，且新写入照常工作
    assert db.get_conn(path).execute(
        "SELECT count(*) FROM sqlite_master WHERE name='conversations_v0'").fetchone()[0] == 0
    db.save_qa(trace_id="new-1", user_id="u1", question="新问题", answer="a", db_path=path)
    assert len(db.get_history("u1", db_path=path)) == 3
    db.close_conn()


def test_migrate_legacy_is_idempotent(tmp_path):
    """迁移完再跑一遍不能重复搬数据 —— 服务重启会反复调 migrate()。"""
    path = str(tmp_path / "legacy2.db")
    old = sqlite3.connect(path)
    old.execute("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            question TEXT NOT NULL, answer TEXT NOT NULL, created_at TEXT NOT NULL)""")
    old.execute("INSERT INTO conversations (user_id,question,answer,created_at)"
                " VALUES ('u1','q','a','2026-07-20T10:00:00')")
    old.commit()
    old.close()

    for _ in range(3):
        db.migrate(path)
    assert len(db.get_history("u1", db_path=path)) == 1
    db.close_conn()


def test_migrate_from_empty_db(tmp_path):
    """全新空库能一路升到最新版本（模拟新环境首次部署）。"""
    path = str(tmp_path / "fresh.db")
    assert db.migrate(path) == db.SCHEMA_VERSION
    db.close_conn()


def test_indexes_exist(tmp_db):
    """索引缺失是"上线三个月后突然变慢"的头号原因，用测试钉死。"""
    idx = {
        r[0] for r in db.get_conn(tmp_db)
        .execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    assert {"idx_conv_user_id", "idx_conv_trace", "idx_fb_conv"} <= idx


def test_pragmas_applied(tmp_db):
    conn = db.get_conn(tmp_db)
    assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


# ============================================================
# 3. 并发写：WAL 是否真的扛得住
# ============================================================
def test_concurrent_writes(tmp_db):
    """10 线程 × 20 条并发写，必须一条不丢、不报 database is locked。

    这是原版 day44 最容易翻车的场景 —— 没开 WAL / 没 busy_timeout 时
    这个用例会随机失败，正是生产上偶发 500 的来源。
    """
    errors: list[Exception] = []

    def worker(k: int):
        try:
            for i in range(20):
                _qa(tmp_db, user=f"u{k}", q=f"q{i}")
        except Exception as e:      # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(k,)) for k in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"并发写出错：{errors[:3]}"
    total = db.get_conn(tmp_db).execute(
        "SELECT count(*) FROM conversations").fetchone()[0]
    assert total == 200


def test_transaction_rolls_back(tmp_db):
    """事务中途抛异常，本次写入必须整体回滚。"""
    with pytest.raises(RuntimeError):
        with db.tx(tmp_db) as conn:
            conn.execute(
                "INSERT INTO conversations (trace_id,user_id,session_id,question,answer,created_at)"
                " VALUES ('t','u','s','q','a','2026-01-01T00:00:00+00:00')")
            raise RuntimeError("boom")
    assert db.get_conn(tmp_db).execute(
        "SELECT count(*) FROM conversations").fetchone()[0] == 0


# ============================================================
# 4. 幂等落库：重试不产生脏数据
# ============================================================
def test_save_qa_is_idempotent(tmp_db):
    tid = str(uuid.uuid4())
    first = _qa(tmp_db, trace_id=tid)
    second = _qa(tmp_db, trace_id=tid, q="重试时内容不同也没关系")
    assert first == second
    assert db.get_conn(tmp_db).execute(
        "SELECT count(*) FROM conversations").fetchone()[0] == 1


def test_feedback_cascade_delete(tmp_db):
    """删对话必须连带删反馈，不能留孤儿行（foreign_keys=ON 才生效）。"""
    cid = _qa(tmp_db)
    db.save_feedback(cid, -1, "答非所问", db_path=tmp_db)
    with db.tx(tmp_db) as conn:
        conn.execute("DELETE FROM conversations WHERE id=?", (cid,))
    assert db.get_conn(tmp_db).execute(
        "SELECT count(*) FROM feedback").fetchone()[0] == 0


def test_feedback_rating_validated(tmp_db):
    cid = _qa(tmp_db)
    with pytest.raises(ValueError):
        db.save_feedback(cid, 5, db_path=tmp_db)


# ============================================================
# 5. 游标分页：边写边翻不漏不重
# ============================================================
def test_keyset_pagination_no_drift(tmp_db):
    for i in range(10):
        _qa(tmp_db, q=f"q{i}")

    page1 = db.get_history("u1", limit=5, db_path=tmp_db)
    _qa(tmp_db, q="翻页期间插入的新数据")     # 用 OFFSET 的话这里就会漂移
    page2 = db.get_history("u1", limit=5, before_id=page1[-1]["id"], db_path=tmp_db)

    ids = [r["id"] for r in page1 + page2]
    assert len(ids) == len(set(ids)) == 10           # 不重复
    assert [r["question"] for r in page2][-1] == "q0"  # 不漏最早那条


def test_sources_roundtrip(tmp_db):
    _qa(tmp_db, sources=["a.pdf#p1", "b.md#L20"])
    assert db.get_history("u1", db_path=tmp_db)[0]["sources"] == ["a.pdf#p1", "b.md#L20"]


def test_session_messages_chronological(tmp_db):
    for i in range(3):
        db.save_qa(trace_id=str(uuid.uuid4()), user_id="u1", session_id="s9",
                   question=f"q{i}", answer=f"a{i}", db_path=tmp_db)
    msgs = db.get_session_messages("s9", db_path=tmp_db)
    assert [m["question"] for m in msgs] == ["q0", "q1", "q2"]   # 正序，可直接拼 prompt


# ============================================================
# 6. 统计与评测集导出
# ============================================================
def test_daily_stats_aggregates(tmp_db):
    _qa(tmp_db, cost_usd=0.001, latency_ms=100)
    _qa(tmp_db, cost_usd=0.002, latency_ms=300)
    _qa(tmp_db, cost_usd=0.0, latency_ms=20000, status="error", error="超时")

    stats = db.daily_stats(days=1, db_path=tmp_db)
    assert stats and stats[0]["n"] == 3
    assert stats[0]["cost_usd"] == pytest.approx(0.003)
    assert stats[0]["error_rate_pct"] == pytest.approx(33.33, abs=0.1)


def test_export_eval_set_picks_failures(tmp_path, tmp_db):
    good = _qa(tmp_db, q="正常问题")
    bad_status = _qa(tmp_db, q="超时问题", status="error", error="上游超时")
    thumbs_down = _qa(tmp_db, q="被点踩的问题")
    db.save_feedback(thumbs_down, -1, "胡说八道", db_path=tmp_db)
    db.save_feedback(good, 1, db_path=tmp_db)

    out = str(tmp_path / "eval.json")
    db.export_eval_set(db_path=tmp_db, out_path=out)
    cases = json.loads(open(out, encoding="utf-8").read())

    qs = {c["question"] for c in cases}
    assert qs == {"超时问题", "被点踩的问题"}    # 只导失败和点踩，不导正常的
    assert all("reason" in c for c in cases)


def test_purge_old_keeps_recent(tmp_db):
    _qa(tmp_db, q="新数据")
    # 用和 save_qa 完全一致的 ISO 格式塞历史数据，才能真正验证时间比较
    with db.tx(tmp_db) as conn:
        for label, offset in [("老数据", "-100 days"), ("边界内数据", "-89 days")]:
            conn.execute(
                "INSERT INTO conversations (trace_id,user_id,session_id,question,answer,created_at)"
                " VALUES (?,?,?,?,?,strftime(?, 'now', ?))",
                (str(uuid.uuid4()), "u1", "s", label, "a", db._ISO_FMT, offset))

    assert db.purge_old(days=90, db_path=tmp_db) == 1        # 只删超过 90 天的那条
    remaining = {r["question"] for r in db.get_history("u1", db_path=tmp_db)}
    assert remaining == {"新数据", "边界内数据"}


# ============================================================
# 7. 连接管理：不泄漏
# ============================================================
def test_thread_local_connections_are_distinct(tmp_db):
    """不同线程必须拿到不同连接，否则 sqlite3 会抛跨线程使用错误。"""
    seen: list[int] = []

    def grab():
        seen.append(id(db.get_conn(tmp_db)))
        db.close_conn()

    main_conn = id(db.get_conn(tmp_db))
    t = threading.Thread(target=grab)
    t.start()
    t.join()
    assert seen and seen[0] != main_conn


def test_close_conn_actually_closes(tmp_db):
    conn = db.get_conn(tmp_db)
    db.close_conn()
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")      # 已关闭 —— 证明不是靠 GC 兜底
