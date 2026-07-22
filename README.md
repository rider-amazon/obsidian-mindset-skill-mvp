# Obsidian Mindset

一个面向 Obsidian 学习场景的 AI Skill 原型。

它的目标在用户需要学习一个固定领域的前提下，帮助使用者理解概念之间的位置、边界和关系。



## 核心思路

obsidian原生自带功能：

- 链接/反链语法与预览 → 强大的文件连接功能
- canvas可视化 → 方便agent生成、编辑导图，优于关系图谱功能



## 当前能力

| 能力 | 产物 | 说明 |
|---|---|---|
| `question_note` | `30_Questions/*.md` | 新建或更新一个标准问题页 |
| `compare_canvas` | `10_Maps/*.canvas` | 新建或更新一个标准 Obsidian Canvas 对比图 |
| `open_route` | 可选新建 Markdown / Canvas | 处理标准链路以外的问题，只允许安全新建 |

`question_note` 和 `compare_canvas` 是当前仅有的标准链路。复杂请求会先拆成 `task_queue`，再逐条判断走标准 route 还是 open route。



## 当前定位

已初步验证：

1. 学习问题稳定沉淀为 `30_Questions/*.md`。
2. 两个概念对比稳定沉淀为 `10_Maps/*.canvas`。

当前用户可见内容默认中文。英文文件名、脚本名、能力名和 route 名保留英文，方便 agent 与代码稳定引用。



## 安装方式

目前仅支持本地下载并解压安装包

### claude code:

解压后放入指定位置

详情见官方https://code.claude.com/docs/en/skills

| 位置 | 路径                                                         | 适用于               |
| :--- | :----------------------------------------------------------- | :------------------- |
| 企业 | 请参阅[托管设置](https://code.claude.com/docs/zh-CN/settings#settings-files) | 你的组织中的所有用户 |
| 个人 | `~/.claude/skills/<skill-name>/SKILL.md`                     | 你的所有项目         |
| 项目 | `.claude/skills/<skill-name>/SKILL.md`                       | 仅此项目             |
| 插件 | `<plugin>/skills/<skill-name>/SKILL.md`                      | 启用插件的位置       |

### codex:

解压后放入指定位置

详情见官方https://learn.chatgpt.com/docs/build-skills（下表为机翻）

| 作用域   | 位置                        | 建议用途                                                     |
| -------- | --------------------------- | ------------------------------------------------------------ |
| `REPO`   | `$CWD/.agents/skills`       | 当前工作目录，也就是你启动 Codex 的位置。适合把只对某个工作目录有用的技能放进仓库里，例如只针对某个微服务或模块的技能。 |
| `REPO`   | `$CWD/../.agents/skills`    | 在 Git 仓库中，位于当前工作目录上一级的文件夹。适合把对父目录共享区域有用的技能放进去。 |
| `REPO`   | `$REPO_ROOT/.agents/skills` | 在 Git 仓库中，最顶层根目录。适合放对整个仓库所有人都通用的技能，仓库内任意子目录都可用。 |
| `USER`   | `$HOME/.agents/skills`      | 用户个人目录中的技能。适合放对该用户在任何仓库里都通用的技能。 |
| `ADMIN`  | `/etc/codex/skills`         | 机器或容器上的共享系统位置。适合放 SDK 脚本、自动化，以及给机器上每个用户都可用的默认管理员技能。 |
| `SYSTEM` | 由 OpenAI 随 Codex 一起打包 | 面向广泛用户的通用技能，比如 `skill-creator` 和 `plan` 类技能。用户启动 Codex 时即可使用。 |

## 工作流程

```text
用户请求
  -> SKILL.md
  -> 新建/回答：references/prompt-reference.md
  -> 更新/保留：references/update-prompt-reference.md
  -> references/route-reference.md        调用确定性 Python Route，为每个 task 选择执行 reference
  -> 按 task_queue 原顺序执行
     -> 语言回答：open_route 直接形成回答片段
     -> 文件产物：references/runtime-check.md
  -> 有文件回执：references/text-output-reference.md
  -> references/quality-check.md          检查完整回答
```

中间 JSON 不写入 Vault 或长期保留，只作为 agent 阶段间的显式契约。Route 调用允许在系统临时目录短暂保存输入 JSON，并在调用后删除。

## 文件结构

```text
SKILL.md
references/
  prompt-reference.md
  update-prompt-reference.md
  route-reference.md
  question-note/
    reference.md
    create-reference.md
    update-reference.md
  compare-canvas/
    reference.md
    create-reference.md
    update-reference.md
  open-route-reference.md
  runtime-check.md
  text-output-reference.md
  quality-check.md
scripts/
  resolve_route.py
  create_question_note.py
  generate_compare_canvas.py
```

## 安全边界

Prompt JSON 或 Update Prompt JSON 在 `request.vault_root` 保存本次请求唯一、已确认的 Vault 根目录绝对路径。纯语言请求允许该字段为 `null`；文件请求缺失该字段时必须在 Route 阶段阻断。脚本调用必须显式传入 `--vault <request.vault_root>`，不得把 Skill 安装目录或当前目录猜作 Vault。

Route 阶段把完整 Prompt JSON 临时写入系统临时目录，并调用：

```text
python scripts/resolve_route.py --input <temp_prompt_json>
```

脚本只读临时输入并在 stdout 返回精简路由结果；Agent 再按 task `id` 把 `reference` 与 `reason` 合并回原队列。Route 会解析 Vault 与已有目标的真实绝对路径，阻断 Vault 外的更新或保留目标；它先处理完整队列，任一 task 被阻断时不执行任何文件写入。临时输入不属于 Vault 产物，调用后删除。

默认只新建文件。只有 `question_note` 和 `compare_canvas` 标准产物支持更新，覆盖必须同时满足三个条件：

1. 用户在当前请求中明确要求覆盖。
2. spec 中写入 `overwrite_authorized: true` 和非空 `overwrite_reason`；spec 不得包含 `force`。
3. 命令行显式传入 `--force`。

更新时必须先读取旧产物、恢复完整 spec，并保留用户未要求修改的标准字段。脚本先写入同目录临时文件，再替换原路径；不得先删除旧文件。

`open_route` 可以在用户明确要求时新建 Markdown 或 Canvas，但不能删除、移动、修改或覆盖已有文件。Canvas 和 Markdown 中的概念引用优先使用 Obsidian `[[概念]]` 语法。

## 脚本示例

生成问题页：

```powershell
python scripts/create_question_note.py --vault <request.vault_root> --spec <question_spec.json>
```

生成对比 Canvas：

```powershell
python scripts/generate_compare_canvas.py --vault <request.vault_root> --spec <compare_spec.json>
```

脚本成功和失败都会输出 JSON。调用方必须检查 `ok`，不能只根据文件路径猜测成功。

## 验证

使用 Codex 官方 skill 校验脚本：

```powershell
$env:PYTHONUTF8='1'
python C:\Users\Lenovo\.codex\skills\.system\skill-creator\scripts\quick_validate.py <skill_dir>
```

当前开发目录已通过 `quick_validate.py`。核心脚本已验证：必填 Vault、类型校验、结构化错误、覆盖授权、Canvas 布局检查和 UTF-8 中文内容。

Route 规则测试：

```powershell
python -m unittest discover -s tests -v
```

## 状态

当前版本适合作为本地 MVP 测试版使用。后续功能，例如主地图更新、用户偏好积累、更多 Canvas 模板和更细的 open route 产物契约，尚未纳入当前稳定链路。
