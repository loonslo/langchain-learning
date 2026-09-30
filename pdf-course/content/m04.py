"""第 4 章　让它自己干活：Agent 与 LangGraph"""
import dia
from comp import (P, E, C, SIDE, KEYPOINT, VERIFY, TRAP, CHECKLIST, UL, OL,
                  CODE, TABLE, HOOK, FIG, PAGEWRAP, CHAPTER, H3, H4,
                  RUN, TASK)


def chapter():
    p = []
    p.append(CHAPTER(4, "让它自己干活：Agent 与 LangGraph",
                     "前三章的系统，每一步顺序都是你写死的。这一章把它变成一张图："
                     "下一步走哪里由程序在运行时决定，出错能兜住，重启还能接着跑。",
                     "ch4"))

    p.append(P(
        "第 1 章的机器人只能「说一句话」，第 2 章的 RAG 只能「查一次资料再答」。",
        "真实任务不是这样的。用户说「帮我看下 A12345 这个订单，如果还没发货就催一下，"
        "顺便看看有没有相关投诉」——这里有三步，而且第二步要不要做取决于第一步的结果。"))
    p.append(FIG(dia.compare(
        ("if/else 写死的顺序", [
            "分支、重试、暂停都挤在一个函数里",
            "步骤一多，读代码看不出会走哪条",
        ]),
        ("画成一张图", [
            "每个方框是一个步骤，每条线是一次判断",
            "中间流动的那份数据叫状态",
        ]),
        note="LangGraph 做的事，就是把这团泥画成一张图。"
             "后面每一节的落点，都是这张图上的某个零件。"),
        "同样三步逻辑，写成函数和画成图，维护代价差一个量级"))

    p.append(SIDE("前置知识",
                  P("需要第 1 章的工具调用、第 3 章的评测（用来验证 Agent 行为）。"
                    "Pydantic 在第 1 章讲过，这里会用到；不熟就回看 1.3。")))

    # ── 4.1 ──
    p.append(H3("4.1　三个词：State、Node、Edge"))
    p.append(P("LangGraph 的核心概念只有三个，先把它们放回一张最小的图上看。"))
    p.append(FIG(dia.flow([
        ("START", "入口"),
        ("retrieve", "读 state，写 answer"),
        ("END", "出口"),
    ], note="节点之间由边连接。整张图跑起来，就是在节点之间传递同一份状态。"),
        "一张最小的图：状态从 START 流到 END"))
    p.append(FIG(dia.cards([
        ("State　状态", "在图里流动的一份数据。每个节点都能读它，也能声明要改它；"
                        "像流水线上传递的工单"),
        ("Node　节点", "一个函数：接收状态，返回对状态的修改。"
                       "像工位——拿到工单，做一件事，写一笔"),
        ("Edge　边", "节点之间的连接。有条件边时，就是「看情况走哪条」；"
                     "像传送带和分岔口"),
    ], cols=3),
        "三个概念分别对应现实里的三样东西"))
    p.append(CODE([
        "from typing import TypedDict",
        "from langgraph.graph import StateGraph, START, END",
        "",
        "class S(TypedDict):",
        "    question: str",
        "    answer: str",
        "",
        "def retrieve(state: S) -> dict:      # 节点：查资料",
        "    return {'answer': search(state['question'])}",
        "",
        "g = StateGraph(S)",
        "g.add_node('retrieve', retrieve)",
        "g.add_edge(START, 'retrieve')",
        "g.add_edge('retrieve', END)",
        "app = g.compile()",
        "app.invoke({'question': '退货几天到账'})",
    ]))
    p.append(KEYPOINT("节点是一个纯函数：给它状态，它返回要改的字段。"
                      "它不直接改状态，而是「声明我想改成什么」——"
                      "这一点是理解后面 reducer 的关键。"))

    # ── 4.2 ──
    p.append(H3("4.2　分支与循环：让它自己决定走哪条"))
    p.append(P(
        "这一节加的是条件边和循环。条件边决定下一步去哪，回边让流程能转回来——"
        "两者合起来，就是 Agent 的雏形。"))
    p.append(FIG(dia.loop([
        ("agent 节点", "判断还要不要再查一次"),
        ("tools 节点", "执行工具，把结果写回状态"),
    ], center="tools 走完回到 agent",
        note="should_continue 返回 'tools' 就走下面这条边，返回 'end' 就出图。"),
        "条件边加回边：agent 和 tools 之间转起来"))
    p.append(CODE([
        "def should_continue(state: S) -> str:",
        "    return 'tools' if state.get('need_tool') else 'end'",
        "",
        "g.add_conditional_edges('agent', should_continue,",
        "                        {'tools': 'tools', 'end': END})",
        "g.add_edge('tools', 'agent')      # 工具执行完回到 agent，形成循环",
    ]))
    p.append(P("循环也带来死循环的可能，所以图需要 " + C("recursion_limit") + "，"
               "限制最多走多少步。一个会自己决定下一步的程序，"
               "去掉步数上限之后，一旦判断卡住，就会一直调用工具，直到把账单烧穿。"))
    p.append(TRAP(P("不给循环设上限。线上真实发生过："
                    "Agent 判断「还需要再查一次」，而每次查完它的判断都没变，"
                    "于是它整晚在调用付费 API。"
                    + E("硬上限是循环唯一的刹车。"))))

    # ── 4.3 ──
    p.append(H3("4.3　State reducer：多个节点同时改状态会怎样"))
    p.append(P(
        "默认情况下，节点返回什么字段，就覆盖状态里的那个字段。"
        "顺序执行时这没问题，但有两种情形会出事。",
        "一种是一串节点都想往同一个列表里追加内容——"
        "每一步的结果被下一步覆盖，最后只剩最后那一步的。"
        "另一种是图分叉（fan-out）：一个节点同时触发几条并行分支，"
        "它们在同一个 step 里写同一个字段。"
        "后者在 LangGraph 里会直接抛 " + C("InvalidUpdateError") + "——"
        "图跑不起来，反而第一时间就被发现。"))
    p.append(FIG(dia.compare(
        ("顺序执行：默认覆盖", [
            "A 节点写「加了 1 条」，B 节点接着写",
            "后写的把先写的冲掉，最后只剩 1 条",
            "不报错——静默丢数据，最难查",
        ]),
        ("并行分支：直接报错", [
            "同一个 step 里两条分支写同一字段",
            "没配 reducer，框架抛 InvalidUpdateError",
            "图根本跑不起来，不是悄悄少一份",
        ]),
        note="两种情形要分开看：顺序执行下是「覆盖」，并行写入下是「报错」。"
             "报错反而好办——第一次运行就告诉你缺了 reducer。"
             "难查的是顺序覆盖，以及手写 state['x'] + [...] 在真并发下的丢更新。"),
        "同一个字段被两处改：顺序执行会覆盖，并行分支会报错"))
    p.append(CODE([
        "from typing import Annotated",
        "import operator",
        "",
        "class S(TypedDict):",
        "    logs: Annotated[list, operator.add]   # 声明：这个字段用「追加」合并",
        "    answer: str                            # 没声明：默认覆盖",
    ]))
    p.append(P("具体的对照是这样的：两条并行分支都往 " + C("logs") + " 里写东西，"
               "一条写「已查订单 A12345：未发货」，另一条写「已查退货政策：7 天」——"
               "因为声明了追加合并，两条都留在状态里，后面的节点能同时看到这两件事。"
               "把 " + C("operator.add") + " 去掉，同样的图第一次运行就会抛 "
               + C("InvalidUpdateError") + "，提示这个字段在一个 step 里收到了多个值。"))
    p.append(VERIFY(P("让两条分支各往同一个列表里加一项，跑两次："
                      "先去掉 reducer——应当直接报 " + C("InvalidUpdateError") + "；"
                      "再加上 " + C("operator.add") + "——两条都应该在。"
                      "两次输出合起来，才说明 reducer 确实在起作用。")))

    # ── 4.4 ──
    p.append(H3("4.4　ReAct：Agent 最基本的工作循环"))
    p.append(P(
        "ReAct 是「Reasoning + Acting」的缩写，中文常译成「边想边做」。"
        "它的循环只有三步，跑通它，Agent 的骨架就立起来了。"))
    p.append(FIG(dia.loop([
        ("想 Reason", "决定直接回答还是调用工具"),
        ("做 Act", "执行工具，把结果放回对话"),
        ("看 Observe", "带着新结果回到第一步"),
    ], center="每转一圈，历史里就多一条结果",
        note="所谓「智能体」，核心就是把这个循环跑起来，再给每一步加上边界："
             "最多几步、能用哪些工具、出错怎么办。"),
        "ReAct 的三步：想、做、看，然后重新判断"))
    p.append(SIDE("白话：为什么它看起来「聪明」",
                  P("它不聪明，它只是每一步都基于「到目前为止的所有信息」重新判断一次。"
                    "第 1 章说「模型没有记忆」，Agent 的「记忆」就是每次把整个循环的历史重新发过去。"),
                  P("理解了这一点，就能预判它的失败：历史太长会超上下文、"
                    "中间某一步的错误结论会被带进后面所有判断。")))

    # ── 4.5 ──
    p.append(H3("4.5　节点容错：工具报错不该让整张图崩掉"))
    p.append(P(
        "前面所有例子都假设工具一定成功。真实情况是：网络会超时、接口会限流、"
        "参数会传错。这一节专门处理这件事，做法是先给错误分类——"
        "不同错误该有不同的应对。"))
    p.append(FIG(dia.cards([
        ("瞬时错误", "网络抖动、429 限流 → 可以重试，但要退避（等一会儿再试）"),
        ("永久错误", "参数格式错、资源不存在 → 重试没用，直接走失败出口"),
        ("超时", "依赖服务不响应 → 设一个 deadline，到点放弃并降级"),
    ], cols=3),
        "三类错误各配一种应对，混在一起处理怎么做都不对"))
    p.append(P("分类的意义在于：" + E("对永久错误重试是纯粹的浪费，还会拖慢整个请求；"
                                      "对瞬时错误不重试则白白失败。")))
    p.append(TRAP(P("无脑加 retry 装饰器。"
                    "如果错误是「参数不合法」，重试 5 次就是把这 5 次都白跑一遍，"
                    "用户还多等了 5 倍时间。先分类，再决定重试策略。")))

    # ── 4.6 ──
    p.append(H3("4.6　结构化路由：让分支判断可靠"))
    p.append(P(
        "分支该走哪条，谁说了算？最省事的写法是让模型输出一段文字，"
        "然后代码里判断 " + C("'退款' in text") + "。"
        "这种写法很脆弱：模型多说一个词，就路由错了。"))
    p.append(FIG(dia.compare(
        ("关键词匹配", [
            "模型输出一整段自然语言",
            "代码里做 '退款' in text",
        ]),
        ("结构化输出", [
            "只允许 next 取三个固定取值",
            "判断变成等号比较，不靠猜",
        ]),
        note="这和第 1 章的结构化输出是同一件事，只是那次约束的是「提取字段」，"
             "这次约束的是「做选择」。"),
        "路由的可靠性来自取值固定，而不是关键词命中"))
    p.append(CODE([
        "class Route(BaseModel):",
        "    next: Literal['refund', 'order', 'other'] = Field(description='下一步该走哪条')",
        "",
        "route = llm.with_structured_output(Route).invoke(question)",
        "if route.next == 'refund': ...",
    ]))
    p.append(KEYPOINT("凡是「让模型做一个程序要用的决定」，都用结构化输出约束，"
                      "不要解析自然语言。这条规矩从第 1 章一直用到第 10 章的协议集成。"))

    # ── 4.7 ──
    p.append(H3("4.7　Plan-and-Execute：先出计划，再逐步执行"))
    p.append(P(
        "ReAct 是一步一步试；Plan-and-Execute 是先让模型把整个计划列出来，再按计划执行。"))
    p.append(FIG(dia.compare(
        ("ReAct：边走边看", [
            "每一步基于当前结果重新决定",
            "灵活，但容易绕圈子",
        ]),
        ("Plan-and-Execute：先列再做", [
            "先产出一份步骤清单",
            "可检查，但计划可能一开始就错",
        ]),
        note="这里把几种主流范式放在一起对比，属于「知道即可」——"
             "面试会问，不必每种都实现一遍。"),
        "两种范式的差别，在于计划是边走边定还是先定好"))
    p.append(SIDE("几种范式一句话",
                  P(E("ReAct") + "：边想边做，最通用。"
                    + E("Plan-and-Execute") + "：先列计划再做，适合步骤明确的复杂任务。"
                    + E("Reflexion") + "：做完反思一遍再改，适合有明确对错的任务。"),
                  P("不需要背定义。知道它们各自解决什么场景的问题，需要时再查。")))

    # ── 4.8 ──
    p.append(H3("4.8　可观测性：Agent 卡住了怎么查"))
    p.append(P(
        "第 3 章讲过 Trace。到了 Agent，它变得更关键——"
        "因为 Agent 的执行路径是运行时决定的，读代码看不出它这次走了哪条路。"))
    p.append(FIG(dia.compare(
        ("只有最终答案", [
            "能看到的只有「这次答得不对」",
            "不知道它在第几步开始偏",
        ]),
        ("每一步都留痕", [
            "每步的输入输出记成结构化日志",
            "定位到具体那一步再动手",
        ]),
        note="这一节做了两件事：把每一步的输入输出记成结构化日志（而不是 print），"
             "以及把 LangGraph 的流式输出用好，实时看到它走到哪一步。"),
        "能看见每一步，是调试 Agent 的入口"))
    p.append(TRAP(P("用 print 打日志。"
                    "print 出来的东西没法筛选、没法按一次请求聚合、"
                    "线上根本关不掉。结构化日志（JSON 格式，一行一条）"
                    "才是能用的——第 5 章会把它接进统一日志。")))

    # ── 4.9 ──
    p.append(H3("4.9　Checkpoint：暂停、重启、接着跑"))
    p.append(P(
        "这一节引入 checkpoint：把图的状态存下来，用一个 thread_id 标记。"
        "同一份被存下来的状态，同时撑起三件事。"))
    p.append(FIG(dia.cards([
        ("多轮对话", "同一个 thread_id 再次调用，接着上次的状态继续"),
        ("故障恢复", "程序崩了重启，状态还在，不用从头再来"),
        ("人工审批", "流程暂停在中间，等人确认后从断点继续"),
    ], cols=3,
        note="它存的不只是对话历史，还包括走到哪一步、中间结果是什么——"
             "所以才能支持「暂停后从断点恢复」。"),
        "一份被存下来的状态，同时撑起三件事"))
    p.append(P("一个具体的中断场景：Agent 走到「确认退款 1200 元」这一步停住等人批准，"
               "审批的人隔了一天才点同意。"
               "这一次启动后，靠 " + C("thread_id") + " 取回的快照里不只有用户说过的话，"
               "还包括「停在 risky_action 这一步、订单号是 A12345、待确认金额是 1200」。"
               "少了后面这几项，程序只能从头再问一遍。"))
    p.append(P("上下文管理也在这一段：状态越攒越多会超出上下文上限，"
               "所以需要「什么时候把旧历史压缩成摘要」的策略。"))
    p.append(TRAP(P("只用内存版的 checkpoint。程序一重启，状态全丢。"
                    "开发阶段用内存版没问题，但只要涉及「重启后要恢复」，"
                    "就得换成落盘版本（第 6 章会用 SQLite）。")))

    # ── 4.10 ──
    p.append(H3("4.10　流式输出与人工审批：AI 起草，人拍板"))
    p.append(P(
        "这一节是这一章离生产最近的一节，讲的是两件配套的事。",
        E("流式输出") + "让用户看到 Agent 正在做什么，而不是干等；"
        + E("人工审批（HITL，human-in-the-loop）") + "让高风险动作停下来等人确认。"))
    p.append(FIG(dia.flow([
        ("Agent 起草", "想退款 1200 元"),
        ("interrupt 暂停", "交决定权"),
        ("人确认", "approve 或拒绝"),
        ("程序执行", "approve 才真执行"),
    ], note="一个能调用工具的 Agent，理论上可以触发「退款」「删数据」这类不可逆操作。"
            "执行权停在人手上，模型只负责起草。"),
        "高风险动作的执行权停在人手上"))
    p.append(CODE([
        "from langgraph.types import interrupt, Command",
        "",
        "def risky_action(state):",
        "    decision = interrupt({'ask': '确认退款 1200 元？', 'order': state['order_id']})",
        "    if decision != 'approve':",
        "        return {'status': 'cancelled'}",
        "    refund_api.execute(state['order_id'], state['amount'])   # 真正扣钱的一行",
        "    return {'status': 'executed'}",
        "",
        "# 恢复时把人的决定传进去",
        "app.invoke(Command(resume='approve'), config={'configurable': {'thread_id': 't1'}})",
    ]))
    p.append(P("这里省掉了 " + C("refund_api") + " 的实现，重点在" + E("扣钱那一行写在")
               + C("interrupt") + E("返回之后") + "："
                 "审批没过就不会被调用。也就是说「暂停等人」是真的停在执行之前，"
                 "不是先执行完再补一次确认。"))
    p.append(KEYPOINT("「AI 起草、人确认」不是妥协，是上线红线。"
                      "会改变现实世界状态（花钱、删数据、发消息）的动作，"
                      "有人工确认或等价的授权机制兜着，"
                      "出错的代价才落在可以回滚的范围内。"))

    # ── 4.11 ──
    p.append(H3("4.11　工具安全：能用工具 ≠ 可以随便用"))
    p.append(P("这一节把「工具」这件事从「能调用」升级到「受控调用」。"))
    p.append(FIG(dia.cards([
        ("白名单", "只允许调用注册过的工具，模型编出来的工具名一律拒绝"),
        ("参数校验", "参数要符合预期格式，不让模型往数据库里塞任意字符串"),
        ("调用预算", "限制最多调用几次、最多花多少 token"),
        ("结果审查", "工具返回的内容也要检查，外部内容可能藏指令"),
    ], cols=2),
        "四道约束各挡一类风险"))
    p.append(SIDE("为什么「结果审查」也必要",
                  P("这叫间接注入：攻击者把指令藏在网页或文档里，"
                    "Agent 搜到这段内容后，会把它当成用户的要求去执行。"
                    "所以工具返回的内容，和用户输入一样，都是不可信输入。"),
                  P("第 6 章会专门讲这个攻击怎么防。")))

    # ── 4.12 ──
    p.append(H3("4.12　Text2SQL：让模型查数据库，但不让它乱查"))
    p.append(P(
        "这一段让模型把自然语言翻译成 SQL 去查数据库。这件事的风险很直接："
        "一条 " + C("DROP TABLE") + " 就能把数据删了。"
        "所以这里的重点不是「怎么生成 SQL」，而是「怎么拦住危险的 SQL」。"))
    p.append(FIG(dia.flow([
        ("自然语言", "用户的问题"),
        ("生成 SQL", "这一步不可信"),
        ("四道守卫", "只放行 SELECT"),
        ("执行", "过了守卫才连库"),
    ], direction="v",
        note="四道守卫是：只允许 SELECT 开头、关键字黑名单、表名白名单、"
             "没写 LIMIT 就补上。它们拦的是明显的错误和误操作；"
             "真正的边界在数据库账号上——那个账号只给只读权限，守卫被绕过了也写不进去。"),
        "把「生成」和「放行」分成两步，模型只负责前一步"))
    p.append(CODE([
        "def validate_and_fix(sql: str) -> str:",
        "    sql = sql.strip()",
        "    assert sql.lower().startswith('select'), '只允许查询'",
        "    banned = ['drop', 'delete', 'update', 'insert', 'alter', 'grant']",
        "    assert not any(w in sql.lower() for w in banned), '含危险关键字'",
        "    assert all(t in ALLOWED_TABLES for t in extract_tables(sql)), '表名必须在白名单'",
        "    if 'limit' not in sql.lower():",
        "        sql = sql.rstrip(';') + ' LIMIT 100'   # 补上限，并且要返回出去",
        "    return sql                                 # 调用方用返回值，不是原字符串",
    ]))
    p.append(P("两个细节值得停一下。",
               E("补好的 SQL 要返回出去") + "——写成 " + C("sql += ' LIMIT 100'")
               + " 却不返回，调用方手里还是原来那句，上限根本没生效，"
                 "而代码读起来像是加上了。",
               E("关键字黑名单只是最后一道补丁，不是安全边界") + "："
                 "大小写、注释、字符串拼接都能绕过朴素的匹配。"
                 "真正管用的是执行查询的那个数据库账号" + E("只有只读权限")
               + "——黑名单被绕过了，它也写不进任何东西。"))
    p.append(KEYPOINT("即使 SQL 是更强的模型生成的，这道校验也留着。"
                      "模型能力越强，越容易被绕过去，护栏的价值反而更高。"))
    p.append(SIDE("前置：SQL 是什么",
                  P("SQL 是操作数据库的查询语言。" + C("SELECT ... FROM ... WHERE ...")
                    + " 表示「从某张表里挑出符合条件的行」。"),
                  P("本书不要求你会写复杂 SQL，"
                    "但要知道" + E("读操作（SELECT）和写操作（INSERT/UPDATE/DELETE）是两回事") + "——"
                    "前面那个可以放开，后面那个要严格限制。")))

    # ── 4.13 ──
    p.append(H3("4.13　多 Agent：一个主管，几个专家"))
    p.append(P(
        "这一节讲 Supervisor 模式：一个「主管」节点负责决定把任务派给哪个「专职 Agent」，"
        "再把它们的结果汇总。"))
    p.append(FIG(dia.seq(["主管", "订单 Agent", "政策 Agent"], [
        (0, 1, "派单：查 A12345"),
        (1, 0, "订单状态：未发货", True),
        (0, 2, "派单：查退货政策"),
        (2, 0, "政策条款：7 天", True),
    ], note="每个专职 Agent 只带自己的工具和自己的提示词，"
            "上下文更短、职责更清楚，也更容易单独测试。"),
        "主管只做分派和汇总，专家各管一段"))
    p.append(TRAP(P("为了显得高级而拆多 Agent。"
                    "每多一个 Agent，就多一层调用、多一份延迟、"
                    "多一处可能出错的地方。"
                    "一个问题用一个 Agent 加几个工具就能解决时，"
                    "拆开换来的是成倍的延迟和故障点。")))

    # ── 4.14 ──
    p.append(H3("4.14　MCP：把工具变成标准接口"))
    p.append(P(
        "到这里，工具都是写在你项目里的函数。"
        "公司里如果有十几个系统，每个都自己接一遍工具，重复得离谱。",
        "MCP（Model Context Protocol）是一个标准协议："
        "把工具做成一个独立的服务，任何支持 MCP 的客户端都能接上它。"
        "相当于给「工具」定了一个 USB 接口。"))
    p.append(FIG(dia.compare(
        ("MCP", [
            "解决「Agent 怎么接工具」",
            "工具做成独立服务，谁都能接",
        ]),
        ("A2A", [
            "解决「Agent 之间怎么协作」",
            "是 Agent 对 Agent，不是对工具",
        ]),
        note="两者不互相替代：一个管「用工具」，一个管「找同事」。"
             "这一节写了三种东西——一个 MCP 服务器、一个 stdio 本地连接版、"
             "一个 HTTP 远程版；第 10 章会把 MCP 用在企业集成上。"),
        "MCP 管 Agent 对工具，A2A 管 Agent 对 Agent"))

    # ── 4.15 轨迹评测 ──
    p.append(H3("4.15　Agent 怎么测：看轨迹，不只看答案"))
    p.append(P(
        "现在回到第 3 章移过来的那一节。"
        "Agent 的评测和 RAG 有一个关键区别：" + E("答案对不代表过程对。")))
    p.append(FIG(dia.compare(
        ("只看答案", [
            "绕了五步、调了不该调的工具",
            "最后碰巧答对，判定为通过",
        ]),
        ("看轨迹", [
            "调了哪些工具、参数对不对",
            "步数有没有超预算、有没有走审批",
        ]),
        note="「答案对」是及格线，「过程对」才是安全线。"
             "测试背景的人在这里有天然优势——你本来就在检查「系统做事的步骤对不对」，"
             "只不过对象从接口换成了 Agent。"),
        "答案对不代表过程对，所以评测要看它走过的路"))

    # ── 综合项目 ──
    p.append(H3("4.16　把它们串成一个作品"))
    p.append(P(
        "这一章能力太多，容易学散。所以这一章最后额外做了一个综合项目："
        "「家庭购车决策 Copilot」，把整章能力重组成五个递进的切片，"
        "最后合并成一个完整应用。"))
    p.append(FIG(dia.timeline([
        ("step01", "走对路、兜住错", "可靠路由\n节点容错"),
        ("step02", "有计划、看得见", "计划执行\n可观测"),
        ("step03", "停得住、接得回", "持久化\n人工审批"),
        ("step04", "工具可控、查询可控", "工具安全\n结构化查询"),
        ("step05", "拆得开、接得上", "多 Agent\nMCP"),
    ], note="五个切片依次叠加，最终成品是 production_graph.py。"),
        "整章能力重组成五个递进的切片"))
    p.append(P("本篇内容按主题编排在章节 4.2–4.15；完整课程入口见章节总地图。"
               "Agent 工作流的整合实现与验收记录集中在 capstone/，不要把单个教学示例当作生产验收结论。"))

    p.append(H4("这一章的产出物"))
    p.append(P("本篇产出是一组可独立阅读的 Agent 工作流练习；"
               "累积项目的能力边界与真实验收情况以 capstone 文档为准。"))
    p.append(RUN([
        ("代码位置", C("chapters/part4-agents-langgraph/") + " 与 "
                      + C("capstone/")),
        ("工作目录", "仓库根目录"),
        ("额外依赖", "无"),
        ("执行命令", C("python tools/run_chapter.py 4.4")),
        ("预期输出", "先打印「默认覆盖」把前一条冲掉的结果，再打印加了 "
                      + C("operator.add") + " 之后两条都在；"
                      "fan-out 那一组会抛出 " + C("InvalidUpdateError")),
        ("常见失败", "没看到 " + C("InvalidUpdateError")
                      + "——多半是跑到了已经配好 reducer 的那个版本"),
        ("完成证据", "能说清「顺序覆盖」和「并发报错」是两种不同的失败，"
                      "以及各自该在哪里加 reducer"),
    ]))
    p.append(TASK("把 4.3 的 " + C("operator.add") + " 换成一个你自己写的函数，"
                  "让它合并的时候顺便去重。再跑一次 fan-out，看三条结果还在不在。"
                  "这一步做完，reducer 对你就不再是框架魔法，只是一个普通函数。"))
    p.append(CHECKLIST([
        "State / Node / Edge 三者的分工，以及节点为什么不直接改状态；",
        "reducer 解决的是什么问题，什么形状的图需要它；",
        "ReAct 循环的三步，以及它「看起来聪明」的来源；",
        "瞬时错误和永久错误为什么要有不同的处理方式；",
        "checkpoint 存的是整张图的状态，而不只是对话历史；",
        "HITL 为什么是上线红线；",
        "Text2SQL 的四道守卫；",
        "Agent 的「答案对」和「过程对」为什么要分开测。",
    ]))

    p.append(HOOK("现在能做出一个会自己决策、能暂停等人、能查数据库的系统了。"
                  "但它还躺在你的电脑里，只有你能运行。"
                  "第 5 章要把它变成别人能调用的服务，"
                  "并且补上那些「本地能跑、上线就崩」的坑：超时、重试、缓存、安全、容器。"))
    return PAGEWRAP("4　让它自己干活：Agent 与 LangGraph", "".join(p))
