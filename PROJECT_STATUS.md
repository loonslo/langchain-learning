---
project_id: langchain-learning
updated: 2026-10-06
status: active
overview: 测试工程师转 AI 应用开发的章节课程、企业客服旗舰项目与岗位选修专项。
progress: "课程书稿最新修订已提交推送，PDF 构建、机械和几何检查通过，并抽查代表页；未逐页目视或重跑课程测试。"
next: "补真实模型、远端 CI/staging、容量、恢复与事故演练证据；核对第三方内容版权。"
evidence:
  - README.md
  - TASKS.md
  - chapters/README.md
  - docs/course-restructure-validation.md
  - docs/course-book-validation.md
  - docs/course-review-validation.md
  - docs/course-book-v1-validation.md
---

# LangChain 学习记录 · 项目概览与进度

本页是本项目的概览与进度摘要。更新进度时先核对证据文件及实际验收；任务细节仍以项目原有的 TASKS、ROADMAP 或验收记录为准。只根据有证据的变化修改状态与日期；未验证事项保留“待核实”，不把文件存在或 Git 改动当作完成。

2026-09-28 完成章节导航、统一还原工具、CI 路径与历史资料归档，并补齐入门章节。真实模型回归暴露拒答仍携带无关引用的问题，已记录到 TASKS；未将其写为验收通过。

同日按用户反馈改为用途文件名，所有学习目录先链接书稿正文；正文涵盖场景、概念、流程、代码导读和练习记录。最新离线结果与未验证边界见 course-book-validation，课程内容调整不表示本人已学完。

2026-09-29 按反馈继续逐个排查旧日编号内容：清理失效路径和日编号命名、更新 PDF 书稿并重建 99 页成品。仅完成静态扫描、PDF 构建检查和页面缩略图目视检查；未运行测试。生成目录和测试缓存清理受限情况见 `docs/project-cleanup-validation.md`。

2026-09-30 按七项要求审查课程：订正断链、文字与代码不符和多处实际缺陷，补充注释与测试；随后按确认清理旧环境和历史输出，并修复拒答附引用与混合检索证据门槛。命令、结果和未验证边界见 `docs/course-review-validation.md`；课程内容调整不表示本人已学完。

同日按本次修订重建 PDF 书稿并定版 v1.0（100 页、120 张图，机械与几何自检通过，书签 97 条）。订正的是与当前仓库对不上的说法：封面配套代码、环境依赖与自检命令、代码地图中的旧日编号与已删除目录、6 章两处实现的验收口径、7.7 端到端的流式表述。命令、核对结果和未做逐页目视检查的边界见 `docs/course-book-v1-validation.md`；书稿定版不表示本人已学完或真实环境验收通过。
