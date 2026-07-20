# Route Reference

## 目的

读取 Prompt JSON 或 Update Prompt JSON，为每个 task 匹配 route。本文件只负责 route 判断、冲突计算和阻断，不重新拆解请求，不执行 py，不生成回答，不做自检。

## 输入

两份 Prompt reference 使用同一 task schema。Route 只消费以下字段，并原样保留其他上下文。

| 字段 | 用途 |
|---|---|
| `request.task_shape` | 判断队列推进方式 |
| `task_queue[].id` | 保持任务顺序 |
| `task_queue[].operation` | 区分新建、回答、更新与保留 |
| `task_queue[].intent.request_route` | 判断用户是否显式指定入口 |
| `task_queue[].intent.task_candidate` | 匹配能力 reference |
| `task_queue[].intent.confidence` | 判断是否需要阻断或回退 |

如果没有前一阶段显式生成的 Prompt JSON 或 Update Prompt JSON，不得继续 route 匹配。

## 冲突计算

`task_candidate` 已由对应 Prompt reference 依据标准入口契约生成。Route 按以下规则计算，不再接收 `has_route_conflict` 字段。

| 条件 | 是否冲突 |
|---|---|
| `request_route = null` | 否 |
| `request_route = open_route` | 否 |
| `request_route` 是标准入口且等于 `task_candidate` | 否 |
| `request_route` 是标准入口且不等于 `task_candidate` | 是 |

任一 task 发生冲突时，将该 task 标记为 `blocked`，暂停整个队列，提醒用户显式入口与任务内容或目标文件不匹配。不得自行改写入口继续执行。

## Route 匹配规则

按 `task_queue[].id` 的原顺序逐条匹配，不允许重排。

| 条件 | `route.type` | `route.reference` |
|---|---|---|
| 已计算出入口冲突 | `blocked` | `null` |
| 显式标准入口且 `confidence = low` | `blocked` | `null` |
| `action = update` 且目标不唯一或 `confidence = low` | `blocked` | `null` |
| `action = update` 且 `request_route = open_route` | `blocked` | `null` |
| `action = update` 且 `task_candidate = open_route` | `blocked` | `null` |
| `action = keep` 且目标唯一 | `no_op` | `references/text-output-reference.md` |
| 隐式新建或回答任务且 `confidence = low` | `open` | `references/open-route-reference.md` |
| `task_candidate = question_note` | `standard` | `references/question-note-reference.md` |
| `task_candidate = compare_canvas` | `standard` | `references/compare-canvas-reference.md` |
| `action = create` 或 `answer`，且 `task_candidate = open_route` | `open` | `references/open-route-reference.md` |

open route 只允许 `create` 或 `answer`。更新已有文件不得因为复杂、低置信度或不属于标准能力而回退 open route。

## 输出 schema

保留完整 `request` 和原顺序 `task_queue`，只在每个 task 内追加 `route`。`reason` 在 `blocked` 时必须说明阻断原因，其他类型可写 `null`。

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
        "raw_user_request": "",
        "summary": ""
      },
      "operation": {
        "action": "create | answer | update | keep",
        "target_path": "absolute path | null",
        "overwrite_authorized": false,
        "overwrite_reason": null
      },
      "intent": {
        "request_route": "question_note | compare_canvas | open_route | null",
        "task_candidate": "question_note | compare_canvas | open_route",
        "confidence": "high | medium | low"
      },
      "route": {
        "type": "standard | open | no_op | blocked",
        "reference": "reference path | null",
        "reason": null
      }
    }
  ]
}
```

## 队列推进

`single` 只执行一个 task；`multi` 按原顺序执行。任一 task 为 `blocked` 时暂停整个队列。`no_op` 不调用执行脚本，但保留其目标路径供最终文字回执使用。

每个文件 task 执行后先读 `references/runtime-check.md`。全部 task 完成后，读 `references/text-output-reference.md` 组织用户可见回答，再读 `references/quality-check.md` 做最终回答检查。

## 下一步

根据当前 task 的 `route.reference` 读取对应执行 reference。不要提前读取不相关能力或自检文档。
