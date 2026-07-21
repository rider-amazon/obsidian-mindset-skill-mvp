# Question Note Reference

## 目的

定义 `question_note` 标准能力的公共契约。当前能力支持新建或完整重写 `30_Questions/*.md` 标准问题页；具体执行规则按当前 task 的 `operation.action` 继续披露。

## 输入

只接收 `route.reference = "references/question-note/reference.md"` 且 `task_candidate = "question_note"` 的当前 task。`operation.action` 只能是 `create` 或 `update`。

## Action 分流

只读取与当前 action 对应的一份文档，不得提前读取另一条路径。

| `operation.action` | 下一份文档 |
|---|---|
| `create` | `references/question-note/create-reference.md` |
| `update` | `references/question-note/update-reference.md` |

action 缺失或不是上述值时停止执行，不得自行推断为新建或更新。

## Spec 生成规则

agent 必须先把当前 task 转成 `question_note spec`，再调用脚本。spec 是脚本输入，也是完整内容容器。

| 字段 | 要求 |
|---|---|
| `title` | 必填，问题页标题 |
| `question` | 必填，用户原始问题或当前 task 原话 |
| `file_stem` | 可选，文件名；新建时不填则使用 `title` |
| `understanding` | 可选，对当前理解的一段话概括 |
| `understanding_points` | 可选，当前理解要点数组 |
| `answer` | 可选，可写入完整 Markdown 正文 |
| `related` | 可选，相关概念数组，使用概念名即可 |
| `status` | 可选，`unresolved` / `partial` / `answered` / `converted_to_concept` |
| `overwrite_authorized` | 仅更新时写入 Update Prompt 已确认的授权 |
| `overwrite_reason` | 仅更新时填写授权原话或简要理由 |

`force` 不是 spec 字段。spec 中出现 `force` 属于接口错误，必须改用命令行 `--force`。

复杂回答写入 `answer`，使用 Markdown 小标题组织。不要因为使用 spec 就降低回答深度。

## 脚本 result

Prompt JSON、Update Prompt JSON 与 Route JSON 不落盘。spec 可临时落盘，仅用于脚本调用，不作为知识库产物。

| 输出字段 | 要求 |
|---|---|
| `ok` | 必须为 `true` |
| `path` | 必须指向 `30_Questions/*.md`；更新时必须等于原目标路径 |
| `title` | 应与 spec 的 `title` 一致 |
| `status` | 应与 spec 的 `status` 一致，或为脚本默认值 |

脚本无论成功或失败都输出 result JSON。退出码非零、目标冲突、JSON 无法解析或 `ok` 不是 `true` 时，不得声称文件已生成或更新。

## 产物规则

问题页用于记录真实学习问题、当前理解、回答、相关概念和状态，不生成“下一步”章节。

## 不负责

不负责对比图、开放模式、任意 Markdown 更新、文件重命名或主地图扩张。
