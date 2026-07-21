# Question Note Update Reference

## 适用条件

仅在父级 `references/question-note/reference.md` 已读取，且当前 task 满足以下条件时读取：

- `route.reference = "references/question-note/reference.md"`
- `task_candidate = "question_note"`
- `operation.action = "update"`

## 更新已有产物

更新必须使用 Update Prompt 提供的唯一 `target_path`，并按以下顺序执行：

1. 确认目标位于已确认 Vault 的 `30_Questions` 内且真实存在。
2. 以 UTF-8 读取旧文件完整内容。
3. 确认它能还原为标准问题页：标题以及“原始问题 / 当前理解 / 回答 / 相关概念 / 状态”结构可识别。
4. 从旧文件恢复完整基础 spec。
5. 只应用用户本轮要求，所有未提及字段保持旧值。
6. `file_stem` 固定为目标文件原文件名，不因正文标题变化而自动重命名。
7. 把 `overwrite_authorized: true` 和非空 `overwrite_reason` 写入 spec。
8. 调用脚本时追加 `--force`，完整重写原路径。

如果存在无法映射到标准 spec 的自定义章节或结构，停止更新并说明可能丢失的内容，不得静默删除。

覆盖时不得先删除旧文件。脚本必须先完整写入同目录临时文件，再用临时文件替换原路径。用户没有要求修改的内容不得仅凭本轮原话重新生成。

```text
python scripts/create_question_note.py --vault <request.vault_root> --spec <temp_spec_json> --force
```

`request.vault_root` 必须与 Update Prompt JSON 中的唯一目标一致，并且目录真实存在。缺少已确认 Vault、唯一目标、覆盖授权或覆盖原因时，不得调用 `--force`。

## 完成后

读取 `references/runtime-check.md` 检查实际文件。全部 task 完成后读取 `references/text-output-reference.md`，再读 `references/quality-check.md`。
