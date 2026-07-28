"""
Day 74 · Text2SQL 加固：参数化防注入 + 只读连接 + 执行超时
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（Agent 段·补缺口：Day38 加固）

Day38 给 Text2SQL 建了四道守卫（只 SELECT / 白名单表 / 拦危险词 / 强制 LIMIT），
挡住了"生成一条删库 SQL"。但生产还差三层纵深防御，正是这节补齐：

【一】参数化查询防注入 —— Day38 的 generate_sql 把 user_id / 公司名用 f-string
    拼进 SQL（WHERE user_id = '{user_id}'）。一旦这个值来自用户输入，注入就来了：
    值填 u1' OR '1'='1 就能读走所有人的数据，而且这条 SQL 仍是 SELECT、表也合法、
    带 LIMIT——Day38 的四道守卫【全都通过】。守卫防的是"语句结构"，防不住"值注入"。
    正解：值永远用 ? 占位、参数单独传，绝不拼进 SQL 字符串。

【二】只读连接 —— 纵深防御：即使前面所有校验都被绕过，数据库连接本身是只读的
    （mode=ro），任何写操作直接被数据库拒绝。安全不押注在单一防线上。

【三】执行超时 —— 一条笛卡尔积/递归 SQL 能把库拖垮（DoS）。给查询设执行上限，
    超时就中断，别让一个慢查询拖垮整个服务。

核心心法（测试背景的纵深防御直觉）：不信任任何单点防线。校验会被绕过、
LLM 会被越狱，所以再叠"参数化 + 只读 + 超时"，每一层独立生效。

衔接：Day38 是 Text2SQL 基础版 + 结构校验；今天补"值注入 / 权限 / 资源"三层。
==========================================================
"""

import sqlite3
import time

DB = "day74_demo.db"
ALLOWED_TABLES = {"conversations"}


def init_demo_data() -> None:
    """建一张演示表，塞两个用户的数据——用来演示"越权读别人的数据"。可重复运行。"""
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL
            )
        """)
        if conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO conversations (user_id, question) VALUES (?, ?)",
                [("u1", "u1 的私密问题A"), ("u1", "u1 的私密问题B"),
                 ("u2", "u2 的私密问题X"), ("u2", "u2 的私密问题Y")],
            )


# ============================================================
# 【一】参数化防注入：拼接 vs 占位，同一个恶意输入两种命运
# ============================================================
def query_unsafe(conn, user_id: str) -> list:
    """危险写法（Day38 的隐患）：把用户输入直接拼进 SQL 字符串。"""
    sql = f"SELECT user_id, question FROM conversations WHERE user_id = '{user_id}' LIMIT 10"
    return conn.execute(sql).fetchall()


def query_safe(conn, user_id: str) -> list:
    """安全写法：值用 ? 占位、参数单独传。注入串会被当成普通字符串去匹配。"""
    sql = "SELECT user_id, question FROM conversations WHERE user_id = ? LIMIT 10"
    return conn.execute(sql, (user_id,)).fetchall()


def demo_injection():
    with sqlite3.connect(DB) as conn:
        # 正常输入：两种写法都只返回 u1 自己的 2 条
        print("  正常 user_id='u1'：")
        print("    拼接 →", len(query_unsafe(conn, "u1")), "条")
        print("    参数化 →", len(query_safe(conn, "u1")), "条")

        # 恶意输入：想用 ' OR '1'='1 绕过 user_id 过滤，读走所有人的数据
        evil = "u1' OR '1'='1"
        print(f"\n  恶意 user_id={evil!r}：")
        unsafe_rows = query_unsafe(conn, evil)
        print(f"    拼接 → {len(unsafe_rows)} 条 ← 越权！u2 的数据也被读走了：",
              sorted({r[0] for r in unsafe_rows}))
        safe_rows = query_safe(conn, evil)
        print(f"    参数化 → {len(safe_rows)} 条 ← 注入串被当普通值匹配，读不到任何人")


# ============================================================
# 【二】只读连接：纵深防御，写操作被数据库直接拒绝
# ============================================================
def readonly_conn(db: str) -> sqlite3.Connection:
    """只读连接：mode=ro 要求文件已存在，且任何写操作都会被拒绝。"""
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def demo_readonly():
    conn = readonly_conn(DB)
    try:
        # 读：正常
        n = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        print(f"  只读连接查询 → OK，共 {n} 条")
        # 写：即便 SQL 侥幸通过了上层校验，只读连接这一层也挡死
        try:
            conn.execute("INSERT INTO conversations (user_id, question) VALUES ('x','hack')")
            print("  写入 → 居然成功了（不该发生）")
        except sqlite3.OperationalError as e:
            print(f"  尝试写入 → 被拒 ✓（{e}）")
    finally:
        conn.close()


# ============================================================
# 【三】执行超时：给查询设上限，慢查询中断，别拖垮服务
# ============================================================
def run_with_timeout(conn, sql: str, seconds: float):
    """用 sqlite3 的 progress_handler 实现执行超时：每跑一批 VM 指令回调一次，
    超时就返回非 0 让数据库中断本次查询（抛 OperationalError）。"""
    start = time.time()
    # 回调返回非 0 → 中断查询；100000 = 每 10 万条 VM 指令检查一次时间
    conn.set_progress_handler(lambda: 1 if time.time() - start > seconds else 0, 100000)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.set_progress_handler(None, 0)   # 用完撤掉，别影响后续查询


def demo_timeout():
    with sqlite3.connect(DB) as conn:
        # 快查询：秒回
        fast = run_with_timeout(conn, "SELECT COUNT(*) FROM conversations", seconds=1.0)
        print(f"  快查询 → OK，结果 {fast[0][0]}")

        # 慢查询：递归 CTE 造一个跑很久的查询，触发超时中断
        slow_sql = ("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL "
                    "SELECT x+1 FROM c WHERE x < 100000000) SELECT COUNT(*) FROM c")
        try:
            run_with_timeout(conn, slow_sql, seconds=0.5)
            print("  慢查询 → 居然跑完了（机器太快，可调小阈值）")
        except sqlite3.OperationalError as e:
            print(f"  慢查询 → 超时中断 ✓（{e}）")


if __name__ == "__main__":
    init_demo_data()
    print("===== 【一】参数化防注入：结构校验挡不住的值注入 =====")
    demo_injection()
    print("\n===== 【二】只读连接：写操作被数据库直接拒绝 =====")
    demo_readonly()
    print("\n===== 【三】执行超时：慢查询中断，别拖垮服务 =====")
    demo_timeout()


# ----------------------------------------------------------
# 小结：
# - Day38 的四道守卫防的是"语句结构"（SELECT-only/白名单/危险词/LIMIT），
#   但防不住"值注入"——恶意值拼进 WHERE 仍是合法 SELECT，全部守卫通过却越权读数据。
# - 参数化查询（? 占位 + 参数单独传）是防注入的根：值永远不拼进 SQL 字符串。
# - 只读连接（mode=ro）是纵深防御：校验被绕过，写操作仍被数据库拒绝。
# - 执行超时（progress_handler）防慢查询 DoS：一条查询拖不垮整个服务。
# - 心法：不信任单一防线。结构校验 + 参数化 + 只读 + 超时，四层独立生效。
#
# 面试话术：
#   "Text2SQL 我不只做 SQL 结构校验——那挡不住值注入。我一定参数化：值用占位符、
#    绝不拼进 SQL。再叠只读数据库连接和执行超时做纵深防御：就算校验被越狱绕过，
#    数据库层也写不了、拖不垮。安全我从不押在单一防线上。"
#
# 动手练习：把 Day38 的 generate_sql 改造成"SQL 模板 + 参数列表"两段式返回，
#          execute 用参数化执行；再给 execute_sql 换成 readonly_conn，跑通全链。
# ----------------------------------------------------------
