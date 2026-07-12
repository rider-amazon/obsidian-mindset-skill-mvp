# Compare Canvas Reference

## 目的

定义 `compare_canvas` 这条标准链路：把两个概念的对比结果写成 `10_Maps/*.canvas`。

## 输入

只接收 `route.type = "standard"` 且 `task_candidate = "compare_canvas"` 的当前 task。

## Spec 生成规则

agent 必须先把当前 task 转成 `compare_canvas spec`，再调用脚本。spec 是脚本输入，也是图的语义容器；不要让 agent 直接手写 Canvas JSON。

| 字段 | 要求 |
|---|---|
| `title` | 必填，Canvas 标题 |
| `left` | 必填，左侧概念 |
| `right` | 必填，右侧概念 |
| `question` | 必填，这张图要回答的核心比较问题 |
| `file_stem` | 可选，文件名；不填则脚本用 `title` 生成 |
| `summary` | 可选，一句话判断 |
| `left_subtitle` | 可选，左侧概念短定位 |
| `right_subtitle` | 可选，右侧概念短定位 |
| `same_points` | 可选，共同点数组 |
| `left_points` | 可选，左侧概念更强调什么 |
| `right_points` | 可选，右侧概念更强调什么 |
| `related` | 可选，背景节点数组，格式为 `名称|说明|左侧关系标签|右侧关系标签` |
| `force` | 可选，默认 `false`；不得用 spec 单独请求覆盖 |
| `overwrite_authorized` | 仅用户明确要求覆盖时可写 `true` |
| `overwrite_reason` | 仅覆盖时填写，记录用户授权原话或简要理由 |

`related` 只放能帮助理解主轴的背景概念，不要为了显得完整而堆概念。

## 脚本调用

标准运行入口使用 `scripts/generate_compare_canvas.py`。

agent 必须先生成 `compare_canvas spec`，再调用脚本。复杂内容优先通过 `--spec` 传入，避免多段文本在命令行参数中转义失败。

| 调用材料 | 规则 |
|---|---|
| `Prompt JSON` | 不落盘 |
| `Route JSON` | 不落盘 |
| `compare_canvas spec` | 可临时落盘，仅用于脚本调用，不作为知识库产物 |

推荐新建调用形式：

```text
python scripts/generate_compare_canvas.py --vault <vault_root> --spec <temp_spec_json>
```

覆盖已有文件必须同时满足：用户在当前请求中明确要求覆盖；spec 写入 `overwrite_authorized: true` 和非空 `overwrite_reason`；命令行显式追加 `--force`。缺任一条件都不得覆盖。

`--vault` 是必填参数。agent 必须使用用户当前指定或当前工作区中已确认的 Obsidian Vault 根目录；无法可靠确定时先询问用户，不得省略参数，也不得把 skill 安装目录当作 Vault。

如果内容很短，也可以用 CLI 参数逐项传入；但只要 `same_points`、`left_points`、`right_points` 或 `related` 较多，就必须使用 `--spec`。

脚本执行后必须读取脚本输出 result。以下字段来自脚本输出 result，不属于 `compare_canvas spec`。

| 输出字段 | 要求 |
|---|---|
| `ok` | 必须为 `true` |
| `path` | 必须指向 `10_Maps/*.canvas` |
| `title` | 应与 spec 的 `title` 一致 |
| `left` | 应与 spec 的 `left` 一致 |
| `right` | 应与 spec 的 `right` 一致 |
| `layout_valid` | 必须为 `true` |

脚本无论成功或失败都输出 result JSON。若退出码非零、目标文件已存在、输出 JSON 无法解析，`ok` 不是 `true`，或 `layout_valid` 不是 `true`，不得声称文件已生成；应读取 `error + message` 说明原因，并停止当前 task。

## 可视化规则

对比图只服务一个核心比较问题。默认左/右放两个主概念，中间放共同点，差异写入左右详情框，背景概念只保留少量关键节点。

优先少线、主干清楚、避免交叉；能写进节点文字的次级关系，不强行画线。背景节点超过 3 个时，脚本只保留节点内的关系说明，不再为每个背景节点画线。

## 产物规则

产物写入 `10_Maps/*.canvas`，用于表示两个概念的边界、共同点和主干差异。

## 不负责

不负责问题页逻辑，不负责开放模式，不决定是否补概念页，也不定义复杂图模板。

## 下一步

生成了文件产物就读 `references/runtime-check.md`；回答结束前再读 `references/quality-check.md`。如果队列里还有其他 task，由 `references/route-reference.md` 继续推进。
