# Runtime Check

## 目的

检查本次运行生成的文件产物是否真的可用。

## 何时读取

只有当前 task 生成或更新了文件产物时，才读取本文件。纯语言回答与 `keep` 不读取本文件。

## 检查项

| 检查项 | 要求 |
|---|---|
| 脚本 result | `ok` 必须为 `true`，`path` 必须存在 |
| 路径 | 产物必须位于 `request.vault_root` 内；标准问题页在 `30_Questions/*.md`，标准对比图在 `10_Maps/*.canvas` |
| 文件存在 | 必须确认目标文件真实存在 |
| 内容 | 文件不能空白，不能明显乱码 |
| 格式 | `.canvas` 必须是合法 JSON |
| Obsidian 链接 | open route 新建 Markdown 或 Canvas 时，概念引用优先使用 `[[概念]]` |
| Canvas 布局 | 脚本 result 的 `layout_valid` 必须为 `true`；节点不得越出 group，节点矩形不得互相遮挡 |
| 任务对应 | 产物必须对应当前 task，不能拿旧文件冒充 |
| 更新路径 | `action = update` 时，脚本 result 的 `path` 必须等于 Update Prompt 确认的 `target_path` |
| 保留内容 | 更新后，用户未要求修改的标准字段仍应存在；不得因重写丢失 |

## 失败处理

任一检查失败，不得声称产物已生成或更新。应回到当前 task 修正；如果无法修正，说明失败原因，并停止当前 task。

## 不负责

不判断回答是否答题，不判断结构是否过载，也不决定是否补新内容。

## 下一步

产物有效就保存当前 task 结果并按 Route JSON 继续推进。全部 task 完成后，存在文件回执时读取 `references/text-output-reference.md`；产物无效则不要进入下一个 task。
