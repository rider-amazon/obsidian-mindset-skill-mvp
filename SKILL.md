---
name: obsidian-mindset
description: Build and update Obsidian learning artifacts from user questions. Use when the user wants to learn concepts, decompose requests into task queues, create or revise question notes, generate or adjust concept comparison Canvas files, compress or overwrite a recent standard artifact, convert learning outputs, or route learning tasks through standard and open workflows.
---

# Obsidian Mindset

## 适用范围

只处理两类稳定文件能力：学习问题沉淀成问题页，或两个概念沉淀成对比图。支持继续修改这两类标准产物。默认中文、结构优先、不扩写无关内容，不把未实现能力写入当前流程。

## 强制原则

只按渐进式披露读取文档。`SKILL.md` 只做总入口，不展开命令细节、route 细节、自检细节，也不承载 py 参数说明。
每个阶段必须先显式产出对应中间 JSON，再进入下一阶段；中间 JSON 不默认落盘。

## 入口分流

| 当前 task | 首先读取 |
|---|---|
| 新建产物或语言回答 | `references/prompt-reference.md` |
| 修改、压缩、覆盖或保留已有文件 | `references/update-prompt-reference.md` |

一个请求同时包含新建与修改时，按独立可验收目标拆分，分别读取对应 Prompt reference，再按用户原顺序合并为同一 `task_queue`。

## 主流程

| 步骤 | 读取文件 |
|---|---|
| 1a | `references/prompt-reference.md` |
| 1b | `references/update-prompt-reference.md` |
| 2 | `references/route-reference.md` |
| 3a | `references/question-note/reference.md`，再按 `operation.action` 只读取对应子文档 |
| 3b | `references/compare-canvas/reference.md`，再按 `operation.action` 只读取对应子文档 |
| 3c | `references/open-route-reference.md` |
| 4 | 文件产物读取 `references/runtime-check.md` |
| 5 | 存在文件回执时读取 `references/text-output-reference.md`；纯语言回答跳过 |
| 6 | 全部 task 完成后读取 `references/quality-check.md` |

## 文档索引

`question_note` 与 `compare_canvas` 是当前仅有标准文件能力。open route 可以直接回答；涉及文件时只允许新建。两份 Prompt reference 使用相同 task schema，并在 `request.vault_root` 保存本次请求唯一、已确认的 Vault；再由 `references/route-reference.md` 逐条匹配执行 reference。
