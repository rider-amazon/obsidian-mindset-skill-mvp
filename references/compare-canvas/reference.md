# Compare Canvas Reference

## 目的

定义 `compare_canvas` 标准能力的公共契约。当前能力支持新建或完整重写 `10_Maps/*.canvas` 双概念对比图；具体执行规则按当前 task 的 `operation.action` 继续披露。

## 输入

只接收 `route.reference = "references/compare-canvas/reference.md"` 且 `task_candidate = "compare_canvas"` 的当前 task。`operation.action` 只能是 `create` 或 `update`。

## Action 分流

只读取与当前 action 对应的一份文档，不得提前读取另一条路径。

| `operation.action` | 下一份文档 |
|---|---|
| `create` | `references/compare-canvas/create-reference.md` |
| `update` | `references/compare-canvas/update-reference.md` |

action 缺失或不是上述值时停止执行，不得自行推断为新建或更新。

## Spec 生成规则

agent 必须先把当前 task 转成 `compare_canvas spec`，再调用脚本。spec 是完整语义容器，不要直接手写 Canvas JSON。

| 字段 | 要求 |
|---|---|
| `title` | 必填，Canvas 标题 |
| `left` | 必填，左侧概念 |
| `right` | 必填，右侧概念 |
| `question` | 必填，核心比较问题 |
| `file_stem` | 可选，文件名；新建时不填则使用 `title` |
| `summary` | 可选，一句话判断 |
| `left_subtitle` | 可选，左侧概念短定位 |
| `right_subtitle` | 可选，右侧概念短定位 |
| `same_points` | 可选，共同点数组 |
| `left_points` | 可选，左侧概念更强调什么 |
| `right_points` | 可选，右侧概念更强调什么 |
| `related` | 可选，格式为 `名称|说明|左侧关系标签|右侧关系标签`；具体保留或生成规则由 action 文档规定 |
| `overwrite_authorized` | 仅更新时写入 Update Prompt 已确认的授权 |
| `overwrite_reason` | 仅更新时填写授权原话或简要理由 |

`force` 不是 spec 字段。spec 中出现 `force` 属于接口错误，必须改用命令行 `--force`。

## 脚本 result

Prompt JSON、Update Prompt JSON 与 Route JSON 不落盘。spec 可临时落盘，仅用于脚本调用，不作为知识库产物。

| 输出字段 | 要求 |
|---|---|
| `ok` | 必须为 `true` |
| `path` | 必须指向 `10_Maps/*.canvas`；更新时必须等于原目标路径 |
| `title` | 应与 spec 的 `title` 一致 |
| `left` | 应与 spec 的 `left` 一致 |
| `right` | 应与 spec 的 `right` 一致 |
| `layout_valid` | 必须为 `true` |

脚本退出码非零、目标冲突、输出无法解析、`ok` 不是 `true` 或 `layout_valid` 不是 `true` 时，不得声称文件已生成或更新。

## 可视化规则

对比图只服务一个核心比较问题。默认左、右放两个主概念，中间放共同点，差异写入左右详情框。优先少线、主干清楚、避免交叉；背景节点超过 3 个时不再逐个连线。

节点尺寸由脚本动态估算。中文全角字符、英文与数字、空格和标点分别计算显示宽度；英文优先按完整单词换行；左右详情框分别定高。脚本比较多组宽度与网格，选择接近目标宽高比且无重叠的布局。

生成内容使用以下软参考：

| 范围 | 中文 | 英文 |
|---|---:|---:|
| 单个核心节点 | 80～180 字 | 40～100 词 |
| 整张 Canvas | 300～700 字 | 150～350 词 |

这些数值不是硬上限。内容超过参考值时仍完整生成，不暂停要求选择，不自动压缩或截断。最终是否提示内容偏重，由 `references/text-output-reference.md` 根据实际产物统一组织。

## 产物规则

Canvas 用于表示两个概念的边界、共同点和主干差异。

## 不负责

不负责问题页、开放模式、任意 Canvas 更新、文件重命名、补概念页或复杂图模板。
