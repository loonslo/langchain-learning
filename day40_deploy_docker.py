"""
Day 40 · 用 Docker 打包部署
==========================================================
测试工程师转 AI 应用开发  ← 阶段4 工程化收尾

"在我机器上能跑"不算交付。Docker 把代码 + 依赖 + 运行环境装进一个镜像，
到哪台机器都一样跑，这是现代部署的基本功。本节把 Day35 的 FastAPI 服务
打包成镜像。

这个文件本身不是要运行的程序——跑它会在当前目录生成 Dockerfile.example 等
示例文件，你照着改成正式的 Dockerfile 即可（用 .example 后缀避免覆盖你已有的）。
==========================================================
"""

from pathlib import Path

DOCKERFILE = """\
# 基础镜像：带 Python 的精简版
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（单独一层，依赖没变时能用缓存，构建更快）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷代码
COPY . .

# 服务监听端口
EXPOSE 8000

# 启动 Day35 的 FastAPI 服务
CMD ["uvicorn", "day35_serve_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKERIGNORE = """\
.venv/
__pycache__/
*.pyc
.env
chroma_db/
*.log.jsonl
.git/
"""

REQUIREMENTS = """\
langchain
langchain-openai
langchain-community
langchain-text-splitters
langchain-huggingface
langchain-chroma
langgraph
faiss-cpu
pypdf
rank_bm25
python-dotenv
fastapi
uvicorn
"""


def write_examples():
    Path("Dockerfile.example").write_text(DOCKERFILE, encoding="utf-8")
    Path(".dockerignore.example").write_text(DOCKERIGNORE, encoding="utf-8")
    Path("requirements.example.txt").write_text(REQUIREMENTS, encoding="utf-8")
    print("已生成：Dockerfile.example / .dockerignore.example / requirements.example.txt")


if __name__ == "__main__":
    write_examples()
    print("""
下一步（在本机终端跑）：
  1) 把 .example 后缀去掉，按需微调
  2) 构建镜像：   docker build -t rag-app .
  3) 运行容器：   docker run -p 8000:8000 --env-file .env rag-app
  4) 访问：       http://127.0.0.1:8000/docs

注意：
  - 密钥用 --env-file .env 注入，绝不写进镜像（.env 已在 .dockerignore 里）
  - 本地 embedding 模型较大，要么挂载卷 -v 进去，要么改用 API embedding
""")


# ----------------------------------------------------------
# 小结：
# - Dockerfile 三段式：装依赖（可缓存）→ 拷代码 → 定启动命令。
# - 分层缓存：先 COPY requirements 再装，依赖没变就不重装，构建快。
# - 密钥走 --env-file 注入，不进镜像；大模型文件用挂载卷，别打进镜像。
# - 这是阶段4 的收尾：到这里你的应用有接口、可靠性、安全、测试、可观测、能容器化部署。
#
# 动手练习：本机装 Docker，把服务真打成镜像跑起来，curl /chat 验证。
# ----------------------------------------------------------
