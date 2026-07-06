# Prompt Reference

## 目的

把用户原始请求解析为 intent JSON。只做意图解析，不回答、不执行、不选择 py、不读取其他 reference。

## 调用来源判定

先判断调用来源，再只使用对应分支。

| 调用来源 | 判定规则 |
|---|---|
| `explicit` | 输入以 `/question_note`、`/compare_canvas`、`/open_mode` 开头；或明确说“按 question_note 模式处理”“按 compare_canvas 模式处理”“进入 open mode” |
| `implicit` | 不满足 explicit 规则的一律视为 implicit |

“生成图”“保存”“沉淀”“写入”“生成 canvas”不是显式调用，只是隐式调用里的需求信号。

## 显式参数词典

仅当 `invoke.source = "explicit"` 时使用本节。

| 字段 | 含义 | 可填值 |
|---|---|---|
| `invoke.source` | 调用来源 | `"explicit"` |
| `invoke.raw_user_request` | 用户原话 | 字符串 |
| `invoke.summary` | 一句话重述需求 | 字符串 |
| `explicit.requested_mode` | 用户显式指定的模式 | `"question_note"` / `"compare_canvas"` / `"open_mode"` |
| `explicit.has_mode_conflict` | 显式模式是否和真实需求冲突 | `true` / `false` |

| 用户重点                   | `explicit.requested_mode` |
| -------------------------- | ------------------------- |
| 回答并沉淀一个学习问题     | `"question_note"`         |
| 区分两个概念并生成对比结果 | `"compare_canvas"`        |
| 边界模糊或明显超出两类     | `"open_mode"`             |

## 显式输出 schema

显式输出只能包含 `invoke` 和 `explicit`，不得包含 `implicit`。

```json
{
  "invoke": {
    "source": "explicit",
    "raw_user_request": "",
    "summary": ""
  },
  "explicit": {
    "requested_mode": "question_note | compare_canvas | open_mode",
    "has_mode_conflict": false
  }
}
```

## 隐式参数词典

仅当 `invoke.source = "implicit"` 时使用本节。

| 字段 | 含义 | 可填值 |
|---|---|---|
| `invoke.source` | 调用来源 | `"implicit"` |
| `invoke.raw_user_request` | 用户原话 | 字符串 |
| `invoke.summary` | 一句话重述需求 | 字符串 |
| `implicit.task_candidate` | agent 推断出的任务候选 | `"question_note"` / `"compare_canvas"` / `"open_mode"` |
| `implicit.extra_outputs` | 用户额外要求的产物 | `[]` / `["note"]` / `["canvas"]` / `["note", "canvas"]` |
| `implicit.compare_target_count` | 对比对象数量 | `0` / `1` / `2` / `"3+"` |
| `implicit.confidence` | 意图解析置信度 | `"high"` / `"medium"` / `"low"` |

| 用户重点 | `implicit.task_candidate` |
|---|---|
| 回答并沉淀一个学习问题 | `"question_note"` |
| 区分两个概念并生成对比结果 | `"compare_canvas"` |
| 边界模糊或明显超出两类 | `"open_mode"` |

## 隐式输出 schema

隐式输出只能包含 `invoke` 和 `implicit`，不得包含 `explicit`。

```json
{
  "invoke": {
    "source": "implicit",
    "raw_user_request": "",
    "summary": ""
  },
  "implicit": {
    "task_candidate": "question_note | compare_canvas | open_mode",
    "extra_outputs": [],
    "compare_target_count": 0,
    "confidence": "high | medium | low"
  }
}
```

## 下一步

固定进入 `references/mode-reference.md`，不要在这里提前读取命令文档、自检文档或图规则。
