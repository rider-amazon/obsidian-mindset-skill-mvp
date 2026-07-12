# Prompt Reference

## 目的

把用户原始请求拆解成 `request + task_queue`。本文件只负责理解用户要什么，不判断 route，不执行 py，不读取命令 reference，不拦截冲突。

## 调用来源判定

先判断每个任务的调用来源，再写入对应 task 的 `invoke.source`。

| 调用来源 | 判定规则 |
|---|---|
| `explicit` | 任务以 `/question_note`、`/compare_canvas`、`/open_mode` 开头；或明确说“按 xxx 模式处理” |
| `implicit` | 不满足 explicit 规则的一律视为 implicit |

“生成图”“保存”“沉淀”“写入”“生成 canvas”不是显式调用，只是需求信号。

当显式调用为 `/open_mode` 或明确要求“进入 open mode”时，该 task 的 `requested_mode` 与 `task_candidate` 都写 `"open_mode"`，`has_mode_conflict` 写 `false`。`open_mode` 表示用户主动绕开标准链路，不因内容像对比或问题沉淀而触发冲突。

## 任务拆分规则

| 情况 | 写法 |
|---|---|
| 只有一个明确目标 | `request.task_shape = "single"`，`task_queue` 只放一个 task |
| 有多个可独立完成的目标 | `request.task_shape = "multi"`，按用户表达顺序写入多个 task |
| 顺序不明确 | 按“先回答理解，再生成产物，再沉淀记录”的顺序排列 |
| 某个目标超出当前标准能力 | 该 task 的 `task_candidate` 写 `"open_mode"`，不要发明新 candidate |
| 同时要求回答、问题页、Canvas 等多个结果 | 每个可独立验收的结果拆成一个 task，不使用附加产物字段合并执行 |

每个 task 都必须保留自己的 `invoke + intent`，不要只在顶层记录一次。

## 参数词典

| 字段 | 含义 | 可填值 |
|---|---|---|
| `request.raw_user_request` | 用户完整原话 | 字符串 |
| `request.summary` | 对整次请求的一句话概括 | 字符串 |
| `request.task_shape` | 任务形状 | `"single"` / `"multi"` |
| `task_queue[].id` | 任务编号 | `"task_1"`、`"task_2"` |
| `task_queue[].invoke.source` | 当前 task 的调用来源 | `"explicit"` / `"implicit"` |
| `task_queue[].invoke.raw_user_request` | 当前 task 对应的原话片段 | 字符串 |
| `task_queue[].invoke.summary` | 当前 task 的一句话概括 | 字符串 |
| `task_queue[].intent.requested_mode` | 用户显式指定的模式 | `"question_note"` / `"compare_canvas"` / `"open_mode"` / `null` |
| `task_queue[].intent.task_candidate` | agent 推断的任务候选 | `"question_note"` / `"compare_canvas"` / `"open_mode"` |
| `task_queue[].intent.confidence` | 意图解析置信度 | `"high"` / `"medium"` / `"low"` |
| `task_queue[].intent.has_mode_conflict` | 显式模式是否和任务内容冲突 | `true` / `false` |

## 显式模式判定

先按产物拆分 task，再逐条判定。显式命令只绑定与它产物相符的当前 task；额外、可独立验收的结果必须拆成新 task。

| 判定层 | 规则 |
|---|---|
| 无显式模式 | `requested_mode` 写 `null`，按实际目标填写 `task_candidate`，`has_mode_conflict` 写 `false` |
| 显式 `open_mode` | `requested_mode` 与 `task_candidate` 都写 `"open_mode"`，`has_mode_conflict` 写 `false` |
| 显式标准模式且满足契约 | `task_candidate` 写该模式，`has_mode_conflict` 写 `false` |
| 显式标准模式但不满足契约 | `task_candidate` 按实际目标填写，`has_mode_conflict` 写 `true` |

当前标准模式契约：

| `requested_mode` | 可验收产物 | 最小条件 |
|---|---|---|
| `question_note` | 一个问题页 | 有可记录的学习问题；正文可以包含解释、对比或例子 |
| `compare_canvas` | 一个双概念对比 Canvas | 有两个明确可比较概念；用户目标包含对比或要求生成 Canvas |

`confidence` 只表示意图解析是否确定，不等于冲突。比如用户显式要求 `/compare_canvas MCP 是什么`，应写 `confidence = "high"` 且 `has_mode_conflict = true`，因为缺少第二个可比较概念。

## 候选判定表

| 用户目标 | `task_candidate` |
|---|---|
| 回答并沉淀一个学习问题 | `"question_note"` |
| 区分两个概念并生成对比结果 | `"compare_canvas"` |
| 边界模糊、复杂组合、或不属于当前标准能力 | `"open_mode"` |

## 阶段产物

读取本文件后，agent 必须显式生成一份 `Prompt JSON`，内容必须符合下方 schema。
`Prompt JSON` 是下一阶段 `references/route-reference.md` 的唯一输入。
不允许只在脑中保留判断结果，也不允许跳过 JSON 直接进入 route。
`Prompt JSON` 不默认落盘。

## 输出 schema

无论显式、隐式、单任务、多任务，都只使用这一套 schema。

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
      }
    }
  ]
}
```

## 下一步

固定进入 `references/route-reference.md`。本文件只提供 `task_queue`，不提前读取命令文档、自检文档或 open mode 文档。
