# Tasks

状态核对：2026-09-30。当前课程采用章节和用途命名，82 个章节与 29 个项目步骤先提供文字教程，再引导阅读实现。统一入口见 `chapters/README.md`；目录与文件存在不代表本人已学完或真实环境验收通过。最新验证见 `docs/course-review-validation.md`。

## Active

- [ ] **核对旗舰项目与选修阶段验收** - 按当前章节或里程碑读取代码与测试，补运行证据；`python -m capstone.milestones --strict-evidence` 只确认所列文件存在，不等于运行验收
- [ ] **完成真实环境证据** - 依次补齐真实模型评测（含第 1–6 篇需要模型的章节，本轮审查只做了离线运行）、远端 CI、staging、容量、恢复和事故演练
- [ ] **核对第三方内容与保留的证据文件** - `面试题/` 含第三方整理内容，公开前先核对版权；`reports/` 保留了 3 个被引用的文件（见 `reports/README.md`），删除它们会让 `python -m capstone.interview_evidence --strict-evidence` 失败，并使 `capstone/docs/portfolio/` 引用的压测数字失去来源

## Waiting On

## Someday

- [ ] **求职准备** - 只从 `capstone/docs/portfolio/` 和真实报告提取可证明结论

## Done

- [x] **清理与两项遗留修复（2026-09-30）** - 删除两个旧虚拟环境（约 1.2 GB）、`debug_weather.py`、根目录三个示例文件、`artifacts/`、整个 `archive/` 和 `reports/` 的历史输出（备份在 `.tmp/deleted-backup-20260930/`），`_capstone_driver.py` 移入 `capstone/driver.py`；修复真实模型拒答仍附引用（`capstone/knowledge_base.py` 的 `is_refusal`：真实回答是“文档中没有提到。”，旧判断只认无标点的原句），真实模型回归 6 passed；旗舰 m1/step4 关键词一路加证据门槛，m1/step1、m2/step2、m5/step1 拒答时不附来源。离线测试 201 项通过，另有一次 capstone 真实模型回归 6 项通过；未运行远端服务和浏览器。证据：`docs/course-review-validation.md`

- [x] **课程全面审查与订正（2026-09-30）** - 按精简、层次、衔接、初学者视角、订正、注释、文字七项要求审查：修复共用资料与评测集断链，补依赖清单和环境自检；82 个章节与 29 个项目步骤 README 去除重复模板并改写与代码不符的说明；订正 8.7–8.10、9.1–9.7、10.2–10.4、7.7 / step2 中的实际缺陷；补充语义型注释。3.7、3.10 的示例资产已随此项补齐（3.7 读共用评测集，3.10 自带合成样本）。证据：`docs/course-review-validation.md`

- [x] **清理旧日编号内容与产物命名** - 逐项清理旧专题、课程草稿、报告/模型输出命名和失效生成脚本；PDF 书稿已更新路径并重建，99 页目录页码收敛、机械检查通过且完成页面缩略图目视检查。源码与文档扫描无旧日编号命名匹配；`.build/` 下仍有 42 个被忽略的历史生成目录，旧 pytest 缓存也残留历史测试名；当前环境拦截了清理操作，详见 `docs/project-cleanup-validation.md`。

- [x] **课程用途命名与书稿正文** - 62 个文件改为用途名称并修复导入、命令和运行标识；82 个章节及 29 个项目步骤补写问题、概念、过程、导读、练习和边界说明，目录全部先进入文字教程。174 项离线测试通过；不代表个人学完或真实模型问题已修复。证据：`docs/course-book-validation.md`

- [x] **课程章节重构与新增入门内容** - 保留物理迁移，完成统一还原工具、CI 路径、章节总地图、历史资料归档与客服阅读入口整合，补齐七个新增 / 重写位置；离线 173 项通过，真实模型回归未通过。证据：`docs/course-restructure-validation.md`。此项表示结构与内容调整，不表示个人已学完
- [x] **里程碑 7.1–7.8 内容收敛** - 旧 Demo 已删除；阶段性业务实现统一进入 `capstone/`。这一项只表示内容整理完成，不代表真实环境验收完成
