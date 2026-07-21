# Prompt Reference

## 目的

把新建产物或语言回答请求拆解成 `request + task_queue`。本文件只负责理解用户要什么，不处理已有文件的修改或保留，不判断 route，不执行 py，不读取执行 reference。

## 入口边界

| 请求 | 处理方式 |
|---|---|
| 新建问题页、Canvas 或其他文件 | 继续使用本文件 |
| 只需要语言回答 | 继续使用本文件 |
| 修改、压缩、覆盖或保留已有文件 | 改读 `references/update-prompt-reference.md` |
| 同时包含新建与修改 | 只解析其中的新建或回答 task；修改 task 交给 Update Prompt，并按原顺序合并 |

## 任务拆分规则

| 情况 | 写法 |
|---|---|
| 只有一个明确目标 | `request.task_shape = "single"`，`task_queue` 只放一个 task |
| 有多个可独立完成的目标 | `request.task_shape = "multi"`，按用户表达顺序写入多个 task |
| 顺序不明确 | 按“先回答理解，再生成产物，再沉淀记录”的顺序排列 |
| 某个新建或回答目标超出当前标准能力 | `task_candidate` 写 `"open_route"`，不要发明新 candidate |
| 同时要求回答、问题页、Canvas 等多个结果 | 每个可独立验收的结果拆成一个 task，不使用附加产物字段合并执行 |

顶层 `request` 保存整次请求；每个 task 的 `invoke` 只保存属于当前 task 的原话片段与摘要，两者不得互相替代。

## Vault 定位

`request.vault_root` 保存本次请求中所有文件 task 共用且已经确认的 Obsidian Vault 根目录绝对路径。按以下规则填写：

1. 用户明确给出 Vault 根目录时，验证目录真实存在后使用。
2. 当前工作区或前文已经明确确认唯一 Vault 时，可复用该绝对路径。
3. 无法唯一确认时写 `null`；不得使用 Skill 安装目录、仓库目录或当前目录猜测代替。

纯语言请求允许 `vault_root = null`。只要队列包含文件新建 task，`vault_root` 就必须是非空绝对路径，否则交给 Route 阻断。当前 schema 一次请求只支持一个 Vault；多个文件 task 指向不同 Vault 时，不得合并执行。

## 显式入口识别

`request_route` 只记录用户明确指定的 `question_note`、`compare_canvas` 或 `open_route`。没有明确指定时写 `null`。“生成图”“保存”“沉淀”“写入”“生成 Canvas”只是需求信号，不等于指定 route。

明确指定 `open_route` 时，`request_route` 与 `task_candidate` 都写 `"open_route"`。open route 表示用户主动绕开标准链路，不因内容像问题页或对比图而改写 candidate。

## 标准入口契约

先按产物拆分 task，再依据以下契约填写 `task_candidate`。

| 标准入口 | 可验收产物 | 最小条件 |
|---|---|---|
| `question_note` | 一个问题页 | 有可记录的学习问题；正文可以包含解释、对比或例子 |
| `compare_canvas` | 一个双概念对比 Canvas | 有两个明确可比较概念；用户目标包含对比或要求生成 Canvas |

| 情况 | `request_route` 与 `task_candidate` |
|---|---|
| 无显式入口 | `request_route = null`，按实际目标填写 candidate |
| 显式 `open_route` | 两者都写 `open_route` |
| 显式标准入口且满足契约 | candidate 写该标准入口 |
| 显式标准入口但不满足契约 | 保留用户指定的 `request_route`，candidate 按实际目标填写 |

`confidence` 只表示意图解析是否确定，不表示 route 是否冲突。Route 会根据 `request_route` 与契约化的 `task_candidate` 计算冲突。

## 候选与操作判定

| 用户目标 | `operation.action` | `task_candidate` |
|---|---|---|
| 回答并沉淀一个学习问题 | `create` | `question_note` |
| 区分两个概念并生成对比结果 | `create` | `compare_canvas` |
| 只需要语言回答 | `answer` | `open_route` |
| 新建请求边界模糊、复杂组合或不属于标准能力 | `create` 或 `answer` | `open_route` |

新建与回答 task 的 `target_path`、`overwrite_authorized`、`overwrite_reason` 都写 `null` 或 `false`。

## 参数词典

| 字段 | 含义 |
|---|---|
| `request.raw_user_request` | 用户本轮完整原话 |
| `request.summary` | 对整次请求的一句话概括 |
| `request.task_shape` | `single` / `multi` |
| `request.vault_root` | 本次请求唯一、已确认的 Vault 根目录绝对路径；纯语言请求可为 `null` |
| `task_queue[].id` | 保持任务顺序的编号 |
| `task_queue[].invoke.raw_user_request` | 当前 task 对应的原话片段 |
| `task_queue[].invoke.summary` | 当前 task 的独立目标 |
| `task_queue[].operation.action` | `create` / `answer` |
| `task_queue[].intent.request_route` | 用户明确指定的入口或 `null` |
| `task_queue[].intent.task_candidate` | Agent 依据契约推断的能力候选 |
| `task_queue[].intent.confidence` | `high` / `medium` / `low` |

## 阶段产物

读取本文件后，显式生成一份 `Prompt JSON`。它是 `references/route-reference.md` 的输入，不默认落盘。

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
        "action": "create | answer",
        "target_path": null,
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

固定进入 `references/route-reference.md`。本文件不提前读取执行 reference、更新规则、自检文档或 open route 文档。
