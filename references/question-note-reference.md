# Question Note Reference

## 用途

定义 `question_note` 这条标准链路：把学习问题写成 `30_Questions/*.md`。

## 负责

标准运行入口优先使用 `scripts/create_question_note.py`。如果同次请求还要生成对比图，则改走 `scripts/dispatch_learning_artifact.py` 的内部组合链路。

## 不负责

不负责对比图逻辑，不负责开放模式，不决定回答深度，也不扩张主地图。

## 下一步

生成了文件产物就读 `references/runtime-check.md`；回答结束前再读 `references/quality-check.md`。
