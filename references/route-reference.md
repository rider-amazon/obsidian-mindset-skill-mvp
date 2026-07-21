# Route Reference

## 目的

读取 Prompt JSON 或 Update Prompt JSON，为每个 task 选择唯一执行 reference。本文件只负责能力匹配、冲突计算和阻断；不重新拆解请求，不执行脚本，不生成回答，不做自检。

## 字段职责

| 字段 | 唯一职责 |
|---|---|
| `operation.action` | 表示用户要求的操作：`create`、`answer`、`update` 或 `keep` |
| `intent.task_candidate` | 表示 Prompt 阶段依据能力契约推断的候选能力 |
| `route.reference` | 表示当前 task 唯一应读取的执行文档 |
| `route.reason` | 仅在 task 被阻断时记录明确原因 |

不得通过新增状态字段重复表达 `operation.action` 或 `route.reference` 已经能够表达的信息。

## 输入

两份 Prompt reference 使用同一 task schema。Route 消费以下字段，并原样保留其余上下文：

| 字段 | 用途 |
|---|---|
| `request.task_shape` | 判断队列推进方式 |
| `request.vault_root` | 验证文件 task 是否具有唯一、已确认的 Vault |
| `task_queue[].id` | 保持任务顺序 |
| `task_queue[].operation` | 区分新建、回答、更新与保留 |
| `task_queue[].intent.request_route` | 判断用户是否显式指定入口 |
| `task_queue[].intent.task_candidate` | 匹配能力 reference |
| `task_queue[].intent.confidence` | 判断是否需要阻断或回退 |

如果没有前一阶段显式生成的 Prompt JSON 或 Update Prompt JSON，不得继续匹配。

## 冲突计算

`task_candidate` 已由对应 Prompt reference 依据标准入口契约生成。Route 按以下规则计算，不接收额外的冲突字段。

| 条件 | 是否冲突 |
|---|---|
| `request_route = null` | 否 |
| `request_route = open_route` | 否 |
| `request_route` 是标准入口且等于 `task_candidate` | 否 |
| `request_route` 是标准入口且不等于 `task_candidate` | 是 |

冲突 task 的 `route.reference` 必须为 `null`，`route.reason` 必须说明显式入口与任务内容或目标文件不匹配。不得自行改写入口继续执行。

## 匹配规则

按 `task_queue[].id` 原顺序逐条匹配，不允许重排。表格从上到下匹配，命中后停止。

| 条件 | `route.reference` | `route.reason` |
|---|---|---|
| 已计算出入口冲突 | `null` | 非空冲突原因 |
| 显式标准入口且 `confidence = low` | `null` | 非空不确定原因 |
| `action = create` 或 `update`，且 `request.vault_root = null` | `null` | 缺少已确认 Vault |
| `action = update` 且目标不唯一、目标不存在或 `confidence = low` | `null` | 非空目标原因 |
| `action = update` 且 `request_route = open_route` | `null` | open route 不允许更新 |
| `action = update` 且 `task_candidate = open_route` | `null` | 现有标准能力无法安全更新该文件 |
| `action = keep` 且目标唯一 | `null` | `null` |
| 隐式 `create` 或 `answer` 且 `confidence = low` | `references/open-route-reference.md` | `null` |
| `task_candidate = question_note` 且 `action = create` 或 `update` | `references/question-note/reference.md` | `null` |
| `task_candidate = compare_canvas` 且 `action = create` 或 `update` | `references/compare-canvas/reference.md` | `null` |
| `task_candidate = open_route` 且 `action = create` 或 `answer` | `references/open-route-reference.md` | `null` |
| 其他组合 | `null` | 非空的 schema 或能力不兼容原因 |

`keep` 是明确的无写入操作：由 `operation.action` 表达，不需要执行 reference。`route.reference = null` 且 `route.reason = null` 只允许出现在有效的 `keep` task；其他 `reference = null` 都必须提供非空阻断原因。

## 输出 schema

保留完整 `request` 和原顺序 `task_queue`，只在每个 task 内追加 `route`。

```json
{
  "request": {
    "raw_user_request": "",
    "summary": "",
    "task_shape": "single | multi",
    "vault_root": "absolute path | null"
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
        "reference": "reference path | null",
        "reason": "blocked reason | null"
      }
    }
  ]
}
```

## 队列推进

`single` 只执行一个 task；`multi` 始终按 `task_queue[].id` 原顺序执行和保存结果。开始执行前先完成整条队列的 Route 匹配；任一 task 存在非空 `route.reason` 时暂停整个队列，避免前半部分已经产生副作用后才发现后续任务被阻断。

每个 task 产生一种结果：

| action | task 结果 |
|---|---|
| `answer` | open route 直接形成语言回答片段 |
| `create` / `update` | 执行 reference 的结果；文件产物还必须通过 Runtime Check |
| `keep` | 保存目标路径与“未修改”状态，不调用执行文档 |

所有 task 完成后按原顺序合并结果。纯语言队列直接进入 Quality Check，不读取 `references/text-output-reference.md`。队列中存在文件 task 或 `keep` 时，只用该文档格式化文件回执；已形成的语言回答片段保持原意和位置，不由文件回执规则改写。

## 下一步

对每个非 `keep` task 读取其 `route.reference`。不得提前读取未命中的能力文档或自检文档。
