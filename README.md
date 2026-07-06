# Obsidian Mindset MVP

一个面向学习场景的 AI Skill 原型项目。

它的目标不是简单把问答存成 Markdown，而是把用户的学习问题先做意图拆解，再按最小可用链路沉淀为结构化笔记或可视化对比图，帮助使用者在 Obsidian 语境中更清楚地理解概念之间的位置关系。

## 项目定位

当前版本是 `MVP`，只验证两件事：

1. 学习型问题能否被稳定沉淀为问题页
2. 两个概念能否被稳定沉淀为对比图

项目重点不是功能堆叠，而是把 Skill 文档做成渐进式披露结构，让 agent 每一步只读取当前必要信息。

## 当前能力

| 能力 | 说明 |
|---|---|
| `question_note` | 把一个学习问题沉淀成问题页 |
| `compare_canvas` | 把两个概念沉淀成对比图 |
| `open_mode` | 当请求超出标准命令时，进入最小约束的开放模式 |

## 核心设计

这个 MVP 目前主要验证四个设计点：

- `渐进式披露`
  Skill 入口只暴露总流程，下游文档按步骤逐层读取，避免一次性灌入全部规则。
- `显式 / 隐式调用区分`
  用户既可以明确指定模式，也可以自然语言提问，再由 agent 判断任务候选。
- `标准模式 / 开放模式分流`
  能命中稳定能力时走标准链路；超出能力边界时进入开放模式，而不是假装命中。
- `运行后自检`
  文件产物和回答质量分开检查，减少“生成了但不可用”或“说了很多但没答到点上”的情况。

## 当前文档结构

```text
SKILL.md
references/
  prompt-reference.md
  mode-reference.md
  question-note-reference.md
  compare-canvas-reference.md
  open-mode-reference.md
  runtime-check.md
  quality-check.md
```

## 运行思路

1. 从 `SKILL.md` 进入
2. 读取 `prompt-reference.md` 做意图解析
3. 读取 `mode-reference.md` 做标准模式 / 开放模式分流
4. 命中标准能力时进入对应 reference
5. 结束前进行运行检查和质量检查

## 当前状态

当前仓库更接近“Skill 架构与文档路由 MVP”，重点在：

- 定义最小可用调用链路
- 约束 agent 读取顺序
- 控制文档边界和 token 开销
- 为后续接入脚本调度、Obsidian 产物生成和用户偏好积累预留清晰接口



## 说明

这是一个仍在推进中的项目。当前版本优先强调架构清晰、边界明确和可扩展性。
后续计划架构在Project_Framework.canvas，可在Obsidian中打开查看。
