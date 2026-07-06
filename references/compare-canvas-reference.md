# Compare Canvas Reference

## 用途

定义 `compare_canvas` 这条标准链路：把两个概念的对比结果写成 `10_Maps/*.canvas`。

## 负责

标准运行入口优先使用 `scripts/generate_compare_canvas.py`。如果同次请求还要生成问题页，则改走 `scripts/dispatch_learning_artifact.py` 的内部组合链路。

## 不负责

不负责问题页逻辑，不负责开放模式，不决定是否补概念页，也不定义复杂图模板。

## 下一步

生成了文件产物就读 `references/runtime-check.md`；回答结束前再读 `references/quality-check.md`。
