# Mode Reference

## 用途

把 `prompt-reference.md` 给出的候选，分流到当前可用标准链路，或转入 open mode。

## 负责

| 命中结果 | 去向 |
|---|---|
| `question_note` | `references/question-note-reference.md` |
| `compare_canvas` | `references/compare-canvas-reference.md` |
| 同时要问题页和对比图 | `scripts/dispatch_learning_artifact.py` 组合链路 |
| 未命中标准能力 | `references/open-mode-reference.md` |

## 不负责

不负责回答策略、图策略、自检策略，也不展开具体命令细节。

## 下一步

只允许进入问题页链路、对比图链路或 open mode。不要在本文件中顺手扩展未来命令。
