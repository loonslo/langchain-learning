"""
Day 60 · 真部署：拿一个能点的公网地址
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

`docker run` 在本机起来 ≠ 上线。上线 = 有一个手机能打开的公网 URL。
线上这一版用可公开语料（自己写的/开源年报），真实脏数据只在本地跑——这是合规边界。

详细步骤见 capstone/DEPLOY.md（本机容器跑通 → Render/Fly 部署 → 上线自检）。
这个文件是出门前的检查单。
==========================================================
"""

PRECHECK = [
    "key 走环境变量注入，不进镜像/不进仓库（git log -p | grep -i key 自查）",
    "线上知识库换可公开语料",
    "接口在 /v1 下，OpenAPI 文档 /docs 能打开（Day66）",
    "健康检查 /health 返回 200（平台靠它判活）",
    "给 /v1/chat 配限流，别被人刷爆 API 账单（Day56 已做）",
]

PLATFORMS = {
    "Render": "连 GitHub 自动构建，免费档够 demo——最省事，推荐先用这个",
    "Fly.io": "fly launch / fly deploy 一条命令，全球边缘，低延迟",
    "云主机": "自己装 Docker，最自由，适合已有机器",
}


if __name__ == "__main__":
    print("===== 部署前检查单 =====")
    for i, x in enumerate(PRECHECK, 1):
        print(f"  {i}. {x}")
    print("\n===== 平台选型（按省事排序）=====")
    for k, v in PLATFORMS.items():
        print(f"  [{k}] {v}")
    print("\n详细步骤：capstone/DEPLOY.md")
    print("验收：公网 URL 手机能开 /docs；无 token 调 /v1/chat → 401。")
