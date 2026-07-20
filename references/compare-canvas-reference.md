# Compare Canvas Reference

## 目的

定义 `compare_canvas` 标准链路：新建或完整重写 `10_Maps/*.canvas` 双概念对比图。

## 输入

只接收 `route.type = "standard"` 且 `task_candidate = "compare_canvas"` 的当前 task。`operation.action` 只能是 `create` 或 `update`。

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
| `related` | 仅用户明确要求时可选，格式为 `名称|说明|左侧关系标签|右侧关系标签` |
| `overwrite_authorized` | 仅更新时写入 Update Prompt 已确认的授权 |
| `overwrite_reason` | 仅更新时填写授权原话或简要理由 |

`force` 不是 spec 字段。spec 中出现 `force` 属于接口错误，必须改用命令行 `--force`。

新建时默认省略 `related`。只有用户明确要求补充相关概念、背景概念或扩展关系时才允许生成，而且只保留直接帮助理解主轴的概念。

## 新建文件

标准入口使用 `scripts/generate_compare_canvas.py`：

```text
python scripts/generate_compare_canvas.py --vault <vault_root> --spec <temp_spec_json>
```

`--vault` 必须是用户当前指定或工作区中已经确认的 Obsidian Vault 根目录。无法可靠确定时先询问，不得把 Skill 安装目录当作 Vault。

## 更新已有产物

更新必须使用 Update Prompt 提供的唯一 `target_path`，并按以下顺序执行：

1. 确认目标位于已确认 Vault 的 `10_Maps` 内且真实存在。
2. 以 UTF-8 读取并解析旧 Canvas JSON。
3. 确认存在标准节点 `g1`、`title`、`left`、`right`、`same`、`left_details`、`right_details`、`summary`；其他节点只能是脚本生成的 `related_<编号>`。
4. 从标准节点文本和 group 标签恢复完整基础 spec。
5. 只应用用户本轮要求，所有未提及字段保持旧值。旧图已有 `related` 时，除非用户要求删除或修改，否则必须保留。
6. `file_stem` 固定为目标文件原文件名，不因图内标题变化而自动重命名。
7. 把 `overwrite_authorized: true` 和非空 `overwrite_reason` 写入 spec。
8. 在新建命令末尾追加 `--force`，完整重写原路径。

如果存在无法还原的自定义节点、未知节点 ID 或非标准结构，停止更新并说明可能丢失的内容，不得静默删除。

覆盖时不得先删除旧文件。脚本必须先完整写入同目录临时文件，再用临时文件替换原路径。

```text
python scripts/generate_compare_canvas.py --vault <vault_root> --spec <temp_spec_json> --force
```

缺少唯一目标、覆盖授权或覆盖原因时，不得调用 `--force`。

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

## 下一步

生成或更新文件后读取 `references/runtime-check.md`。全部 task 完成后读取 `references/text-output-reference.md`，再读 `references/quality-check.md`。
