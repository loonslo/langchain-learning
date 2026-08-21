# Day79 · 前端工作台对接 Day78 API

Day79 不再新增一套客服后端，而是把 Day78 已经完成的能力接到一个独立的浏览器前端：

```text
浏览器页面（Day79 / Vite）
  → /api 代理
  → Day78 FastAPI
  → JWT 身份校验
  → 统一业务应用
  → RAG / 会话 / 订单工具 / 工单 / 反馈
```

## 页面能演示什么

- JWT token 连接与本地保存
- 多轮客服问答和新会话切换
- Day78 返回的知识来源展示
- 订单号进入只读订单工具分支
- 人工工单编号展示
- 正负反馈进入 Day78 `/feedback`
- API 在线状态和错误提示

前端不会自报 `user_id`，身份仍由 Day78 的签名 token 决定；页面上的 token 输入框是为了让 Day63 的可信身份能力可以在演示中被看见。

## 运行 Day78 后端

先在仓库根目录还原最终后端：

```bash
python tools/materialize_day.py 78
cd .build/day78/customer-support
uv sync
```

设置 Day78 所需环境变量：

```bash
export JWT_SECRET="day79-local-secret-at-least-32-characters"
export LLM_API_KEY="你的 DeepSeek Key"
uv run uvicorn customer_support.runtime:create_runtime_api --factory --reload --port 8000
```

PowerShell 对应写法：

```powershell
$env:JWT_SECRET = "day79-local-secret-at-least-32-characters"
$env:LLM_API_KEY = "你的 DeepSeek Key"
uv run uvicorn customer_support.runtime:create_runtime_api --factory --reload --port 8000
```

## 生成本地演示 token

保持后端虚拟环境可用，在仓库根目录另开一个终端运行：

```bash
export JWT_SECRET="day79-local-secret-at-least-32-characters"
uv run --directory .build/day78/customer-support python \
  ../../../day79/scripts/issue_demo_token.py
```

把终端输出的 token 粘贴到 Day79 页面右侧“连接后端”卡片中。

## 启动 Day79 前端

```bash
cd day79
npm install
npm run dev
```

打开 <http://127.0.0.1:5173>。`vite.config.js` 会把 `/api/*` 代理到 `127.0.0.1:8000`，因此本地开发不需要额外配置 CORS。

生产部署时可以设置 `VITE_API_BASE` 指向反向代理后的 Day78 API；生产环境不应开放演示 token 生成脚本，也不应把 JWT 写入 URL。

## 验收

1. 未连接 token 时发送问题，页面应提示先连接身份。
2. 连接有效 token 后，发送“退款多久到账？”，页面应显示答案和 `refund.md` 来源。
3. 发送“那发票呢？”，验证会话上下文仍由 Day78 保存。
4. 填写订单号后发送查询，验证请求包含 `order_id`。
5. 点击反馈按钮，验证 Day78 `/feedback` 返回 202。
6. 输入错误 token，验证页面显示 401 并清除本地 token。
