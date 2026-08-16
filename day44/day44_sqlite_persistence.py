"""
Day 44 · 数据持久化：LLM 应用的生产级 SQLite 数据层
==========================================================
测试工程师转 AI 应用开发  ← 阶段4 工程化

Day35/Day73 的 checkpoint 存的是"图状态"，用来恢复会话。
但业务上你还需要一张【可查询的对话日志表】：谁在什么时候问了什么、
用了哪个模型、花了多少钱、多久返回、失败没有、用户点没点踩。
这张表才是后面成本核算、失败分析、评测集回流的数据源。

为什么是 SQLite：一个文件就是一个库、零部署、标准库自带。
单机服务 / 内部工具 / 中小并发完全够用；真正扛不住了再迁 PostgreSQL。

⚠️ 准确的说法不是"SQLite 不能上生产"，而是【SQLite 不能多机部署】：
它支持多进程并发读、开 WAL 后读写也不互相阻塞，真正的限制是
"同一时刻只有一个写事务"且这个锁基于文件——一旦服务多副本部署
（k8s 起 3 个 pod 写同一个网络文件），文件锁在 NFS 上不可靠，会损坏数据。
所以【多副本部署】是迁 Postgres 最硬的触发条件，和数据量多少无关。

存储选型的完整取舍（为什么不用 Redis / ES / Mongo、什么时候该迁、
面试被追问怎么答）见 docs/ADR-001-对话日志存储选型.md。
一句话版：Redis 是热路径加速层不是真相源；我们的查询是数值聚合不是
全文检索，所以 ES 用不上强项却要背运维成本；分析层真要拆该上 ClickHouse。

⚠️ 但"能跑"和"能上生产"之间隔着 6 个坑，本文件逐个填掉：
  1. 连接泄漏     —— with sqlite3.connect(...) 只提交事务，【不关连接】
  2. database is locked —— 默认 journal 模式下写阻塞读，并发一来就炸
  3. 全表扫描     —— WHERE user_id ORDER BY id 没索引
  4. 表结构改不动 —— 没有版本号，加字段就得手工 ALTER，各环境不一致
  5. 数据没法用   —— 只存 Q/A，算不出成本、查不出失败、导不出评测集
  6. 分页会漂移   —— LIMIT/OFFSET 在持续写入的表上会漏数据 / 重复数据

运行：python day44_sqlite_persistence.py
测试：pytest test_day44.py -v
==========================================================
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# ---- 坑 0：DB 路径必须是绝对路径 ----------------------------------
# "app.db" 这种相对路径跟着【当前工作目录】走：从项目根跑和从 IDE 跑，
# 会连到两个不同的文件，表现就是"我的数据莫名其妙丢了"。
DEFAULT_DB = str(Path(__file__).parent / "app.db")
DB_PATH = os.getenv("APP_DB_PATH", DEFAULT_DB)

SCHEMA_VERSION = 2          # 每次改表结构 +1，见 migrate()
BUSY_TIMEOUT_MS = 5000      # 写锁被占时最多等 5 秒再报 locked


# ============================================================
# 【一】连接管理：坑 1（泄漏）+ 坑 2（locked）
# ============================================================
# 原来的写法 ——
#     with sqlite3.connect(DB) as conn:
#         conn.execute(...)
# 这里的 with 是 sqlite3 的【事务上下文】，退出时只做 commit/rollback，
# 【不会 close 连接】。短脚本靠 GC 兜底看不出问题；跑在 FastAPI 里
# 每请求泄一个连接，几万请求后就是 "too many open files"。
#
# 另外 sqlite3 连接默认不能跨线程用（check_same_thread=True）。
# FastAPI 的同步接口跑在线程池里，全局共享一个连接必炸。
# 正确做法：每个线程持有自己的连接（thread-local），用完显式关闭。

_local = threading.local()


def _configure(conn: sqlite3.Connection) -> None:
    """开库必设的 4 个 PRAGMA。少一个都算生产隐患。"""
    # WAL：读写分离，写事务不再阻塞读事务 —— 治 "database is locked" 的主药
    conn.execute("PRAGMA journal_mode=WAL")
    # 写锁被别人占着时，先等 5 秒再抛错，而不是立刻失败
    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
    # NORMAL：WAL 模式下的推荐值，比 FULL 快一个量级，断电最多丢最后几个事务
    conn.execute("PRAGMA synchronous=NORMAL")
    # SQLite 外键约束【默认是关的】，不显式打开写了 FOREIGN KEY 也不生效
    conn.execute("PRAGMA foreign_keys=ON")


def get_conn(db_path: str | None = None) -> sqlite3.Connection:
    """取当前线程的连接（没有就建），已配置好 PRAGMA 和 Row 工厂。"""
    path = db_path or DB_PATH
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != path:
        if conn is not None:
            conn.close()
        conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1000)
        conn.row_factory = sqlite3.Row       # 结果按列名访问，dict(row) 直接可用
        _configure(conn)
        _local.conn, _local.path = conn, path
    return conn


def close_conn() -> None:
    """显式关闭本线程连接。FastAPI 的 shutdown 事件 / 测试 teardown 里调。"""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        conn.close()
        _local.conn = None
        _local.path = None


@contextmanager
def tx(db_path: str | None = None):
    """事务上下文：正常提交，异常回滚。写操作一律走它。

    比裸 conn.execute 多的一层保证：一次业务里的多条写要么全成功要么全回滚。
    """
    conn = get_conn(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ============================================================
# 【二】表结构 + 迁移：坑 3（索引）+ 坑 4（版本）+ 坑 5（字段）
# ============================================================
# 表结构一定会变。生产里靠 PRAGMA user_version 记录当前版本，
# 启动时把缺的迁移补上 —— 幂等、可重复执行、各环境一致。
# 这是"能上线"和"手工改库"的分界线。

# ---- v1：对话日志主表 ----
# 字段不是拍脑袋加的，每个都对应一个后面要回答的问题：
#   trace_id            → 出问题了能跟日志/LangSmith 对上号（Day34 可观测性）
#   model / tokens/cost → 这个月花了多少钱、哪个用户最贵（Day43 成本）
#   latency_ms          → p95 是多少、慢在哪（Day62 监控）
#   status / error      → 失败率多少、失败长什么样（Day42 可靠性）
#   sources             → 答案引用了哪些文档，能不能追溯（Day12 引用）
#   session_id          → 区分"同一个人的不同会话"，多轮上下文靠它
_MIGRATIONS: dict[int, list[str]] = {
    1: [
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            trace_id    TEXT    NOT NULL,
            user_id     TEXT    NOT NULL,
            session_id  TEXT    NOT NULL,
            question    TEXT    NOT NULL,
            answer      TEXT    NOT NULL,
            model       TEXT,
            prompt_tokens     INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            cost_usd    REAL    DEFAULT 0.0,
            latency_ms  INTEGER DEFAULT 0,
            status      TEXT    NOT NULL DEFAULT 'ok',   -- ok / error / refused
            error       TEXT,
            sources     TEXT,                            -- JSON 数组字符串
            created_at  TEXT    NOT NULL                 -- UTC ISO8601
        )
        """,
        # 坑 3：查历史是 WHERE user_id=? ORDER BY id DESC，
        # 没这个复合索引就是全表扫 —— 一万条时感觉不到，一百万条时接口超时。
        "CREATE INDEX IF NOT EXISTS idx_conv_user_id  ON conversations(user_id, id DESC)",
        "CREATE INDEX IF NOT EXISTS idx_conv_session  ON conversations(session_id, id)",
        "CREATE INDEX IF NOT EXISTS idx_conv_created  ON conversations(created_at)",
        # trace_id 唯一：同一次请求重试落库不会写出两条（幂等的基础）
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_conv_trace ON conversations(trace_id)",
    ],
    # ---- v2：反馈表（数据飞轮的起点）----
    # 用户点的 👍/👎 是最廉价、最真实的标注。攒够了就能：
    #   ① 把 👎 的问题导成评测集（Day20）→ 回归测试（Day48）
    #   ② 算"点赞率"当线上质量指标（Day26 失败分析）
    # 这一步是评估护城河和真实业务的接口，别省。
    2: [
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            rating          INTEGER NOT NULL,     -- 1 = 赞, -1 = 踩
            comment         TEXT,
            created_at      TEXT    NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_fb_conv ON feedback(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_fb_rating ON feedback(rating)",
    ],
}


def _baseline_legacy(conn: sqlite3.Connection) -> bool:
    """把【旧版 day44 建的表】接管进版本化体系，保留数据。

    真实事故长这样：老库里已经有一张 conversations（只有 id/user_id/
    question/answer/created_at），但 user_version 还是 0。
    直接跑 v1 迁移时，CREATE TABLE IF NOT EXISTS 看到表在就【静默跳过】，
    紧接着建 session_id 的索引就炸：no such column: session_id。

    教训：IF NOT EXISTS 只保证"不重复建"，不保证"结构对得上"。
    任何迁移系统都必须处理"库已存在但没有版本号"这一步，业内叫 baseline。
    正确做法不是让用户删库，是把老数据搬进新结构。
    """
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='conversations'"
    ).fetchone():
        return False                      # 全新库，正常走 v1

    cols = {r[1] for r in conn.execute("PRAGMA table_info(conversations)")}
    if "session_id" in cols:
        return False                      # 已经是新结构，不用管

    conn.execute("ALTER TABLE conversations RENAME TO conversations_v0")
    conn.execute(_MIGRATIONS[1][0])       # 用 v1 的建表语句建新表

    # 搬数据。老表没有的字段给默认值：
    # - trace_id 有唯一索引，用 'legacy-'||id 保证不重复
    # - session_id 老数据没有会话概念，退化成按 user 一个会话
    # - created_at 老数据存的是【本地时间且不带时区】，这里按 UTC 处理。
    #   ⚠️ 这是个有损假设：时区信息在写入时就已经丢了，迁移救不回来。
    #   迁移里遇到"信息本来就没有"的情况，要把假设写在代码里，
    #   而不是假装它不存在——这是数据迁移最容易出事也最该留痕的地方。
    conn.execute("""
        INSERT INTO conversations
            (id, trace_id, user_id, session_id, question, answer,
             status, sources, created_at)
        SELECT id, 'legacy-' || id, user_id, user_id, question, answer,
               'ok', '[]',
               CASE WHEN created_at LIKE '%+%' OR created_at LIKE '%Z'
                    THEN created_at ELSE created_at || '+00:00' END
        FROM conversations_v0
    """)
    moved = conn.execute("SELECT count(*) FROM conversations").fetchone()[0]
    conn.execute("DROP TABLE conversations_v0")
    print(f"[migrate] 检测到旧版表，已迁移 {moved} 条历史数据到新结构")
    return True


def migrate(db_path: str | None = None) -> int:
    """把库升到 SCHEMA_VERSION。幂等：跑一百遍结果一样。"""
    conn = get_conn(db_path)
    current = conn.execute("PRAGMA user_version").fetchone()[0]

    if current == 0:
        # 只在"没有版本号"时做一次接管，之后一律走正常版本迁移
        try:
            _baseline_legacy(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    for version in range(current + 1, SCHEMA_VERSION + 1):
        for stmt in _MIGRATIONS.get(version, []):
            conn.execute(stmt)
        # user_version 不支持参数占位符，只能拼接 —— 但 version 来自内部 range，
        # 不是用户输入，所以安全。凡是拼 SQL 都要能像这样说清"值从哪来"。
        conn.execute(f"PRAGMA user_version={version}")
        conn.commit()
    return conn.execute("PRAGMA user_version").fetchone()[0]


init_db = migrate   # 兼容旧调用名


# ============================================================
# 【三】写入：参数化 + UTC + 幂等
# ============================================================
def _utc_now() -> str:
    """统一存 UTC ISO8601。

    原来用 datetime.now() 存的是【机器本地时间】且不带时区：
    开发机在东八区、服务器在 UTC，同一张表里的时间就没法比大小、没法算区间。
    展示时再按用户时区转，存储层永远用 UTC —— 这是硬规矩。
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# SQLite 的 datetime('now') 返回 "2026-07-26 15:47:59"（空格分隔、无时区），
# 而我们存的是 "2026-07-26T15:47:59+00:00"。两者做【字符串比较】时
# 'T'(0x54) 和 ' '(0x20) 不同，跨天边界会判错。
# 解法：用 strftime 把比较基准也拼成完全相同的格式。
# 这类"格式不一致导致的静默错误"最难查——统一格式是唯一解。
_ISO_FMT = "%Y-%m-%dT%H:%M:%S+00:00"


def save_qa(
    trace_id: str,
    user_id: str,
    question: str,
    answer: str,
    *,
    session_id: str | None = None,
    model: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
    latency_ms: int = 0,
    status: str = "ok",
    error: str | None = None,
    sources: list[str] | None = None,
    db_path: str | None = None,
) -> int:
    """落一条对话日志，返回主键 id（前端拿它来提交反馈）。

    参数化 (?, ?, ...) 而不是字符串拼接 —— 防 SQL 注入，安全红线。
    trace_id 唯一 + ON CONFLICT DO NOTHING：重试重复落库不会写出两条。
    """
    with tx(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO conversations
                (trace_id, user_id, session_id, question, answer, model,
                 prompt_tokens, completion_tokens, cost_usd, latency_ms,
                 status, error, sources, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(trace_id) DO NOTHING
            """,
            (
                trace_id, user_id, session_id or trace_id, question, answer, model,
                prompt_tokens, completion_tokens, cost_usd, latency_ms,
                status, error, json.dumps(sources or [], ensure_ascii=False), _utc_now(),
            ),
        )
        if cur.rowcount == 0:   # 命中幂等，取已存在那条的 id
            row = conn.execute(
                "SELECT id FROM conversations WHERE trace_id=?", (trace_id,)
            ).fetchone()
            return row["id"]
        return cur.lastrowid


def save_feedback(conversation_id: int, rating: int, comment: str | None = None,
                  db_path: str | None = None) -> int:
    """记一条用户反馈。rating: 1=赞, -1=踩。"""
    if rating not in (1, -1):
        raise ValueError("rating 只能是 1 或 -1")
    with tx(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO feedback (conversation_id, rating, comment, created_at) VALUES (?,?,?,?)",
            (conversation_id, rating, comment, _utc_now()),
        )
        return cur.lastrowid


# ============================================================
# 【四】查询：坑 6（分页漂移）+ 三个真实业务问题
# ============================================================
def get_history(user_id: str, limit: int = 20, before_id: int | None = None,
                db_path: str | None = None) -> list[dict]:
    """按用户查历史，游标分页（keyset pagination）。

    为什么不用 LIMIT/OFFSET：翻第 2 页时如果有新数据插进来，
    整个窗口会往后挪，用户会看到【重复】或【漏掉】的记录。
    用"上一页最后一条的 id"当游标就没这个问题，而且大表上更快
    （OFFSET 要先扫过前面 N 行，游标直接走索引定位）。
    """
    sql = "SELECT * FROM conversations WHERE user_id=?"
    params: list = [user_id]
    if before_id is not None:
        sql += " AND id < ?"
        params.append(before_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = get_conn(db_path).execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d["sources"] or "[]")
        out.append(d)
    return out


def get_session_messages(session_id: str, limit: int = 10,
                         db_path: str | None = None) -> list[dict]:
    """取一个会话最近 limit 轮（时间正序），拼进 prompt 当多轮上下文。"""
    rows = get_conn(db_path).execute(
        "SELECT question, answer, created_at FROM conversations "
        "WHERE session_id=? ORDER BY id DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def daily_stats(days: int = 7, db_path: str | None = None) -> list[dict]:
    """按天聚合：请求数、失败率、总成本、平均/p95 延迟。

    这就是把"日志表"变成"运营看板"的一句 SQL —— 不用另外接 BI。
    SQLite 没有内置 percentile，p95 用窗口函数手算（3.25+ 支持）。
    """
    rows = get_conn(db_path).execute(
        """
        WITH ranked AS (
            SELECT substr(created_at, 1, 10) AS day, status, cost_usd, latency_ms,
                   NTILE(20) OVER (PARTITION BY substr(created_at,1,10)
                                   ORDER BY latency_ms) AS bucket
            FROM conversations
            WHERE created_at >= strftime(?, 'now', ?)
        )
        SELECT day,
               COUNT(*)                                        AS n,
               ROUND(AVG(status <> 'ok') * 100, 2)             AS error_rate_pct,
               ROUND(SUM(cost_usd), 6)                         AS cost_usd,
               ROUND(AVG(latency_ms))                          AS avg_ms,
               MAX(CASE WHEN bucket <= 19 THEN latency_ms END) AS p95_ms
        FROM ranked GROUP BY day ORDER BY day DESC
        """,
        (_ISO_FMT, f"-{days} days"),
    ).fetchall()
    return [dict(r) for r in rows]


def export_eval_set(db_path: str | None = None, out_path: str = "eval_set_from_prod.json",
                    limit: int = 200) -> str:
    """把线上【踩过的 / 失败的】问题导成评测集 JSON。

    ★ 这是整个文件最值钱的函数，也是评估护城河的闭环：
      线上真实失败 → 评测集 → pytest 回归（Day48）→ CI 门禁（Day58）
    自己编的测试用例永远不如线上真实翻车的问题有价值。
    """
    rows = get_conn(db_path).execute(
        """
        SELECT c.id, c.question, c.answer, c.status, c.error,
               f.rating, f.comment
        FROM conversations c
        LEFT JOIN feedback f ON f.conversation_id = c.id
        WHERE c.status <> 'ok' OR f.rating = -1
        ORDER BY c.id DESC LIMIT ?
        """,
        (limit,),
    ).fetchall()
    cases = [
        {
            "id": f"prod-{r['id']}",
            "question": r["question"],
            "bad_answer": r["answer"],
            "reason": r["error"] or r["comment"] or ("用户点踩" if r["rating"] == -1 else "未知"),
            "expected_keywords": [],   # 人工补：期望答案里必须出现的词
        }
        for r in rows
    ]
    Path(out_path).write_text(
        json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_path


def purge_old(days: int = 90, db_path: str | None = None) -> int:
    """删除 N 天前的对话（含级联删反馈），返回删除条数。

    对话表只增不减，一年后几百万行、几个 G，备份和查询都会变慢。
    生产必须有保留策略；合规上也常要求"用户数据只留 N 天"。
    定时跑（cron / APScheduler）即可。
    """
    with tx(db_path) as conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE created_at < strftime(?, 'now', ?)",
            (_ISO_FMT, f"-{days} days"),
        )
        n = cur.rowcount
    get_conn(db_path).execute("VACUUM")   # 回收磁盘空间
    return n


# ============================================================
# 【五】演示
# ============================================================
if __name__ == "__main__":
    import uuid

    print(f"库文件：{DB_PATH}")
    print(f"schema 版本：v{migrate()}")

    t0 = time.time()
    cid = save_qa(
        trace_id=str(uuid.uuid4()), user_id="u1", session_id="s1",
        question="RAG 是什么", answer="检索增强生成：先检索再让模型基于检索结果作答。",
        model="deepseek-chat", prompt_tokens=120, completion_tokens=48,
        cost_usd=0.00012, latency_ms=int((time.time() - t0) * 1000) + 830,
        sources=["handbook.pdf#p3"],
    )
    save_qa(
        trace_id=str(uuid.uuid4()), user_id="u1", session_id="s1",
        question="FAISS 干嘛的", answer="向量检索库，用来做近似最近邻搜索。",
        model="deepseek-chat", prompt_tokens=90, completion_tokens=30,
        cost_usd=0.00008, latency_ms=610, sources=["handbook.pdf#p9"],
    )
    bad = save_qa(
        trace_id=str(uuid.uuid4()), user_id="u2", session_id="s2",
        question="公司年假几天", answer="", model="deepseek-chat",
        status="error", error="上游超时", latency_ms=20000,
    )
    save_feedback(bad, -1, "什么都没回答")

    print("\n— u1 的历史（游标分页）—")
    for r in get_history("u1"):
        print(f"  #{r['id']} [{r['created_at']}] {r['question']} "
              f"| {r['latency_ms']}ms | ${r['cost_usd']} | {r['sources']}")

    print("\n— 按天统计 —")
    for s in daily_stats():
        print(f"  {s['day']}  请求 {s['n']}  失败率 {s['error_rate_pct']}%  "
              f"成本 ${s['cost_usd']}  avg {s['avg_ms']}ms  p95 {s['p95_ms']}ms")

    print(f"\n— 导出评测集 → {export_eval_set()} —")
    close_conn()


# ----------------------------------------------------------
# 小结（面试能直接讲的版本）：
# 1. sqlite3 的 `with conn` 只管事务【不关连接】—— 跑在 Web 服务里会连接泄漏。
#    连接要按线程持有（thread-local）并显式 close。
# 2. 开库必设 4 个 PRAGMA：WAL（写不阻塞读，治 database is locked）、
#    busy_timeout（锁竞争时先等再报错）、synchronous=NORMAL、foreign_keys=ON。
# 3. 表结构靠 PRAGMA user_version 做版本化迁移，幂等可重复跑，各环境一致。
# 4. 查询条件对应的复合索引要建全；分页用游标（id < ?）而不是 OFFSET，避免漂移。
# 5. 时间统一存 UTC ISO8601，展示层再转时区。
# 6. 对话表要带 trace_id / model / tokens / cost / latency / status / sources ——
#    有这些字段才能回答"这个月花了多少钱""p95 多少""失败长什么样"。
#    trace_id 加唯一索引 + ON CONFLICT DO NOTHING = 重试幂等。
# 7. feedback 表是数据飞轮起点：线上点踩 → export_eval_set() → 回归测试 → CI 门禁。
# 8. 保留策略（purge_old）不能少，否则表无限膨胀。
#
# 迁 PostgreSQL 时要改的：占位符 ? → %s、AUTOINCREMENT → SERIAL/IDENTITY、
# PRAGMA 换成正式的 migration 工具（alembic）、连接换成连接池（psycopg_pool）。
# 因为所有 SQL 都收在本文件的函数里，换库只改这一层，业务代码不动。
#
# 动手练习：把 day41 的 /chat 接口接上来，每次问答落一条日志（带 latency 和 token），
# 再加 /feedback 和 /stats 两个接口 —— 这就是一个最小可用的 LLM 应用后台。
# ----------------------------------------------------------
