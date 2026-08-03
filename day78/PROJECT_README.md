# 企业客服与工单 Copilot

这是 Day51–78 累积得到的最终项目。核心能力包括可引用 RAG、离线评测、LangGraph 控制流、受控订单工具、人工升级、持久化、API、可信身份、注入与 PII 防护、观测、缓存、质量门、容器、存储迁移契约、容量报告和恢复验证。

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
python -m customer_support.cli --check-data
uvicorn customer_support.runtime:create_runtime_api --factory
```

启动 API 前还需要配置模型环境变量和长度至少 32 的 `JWT_SECRET`。生产边界与面试演示见 `docs/PROJECT_STORY.md`。
