"""应用层：把“多轮会话”能力接到已有客服助手上。

可以把本模块看成服务台的协调员：它不负责检索资料或生成答案，而是在调用
``CustomerSupportAssistant`` 前读取历史记录，把很短的追问补成独立问题；收到回答后，
再把本轮问答写回历史。这样核心问答规则可以保持简单，并能被命令行、网页或 API 复用。

当前 ``History`` 是内存版本，程序关闭后记录会丢失。``tenant_id`` 和 ``user_id`` 已沿着
调用链传递，但现有历史记录尚未用它们分隔数据，因此它还不是可用于多租户生产环境的实现。
"""

from typing import Protocol

from src.assistant import SupportAnswer
from src.conversation import History, Turn


class Assistant(Protocol):
    """本应用层所需的最小问答能力。

    这里的协议只有 ``ask``，所以真实的 ``CustomerSupportAssistant`` 和测试里手写的
    Fake 都能传入 ``SupportApplication``；这降低了模块之间的耦合。
    """

    def ask(self, question: str) -> SupportAnswer: ...


class SupportApplication:
    """协调单轮客服助手与会话历史，提供支持多轮提问的统一入口。

    一次调用的顺序是：原始问题 → ``History.standalone`` 补全上下文 → assistant 回答
    → ``History.add`` 保存原始问题与回答 → 返回结构化 ``SupportAnswer``。
    """

    def __init__(self, assistant: Assistant, history: History):
        """保存两个外部依赖，而不是在这里自行创建它们。

        这种写法让调用方决定使用真实模型还是测试替身、内存历史还是未来的数据库历史，
        因而更容易测试和替换基础设施。
        """
        self.assistant = assistant
        self.history = history

    def ask(
            self,
            question: str,
            *,
            session_id: str,
            tenant_id: str = "local",
            user_id: str = "local",
    ) -> SupportAnswer:
        """回答本会话中的一个问题，并记录本轮结果。

        ``session_id`` 是一次聊天的唯一编号；``tenant_id`` 和 ``user_id`` 是为未来
        多租户和用户隔离预留的上下文参数。它们必须以关键字方式传入（``*`` 之后的参数），
        能降低调用时把多个字符串位置写错的风险。
        """
        # 对短追问（例如“那多久到？”）补上上一轮问题，减少模型只看到代词时的歧义。
        standalone = self.history.standalone(
            session_id, question, tenant_id=tenant_id, user_id=user_id
        )
        # application 只调用接口约定的 ask，不依赖某个具体模型或向量库。
        answer = self.assistant.ask(standalone)
        # 历史保存原始问题而非补全后的 standalone，便于日后界面展示用户真实输入。
        self.history.add(
            session_id,
            Turn(question, answer.text),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        # 返回完整 SupportAnswer，保留回答文本以及由知识库生成的来源列表。
        return answer
