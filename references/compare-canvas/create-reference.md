# Compare Canvas Create Reference

## 适用条件

仅在父级 `references/compare-canvas/reference.md` 已读取，且当前 task 满足以下条件时读取：

- `route.reference = "references/compare-canvas/reference.md"`
- `task_candidate = "compare_canvas"`
- `operation.action = "create"`

## 新建文件

新建时默认省略 `related`。只有用户明确要求补充相关概念、背景概念或扩展关系时才允许生成，而且只保留直接帮助理解主轴的概念。

标准入口使用 `scripts/generate_compare_canvas.py`：

```text
python scripts/generate_compare_canvas.py --vault <request.vault_root> --spec <temp_spec_json>
```

`request.vault_root` 必须是 Prompt JSON 中已经确认的 Obsidian Vault 根目录绝对路径，并且目录真实存在。不得在本阶段重新猜测 Vault。

生成完整 spec 后调用脚本。新建路径已存在时停止，不得追加 `--force`、覆盖原文件或自动改成更新任务。

## 完成后

读取 `references/runtime-check.md` 检查实际文件。全部 task 完成后读取 `references/text-output-reference.md`，再读 `references/quality-check.md`。
