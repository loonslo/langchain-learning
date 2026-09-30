# 9.9 Compose 与运维：依赖也进入交付清单

[全书目录](../../README.md) · [上一章 9.8](../9.8-vectorstore-selection/README.md) · [下一章 9.10](../9.10-openai-compatible-provider/README.md)

- **目标**：把 PostgreSQL（真相源）、Redis（缓存与限流）、Qdrant（检索）固定为一个本地交付单元；服务只绑定 loopback，默认不向公网暴露数据库端口。
- **前置**：9.8（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.9-compose-linux-ops`，进入 `.build/enterprise/9.9-compose-linux-ops/enterprise-support` 后运行 `python -m pytest -q`

## 问题

应用依赖数据库、缓存和检索服务后，手工启动容易遗漏配置。Compose 整理本地依赖，运维文档说明健康检查、备份与回滚，让环境可复查。

## 概念

服务定义描述容器与连接；健康检查确认依赖状态；卷保存持久数据；RuntimeSettings 核对应用配置。`.env.example` 里的主机名 `postgres`、`redis`、`qdrant` 只在 Compose 网络内有效；应用直接在宿主机运行时改成 `127.0.0.1`（端口只映射到本机回环地址）。

## 流程

1. 阅读服务和网络定义。
2. 检查配置范围。
3. 在本机环境启动依赖。
4. 核对健康与持久数据。
5. 记录备份和恢复过程。

## 本章交付

- `compose.yaml`：Postgres、Redis、Qdrant 的本地可复现依赖。
- `ops/linux-compose.md`：Linux 主机部署、健康检查、备份和回滚步骤。
- `runtime.py`：启动前检查三个 URL 的协议，并在生产环境拒绝示例数据库密码（`change-me`）。

## 代码导读

先读 compose.yaml 与 ops/linux-compose.md，再读 runtime.py 的 configuration_errors，区分应用与基础设施的责任。

实现文件：

- [runtime.py](src/enterprise_support/runtime.py)

## 练习

不启动服务也先列出每个端口和数据卷用途；具备 Docker 后用合成数据做备份恢复演练，记录实际命令。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.9-compose-linux-ops
cd .build/enterprise/9.9-compose-linux-ops/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

本章文件存在不代表容器已启动；真实 Linux、网络和数据恢复均需环境验收。

Compose 是单机交付起点，不是高可用方案；生产镜像必须锁定 digest，密钥由 Secret/密钥管理服务注入，而不是保存在 `.env`。
