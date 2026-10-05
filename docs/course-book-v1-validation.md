# PDF 书稿 v1.0 定稿验证 · 2026-09-30

把 2026-09-30 课程审查（`docs/course-review-validation.md`）修订后的项目现状同步进 PDF 书稿，并定版为 v1.0。只改 `pdf-course/content/` 下书稿内容模块与后续构建产物，不改业务代码。

## 为什么要重建

上一份 PDF 生成于 2026-09-29 16:39，早于 09-30 的课程审查。审查后仓库发生了这些与书稿直接相关的变化，旧书稿里的对应说法已经对不上：

- `archive/` 整个目录（含客服原型 `customer_support-prototype`，旧路径 `customer_support/`）被删除；阶段教程统一在 `flagship-project/`，整合实现在 `capstone/`。
- 旧日编号命名（`dayNN/`）全部改为用途命名（`chapters/partN-*/`）；还原脚本统一为 `tools/materialize.py`，`tools/materialize_enterprise_day.py` 已不存在。
- 新增课程依赖清单 `requirements-course.txt` 与环境自检 `python tools/run_chapter.py 0.1`。
- 8.7 章节说明按代码实际行为改写：旗舰前后端目前都不用流式，SSE 解析器是为以后接入流式接口准备的，且不去重、不检查流是否走完。

## 改了哪些位置

| 位置 | 原内容 | 改后 |
|---|---|---|
| `content/front.py` 封面 | 配套代码写 `customer_support / capstone / enterprise_support` | 改为 `chapters/ 各篇练习、flagship-project/ 与 capstone/，以及三个选修专项`；新增「版本：v1.0 · 2026-09-30 定稿」 |
| `content/front.py` 环境准备 | Python 3.11 或 3.12；装 `requirements.txt`；跑通最小例子 | Python 3.11 及以上（仓库 3.14、最低 3.11）；装 `requirements-course.txt`；第五步改为跑 `python tools/run_chapter.py 0.1` 自检 |
| `content/front.py` 代码地图 | 时间线图与流程图都出现 `dayNN/`、`customer_support/`、`.build/dayNN/...` | 改为 `chapters/ 各篇`、`flagship-project/ 与 capstone/`、`还原后的 .build/quality/`、`还原后的 .build/enterprise/`，并说明两个累积项目先还原再运行 |
| `content/m06.py` 代码结构交代 | `customer_support/` 是可运行的产品，两处存在「版本漂移」 | `flagship-project/` 是 8 个里程碑、29 个步骤的阶段教程，`capstone/` 是整合实现，两处分别验收；补还原与累计测试的做法 |
| `content/m06.py` 运行表 | 执行命令见 `customer_support/README.md`；常见失败写版本漂移 | 改为 `flagship-project/README.md`、前端见 里程碑 7.8 / step3；常见失败改为两处结论不混用 |
| `content/m07.py` 7.7 端到端 | 流程图与侧栏称流式输出「有明确的结束信号」，测试关键是顺序与完整性 | 按 8.7 实际行为改写：真实 HTTP 响应按契约校验、SSE 解析器为将来流式准备、不去重不查结尾、截断检测是调用方的责任 |
| `content/m07.py` 7.9 flaky 举例 | 举例绑定「结束信号到得比断言晚」 | 改为通用的外部条件（响应快慢、执行顺序、瞬时状态），不再对应一个不存在的实现 |
| `content/m07.py` 自检清单 | 「SSE 测试要检查的顺序、完整性与结束信号」 | 改为「SSE 解析的边界：拼顺序、不去重、不查结尾，截断检测留给调用方」 |
| `content/m08.py` 代码交代 | `enterprise_support`（由 `tools/materialize_enterprise_day.py` 还原） | 改为 `chapters/part9-enterprise-infra-optional/9.1-9.4`，由 `tools/materialize.py enterprise <chapter>` 还原 |
| `content/m08.py`、`m09.py`、`m10.py` 产出物 | 「…… 的 `enterprise-support/`」 | 改为「由 `tools/materialize.py` 还原后运行」 |

复扫确认：书稿源码中 `customer_support`、`dayNN`、`materialize_enterprise_day`、`enterprise_support`、`版本漂移`、`3.11 或 3.12` 均无匹配。`m05.py` 里 Docker 分层提到 `requirements.txt` 未改——根目录 `Dockerfile` 第 13–14 行装的确实是 `requirements.txt`，说法成立。

## 实际验证

Windows，项目虚拟环境 `.venv`（Python 3.14.4）。渲染用本机 Chrome（render.py 的 `channel="chrome"`），未下载 Chromium。

| 检查 | 命令 | 结果 |
|---|---|---|
| 组装 HTML | `cd pdf-course && python build.py` | 输出 `out/tutorial.html`，405 KB，11 个章节位 |
| 渲染 PDF（含目录回填） | `python assets/render.py build.py out/tutorial.html "out/AI应用开发 零基础到交付.pdf"` | 第 1 轮回填 12 个锚点，第 2 轮页码收敛；共 100 页、120 张图 |
| 机械与几何自检 | 同上（`--check-only` 复跑一次） | 通过；无留白不足、无整页空白、无残留占位符，中文标点后残留空格 0 处 |
| 书签与目录跳转 | 同上 | 书签 97 条（一级 12 条：序章 + 11 章），目录页 12 个跳转链接；章首页页码与书签一致 |
| 成品文本层核对 | PyMuPDF 取全文后去空白比对 | `customer_support` 0 处、`dayNN` 0 处；含 `v1.0` 1 处、`requirements-course.txt` 2 处、`tools/run_chapter.py 0.1` 1 处、`flagship-project/README.md` 1 处 |

构建环境变化：`.venv` 原来没有渲染依赖，本次安装了 `playwright 1.63.0`、`pymupdf 1.28.2`（`playwright` 用系统 Chrome，不下载浏览器）。这两个包是构建书稿用的，不是课程依赖，未写入 `requirements-course.txt`。

## 未验证与限制

- 只做了构建检查、机械自检、几何自检和成品文本层核对；**没有**按 render.py 列出的 9 项逐页渲染成 PNG 用眼睛看，版面细节（列缝粘连、标注被切、跨页页眉）未经目视确认。
- 本次没有重跑课程测试，也没有调用真实模型；书稿内容与代码的一致性靠逐处比对章节 README 与目录结构得出，真实运行证据见 `docs/course-review-validation.md`。
- 09-30 审查中未验证的边界继续有效：第 1–6 篇真实模型运行、远端 CI / staging、第 9–10 篇真实 PostgreSQL / Redis / Qdrant / vLLM、浏览器端到端均未运行。
- 书稿定版为 v1.0 只表示内容已与当前仓库对齐并通过构建自检，**不代表本人已学完或真实环境验收通过**。

## 版式修订（同日第二轮，用户反馈 5 项）

| 反馈 | 改动 | 落点 |
|---|---|---|
| 图编号徽章太抢眼 | 实心深青圆 → 空心细描边圆 + 灰色小数字（T1 7.5pt） | `extra.css` `.fignum` |
| 字号标准统一为 6 级 | 定义 T1–T6 字阶令牌（7.5/9/10.5/14/25/40pt），base.css 与 extra.css 全部组件挂到令牌；h3 15→14pt、figtitle 11→9pt、caption 7.8→7.5pt、页眉 6.8→7.5pt 等 | `base.css` `:root`、`extra.css` |
| 序章 8 词递进图太小 | `.figbody svg` 76mm 封顶把纵向图压成邮票；`FIG()` 按 viewBox 纵横比 ≥0.62 自动加 `.fig-tall`，封顶放宽 150mm（全书 3 张命中） | `comp.py`、`extra.css` |
| 章首太拥挤 | `.chead` 顶部留白 4→15mm、与正文间距 6→9mm；h3/h4/p/图 上下间距同步加大 | `extra.css` |
| 去掉测试工程师背景 | 序章改为「作者从零开始学」；第 7 章钩子改为通用表述；成品文本层 `测试工程师`/`转行` 均 0 处 | `front.py`、`m07.py` |

顺带修复：环境准备流程图中 `requirements-course.txt` 被 SVG 按字宽硬折行，图内文字改为「根目录的依赖清单，一条命令装齐」。

复渲染结果：106 页（章首留白加大后页数 +6）、120 张图、机械自检通过、目录页码收敛、书签 97 条。逐页 PNG 抽查了第 4 页（递进图 + 徽章 + 断词）与第 11 页（第 1 章章首留白），均确认符合预期；其余页面未逐页目视。
