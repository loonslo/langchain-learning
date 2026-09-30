"""
章节 5.5 · 用 Docker 打包部署
==========================================================
"在我机器上能跑"不算交付。Docker 把代码、依赖和运行环境装进一个镜像，到哪台机器都一样跑。
本章把 5.1 的 FastAPI 服务打包成镜像。

本文件不是要运行的服务：运行它会在本章目录生成 Dockerfile.example 和 .dockerignore.example，
你照着改成正式的 Dockerfile 即可（用 .example 后缀避免覆盖已有文件）。

前置：5.1
运行：python tools/run_chapter.py 5.5（离线；构建和运行容器需要本机安装 Docker）
输出：本章目录下的 Dockerfile.example 和 .dockerignore.example，以及后续的构建、运行命令
==========================================================
"""

from pathlib import Path

DOCKERFILE = """\
# 基础镜像：带 Python 的精简版
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（单独一层，依赖没变时能用缓存，构建更快）。
# requirements.txt 是锁定依赖；5.1 的检索还需要 faiss-cpu，它不在锁定文件里，这里单独安装。
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt faiss-cpu

# 再拷代码。章节脚本依赖根目录的 common.py 和 tools/，所以拷整个仓库（.dockerignore 排除密钥和缓存）
COPY . .

# 服务监听端口
EXPOSE 8000

# 启动 5.1 的 FastAPI 服务。容器里必须监听 0.0.0.0，宿主机才访问得到
CMD ["python", "tools/run_chapter.py", "5.1", "run_server.py", "--host", "0.0.0.0"]
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

def write_examples():
    Path("Dockerfile.example").write_text(DOCKERFILE, encoding="utf-8")
    Path(".dockerignore.example").write_text(DOCKERIGNORE, encoding="utf-8")
    print("已生成：Dockerfile.example / .dockerignore.example")


if __name__ == "__main__":
    write_examples()
    print("""
下一步（在仓库根目录的终端里运行）：
  1) 构建镜像（构建上下文是仓库根目录，用 -f 指定本章生成的 Dockerfile）：
       docker build -f chapters/part5-production/5.5-docker-packaging/Dockerfile.example -t rag-app .
  2) 运行容器（模型目录挂载进容器，并用环境变量告诉程序在哪里）：
       docker run -p 8000:8000 --env-file .env -v <本机模型目录>:/models -e EMBED_MODEL_PATH=/models/bge-small-zh-v1___5 rag-app
  3) 访问：       http://127.0.0.1:8000/docs

注意：
  - 密钥用 --env-file .env 注入，绝不写进镜像（.env 已在 .dockerignore 里）
  - 本地 embedding 模型较大，不要打进镜像：用挂载卷，或改用 API embedding
  - 没有挂载模型时，/ready 会返回 503（依赖没准备好），/health 仍然存活
""")


# ----------------------------------------------------------
# 小结：
# - Dockerfile 三段式：装依赖（可缓存）→ 拷代码 → 定启动命令。
# - 分层缓存：先 COPY requirements 再装，依赖没变就不重装，构建快。
# - 密钥走 --env-file 注入，不进镜像；大模型文件用挂载卷，别打进镜像。
# - 到这里，应用有了接口、可靠性、安全、测试、可观测，也能容器化部署。
#
# 动手练习：本机装 Docker，把服务真打成镜像跑起来，curl /chat 验证。
# ----------------------------------------------------------
