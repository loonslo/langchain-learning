# Day86 · AI API、流式与 E2E

> 今天解决：API 单元测试通过了，但真实 HTTP、流式边界和前后端拼接仍可能失败。
>
> 第一性原则：端到端测试要覆盖网络契约和用户实际收到的事件序列。

## 与 Day85 的文件衔接

Day85 验证 Agent 轨迹；Day86 站在 HTTP 边界验证 Day78 API 的响应契约，并补充流式事件解析工具，供 Day79 前端对接测试使用。

### 今天新增

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/api_e2e.py` | 新增 | SSE 解析、token 合并和 E2E 响应校验 |
| `tests/test_api_e2e.py` | 新增 | 验证事件顺序、事件 ID 和 HTTP 字段 |

## 真实调用链

```text
Browser/HTTP → SSE parser → ChatResponse contract → UI assertion
```

## 验收

```bash
python tools/materialize_ai_testing_day.py 86
cd .build/day86/ai-testing
python -m pytest -q
```

## 今日边界

离线 SSE 解析不能证明浏览器、代理和真实上游连接都稳定；真实服务仍要增加受控 E2E 环境。
