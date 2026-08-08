# Day55–Day78 连续重构总览

Day55–Day78 继续开发 Day51–54 的同一个客服产品。每天的完成标准不再是“新增模块测试通过”，而是：

1. 新能力进入当天已有的正式入口或发布入口；
2. README 明确列出新增文件、修改的旧文件和关键继承文件；
3. workbook 要求解释如果不修改集成点会发生什么；
4. 还原当天完整项目后，Day51 到当天的累计测试全部通过。

## 四段连续主线

| 阶段 | Day | 累积方式 | 关键集成点 |
|---|---|---|---|
| 业务主链 | 55–60 | 会话 → LangGraph → 订单 → 重试 → 工单 → SQLite | `application.py`、`bootstrap.py`、`app.py` |
| 服务与安全 | 61–68 | FastAPI → 幂等 → 身份 → 同步 → 注入 → 脱敏 → 观测 → 缓存 | `api.py`、`runtime.py`、`workflow.py`、逐层应用装饰器 |
| 发布与运维 | 69–75 | 质量门 → 启动检查 → 存储契约 → 容量门 → 反馈 → fallback → 备份 | `evaluation.py`、`readiness.py`、`sync.py`、`runtime.py` |
| 收口与证据 | 76–78 | 统一组合 → 证据核验 → 可执行最终验收 | `application.py`、`api.py`、`runtime.py`、`acceptance.py` |

## 每天应先看的旧文件

| Day | 新能力 | 为了生效而修改的旧文件 |
|---|---|---|
| 55 | 连续追问 | `app.py`、`bootstrap.py` |
| 56 | LangGraph 控制流 | `bootstrap.py` |
| 57 | 订单查询 | `application.py`、`bootstrap.py` |
| 58 | 工具重试 | `application.py` |
| 59 | 人工工单 | `application.py`、`bootstrap.py` |
| 60 | SQLite 会话 | `conversation.py`、`settings.py`、`bootstrap.py` |
| 61 | FastAPI | 新增 `runtime.py`，API 直接调用累积 application |
| 62 | 幂等 | `application.py`、`api.py`、`bootstrap.py` |
| 63 | 签名身份 | `api.py`、`runtime.py` |
| 64 | 增量同步 | `api.py`、`runtime.py` |
| 65 | 注入防护 | `workflow.py`、`bootstrap.py` |
| 66 | PII 脱敏 | `bootstrap.py` |
| 67 | 可观测性 | `bootstrap.py` |
| 68 | 安全缓存 | `bootstrap.py` |
| 69 | CI 质量门 | `evaluation.py` |
| 70 | 启动检查 | `bootstrap.py` |
| 71 | 向量存储契约 | `sync.py` |
| 72 | 容量门 | `readiness.py` |
| 73 | 反馈闭环 | `runtime.py` |
| 74 | 模型 fallback | `bootstrap.py` |
| 75 | 备份恢复 | `thread_store.py`、`runtime.py` |
| 76 | 最终统一应用 | `application.py`、`api.py`、`runtime.py` |
| 77 | 项目证据 | `runtime.py` |
| 78 | 最终验收 | `acceptance.py` 直接调用前序真实组件 |

## 查看和验证

查看任意一天相对前一天的真实项目文件差异：

```powershell
python tools/day_change_report.py 68
```

还原并运行任意一天的累计测试：

```powershell
python tools/materialize_day.py 68
cd .build/day68/customer-support
python -m pytest -q
```

课程维护时运行 `python tools/generate_day_guides.py`，只会根据实际快照重新生成 Day55–78 的 README 和 workbook，不覆盖 Day51–54。
