# Question Note Reference

## 目的

定义 `question_note` 这条标准链路：把学习问题写成 `30_Questions/*.md`。

## 输入

只接收 `route.type = "standard"` 且 `task_candidate = "question_note"` 的当前 task。

## Spec 生成规则

agent 必须先把当前 task 转成 `question_note spec`，再调用脚本。spec 是脚本输入，也是内容容器；不要因为使用 spec 就降低回答深度。

| 字段 | 要求 |
|---|---|
| `title` | 必填，问题页标题 |
| `question` | 必填，用户原始问题或当前 task 原话 |
| `file_stem` | 可选，文件名；不填则脚本用 `title` 生成 |
| `understanding` | 可选，对当前理解的一段话概括 |
| `understanding_points` | 可选，当前理解要点数组 |
| `answer` | 可选，可写入完整 Markdown 正文 |
| `related` | 可选，相关概念数组，使用概念名即可 |
| `status` | 可选，`unresolved` / `partial` / `answered` / `converted_to_concept` |
| `force` | 可选，默认 `false`；不得用 spec 单独请求覆盖 |
| `overwrite_authorized` | 仅用户明确要求覆盖时可写 `true` |
| `overwrite_reason` | 仅覆盖时填写，记录用户授权原话或简要理由 |

复杂回答应写入 `answer` 字段，并使用 Markdown 小标题组织，例如“结论 / 相同点 / 不同点 / 一句话压缩”。不要只写摘要。

## 脚本调用

标准运行入口使用 `scripts/create_question_note.py`。

agent 必须先生成 `question_note spec`，再调用脚本。复杂正文优先通过 `--spec` 传入，避免长 Markdown 在命令行参数中转义失败。

| 调用材料 | 规则 |
|---|---|
| `Prompt JSON` | 不落盘 |
| `Route JSON` | 不落盘 |
| `question_note spec` | 可临时落盘，仅用于脚本调用，不作为知识库产物 |

推荐新建调用形式：

```text
python scripts/create_question_note.py --vault <vault_root> --spec <temp_spec_json>
```

覆盖已有文件必须同时满足：用户在当前请求中明确要求覆盖；spec 写入 `overwrite_authorized: true` 和非空 `overwrite_reason`；命令行显式追加 `--force`。缺任一条件都不得覆盖。

`--vault` 是必填参数。agent 必须使用用户当前指定或当前工作区中已确认的 Obsidian Vault 根目录；无法可靠确定时先询问用户，不得省略参数，也不得把 skill 安装目录当作 Vault。

如果内容很短，也可以用 CLI 参数逐项传入；但只要 `answer` 包含多段 Markdown，就必须使用 `--spec`。

脚本执行后必须读取脚本输出 result。以下字段来自脚本输出 result，不属于 `question_note spec`。

| 输出字段 | 要求 |
|---|---|
| `ok` | 必须为 `true` |
| `path` | 必须指向 `30_Questions/*.md` |
| `title` | 应与 spec 的 `title` 一致 |
| `status` | 应与 spec 的 `status` 一致，或为脚本默认值 |

脚本无论成功或失败都输出 result JSON。若退出码非零、目标文件已存在、输出 JSON 无法解析，或 `ok` 不是 `true`，不得声称文件已生成；应读取 `error + message` 说明原因，并停止当前 task。

## 产物规则

产物写入 `30_Questions/*.md`，用于记录真实学习问题、当前理解、回答、相关概念和状态。问题页不生成“下一步”章节，避免由单个问题无限扩张学习范围。

## 不负责

不负责对比图逻辑，不负责开放模式，不决定回答深度，也不扩张主地图。

## 下一步

生成了文件产物就读 `references/runtime-check.md`；回答结束前再读 `references/quality-check.md`。如果队列里还有其他 task，由 `references/route-reference.md` 继续推进。
