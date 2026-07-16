# Quality Check

## 目的

检查这次输出是否真正对题，并且没有越界。

## 何时读取

每个 task 完成前都读取本文件。若当前 task 生成了文件产物，应先完成 `references/runtime-check.md`。

## 检查项

| 检查项 | 要求 |
|---|---|
| 是否答题 | 必须回应当前 task 的核心问题 |
| 是否过空 | 不能只有空泛概括 |
| 是否过载 | 不堆无关概念，不扩写无关内容 |
| 是否越界 | 不声称未实现能力，不伪装未生成产物 |
| route 一致 | standard task 按标准 reference；open route 不伪装标准产物 |
| 语言 | 默认中文，专业术语可保留英文 |
| 队列完整性 | 如果还有后续 task，不得遗忘队列推进 |
| 产物完整性 | 用户要求的每个独立产物都必须对应一个 task，不能作为附加要求被静默忽略 |

## 失败处理

不通过时，在当前 route 内收缩、补充或重写；仍无法通过时说明残留问题，不要假装完成。

## 不负责

不检查 JSON、Markdown、Canvas 是否损坏，也不检查目标目录是否正确；这些都属于 `runtime-check.md`。

## 下一步

质量通过后，如果 `Route JSON` 里还有下一个 task，回到 `references/route-reference.md` 继续；没有下一个 task 则结束运行。
