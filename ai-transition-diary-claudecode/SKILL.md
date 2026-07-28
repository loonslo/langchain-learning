---
name: ai-transition-diary
description: Compare today's and the previous day's AI or LangChain Python files, then turn only today's new or changed work into ajar's Chinese Xiaohongshu "转行日记" post. Teach a beginner step by step in everyday Chinese, with full code only in the Word attachment. Generate vertical study-note cards plus at least one mandatory horizontal code flowchart on every run; unfold the real changed/new function or execution path with nodes, conditions, branches, loops, error exits, legend, and numbered explanation. Fade reused parts, highlight today's focus, and always end with a 关键知识点 summary card. Produce a Word attachment of today's source code in one uninterrupted workflow. Use when the user provides two consecutive Python files and asks to write, rewrite, continue, compare, illustrate, or add a code-flow explanation to a 转行日记. Append the fixed source-code attachment notice, generate the .docx and images automatically, and do not wait for copy approval unless the user explicitly requests a copy-only result.
---

# 转行日记 (AI Transition Diary)

Recurring AI-learning series for ajar (Xiaohongshu account **@测试阿甲**, series name **转行日记**).

Core goal: a complete beginner who has never seen the code should finish the post able to say "I understand what today's thing does, why it matters, and roughly how it works." Optimize every choice for that, not for logging what changed since yesterday.

Treat today's and the previous day's code as the source of truth. Compare them to decide what is new vs reused, but write the post so it stands on its own. When two Python files are supplied, complete copy, Word attachment, images, verification, and draft updates in one run. Pause after copy only when the user explicitly asks to review copy first or asks for no images/attachment.

Canonical style and final QA details live in [references/style-checklist.md](references/style-checklist.md). Keep this file focused on workflow, required artifacts, and hard boundaries; when wording details appear in both places, the checklist is the tie-breaker for drafting and visual QA.

Horizontal code-flow rules live in [references/code-flowchart-guide.md](references/code-flowchart-guide.md). Read that guide on every run. These horizontal diagrams are mandatory deliverables, not an optional enhancement for unusually complex code.

## Load Local Context

1. Locate the `自媒体` vault under the current Obsidian workspace.
2. Read the workspace root `AGENTS.md`, `自媒体/AGENTS.md`, and `自媒体/index.md` before writing.
3. Identify today's code and the previous day's code from the user's labels, filenames, or dates. Do not guess when roles are ambiguous.
4. Read both files in full. If the previous day's file is missing and cannot be located confidently, request it before drafting.
5. Read [references/day-over-day-comparison.md](references/day-over-day-comparison.md) and classify the code before choosing the day's main thread.
6. Inspect the latest one or two 转行日记 drafts and renderers only when needed for series continuity.
7. Read [references/style-checklist.md](references/style-checklist.md) before drafting or rendering.
8. Read [references/code-flowchart-guide.md](references/code-flowchart-guide.md) and inspect [scripts/render_flowchart_template.py](scripts/render_flowchart_template.py) before planning images.

## Compare The Two Days

1. Map both files by function, class, processing stage, important API, input, and output.
2. Classify each relevant part as `reused`, `changed`, `new`, or `removed`. The basis is the actual code diff against the **most recently published day's code**, not "what I assume the reader knows" and not strictly calendar-yesterday.
3. Treat copied setup, imports, loaders, splitters, shared helpers, and unchanged parameters as `reused`.
4. Choose the main thread only from `changed` or `new` behavior. Use `removed` only when the removal changes the result.
5. Record the classification in the saved draft's `今昨代码差异` section (what is reused / changed / new), so it is checkable and the user can correct a mislabel. This same classification drives image fading vs highlighting (see Images).

## Output Layout

1. Keep the series under `自媒体/output/ai-transition-diary/`.
2. One folder per day: `自媒体/output/ai-transition-diary/dayN/`.
3. Store that day's publishable Markdown draft, source-code DOCX, all PNG images, and the deterministic renderer in the same `dayN/` folder. Do not place the draft at `output/` root or images in a separate folder.
4. Filename pattern inside the day folder, for example:

```text
自媒体/output/ai-transition-diary/day14/
├── 20260624-AI转型日记Day14小红书发布稿.md
├── AI-Day14-source-code.docx
├── 2026-06-24-AI-Day14-01-cover.png
├── 2026-06-24-AI-Day14-02-pipeline.png
├── 2026-06-24-AI-Day14-03-compare.png
├── 2026-06-24-AI-Day14-04-source-logic.png
├── 2026-06-24-AI-Day14-05-<method-a>.png
├── 2026-06-24-AI-Day14-06-<method-b>.png
├── 2026-06-24-AI-Day14-flow-1-<function-a>.png
├── 2026-06-24-AI-Day14-flow-contact-sheet.png
├── 2026-06-24-AI-Day14-07-glossary.png
├── render_day14_cards.py
└── render_day14_flowcharts.py
```

5. Reuse the same `dayN/` folder when revising. Do not create a second folder for revisions.

## Draft Template

Save the Markdown draft with this section order so revisions, image rendering, and final checks are deterministic:

```md
# DayN 发布稿

## 标题备选

## 封面文案

## 今昨代码差异

## 关键知识点

## 小红书正文

## Word 附件

## 图片路径

## 图片计划

## 状态
```

Keep the published body only under `## 小红书正文`; everything else is planning or delivery metadata for ajar.

## Write The Copy

Audience: a beginner following the series casually. The job is to teach, not to log a diff.

**Structure — follow Why → What → How → 收尾 (干货类结构):**

1. In private working notes first, explain today's `changed`/`new` code: purpose, input, output, problem solved; runtime order; the 3-5 APIs/functions/parameters worth knowing; 1-2 pitfalls or next steps.
2. Pick one main thread from a concrete new capability or behavioral change — never reused setup or a broad AI topic.
3. Write the publishable body in this order:
   - **Why** — open with a concrete situation the reader can picture, that shows the problem. State the minimal mechanism the example depends on first (e.g. "RAG 的流程是:提问 → 检索 → 回答"), then the breakdown. An example must never be a cold-open fragment with no mechanism before it.
   - **What** — name the problem and the method(s) that fix it in everyday words. Keep jargon to a minimum: only the day's unavoidable topic names (e.g. the method names that also appear on the cover, like `Multi-Query` / `HyDE`) belong in the body, and each must be immediately followed by a plain-language, colloquial translation of what it does. Move precise API/class/function names (`MultiQueryRetriever`, `StrOutputParser`, parameters, etc.) into the `关键知识点` section and the Word attachment, not the body. Never leave a bare API name unexplained.
   - **How** — walk through the actual steps in plain words. The published body is PLAIN TEXT for Xiaohongshu, which does not support Markdown: code fences (```), indented multi-line code, and backticks all paste as garbled text. Do NOT put code blocks in the body — not even a single fenced or indented line. The full code lives ONLY in the Word attachment; images show framework / flow logic, not source listings. When the source has code worth explaining, do not paste it: abbreviate it into a one-line plain-language description (e.g. describe `prompt | llm | parser` as "把提示、模型、解析三段用竖线接成一条链"; describe `chain.stream()` as "把一次性返回换成边生成边返回"). At most mention one or two bare method names inline as ordinary single-line text (no fence, no backtick); otherwise skip names entirely and just say what each step does.
   - **收尾** — what it costs / when to use it / when not to. No neat-essay moral.

**Voice rules (quick guardrails — use `references/style-checklist.md` as the canonical full checklist):**

- Natural spoken Chinese, short paragraphs, one fact or action each.
- Omit `我` by default; state the action or result directly. Never use `我开始`, `我了解`, `我发现`, `我觉得`.
- No fabricated feeling or filler framing: ban `今天踩到一个坑`, `记录一下`, `这个很妙`, `有点反直觉`, `今天的收获`, `最大的感受是`, and similar narrator padding.
- No mechanical enumeration like `第一招 / 第二招 / 首先 / 其次`. Connect methods conversationally ("一种做法是…… / 还有个思路反过来……").
- No headings, bold, bullet lists, code fences, backticks, or indented code inside the body — Xiaohongshu is plain text and any of these paste as garbled output. The body must be clean, continuous plain text.
- Use everyday, colloquial language, like talking to a friend. Minimize jargon: prefer plain words over 专有名词, and beyond the day's unavoidable topic names keep English API/terms out of the body (they belong in `关键知识点` and the attachment).
- Write the body the way people actually talk, not like an essay or written prose. Avoid 成语 / 四字格 and clever, performative phrasings (e.g. `一抓一个准`, `稳赚不赔`, `一气呵成`); if a plain spoken phrase works, use it. Read each sentence aloud — if no one would say it in conversation, rewrite it.
- Avoid formulaic contrasts (`不是……而是……`) and corporate/internet jargon when plain words work.
- Length cap: the published Xiaohongshu body must stay under 900 characters (Xiaohongshu's hard limit is 1000; leave headroom). Count every visible character of the body including punctuation, spaces, inline English/API names, and the fixed ending paragraph; line breaks do not count. If over, tighten — cut filler connectors and repeated explanations — without dropping any of the day's facts. This cap applies only to the body pasted to Xiaohongshu, not to the title, cover copy, `今昨代码差异`, `关键知识点`, or the image plan.
- End the body with exactly this standalone paragraph: `📚 本节涉及的源代码已放在附件中，可以自行下载配合理解`.

**Title:** lead with the reader's pain or benefit, not the progress number. Use a proven Xiaohongshu structure (痛点 / 对比 / 干货 Why-What-How). Examples: `RAG 总搜不到答案?可能是问题问得太短`. Avoid titles that only state `DayN + 术语`.

4. Self-review the body before moving on — do not ship the first draft unread. Read the whole body top to bottom as if seeing it for the first time, and check it actually makes sense: the opening sets up the mechanism before any example (no cold open mid-flow like starting at "检索这步" without first saying what RAG does); every sentence is something a person would actually say aloud; references like "这个库" / "它" have a clear antecedent; the logic flows step to step with no gap a beginner would stumble on; and it is under the 900-character cap. Fix anything awkward, vague, or out of order. If a sentence is confusing or you cannot follow it yourself, rewrite it — an unreadable body is a defect, not a stylistic choice.
5. Save the draft in `dayN/` using the fixed Draft Template above: title options, cover copy, `今昨代码差异` (the reused/new classification), `关键知识点`, the Xiaohongshu body, Word attachment path, image paths, image plan, and status. Weave the strongest 3-5 knowledge points naturally into the body; do not let them live only in the `关键知识点` list or in images.
6. Continue directly to the Word attachment and images without requesting approval, unless the user asked for copy review only or no images/attachment.
7. Update `自媒体/index.md` when listing/status changes; append `自媒体/log.md` and the current `自媒体/daily/YYYY-MM-DD.md`.

## Generate And Verify The Word Attachment

1. Convert today's complete Python file (never yesterday's) into `AI-DayN-source-code.docx` beside the draft. No date prefix on the DOCX filename.
2. Use [scripts/python_to_docx.py](scripts/python_to_docx.py) so the attachment is a valid `.docx` with title, source filename, and the full source in line-preserving code paragraphs.

```text
python scripts/python_to_docx.py --input <today.py> --output <dayN/AI-DayN-source-code.docx> --title "转行日记 DayN 源代码"
```

3. The script's credential scan, package verification, and line-by-line verification are mandatory. Reject the attachment if the source appears to contain literal credentials, the DOCX cannot be reopened, parts are missing, or extracted lines differ from today's source.
4. Never copy literal passwords, tokens, API keys, or `.env` values into the attachment. If a credential is embedded, stop and ask whether to create a redacted attachment; do not alter the original Python file.
5. Add the absolute DOCX path to the draft's `Word 附件` section and return a clickable path.

## Generate And Verify Images

Images carry the **big-picture framework / flow logic only**. Their job is to help understanding, not to reproduce code.

1. Reload the saved draft and image plan from disk. Re-run the day-over-day comparison.
2. **No raw source listings in images.** Full code belongs only in the Word attachment. Images use framed boxes, short labels, arrows, and flow. Exact function/API names and one short call signature are allowed when they help the reader map a diagram node back to the source; never paste a multi-line implementation.
3. **Fade vs highlight (drives "what's different each day"):** render `reused` stages in muted gray with a small `沿用` tag; render today's `new`/`changed` focus in a vivid accent color with a `今天新增` / `今天重点` tag. Drive this strictly from the `今昨代码差异` classification.
4. **Standard vertical image set (the last official image is mandatory — never skip it):**
   - **Cover** — title (reader pain/benefit), 1-2 line subtitle, and a small horizontal idea-flow band to fill the lower area. Top-left: series chip `转行日记 · DayN`; immediately to its right (not pinned to the edge): the handle `@测试阿甲`.
   - **定位图** — the full pipeline with reused stages faded and today's new layer highlighted ("今天补在哪").
   - **前后对比图** — a before/after that shows a concrete result (e.g. 漏了 vs 命中). This is the only card that may use a two-color red/green contrast, because the contrast is the point.
   - **源码结构图解（mandatory）** — unfold one real function, class, or wrapper from today's changed/new code into a beginner-readable execution diagram. Choose the form from the source, not from aesthetics:
     - `branch_loop`: START → main node → condition diamond → branch/end, with the return arrow drawn when execution loops.
     - `linear`: input → 2-5 processing nodes → output when there is no real branch.
     - `equivalence`: two outer call styles at the top, an equals/"外层写法不同" bridge, then their shared internal flow and a small mapping/difference area when today's lesson is a manual implementation versus a wrapper/helper.
     - Title the card with the actual function/API under explanation (for example `build_handmade() 流程图`), label node roles in plain Chinese, put `是/否` or the real branch meaning beside outgoing arrows, and explain any loop/result return beside the arrow. Add a compact 3-5 step explanation or mapping area below the diagram and finish with one plain-language conclusion. Do not invent hidden framework internals: if equivalence is inferred rather than visible in supplied code or authoritative documentation, mark it `待核实` or use `linear`/`branch_loop` instead.
   - **Optional method cards** — use a 3-step framework (no code) only when it teaches a changed/new method that is not already explained by a horizontal flowchart. Never duplicate the same mechanism in both formats.
   - **关键知识点总结（mandatory final official image）** — ALWAYS end the complete official image set, after the horizontal flowcharts, with one summary card that collects the day's `关键知识点`: list the day's key terms (including the precise API/class names like `BM25` / `EnsembleRetriever`) each with a one-line plain-language definition. This card mirrors the draft's `关键知识点` section, and is where the exact names live as an image since the body stays jargon-light. Title it like a summary ("关键知识点" / "本节小结" / "知识点小词典"), not `DayN`. If the body had to drop code/API detail to stay plain text, this card is where that detail is preserved.
5. **Mandatory horizontal code flowcharts:** render at least one 1560×1075 horizontal diagram on every run. Pick each chart from today's `changed`/`new` code. Use one chart per meaningful function or distinct execution path, normally 1–4 charts. If the code has branches, loops, retries, tool calls, fallbacks, or error exits, draw them explicitly. If it is purely linear, draw the real end-to-end input → processing/API calls → output path instead. Do not create separate charts for trivial setters, getters, imports, or unchanged setup. Follow [references/code-flowchart-guide.md](references/code-flowchart-guide.md).
6. Every content image, including every horizontal flowchart, carries a faint `@测试阿甲` signature in a corner (so reshared screenshots keep the ID). Do not show internal labels like `图片2`, `配图方案`, `封面图`; do not show `DayN` on content images (the cover may).
7. Image text must stay inside the reader-facing topic. Do not mention production or writing mechanics such as `正文里少放 API 名`, `正文里尽量少放术语`, `这里把名字放一起`, `代码放在附件`, `图片计划`, or similar meta-explanations. Replace them with a topic-specific reader benefit, e.g. what the terms help judge, compare, debug, or remember.
8. **Style:** vertical cards use 3:4; horizontal flowcharts use 1560×1075. Both use off-white paper, dark gray text, and distinct per-box colors. Reserve red/green for the before/after card; keep a single calm accent elsewhere.
9. **No white box nested inside a colored card.** For emphasis inside a colored card, use a short left accent bar before the line, not a white inner box.
10. **Vertical centering:** center each box's title+text block within the box height; never top-align text leaving a large empty lower half.
11. Use the deterministic vertical renderer [scripts/render_cards_template.py](scripts/render_cards_template.py): copy it into `dayN/`, set `DAY`/`DATE`/`OUTDIR`, and edit only the top `D` content dict (cover, pipeline, compare, source_logic, methods, glossary) — palette, fading, signature, bounds audit, and layout are already fixed. Set `source_logic.mode` to `branch_loop`, `linear`, or `equivalence` to match the real code. Run `OUTDIR=<dayN> python render_cards_template.py`. Each node's `kind` controls fading: `"now"` = today's highlight (+`今天重点`/`今天新增` tag), `"fade"` = reused gray (+`沿用` tag), `"plain"` = neutral.
12. Use the deterministic horizontal renderer [scripts/render_flowchart_template.py](scripts/render_flowchart_template.py): copy it into `dayN/` as `render_dayN_flowcharts.py`, set `DAY`/`DATE`, edit only `SCENES`, and run it with `OUTDIR=<dayN>`. The renderer must fail closed when its bounds/collision audit detects a bad layout; fix the scene data and rerun rather than suppressing the audit.
13. Title wrapping: measure with the final font; keep a short title on one line, wrap dynamically only when it overflows. Never force a two-line title with a fixed newline.
14. **Collision-free diagram layout is mandatory.** Before drawing, reserve separate lanes for node boxes, straight-through arrows, branch/loop arrows, and edge labels. Attach arrow endpoints to node boundaries; never let an arrow shaft or arrowhead pass through a node, node text, label, badge, or explanation panel. Keep at least 12 px between arrowheads and unrelated text.
15. Measure the final-font bounding box of every node title, subtitle, edge label, badge, and note. For diamonds, validate text against the diamond's narrowing interior, not merely its rectangular bounding box. Expand each text box by at least 8 px and reject the render if it intersects another text box, any unrelated node border, arrow shaft, arrowhead, or the outer safe frame. Text intentionally contained by its own node is the only allowed text/node intersection.
16. Give every edge label a clear gap from its arrow and neighboring nodes. If the open corridor cannot hold the full label with padding, shorten the label, route the edge through a wider lane, or move the explanation into the numbered panel below; never squeeze text across a border or arrow. Prefer a short `是` / `否` beside a crowded branch and keep the full meaning in the explanation panel.
17. Run both a bounds audit and a collision audit before saving each image. Preview every official image at original size, including every individual horizontal flowchart and the densest branch/loop areas; the flowchart contact sheet is a navigation aid, not a substitute for original-resolution QA. Reject and re-render until there are zero title/node, text/border, text/arrow, arrow/node, text/text, badge/text, and lower-panel overflows; also check that fading/highlighting matches the classification and the signature is present and subtle.
18. List official image paths in this order: vertical content cards except the glossary → horizontal flowcharts → glossary last. The contact sheet is QA-only and is not part of the publishable image order.
19. Write final absolute image paths back into the draft and update status. Append `log.md` and the daily note; update `index.md` if status changes.
20. Return clickable paths to the Word attachment and all official images. Do not publish or upload.

## Run Checklist

Use this checklist every time two Python files are supplied:

1. Read vault context (`AGENTS.md`, `自媒体/AGENTS.md`, `自媒体/index.md`) and required references.
2. Identify and read today's code and the most recently published previous code in full.
3. Classify `reused` / `changed` / `new` / `removed`; choose one main thread from changed/new behavior.
4. Save the draft with the fixed Draft Template, including `今昨代码差异`, `关键知识点`, body, and image plan.
5. Generate and verify the DOCX from today's complete source only; stop on literal credential detection.
6. Render cover, pipeline, compare, the mandatory vertical source-logic diagram, any non-duplicate method cards, at least one mandatory horizontal code flowchart, and the final glossary card. Run bounds and collision audits, then visually preview every PNG at original size. Do not deliver any image with text/border/arrow overlap.
7. Write final absolute DOCX/image paths back into the draft, update status, append `log.md` and the daily note, update `index.md` if status changed.
8. Return clickable paths; do not publish or upload.

## Boundaries

- Never invent code behavior not supported by the supplied files.
- Mark uncertain facts as `待核实`; browse only when current external facts are necessary.
- Never publish, upload, message, delete, bulk-rename, or alter credentials without explicit permission.
- Keep every generated vault artifact inside `自媒体/output/`, except required updates to `index.md`, `log.md`, and `daily/`.
