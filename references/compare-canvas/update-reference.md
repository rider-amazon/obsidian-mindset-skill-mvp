# Compare Canvas Update Reference

## 适用条件

仅在父级 `references/compare-canvas/reference.md` 已读取，且当前 task 满足以下条件时读取：

- `route.reference = "references/compare-canvas/reference.md"`
- `task_candidate = "compare_canvas"`
- `operation.action = "update"`

## 更新已有产物

更新必须使用 Update Prompt 提供的唯一 `target_path`，并按以下顺序执行：

1. 确认目标位于已确认 Vault 的 `10_Maps` 内且真实存在。
2. 以 UTF-8 读取并解析旧 Canvas JSON。
3. 确认存在标准节点 `g1`、`title`、`left`、`right`、`same`、`left_details`、`right_details`、`summary`；其他节点只能是脚本生成的 `related_<编号>`。
4. 从标准节点文本和 group 标签恢复完整基础 spec。
5. 只应用用户本轮要求，所有未提及字段保持旧值。旧图已有 `related` 时，除非用户要求删除或修改，否则必须保留。
6. `file_stem` 固定为目标文件原文件名，不因图内标题变化而自动重命名。
7. 把 `overwrite_authorized: true` 和非空 `overwrite_reason` 写入 spec。
8. 调用脚本时追加 `--force`，完整重写原路径。

如果存在无法还原的自定义节点、未知节点 ID 或非标准结构，停止更新并说明可能丢失的内容，不得静默删除。

覆盖时不得先删除旧文件。脚本必须先完整写入同目录临时文件，再用临时文件替换原路径。

```text
python scripts/generate_compare_canvas.py --vault <request.vault_root> --spec <temp_spec_json> --force
```

`request.vault_root` 必须与 Update Prompt JSON 中的唯一目标一致，并且目录真实存在。缺少已确认 Vault、唯一目标、覆盖授权或覆盖原因时，不得调用 `--force`。

## 完成后

读取 `references/runtime-check.md` 检查实际文件。全部 task 完成后读取 `references/text-output-reference.md`，再读 `references/quality-check.md`。
