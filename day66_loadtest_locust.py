"""
Day66 · 负载压测（locust）+ OpenAPI 版本化
==========================================================
测试工程师转 AI 应用开发 · 阶段6 上线补全

这天学什么：
- `docker run` 起来 ≠ 扛得住并发。压测是回答"大概扛多少 QPS、瓶颈在哪"。
- locust 用 Python 写压测脚本，逐步加并发用户，看 QPS 和延迟的拐点
  （延迟突然飙升那一点，就是当前架构的并发上限）。
- LLM 应用的瓶颈通常不在你的服务，而在上游模型 API 的限流和响应时间——
  压测能让你拿数据说话，而不是拍脑袋。

跑法（先把 capstone 服务起起来：uvicorn capstone.api:app）：
  pip install locust
  locust -f day66_loadtest_locust.py --host http://127.0.0.1:8000
  浏览器开 http://localhost:8089，设并发用户数和加压速率，开始压。
  命令行无头模式：
  locust -f day66_loadtest_locust.py --host http://127.0.0.1:8000 \
         --headless -u 20 -r 5 -t 60s

顺带：接口加 /v1 版本前缀 + OpenAPI 文档，是上线规范动作——
见文件末尾 versioned_router() 示例，FastAPI 自带 /docs 和 /openapi.json。
==========================================================
"""

try:
    from locust import HttpUser, task, between

    class ChatUser(HttpUser):
        """模拟一个不断提问的用户。"""
        wait_time = between(1, 3)   # 每次请求间隔 1-3 秒，贴近真人

        @task(3)                    # 权重 3：问答是主路径
        def ask(self):
            self.client.post("/v1/chat", json={
                "question": "RAG 为什么能减少幻觉？",
                "user_id": "load_test",
            }, name="/v1/chat")

        @task(1)                    # 权重 1：健康检查
        def health(self):
            self.client.get("/health", name="/health")

except ImportError:
    # 没装 locust 也能 import 本文件读说明
    print("未安装 locust：pip install locust 后再用 locust -f 跑。")


# ---- OpenAPI 版本化示例：上线规范，接口挂在 /v1 下 ----
def versioned_router():
    """把接口收进 /v1 前缀；FastAPI 自动生成 /docs 和 /openapi.json。
    在 capstone/api.py 里用 app.include_router(router) 挂上即可。"""
    from fastapi import APIRouter
    router = APIRouter(prefix="/v1", tags=["v1"])
    # 实际路由在 capstone/api.py 注册；这里只示意版本前缀写法
    return router


if __name__ == "__main__":
    print(__doc__)
    print("拐点判读：QPS 涨到某点后不再涨、p95 延迟却陡升 → 那就是并发上限。")
    print("LLM 应用常见瓶颈：上游模型 API 限流 / 单次推理耗时，不是你的 FastAPI。")
