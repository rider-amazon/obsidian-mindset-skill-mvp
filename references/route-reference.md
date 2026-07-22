# Route Reference

## 目的

读取 Prompt JSON 或 Update Prompt JSON，通过 `scripts/resolve_route.py` 为每个 task 选择唯一执行 reference。本文件只定义 Route 的调用契约和队列推进方式；能力匹配、冲突计算和阻断规则由脚本确定性执行。

Route 不重新拆解请求，不执行产物脚本，不生成回答，也不替代 Runtime Check、Text Output Reference 或 Quality Check。

## 前置条件

两份 Prompt reference 使用同一 task schema。调用 Route 前必须已经显式生成完整 Prompt JSON 或 Update Prompt JSON，其中至少包含：

- `request.task_shape`
- `request.vault_root`
- `task_queue[].id`
- `task_queue[].operation`
- `task_queue[].intent.request_route`
- `task_queue[].intent.task_candidate`
- `task_queue[].intent.confidence`

`task_candidate`、显式入口、action、目标定位与 confidence 仍由对应 Prompt reference 判断。Route 脚本只消费这些结构化结果，不从用户原话重新推断语义。

## 调用

把完整 Prompt JSON 或 Update Prompt JSON 写入系统临时 JSON 文件，再调用：

```text
python scripts/resolve_route.py --input <temp_prompt_json>
```

临时输入只用于本次调用，不得写入 Vault 或作为学习产物保留。调用方在获得结果后删除临时输入；脚本只读该文件，不主动删除调用方提供的路径。

不得由 Agent 手工复刻脚本内的匹配表，也不得在脚本返回后自行改写 reference 绕过阻断。

## 精简结果

脚本成功解析输入后，退出码为 `0`，stdout 只输出一行 JSON。

全部 task 可继续：

```json
{"ok":true,"routes":[{"id":"task_1","reference":"references/question-note/reference.md","reason":null}]}
```

存在被阻断的 task：

```json
{"ok":false,"routes":[{"id":"task_1","reference":null,"reason":"明确阻断原因"}]}
```

`ok = false` 且存在 `routes` 是正常的 Route 阻断，不是脚本故障。脚本仍然完成整条队列的匹配并保持 task 原顺序，但任一非空 `reason` 都会使整条队列停止，不能产生部分写入。

输入文件、参数或 schema 无效时，退出码非零并返回：

```json
{"ok":false,"error":"invalid_input","message":"明确错误"}
```

此时不得继续执行，也不得把脚本故障改写成 open route。

## 合并为 Route JSON

精简结果不是新的 Prompt schema。Agent 按 `id` 把每项 `reference` 与 `reason` 追加回原 task，形成现有完整 Route JSON：

```json
{
  "request": {},
  "task_queue": [
    {
      "id": "task_1",
      "invoke": {},
      "operation": {},
      "intent": {},
      "route": {
        "reference": "reference path | null",
        "reason": "blocked reason | null"
      }
    }
  ]
}
```

必须保留完整 `request`、原 task 内容和队列顺序。不得只保留脚本的精简结果进入执行阶段。

`route.reference = null` 且 `route.reason = null` 只表示有效的 `keep` task；其他 `reference = null` 必须具有非空阻断原因。

## 规则来源

`scripts/resolve_route.py` 是 Route 条件顺序与匹配行为的单一执行来源，保持原有规则：

- 计算显式标准入口与 `task_candidate` 的冲突；
- 阻断不确定的显式标准入口；
- 阻断缺少真实绝对 Vault 的新建、更新或保留文件 task；
- 解析真实路径，阻断目标不唯一、不存在、低置信度或位于已确认 Vault 外的更新；
- `keep` 目标同样必须真实存在且位于已确认 Vault 内；
- 禁止 open route 更新已有文件；
- `keep` 不读取执行 reference；
- 隐式低置信度的新建或回答回退到 open route；
- `question_note`、`compare_canvas`、`open_route` 只接受各自兼容的 action；
- 先匹配整条队列，任一 task 阻断时不执行任何 task。

规则覆盖由 `tests/test_resolve_route.py` 验证。修改 Route 行为时必须同时修改测试，不在本文档复制完整条件表形成第二份规则来源。

## 队列推进

只有脚本退出码为 `0`、结果可解析且 `ok = true` 时，才能按合并后的 Route JSON 推进：

- 非 `keep` task 读取其唯一 `route.reference`；
- `keep` 保存目标路径与“未修改”状态，不读取执行 reference；
- `answer` 保存 open route 的语言回答片段；
- `create` / `update` 文件产物继续读取 `references/runtime-check.md`；
- 全部 task 按 `task_queue[].id` 原顺序形成结果；
- 纯语言队列跳过 `references/text-output-reference.md`；
- 队列存在文件 task、`keep` 或文件执行失败时，使用该文档格式化文件回执；
- 最后读取 `references/quality-check.md`。

本次 Python 化不改变上述三个后续 reference 的职责或触发条件。
