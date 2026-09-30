"""第 1 章　让程序先会说话：模型调用基础"""
import dia
from comp import (P, E, C, SIDE, KEYPOINT, VERIFY, TRAP, CHECKLIST, UL, OL,
                  CODE, TABLE, HOOK, FIG, PAGEWRAP, CHAPTER, H3, H4,
                  RUN, TASK)


def chapter():
    p = []
    p.append(CHAPTER(1, "让程序先会说话：模型调用基础",
                     "这一章只做一件事：让程序用上大模型。六个小练习里，"
                     "会拿到后面反复用到的三样东西——一条链、一个状态、一次工具调用。",
                     "ch1"))

    p.append(P(
        "把大模型接进程序，第一行代码通常是这样：把一段话发过去，它回一段话。"
        "很多人到这一步就停了，觉得「会用 API 了」。",
        "真正做项目时，问题马上变成另外几个：怎么让它稳定地按指定格式输出？"
        "怎么让它记住上一句？怎么让它去查一个数据库？"
        "这一章把这几个问题依次解决掉，最后拼成一个能连续对话的命令行机器人。"))

    p.append(SIDE("前置知识",
                  P("会写 Python 函数、会读 " + C(".env") + " 里的配置就够了。"
                    "类、装饰器、类型注解如果不熟，序章那张表看五分钟即可。")))

    # ── 1.1 ──
    p.append(H3("1.1　第一次调用：一条链的三个位置"))
    p.append(P(
        "第一段代码只有十几行，但它定下了整本书的骨架。"))
    p.append(CODE([
        "import os",
        "from dotenv import load_dotenv",
        "from langchain_openai import ChatOpenAI",
        "from langchain_core.prompts import ChatPromptTemplate",
        "from langchain_core.output_parsers import StrOutputParser",
        "",
        "load_dotenv()                       # 从仓库根目录的 .env 读密钥",
        "llm = ChatOpenAI(",
        "    model='deepseek-chat',",
        "    api_key=os.getenv('DEEPSEEK_API_KEY'),",
        "    base_url='https://api.deepseek.com',   # DeepSeek 兼容 OpenAI 接口",
        "    temperature=0,",
        ")",
        "",
        "prompt = ChatPromptTemplate.from_template('用一句话解释：{topic}')",
        "chain = prompt | llm | StrOutputParser()",
        "print(chain.invoke({'topic': '什么是 RAG'}))",
    ]))
    p.append(P("这条 " + C("prompt | llm | parser") + " 的链，是全书唯一的根。"
               "后面所有事都是在给它换零件——换的是下面三个位置之一："))
    p.append(FIG(dia.flow([
        ("输入 prompt", "现在是固定模板 → 以后是资料 + 历史 + 工具定义"),
        ("推理 llm", "现在是一次调用 → 以后是有分支和循环的状态图"),
        ("输出 parser", "现在是取纯文本 → 以后是有字段校验的结构化数据"),
    ], note="后面每一个新概念，落点都在这三个位置之一。"),
        "三个位置各自会长成什么样"))
    p.append(SIDE("先说清：LangChain 的「链」和管道符号",
                  P(C("prompt | llm | parser") + " 里的 " + C("|") + " 和 Linux 管道的含义一样："
                    "左边东西的输出，变成右边东西的输入。"),
                  P("所以这段代码可以直译为：把问题填进模板 → 交给模型 → 把结果取成纯文本。"
                    "LangChain 的价值不在于发明了新概念，"
                    "而在于把这些步骤标准化成可以互换的零件。")))
    p.append(VERIFY(P("终端打印出一句对 RAG 的解释，链路就通了。"
                      "如果报错，九成是 " + C(".env") + " 里的密钥没配好——"
                      "回到序章第 3 步看一眼。")))
    p.append(TRAP(P("密钥写在代码里。这类提交一旦进了公开仓库，"
                    "密钥通常几分钟内就会被扫到并盗用。"
                    "放进 " + C(".env") + " 并加到 " + C(".gitignore") + " 就能避开。")))

    # ── 1.2 ──
    p.append(H3("1.2　控制它怎么说话：temperature 和流式输出"))
    p.append(P(
        "这一节只多了两个参数，但它们决定了后面所有评测能不能成立。"))
    p.append(FIG(dia.compare(
        ("temperature = 0", [
            "每次都挑最可能的那个词",
            "两次回答的波动被压到最小",
            "变化更容易归因到你的改动",
        ]),
        ("temperature 调高", [
            "愿意挑冷门词，回答更花哨",
            "两次回答的差异明显变大",
            "变化来源分不清，对比失效",
        ]),
        note="它压低的是波动，不是把输出变成确定值——同一句话问两次，"
             "仍可能有一两个字的差别。第 3 章做对比实验靠的是「同一批问题、同一套指标」"
             "的统计口径，不是逐字相同。"),
        "temperature 压低的是波动，不是把输出变成确定值"))
    p.append(SIDE("先说清：temperature",
                  P("它有点像「模型的胆子」：0 表示每次都挑它认为最可能的那个词，"
                    "所以最稳、最可复现；数值越高越愿意挑冷门词，回答更花哨也更飘。")))
    p.append(P("另一个参数是流式输出（stream）。默认情况下模型要生成完整段话才一次性返回，"
               "用户得盯着空屏幕等几秒；流式让字一个个蹦出来。"))
    p.append(CODE([
        "# 流式输出：一个字一个字地打印",
        "for chunk in llm.stream('讲个笑话'):",
        "    print(chunk.content, end='', flush=True)",
    ]))
    p.append(VERIFY(P("把 temperature 设成 0，同一个问题连续跑两次，看两次差多少。"
                      "多数情况只有个别字不同，偶尔整句换一种说法也属正常——"
                      "低温只降低波动，不保证逐字一致。"
                      "所以后面写评测断言时用的是「关键信息在不在」这类容差判断，"
                      "而不是字符串相等。")))

    # ── 1.3 ──
    p.append(H3("1.3　让它输出程序能用的数据：结构化输出"))
    p.append(P(
        "前两步里，模型的输出都是给人看的文字。程序需要的是数据。"))
    p.append(FIG(dia.compare(
        ("模型的自然回答", [
            "「这位用户比较着急，订单号好像是 A12345」",
            "程序拿这句话查不了数据库",
            "「很急」「比较急」「有点着急」程序判不了",
        ]),
        ("加上结构约束后", [
            "order_id = 'A12345'",
            "urgency = '高'",
            "字段名和取值范围都固定，程序可以直接用",
        ]),
        note="结构化输出的作用，是把模型的不确定性挡在程序之外。"),
        "同样是「着急」，程序要的是能判断的字段"))
    p.append(P("这一步用 Pydantic 给输出定一个结构。Pydantic 是 Python 里做数据校验的库："
               "先声明「这个结果必须有哪几个字段、分别是什么类型」，"
               "它负责检查模型给的东西符不符合。"))
    p.append(CODE([
        "from typing import Literal",
        "from pydantic import BaseModel, Field",
        "",
        "class Ticket(BaseModel):",
        "    order_id: str = Field(description='订单号，形如 A12345')",
        "    urgency: Literal['低', '中', '高'] = Field(description='紧急程度')",
        "",
        "structured = llm.with_structured_output(Ticket)",
        "result = structured.invoke('我的订单 A12345 三天了还没发货，很急')",
        "print(result.order_id, result.urgency)   # 直接当对象用",
    ]))
    p.append(P(C("with_structured_output") + " 做的是两件事：把「你要什么结构」"
               "翻译成模型能理解的说明，模型返回后再按结构解析、校验。"
               "解析失败会直接报错，而不是悄悄给一个半成品。",
               "约束要落在" + E("类型") + "上，不只是写在说明里——"
               + C("Literal['低', '中', '高']") + " 让非法取值在解析这一步就被拦下，"
                 "而 " + C("str") + " 加一句描述，拦不住任何东西。"))
    p.append(TRAP(P("把约束写在说明里，却不在类型上落实。"
                    "只写 " + C("urgency: str") + " 再加一句「只能是 低/中/高 之一」，"
                    "模型多半会照着做，但" + E("校验这一层是空的") + "——"
                    "它真回了「非常紧急」，Pydantic 也会照收不误，"
                    "错值一路流到下游才暴露。"
                    "换成 " + C("Literal['低', '中', '高']") + "，"
                    "非法取值在解析阶段就报错。")))
    p.append(VERIFY(P("故意问一个信息不全的问题（比如不给订单号），"
                      "看它是报错、还是编一个订单号。"
                      + C("Literal") + " 拦得住的是「格式不合法」，"
                      "拦不住「格式合法、内容是编的」——"
                      "编出来的订单号照样通过校验。这两件事要分开看："
                      "类型约束管前者，第 2 章的「没有证据就拒答」管后者。")))

    # ── 1.4 ──
    p.append(H3("1.4　让它记住上一句：多轮记忆"))
    p.append(P(
        "在此之前，每次调用都是独立的——问「它多少钱」，模型不知道「它」指什么。"
        "解决办法朴素得有点意外：每次调用时，把之前所有对话都一起发过去。"
        "模型本身没有记忆，记忆是替它保存的。"))
    p.append(FIG(dia.flow([
        ("第 1 轮发出", "[ 问题 1 ]"),
        ("第 2 轮发出", "[ 问题 1 · 回答 1 · 问题 2 ]"),
        ("第 3 轮发出", "[ 问题 1 · 回答 1 · 问题 2 · 回答 2 · 问题 3 ]"),
    ], direction="v",
        note="每轮都要把历史重发一遍，所以上下文会越来越长——这就是「上下文窗口」和"
             "「留多少、丢多少」这两个说法的来源。"),
        "「记忆」的实现方式：每轮把历史重发一遍"))
    p.append(CODE([
        "from langchain_core.messages import HumanMessage, AIMessage",
        "",
        "history = [HumanMessage('我叫 ajar'), AIMessage('你好 ajar')]",
        "history.append(HumanMessage('我叫什么？'))",
        "reply = llm.invoke(history)      # 整段历史一起发过去",
        "print(reply.content)             # 它知道答案",
    ]))
    p.append(P("真实项目里，历史不能无限增长，取舍是免不了的。"
               "这件事在第 4 章讲 Agent 状态、第 6 章讲会话时会再回来。"))
    p.append(VERIFY(P("连续问「我叫什么」，再问「我上一条问的是什么」。"
                      "两个都能答对，说明历史确实被带上了。")))

    # ── 1.5 ──
    p.append(H3("1.5　让它去查东西：工具调用"))
    p.append(P(
        "模型最擅长组织语言，最不擅长查实时数据和做精确计算。"
        "工具调用补的就是这个短板：把一个普通的 Python 函数交给模型，"
        "告诉它「这个函数能查订单」，模型在需要时输出「请调用这个函数、参数是 A12345」，"
        "由程序去执行，再把结果发回给模型。"))
    p.append(FIG(dia.seq(["你的程序", "模型", "工具函数"], [
        (0, 1, "「A12345 发货了吗」"),
        (1, 0, "想调用 get_order_status(A12345)", True),
        (0, 2, "真正执行这个函数"),
        (2, 0, "返回「已发货」", True),
        (0, 1, "把结果交回模型"),
        (1, 0, "生成给用户的回答", True),
    ], note="模型负责决定调不调、传什么参数；程序负责真正执行。"
            "模型从头到尾没有直接访问数据库。"),
        "工具调用是一次往返：模型只出「意图」，执行权在程序手里"))
    p.append(CODE([
        "from langchain_core.tools import tool",
        "",
        "@tool",
        "def get_order_status(order_id: str) -> str:",
        "    '''查询订单状态。order_id 形如 A12345。'''",
        "    return {'A12345': '已发货'}.get(order_id, '查无此单')",
        "",
        "llm_with_tools = llm.bind_tools([get_order_status])",
        "msg = llm_with_tools.invoke('A12345 发货了吗')",
        "print(msg.tool_calls)   # [{'name':'get_order_status','args':{'order_id':'A12345'}}]",
    ]))
    p.append(SIDE("先说清：@tool 这个装饰器在做什么",
                  P("它把「一个普通函数」翻译成「一段模型能读懂的说明书」——"
                    "函数名、参数、注释都会变成说明书的一部分。"),
                  P("所以工具的 " + C("docstring") + " 不只是写给人看的注释，"
                    "也是" + E("写给模型看的接口文档") + "。写含糊了，模型就会用错。")))
    p.append(TRAP(P("以为模型会自己执行函数。模型其实只输出「想调用谁、参数是什么」，"
                    "真正把函数跑起来的是程序。这一点没分清，后面 Agent 会一直绕不出来。")))
    p.append(VERIFY(P("打印 " + C("msg.tool_calls") + "，看到结构化的工具名和参数，"
                      "说明模型正确理解了工具的用途。如果它是空列表，"
                      "多半是 " + C("docstring") + " 写得不清楚。")))

    # ── 1.6 ──
    p.append(H3("1.6　拼起来：一个命令行聊天机器人"))
    p.append(P(
        "最后一步把前面几样东西合到一起：一个能连续对话、记得上下文、"
        "需要时会调用工具的聊天程序。它只有一百多行，"
        "但结构和后面那个企业级产品一致——区别只在零件多寡。"))
    p.append(FIG(dia.cards([
        ("Prompt 模板（1.1）", "规定机器人的身份和回答风格"),
        ("temperature = 0（1.2）", "让同一问题的回答稳定"),
        ("消息历史列表（1.4）", "记住本次对话，支持连续追问"),
        ("工具函数（1.5）", "让它能查订单状态"),
        ("输入循环（新增）", "接收用户输入，直到输入 exit"),
        ("结构化输出（1.3）", "需要时把结果变成程序能用的数据"),
    ], cols=2),
        "六个零件拼成的小程序，结构已经和最终产品一致"))

    p.append(H4("这一章的产出物"))
    p.append(P("一个能跑的命令行聊天机器人，代码在 "
               + C("chapters/part1-foundations/1.8-cli-chatbot/chatbot_project.py") + "。"
               "运行后可以连续输入问题，输入 " + C("exit") + " 退出。"))
    p.append(RUN([
        ("代码位置", C("chapters/part1-foundations/1.1-first-call/") + " 到 "
                      + C("chapters/part1-foundations/1.8-cli-chatbot/")),
        ("工作目录", "仓库根目录"),
        ("额外依赖", "无——序章装好的依赖就够"),
        ("执行命令", C("python tools/run_chapter.py 1.8")),
        ("预期输出", "进入对话循环：能连续追问、能查订单状态，输入 " + C("exit") + " 退出"),
        ("常见失败", C("AuthenticationError") + " 多为密钥没配对；"
                      + C("ConnectionError") + " 多为网络不通或 " + C("base_url") + " 写错"),
        ("完成证据", "连着问三个相关的问题，它记得上下文；给一个订单号，"
                      "它调用工具去查，而不是直接编一个状态"),
    ]))
    p.append(TASK("把 1.1 那个例子的 system 提示词改一句，让它「只回答一句话，"
                  "不超过 20 字」。跑三次，把三次输出摆在一起看：长度都压住了吗？"
                  "如果有一次超了，把这一次的输出留下来——"
                  "它就是你做评测时遇到的第一条不稳定样本。"))
    p.append(CHECKLIST([
        C("prompt | llm | parser") + " 三个位置的分工，以及它们各自会长成什么；",
        "为什么工程里 temperature 默认设 0；",
        "Pydantic 定义输出结构解决了什么问题；",
        "「模型没有记忆，历史是你替它保存的」这句话的含义；",
        "工具调用里，模型和程序各自负责哪一半。",
    ]))

    p.append(HOOK("现在这个机器人有一个明显的毛病：它只会用模型「脑子里」的东西回答。"
                  "问它公司内部的规定，它会一本正经地编。"
                  "第 2 章解决的就是这件事——先查资料，再回答。"))
    return PAGEWRAP("1　让程序先会说话：模型调用基础", "".join(p))
