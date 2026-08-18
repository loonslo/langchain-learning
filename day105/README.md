# Day105 · 客服 Agent → 订单 Agent：企业协议集成验收

最后把课程收束为一个最小跨 Agent 场景：客服 Agent 从用户文本提取订单号，带受控的委托
上下文调用订单 A2A Agent；订单 Agent 若缺少订单号则返回 `input-required`，否则仅通过已
授权的订单读取器返回结果。MCP 用于 Agent 接企业工具，A2A 用于独立 Agent 协作，二者不替代。

## 今日交付

- `integration.py`：订单 Agent、A2A 客户端适配器和不带密钥的委托上下文。
- `acceptance.py`：离线验收 P0–P2 的关键行为。
- `PROJECT_README.md`：Day90–105 可交付能力、运行与边界。

## 验收

```bash
python tools/materialize_enterprise_day.py 105
cd .build/day105/enterprise-support
python -m pytest -q
python -c "from src.enterprise_support.acceptance import run; print(run())"
```

## 完成后的边界

你现在有可讲、可测的企业 Agent 进阶项目骨架；仍不要声称已经完成 Kubernetes/ACK、高可用
发布、企业 IdP 对接、真实 GPU 容量压测或生产 A2A 联调。这些应在目标 JD 明确后继续深化。
