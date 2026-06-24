"""
Day65 · 模型供应商抽象：一处配置切 OpenAI / Azure / DeepSeek / Bedrock
==========================================================
测试工程师转 AI 应用开发 · 阶段6 上线补全

这天学什么：
- 别把 ChatOpenAI(...) 散写在几十个文件里——换供应商会改到崩溃。
- 抽一层 provider 工厂：业务代码只调 get_chat_model()，换供应商改一个环境变量。
- 企业为什么常用 Azure OpenAI：数据驻留在自己租户、走企业合同和 SLA、合规好过。
  国内则常用 DeepSeek / 通义 / 文心；出海团队偏 Bedrock（AWS 一体化）。

设计要点：所有 provider 都返回 LangChain 的 BaseChatModel，
下游 LCEL 链 / Agent 完全不用改——这就是抽象的价值。
==========================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_chat_model(temperature: float = 0.0, **kwargs):
    """按 LLM_PROVIDER 环境变量返回对应供应商的对话模型。
    业务侧只认这个函数，不认具体厂商。"""
    provider = os.getenv("LLM_PROVIDER", "deepseek").lower()

    if provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=temperature, **kwargs)

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature, **kwargs)

    if provider == "azure":
        # Azure 的部署名(deployment)和 endpoint 都在租户里，合规企业的常见选择
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_DEPLOYMENT", "gpt-4o-mini"),
            azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2024-06-01"),
            temperature=temperature, **kwargs)

    if provider == "bedrock":
        # 出海 / AWS 体系：pip install langchain-aws
        from langchain_aws import ChatBedrock
        return ChatBedrock(
            model_id=os.getenv("BEDROCK_MODEL", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={"temperature": temperature}, **kwargs)

    raise ValueError(f"未知 LLM_PROVIDER：{provider}（支持 deepseek/openai/azure/bedrock）")


def describe_active() -> str:
    return f"当前供应商：{os.getenv('LLM_PROVIDER', 'deepseek')}（改 .env 的 LLM_PROVIDER 即可切换）"


if __name__ == "__main__":
    print(describe_active())
    try:
        model = get_chat_model()
        print("已构造模型：", type(model).__name__)
        resp = model.invoke("用一句话说 RAG 是什么")
        print("回答：", resp.content[:80])
    except Exception as e:
        print(f"调用失败（多半是对应供应商的 key 没配）：{type(e).__name__}: {e}")
    print("\n要点：下游只调 get_chat_model()，换厂商改一个环境变量，链/Agent 不动。")
