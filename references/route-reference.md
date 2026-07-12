# Route Reference

## 目的

读取 `prompt-reference.md` 产出的 `request + task_queue`，为每个 task 匹配 route。
本文件只负责 route 判断和冲突拦截，不重新拆解用户请求，不执行 py，不生成回答，不做自检。

## 输入

本文件不重新解释 prompt JSON，只消费以下字段。
本文件必须以前一阶段显式生成的 `Prompt JSON` 为输入。
如果没有可见的 `Prompt JSON`，不得继续 route 匹配，必须先回到 `references/prompt-reference.md` 生成。

| 字段 | 用途 |
|---|---|
| `request.task_shape` | 判断是否需要按队列推进 |
| `task_queue[].id` | 保持任务顺序 |
| `task_queue[].invoke.source` | 区分显式与隐式调用 |
| `task_queue[].intent.requested_mode` | 校验显式模式优先级 |
| `task_queue[].intent.task_candidate` | 判断进入哪个 route |
| `task_queue[].intent.confidence` | 低置信度时转 open route |
| `task_queue[].intent.has_mode_conflict` | 冲突拦截 |

其他字段保留给执行 reference、open route、回答组织和自检使用。

## 冲突拦截

先逐条检查 `task_queue[].intent.has_mode_conflict`。

| 条件 | 行为 |
|---|---|
| 任一 task 为 `true` | 暂停整个队列，不进入任何执行 reference |
| 全部 task 为 `false` | 继续 route 匹配 |

暂停时只提醒用户：显式指定的模式和任务内容不匹配，需要用户确认。不要自行改写用户模式继续执行。

## Route 匹配规则

按 `task_queue[].id` 的原顺序逐条匹配，不允许重排任务。

| 条件 | `route.type` | `route.reference` |
|---|---|---|
| `invoke.source = "explicit"` 且 `requested_mode` 为标准模式，`confidence = "low"` | 暂停 | 请求用户补充必要信息 |
| `task_candidate = "question_note"` | `"standard"` | `references/question-note-reference.md` |
| `task_candidate = "compare_canvas"` | `"standard"` | `references/compare-canvas-reference.md` |
| `task_candidate = "open_mode"` | `"open"` | `references/open-mode-reference.md` |
| 其他 `confidence = "low"` | `"open"` | `references/open-mode-reference.md` |

显式标准模式优先于低置信度回退：信息不足时暂停确认，不得绕开用户指定模式。隐式任务低置信度时才回退 open route。

## 输出 schema

本文件保留完整 `request`，保留 `task_queue` 名称和原顺序，只在每个 task 内追加 `route`。
读取本文件后，agent 必须显式生成一份 `Route JSON`。
`Route JSON` 是后续执行 reference 的任务清单，且不默认落盘。每个 routed task 必须保留原 task 的 `invoke + intent`，不得只保留 `id + route`。

```json
{
  "request": {
    "raw_user_request": "",
    "summary": "",
    "task_shape": "single | multi"
  },
  "task_queue": [
    {
      "id": "task_1",
      "invoke": {
        "source": "explicit | implicit",
        "raw_user_request": "",
        "summary": ""
      },
      "intent": {
        "requested_mode": "question_note | compare_canvas | open_mode | null",
        "task_candidate": "question_note | compare_canvas | open_mode",
        "confidence": "high | medium | low",
        "has_mode_conflict": false
      },
      "route": {
        "type": "standard | open",
        "reference": "references/question-note-reference.md | references/compare-canvas-reference.md | references/open-mode-reference.md"
      }
    }
  ]
}
```

## 队列推进

如果 `request.task_shape = "single"`，只执行 `task_queue[0]`。
如果 `request.task_shape = "multi"`，按 `task_queue` 顺序逐个执行。

每个 task 完成后，若生成文件产物则先进入运行检查，再进入质量检查；若没有文件产物则直接进入质量检查。
如果还有下一个 task，继续执行下一个 route。
全部 task 完成后，做一次最终回答质量检查。

## 下一步

根据当前 task 的 `route.reference` 读取对应 reference。
不要在本文件中提前读取执行 reference、open mode、自检文档或未来功能文档。
