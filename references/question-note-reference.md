# Question Note Reference

## 目的

定义 `question_note` 标准链路：新建或完整重写 `30_Questions/*.md` 问题页。

## 输入

只接收 `route.type = "standard"` 且 `task_candidate = "question_note"` 的当前 task。`operation.action` 只能是 `create` 或 `update`。

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

## 新建文件

标准入口使用 `scripts/create_question_note.py`：

```text
python scripts/create_question_note.py --vault <vault_root> --spec <temp_spec_json>
```

`--vault` 必须是用户当前指定或工作区中已经确认的 Obsidian Vault 根目录。无法可靠确定时先询问，不得把 Skill 安装目录当作 Vault。

## 更新已有产物

更新必须使用 Update Prompt 提供的唯一 `target_path`，并按以下顺序执行：

1. 确认目标位于已确认 Vault 的 `30_Questions` 内且真实存在。
2. 以 UTF-8 读取旧文件完整内容。
3. 确认它能还原为标准问题页：标题以及“原始问题 / 当前理解 / 回答 / 相关概念 / 状态”结构可识别。
4. 从旧文件恢复完整基础 spec。
5. 只应用用户本轮要求，所有未提及字段保持旧值。
6. `file_stem` 固定为目标文件原文件名，不因正文标题变化而自动重命名。
7. 把 `overwrite_authorized: true` 和非空 `overwrite_reason` 写入 spec。
8. 在新建命令末尾追加 `--force`，完整重写原路径。

如果存在无法映射到标准 spec 的自定义章节或结构，停止更新并说明可能丢失的内容，不得静默删除。

覆盖时不得先删除旧文件。脚本必须先完整写入同目录临时文件，再用临时文件替换原路径。用户没有要求修改的内容不得仅凭本轮原话重新生成。

```text
python scripts/create_question_note.py --vault <vault_root> --spec <temp_spec_json> --force
```

缺少唯一目标、覆盖授权或覆盖原因时，不得调用 `--force`。

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

## 下一步

生成或更新文件后读取 `references/runtime-check.md`。全部 task 完成后读取 `references/text-output-reference.md`，再读 `references/quality-check.md`。
