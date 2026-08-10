"""应用层：把“多轮会话”能力接到已有客服助手上。

可以把本模块看成服务台的协调员：普通咨询会先读取历史记录，把很短的追问补成独立
问题，再调用 ``CustomerSupportAssistant``；明确携带 ``order_id`` 的请求则走受控订单查询。
这样知识问答和业务数据查询共用一个应用入口，但各自的底层职责仍保持独立。

当前 ``History`` 是内存版本，程序关闭后记录会丢失。``tenant_id`` 和 ``user_id`` 已沿着
调用链传递，但现有历史记录尚未用它们分隔数据，因此它还不是可用于多租户生产环境的实现。
"""
from dataclasses import dataclass
from typing import Protocol

from src.assistant import SupportAnswer
from src.conversation import History, Turn
from src.orders import OrderRepository
from src.tickets import TicketStore, escalate
from src.tool_runner import call_read_only


class Assistant(Protocol):
    """本应用层所需的最小问答能力。

    这里的协议只有 ``ask``，所以真实的 ``CustomerSupportAssistant`` 和测试里手写的
    Fake 都能传入 ``SupportApplication``；这降低了模块之间的耦合。
    """

    def ask(self, question: str) -> SupportAnswer: ...


@dataclass(frozen=True)
class ApplicationResult:
    """应用层统一返回值，为答案之外的后续业务字段预留扩展位置。

    ``answer`` 兼容现有客服问答结果；``ticket_id`` 可在未来接入工单系统后携带工单编号。
    当前代码尚未创建工单，因此它保持为 ``None``。
    """

    answer: SupportAnswer
    ticket_id: str | None = None


class SupportApplication:
    """协调单轮客服助手与会话历史，提供支持多轮提问的统一入口。

    普通咨询的顺序是：原始问题 → ``History.standalone`` 补全上下文 → assistant 回答
    → ``History.add`` 保存原始问题与回答。订单请求则按订单号和用户身份读取业务数据，
    不进入知识库问答链。
    """

    def __init__(self,
                 assistant: Assistant,
                 history: History,
                 orders: OrderRepository | None = None,
                 tickets: TicketStore | None = None):
        """保存问答助手、历史记录和订单仓库三个外部依赖。

        这种写法让调用方决定使用真实模型还是测试替身、内存历史还是未来的数据库历史，
        以及真实订单存储还是内存数据，因而更容易测试和替换基础设施。
        """
        self.assistant = assistant
        self.history = history
        # 未提供仓库时使用空的内存仓库，让原有的纯知识问答调用仍能正常装配。
        self.orders = orders or OrderRepository([])
        self.tickets = tickets or TicketStore()

    def handle(self,
               question: str,
               *,
               session_id: str = 'cli',
               tenant_id: str = "local",
               user_id: str = "local",
               order_id: str = "",
               ) -> ApplicationResult:
        """按请求类型执行订单查询或知识问答，并返回统一的应用层结果。

        ``order_id`` 非空即选择订单分支。``user_id`` 必须来自可信身份系统，不能直接
        相信客户端自报的值；仓库会同时匹配订单号与用户编号，避免跨用户读取订单。
        """

        if order_id:
            # 订单查询被包装为只读工具调用；最多尝试两次，写操作不应套用此重试器。
            tool_result = call_read_only(
                lambda: self.orders.get_for_user(order_id, user_id),
                max_attempts=2,
            )
            # 工具层用 error 字段表达已归类的失败，应用层负责转换成用户可读文案。
            if tool_result.error:
                return ApplicationResult(SupportAnswer("订单系统暂时不可用，请稍后重试。", ("order-system",)))
            order = tool_result.value
            # 订单状态来自业务系统而非 Markdown，所以使用虚拟来源名区分两类证据。
            return ApplicationResult(
                SupportAnswer(f"订单 {order.order_id}：{order.status}", ("order-system",))
            )

        # 未指定订单号时沿用原来的多轮 RAG 路径，短追问会先补足上一轮上下文。
        standalone = self.history.standalone(
            session_id=session_id,
            question=question,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        answer = self.assistant.ask(standalone)
        # 保存用户原始问题而不是补全后的 standalone，便于界面还原真实对话。
        self.history.add(
            session_id=session_id,
            turn=Turn(question, answer.text),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        ticket = escalate(self.tickets, user_id, question, bool(answer.sources))
        return ApplicationResult(answer, ticket.ticket_id if ticket else None)

    def ask(self, question: str, **kwargs) -> SupportAnswer:
        """兼容原有调用方：执行完整处理，但只返回其中的客服答案。"""
        return self.handle(question, **kwargs).answer
