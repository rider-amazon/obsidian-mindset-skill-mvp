---
name: obsidian-mindset
description: Build Obsidian learning artifacts from user questions. Use when the user wants to learn concepts, decompose learning requests into task queues, create question notes, generate concept comparison Canvas files, or route learning tasks through standard and open workflows.
---

# Obsidian Mindset MVP

## 适用范围

只处理两类稳定能力：学习问题沉淀成问题页，或两个概念沉淀成对比图。默认中文、结构优先、不扩写无关内容，不把未实现能力写入当前流程。

## 强制原则

只按渐进式披露读取文档。`SKILL.md` 只做总入口，不展开命令细节、模式细节、自检细节，也不承载 py 参数说明。
每个阶段必须先显式产出对应中间 JSON，再进入下一阶段；中间 JSON 不默认落盘。

## 主流程

| 步骤 | 读取文件 |
|---|---|
| 1 | `references/prompt-reference.md` |
| 2 | `references/route-reference.md` |
| 3a | `references/question-note-reference.md` |
| 3b | `references/compare-canvas-reference.md` |
| 3c | `references/open-mode-reference.md` |
| 4 | `references/runtime-check.md` |
| 5 | `references/quality-check.md` |

## 文档索引

`question_note` 与 `compare_canvas` 是当前仅有标准能力。复杂请求先拆成 `task_queue`，再由 `references/route-reference.md` 逐条匹配 route。
