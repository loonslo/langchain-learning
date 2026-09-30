# 5.5 容器与运行配置：交付的不只是代码

[全书目录](../../README.md) · [上一章 5.4](../5.4-sqlite-persistence/README.md) · [下一章 5.6](../5.6-ollama-inference/README.md)

- **目标**：把 5.1 的服务打包成 Docker 镜像，并理解交付物里除了代码还有什么。
- **前置**：5.1。
- **环境**：生成示例文件离线运行；构建和运行容器需要本机安装 Docker。
- **命令**：`python tools/run_chapter.py 5.5`

## 问题

“在我机器上能跑”不算交付。Docker 把代码、依赖和运行环境装进一个镜像，到哪台机器都一样运行。

## 概念

- **Dockerfile 三段式**：装依赖（单独一层，依赖没变时能用缓存）→ 拷代码 → 定启动命令。
- **分层缓存**：先 `COPY requirements.txt` 再安装，依赖没变就不重装，构建更快。
- **监听地址**：容器里的服务必须监听 `0.0.0.0`，宿主机才访问得到；本机开发默认只监听 `127.0.0.1`。
- **密钥不进镜像**：用 `--env-file .env` 注入；`.dockerignore` 排除 `.env`、缓存和虚拟环境。
- **大模型文件不进镜像**：本地 embedding 模型较大，用挂载卷提供，并用 `EMBED_MODEL_PATH` 告诉程序路径；或改用 API embedding。
- **就绪与存活**：没有挂载模型时，`/ready` 返回 503，`/health` 仍然存活（5.1）。

## 流程

1. 运行本章脚本，在本章目录生成 `Dockerfile.example` 和 `.dockerignore.example`。
2. 从仓库根目录构建镜像（构建上下文是仓库根目录，用 `-f` 指定本章的 Dockerfile，并使用根目录的 `.dockerignore`）：

   ```bash
   docker build -f chapters/part5-production/5.5-docker-packaging/Dockerfile.example -t rag-app .
   ```

3. 运行容器：

   ```bash
   docker run -p 8000:8000 --env-file .env -v <本机模型目录>:/models -e EMBED_MODEL_PATH=/models/bge-small-zh-v1___5 rag-app
   ```

4. 访问 http://127.0.0.1:8000/docs 验证。

## 代码导读

[docker_examples.py](docker_examples.py)：`DOCKERFILE` 和 `DOCKERIGNORE` 两个模板，`write_examples` 负责写出文件。模板里的注释解释了每一步的原因。

## 练习

1. 本机装好 Docker，把服务真正构建成镜像并运行，用 `curl` 调用 `/health` 和 `/chat`。
2. 不挂载模型运行一次，观察 `/ready` 的状态码。
3. 检查镜像里是否含有 `.env`（不应该有）。

## 运行与边界

- 示例只是模板，没有在本仓库里完成构建验证；实际构建可能需要按环境调整依赖。
- 仓库根目录另有 `Dockerfile`，用于 capstone 的企业版服务，二者用途不同。
- 镜像没有做漏洞扫描、多阶段构建和非 root 运行，生产还需要补上。
