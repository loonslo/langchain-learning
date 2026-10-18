# 课程 v2 全量结构修复验证 · 2026-10-18

按 `docs/curriculum-v2.md` 做第一阶段“全量结构修复”：给 82 章和 29 个旗舰步骤加 v2 路径标签，修跨篇顺序与前置语义，检查全量 Markdown 断链。**没有重排目录，也没有把其余 77 章 gate 化。**

## 范围与结果

| 项目 | 数量 | 结果 |
|---|---|---|
| 章节 README | 82 | 全部写入 `v2 路径` |
| 旗舰步骤 README | 29 | 全部写入 `v2 路径` |
| 合计 | 111 | `apply_v2_map.py --check`：unchanged=111 |
| Markdown 文件链接检查 | 261 | 断链 0 |

## 新增的映射与工具

- `docs/course-v2-map.json`：82 章的阶段、核心/选做/核心阅读、备注；这是单一映射源。
- `tools/apply_v2_map.py`：幂等写入/替换 `v2 路径` 行；`--check` 只报告，`--apply` 才写。
- `tools/check_course_links.py`：检查课程 Markdown 的相对链接，跳过外链、锚点和代码块。

每个 README 的标签形如：

```text
- **v2 路径**：L1.6 / 核心（Gate；手写 Harness）
- **v2 路径**：L4.11 / 核心（建议在 4.10 后学；规则可先当预习）
- **v2 路径**：L9 / 选做（学习前置无；运行累积代码前先还原 8.10）
```

## 修掉的顺序问题

| 位置 | 原问题 | 现在的处理 |
|---|---|---|
| 3.9 Agent 轨迹评测 | 在 Agent 之前学，容易只记住规则 | 保留目录与编号；README/总地图标明“建议在 4.10/4.11 后学”，合成轨迹可先预习 |
| 5.1 / 5.2 | 5.1 写“前置 5.2”，而 5.2 是下一章 | 5.1 的 gate 并入最小超时/重试；5.2 改为“通过 5.1 gate 后读，展开生产细节” |
| 9.1 | 前置写 8.10（其累积代码），像必学前置 | 改为“学习前置无；运行累积代码前先还原 8.10” |
| 10.1 | 前置写 9.12（其累积代码） | 改为“学习前置无；运行累积代码前先还原 9.12” |
| 根 README | 链接到已删除的 `archive/README.md` | 删除失效链接；全量检查后 0 断链 |

## 导航更新

- `chapters/README.md` 增加“v2 路径速查”和四条跨篇顺序说明（2.4/2.5、3.9、5.2、9.1/10.1）。
- 根 `README.md` 指向速查表；课程结构表仍保留原篇号。
- 每个旗舰步骤 README 的 `v2 路径` 指向对应 L 阶段，方便把 29 步映射到 12 周路径。

## 实际执行

```text
python tools/apply_v2_map.py --apply
合计：111 个 README；inserted=111 updated=0 unchanged=0

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python tools/check_course_links.py
检查 261 个 Markdown 文件；断链 0 个。

python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python -m ruff check tools/apply_v2_map.py tools/check_course_links.py
All checks passed!
```

## 未验证

- **没有逐章重读正文**：这次修的是路径、顺序、链接和标签；每章代码与说明是否仍然一致，需要后续逐章审查。
- **没有物理移动 3.9**：保留目录和编号是为了不破坏大量旧链接；v2 顺序通过标签表达。
- **没有把其余 77 章 gate 化**：只有 L1.6、L2.9、L3.4、L4.4、L5.1 五个样板已改；其余仍是阅读/运行型。
- **没有验证个人学习进度**：标签存在不等于学过，更不等于真实环境验收。

## 复现

```bash
python tools/apply_v2_map.py --check
python tools/check_course_links.py
python -m pytest tools chapters/test_new_lessons.py -q
```

## 边界

- `docs/course-v2-map.json` 是导航映射，不是学习完成记录。
- 章节号与目录仍是旧编号；`Lx` 只表示 v2 路径位置，不代表重命名。
- 下一阶段才是分批 gate 化；不要从这次结构修复推断全部章节已闭卷化。
