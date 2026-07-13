# Day-over-Day Comparison

## Classification

Classify code by behavior, not by line-level text alone.

- `reused`: Same responsibility and behavior as yesterday, including copied setup or helpers.
- `changed`: Existing responsibility with different parameters, control flow, API use, input, output, or result.
- `new`: Capability or processing stage absent yesterday.
- `removed`: Yesterday's behavior no longer present today.

Formatting, comments, renaming, and reordered imports do not count as a meaningful change unless they alter behavior.

## Topic Selection

1. List today's changed and new behavior.
2. Rank it by reader value and importance to the program's output.
3. Select one main thread.
4. Use reused behavior only to name the starting input.

Example:

```text
Yesterday: load document → split into chunks
Today: load document → split into chunks → embed → build FAISS → retrieve

reused: load document, split into chunks
new: embed, build FAISS, retrieve
main thread: turn existing chunks into searchable vectors
```

## Copy Rules

- Briefly name reused setup when a beginner needs it to follow today's input, so the post still stands on its own. Do not re-teach its parameters or mechanics in depth.
- Do not repeat yesterday's API definitions, parameters, pitfalls, or conclusions at length.
- Spend the body on today's changed or new actions, outputs, tests, and limits.
- Make the ending point to the next concrete code step only when supported by today's file or user notes.

## Image Rules

- No code blocks in images — images show framework / flow logic only (boxes, labels, arrows). Code lives in the body.
- This classification drives the visual fade/highlight: render `reused` stages muted gray with a `沿用` tag; render today's `new`/`changed` focus in a vivid accent with a `今天新增` / `今天重点` tag.
- Give reused code no standalone content image; when needed, show it only as a faded input node (e.g. `沿用：base_ret 检索器`).
- Reject an image plan when more than one quarter of it repeats yesterday's topic without fading it.
