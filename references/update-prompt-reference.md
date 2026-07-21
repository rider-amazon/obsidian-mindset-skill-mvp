# Update Prompt Reference

## 目的

把指向已有文件的后续请求拆解成 `request + task_queue`。本文件只处理修改、压缩、覆盖或保留已有文件的意图，负责定位目标与记录授权，不负责解析文件内部格式，不执行 py。

## 入口边界

| 请求 | 处理方式 |
|---|---|
| 修改、压缩、补充、删除或修正已有文件内容 | `operation.action = "update"` |
| 保留全文、保持不变、不用压缩 | `operation.action = "keep"` |
| 新建、另存一份或转换成另一种产物 | 交给 `references/prompt-reference.md` |
| 只读查看、分析或解释文件 | 作为语言回答任务交给 `references/prompt-reference.md` |

同一句话同时包含保留与其他修改时，以实际修改为 `update`。转换产物表示新建另一种结果，不删除或覆盖原文件。

## 目标定位

按以下顺序定位当前 task 的目标：

1. 用户明确给出的绝对路径。
2. 用户明确给出的文件名，并且只匹配到一个文件。
3. 最近一次用户可见产物回执中的绝对路径。
4. 最近一次请求、产物类型和实际存在文件共同确定的唯一目标。

必须确认目标真实存在，并位于用户已经确认的 Obsidian Vault 内。存在多个候选、路径不存在或无法可靠定位时，`confidence` 写 `low`、`target_path` 写 `null`，交给 Route 阻断并请求用户确认。

## Vault 定位

`request.vault_root` 保存本次请求中所有文件 task 共用且已经确认的 Obsidian Vault 根目录绝对路径。按以下顺序确定：

1. 使用用户明确给出且真实存在的 Vault 根目录。
2. 目标是标准 `30_Questions/<文件>.md` 或 `10_Maps/<文件>.canvas` 时，可从唯一 `target_path` 反推出对应目录的父目录，并确认它是本次 Vault。
3. 前文已经明确确认唯一 Vault 时，可复用该绝对路径。

无法唯一确认时写 `null`。目标必须位于 `vault_root` 内；两者矛盾时将 `confidence` 写 `low`，不得自行改写路径。当前 schema 一次请求只支持一个 Vault；多个目标属于不同 Vault 时不得合并执行。

## 能力候选

| 目标 | `task_candidate` |
|---|---|
| 可识别的 `30_Questions/*.md` 标准问题页 | `question_note` |
| 可识别的 `10_Maps/*.canvas` 标准对比图 | `compare_canvas` |
| 其他已有文件 | `open_route`，由 Route 阻断更新，不进入 open route |

本阶段只做类型和目标判断。旧文件的完整读取、标准结构确认与基础 spec 恢复由对应执行 reference 完成。

## 显式入口与契约

`request_route` 只记录用户明确指定的标准入口或 `open_route`；未指定时写 `null`。标准能力仍使用 `references/prompt-reference.md` 中定义的入口契约。

如果用户显式指定的标准入口与目标文件类型不同，保留用户的 `request_route`，按目标文件实际类型填写 `task_candidate`，由 Route 计算冲突。open route 只允许新建，因此不能承接任何 `update`。

## 修改授权

| action | `overwrite_authorized` | `overwrite_reason` |
|---|---|---|
| 用户明确要求修改唯一目标 | `true` | 记录用户原话或简要理由 |
| `keep` | `false` | `null` |
| 目标不明确 | `false` | `null` |

“修改这个文件”“压缩当前 Canvas”“删掉刚才问题页中的相关概念”等表达，在目标唯一时已经构成覆盖授权，不需要再次确认。只读查看和保留全文不构成授权。

本文件不生成 `force` 字段。`--force` 是对应标准脚本的 CLI 参数。

## 任务拆分

顶层 `request` 保存整次请求；每个 task 的 `invoke` 保存当前任务片段。一个请求包含多个已有文件操作时，按用户原顺序拆分。若同时包含新建任务，只解析更新或保留部分，再与 Prompt reference 的 task 按原顺序合并。

## 阶段产物

读取本文件后，显式生成一份 `Update Prompt JSON`。字段结构与 Prompt JSON 一致，因此可直接交给同一份 `references/route-reference.md`。

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
        "action": "update | keep",
        "target_path": "absolute path | null",
        "overwrite_authorized": false,
        "overwrite_reason": null
      },
      "intent": {
        "request_route": "question_note | compare_canvas | open_route | null",
        "task_candidate": "question_note | compare_canvas | open_route",
        "confidence": "high | medium | low"
      }
    }
  ]
}
```

## 下一步

固定进入 `references/route-reference.md`。本文件不读取 Question、Compare、open route 或自检细节。
