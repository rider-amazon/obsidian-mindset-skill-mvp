# Runtime Check

## 目的

检查本次运行生成的文件产物是否真的可用。

## 何时读取

只有当前 task 生成了文件产物时，才读取本文件。纯语言回答不读取本文件。

## 检查项

| 检查项 | 要求 |
|---|---|
| 脚本 result | `ok` 必须为 `true`，`path` 必须存在 |
| 路径 | 标准问题页在 `30_Questions/*.md`；标准对比图在 `10_Maps/*.canvas`；open mode 新建文件必须位于用户确认的 Vault 内 |
| 文件存在 | 必须确认目标文件真实存在 |
| 内容 | 文件不能空白，不能明显乱码 |
| 格式 | `.canvas` 必须是合法 JSON |
| Obsidian 链接 | open mode 新建 Markdown 或 Canvas 时，概念引用优先使用 `[[概念]]` |
| Canvas 布局 | 脚本 result 的 `layout_valid` 必须为 `true`；节点不得越出 group，节点矩形不得互相遮挡 |
| 任务对应 | 产物必须对应当前 task，不能拿旧文件冒充 |

## 失败处理

任一检查失败，不得声称产物已生成。应回到当前 task 修正；如果无法修正，说明失败原因，并停止当前 task。

## 不负责

不判断回答是否答题，不判断结构是否过载，也不决定是否补新内容。

## 下一步

产物有效就继续读 `references/quality-check.md`；产物无效则不要进入下一个 task。
