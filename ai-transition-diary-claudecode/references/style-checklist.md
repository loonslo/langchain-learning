# Style Checklist

## Xiaohongshu Body

Goal: a beginner can follow it and learn one thing. Teach plainly — do not log a diff.

**Structure: Why → What → How → 收尾**

- Why: open with a concrete situation that shows the problem. State the minimal mechanism the example relies on first, then the breakdown. Never open with a cold example fragment that has no mechanism before it.
- What: name the problem and the fix in everyday words. Minimize jargon — only the day's unavoidable topic names belong in the body, each immediately followed by a plain-language, colloquial translation. Move precise API/class/function names into `关键知识点` and the attachment. Never leave a bare API name unexplained.
- How: walk through the real steps in plain words. The published body is PLAIN TEXT for Xiaohongshu — no Markdown support — so NEVER use code fences (```), indented multi-line code, or backticks in the body (they paste as garbled text). Keep the full code only in the Word attachment; images show framework / flow logic, and the body may at most mention a method name inline as ordinary single-line text.
- 收尾: cost / when to use / when not. No preachy essay conclusion.

**Voice**

- Conversational Chinese, short sentences, short paragraphs, one fact or action each.
- Omit `我` by default; state the action or result directly. Reject `我开始`, `我了解`, `我发现`, `我觉得`.
- No fabricated feeling or filler framing. Ban `今天踩到一个坑`, `记录一下`, `这个很妙`, `有点反直觉`, `今天的收获`, `今天的感觉`, `真正理解`, `这一步很关键`, `最大的感受是`, `下一步我想`.
- No mechanical enumeration: ban `第一招 / 第二招 / 首先 / 其次`. Connect ideas conversationally ("一种做法是…… / 还有个思路反过来……").
- No headings, bold, bullet lists, code fences, backticks, or indented code in the body — Xiaohongshu is plain text; these paste as garbled output. Body = clean continuous plain text.
- Everyday, colloquial wording; minimize jargon. Keep English API/terms out of the body except the day's unavoidable topic names.
- Write like spoken language, not an essay. Ban 成语/四字格 and performative phrasings (`一抓一个准`, `稳赚不赔`); read each line aloud and rewrite anything no one would say out loud.
- Avoid formulaic contrasts (`不是……而是……`, `不只是……更是……`) and corporate/internet jargon when plain words work.
- During rewrites, preserve all effective information; change breaks, order, tone — do not silently add or drop facts.
- Keep the body under 900 characters (Xiaohongshu caps at 1000; leave headroom). Count every visible character including punctuation, spaces, inline English/API names, and the fixed ending paragraph; line breaks don't count. If over, tighten without dropping facts. The cap covers only the pasted body, not title / cover copy / `今昨代码差异` / `关键知识点` / image plan.
- After writing, read the whole body back as a first-time reader and confirm it actually makes sense: opening sets up the mechanism before any example (no cold open mid-flow), pronouns like `这个库`/`它` have a clear antecedent, every sentence is something a person would say aloud, and the steps flow with no gap. Rewrite anything awkward, vague, or confusing — if you can't follow it yourself, it's a defect.
- End the body with exactly: `📚 本节涉及的源代码已放在附件中，可以自行下载配合理解`.

**Title**

- Lead with reader pain or benefit, not the progress number. Use a proven structure (痛点 / 对比 / 干货 Why-What-How). Avoid `DayN + 术语` titles.

## Images

- **No raw source listings in images.** Full code lives only in the Word attachment. Images show framework / flow logic: framed boxes, short labels, arrows, and flow. Exact function/API names and one short call signature are allowed only to map a node to the source; never paste a multi-line implementation.
- **Fade vs highlight:** reused stages → muted gray + `沿用` tag; today's new/changed focus → vivid accent + `今天新增` / `今天重点` tag. Drive this from the `今昨代码差异` classification.
- Standard set: cover, 定位图 (pipeline with reused faded / today highlighted), 前后对比图 (concrete before→after result), a mandatory vertical 源码结构图解, optional non-duplicate method cards, at least one mandatory horizontal code flowchart, and a final 关键知识点小词典 (glossary) card listing the day's key terms — including the precise API/class names — each with a one-line plain definition.
- **源码结构图解:** select `branch_loop`, `linear`, or `equivalence` from the actual source shape. Show the real function/API name, node roles, decision labels, branch meanings, return loops, and a compact 3-5 step explanation or mapping area. Use `equivalence` only when the shared internal structure is supported by supplied code or authoritative documentation; otherwise mark the claim `待核实`. A first-time reader should be able to trace execution from entry to exit without reading the Word attachment.
- **横版代码流程图（每次必出）:** generate at least one 1560×1075 chart from today's changed/new code. Use one chart per meaningful function or distinct execution path, normally 1–4. Draw real node/function/API names, branch labels, loops, retries, tool calls, fallbacks, and error exits when present. When the source is linear, draw the true end-to-end input → processing/API calls → output path; linear code is never a reason to omit the horizontal chart.
- Horizontal flowcharts supplement the vertical set. Omit a method card when it would repeat the same mechanism, but never omit the horizontal chart. Official order is vertical content cards except glossary → horizontal flowcharts → glossary. The contact sheet is QA-only.
- Cover: top-left chip `转行日记 · DayN`; the handle `@测试阿甲` immediately to its right (not pinned to the edge). Fill the lower area with a small idea-flow band; avoid large empty space.
- Every content image, including every horizontal flowchart: a faint `@测试阿甲` signature in a corner.
- Do not show internal labels (`图片2`, `配图方案`, `封面图`). Do not show `DayN` on content images; the cover may.
- Do not show writing or production mechanics in images, especially lines like `正文里少放 API 名`, `正文里尽量少放术语`, `这里把名字放一起`, `代码放在附件`, or `图片计划`. Image copy must describe the day's topic itself: what the terms help compare, judge, debug, remember, or use.
- Vertical 3:4, off-white grid paper, dark gray text. Distinct per-box colors (blue / teal / green) so blocks separate clearly; reserve a red/green two-color contrast for the before/after card only.
- **No white box nested inside a colored card.** Emphasize a line with a short left accent bar, not a white inner box.
- Vertically center each box's title+text block within the box; never top-align leaving a large empty lower half.
- Title: measure with the final font; one line when it fits, wrap dynamically only when it overflows; never a fixed forced newline.
- Preview every image at phone-readable scale before returning paths. Also inspect every individual horizontal flowchart at original resolution; a contact sheet alone is insufficient.

## Word Attachment

- Generate one `.docx` from today's complete Python file only; never include yesterday's source.
- Keep the DOCX beside the day's Markdown draft and PNG files in the same `dayN/` folder.
- Preserve every source line in order, including blank lines, indentation, comments, and Chinese text.
- Readable title and source filename; code-oriented font; no line numbering that changes copy/paste.
- Reopen the DOCX and compare extracted code paragraphs with the original source before delivery.
- No literal credentials. Pause for redaction approval if the source contains a password, token, API key, or `.env` value.

## Layout Bounds

- Define an outer safe frame; keep every title, card, arrow, badge, signature, and footer fully inside it.
- Keep every text bounding box inside its parent card with visible padding on all four sides; never let glyphs touch a border.
- Measure text with the library's bounding-box API before drawing. For Pillow, use `textbbox()` / `multiline_textbbox()` with the final font, spacing, and line breaks.
- Validate nested elements against their immediate parent first, then the parent against the outer frame.
- Keep the bottom dark conclusion box fully above the frame's bottom edge (include outline and rounded corners).
- Reflow long text before rendering: wrap lines, shorten the display copy without changing meaning, increase card height, or move later cards down. Reduce font size only after reflowing.
- Reject clipped, touching, or overlapping layouts even when text is technically readable.
- For scripted renderers, add coordinate assertions for known boxes where practical. A clean script exit is not visual validation.
- Preview the original-resolution image and inspect all four edges of every container before delivery.

## Final Check

- Title, body, cover copy, and images describe the same main thread.
- The image set contains at least one horizontal code flowchart and ends with a 关键知识点小词典 (glossary) card; the body reads like real speech (no essay tone, no 成语/四字格 filler).
- A reader who has not seen the code can tell what it does, why it matters, and what they can learn — from the body, not only the images.
- The main thread comes from today's changed or new code.
- Body follows Why → What → How → 收尾; every term has a plain-language translation; no banned voice phrases; no `第一招/第二招` enumeration; no cold-open example.
- Body is plain text: no code fences, backticks, or indented code anywhere; wording is colloquial with minimal jargon (only the day's unavoidable topic names kept).
- Body is under 900 characters and has been re-read end to end for coherence (clear setup, resolvable pronouns, spoken-aloud sentences, no logic gaps); anything awkward or confusing was rewritten.
- Images contain no raw multi-line code. The mandatory vertical source-logic card and mandatory horizontal flowchart trace real execution paths, and fading/highlighting matches the `今昨代码差异` classification (`沿用` gray, today's focus highlighted).
- Images contain no meta-explanations about how the post was written or why terms are placed in an image; every line is reader-facing and topic-specific.
- The before/after card shows a concrete result (e.g. 漏了 vs 命中).
- No white box nested in a colored card; emphasis uses a left accent bar. Text is vertically centered in its box.
- Cover shows `转行日记 · DayN` + `@测试阿甲`; every content image, including horizontal flowcharts, carries the faint `@测试阿甲` signature.
- Every horizontal flowchart passed the renderer audit and individual original-resolution review: title clears the top flow lane, diamond text stays inside the diamond, edge labels clear nodes/arrows, arrows do not cross unrelated nodes, and both lower panels stay within their frames.
- Every element stays inside its parent and the outer frame with visible padding; nothing clipped or touching an edge.
- When two Python files are supplied, copy and images are completed in one run unless the user requested copy review first or no images.
- The final draft contains verified image paths, the Word attachment path, and an updated completion status; the body ends with the fixed attachment notice.
