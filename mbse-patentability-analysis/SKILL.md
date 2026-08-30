---
name: mbse-patentability-analysis
description: 统一MBSE建模中心，覆盖三种场景——申请前技术交底书可专利性分析（disclosure mode）、专利文本技术建模与多文件对照（document mode）、检索驱动轻量建模（search mode）。当 Codex 需要进行任何专利相关的MBSE建模、技术特征结构化、R/F/S/B/E五层模型构建、创新点提炼、多文件技术对照、审查员逻辑映射，或为专利检索生成结构化检索块时使用。使用时须先选择mode。
---

# 统一 MBSE 建模中心

## Mode 选择（启动必选）

使用本 skill 时，**必须首先指定 mode**。若用户未明确指定，询问用户选择：

| Mode | 名称 | 输入 | 典型用途 | 调用方 |
|------|------|------|---------|--------|
| `disclosure` | 技术交底书可专利性建模 | 技术交底书 + 可选背景材料 | 创新点提炼、检索要素生成、可专利性初判 | 独立使用 / `cn-patent-drafting-workflow` Stage1 |
| `document` | 专利文本技术建模与多文件对照 | 申请文件 / 对比文件 / 审查意见 / 驳回决定 | 技术理解、多文件特征对照、审查员逻辑映射 | `cn-oa-reexam-opinion-drafting` Phase1 |
| `search` | 检索驱动轻量建模 | 技术方案简要描述 | 检索块自动生成、六语关键词展开 | `patent-search-workflow` 可选环节 |

## 统一模型框架

所有 Mode 均使用 **R → F → S → B → E** 五层模型；链路展开时用`F.Output`和`STATE.OutputState`表达直接输出，但不把它们增设为第六层。

| 层 | 含义 | 说明 |
|----|------|------|
| **R** | 技术需求/问题/约束 | 以"如何……"开头；包含约束性条件（原 P 节点的数值阈值/逻辑约束） |
| **F** | 功能 | 实现方式相对中立的`<系统边界,输入,技术变换,直接输出,前提/触发>`合同 |
| **S** | 结构 | 组件、模块、连接关系、空间布局；包含上下文接口（原 C 节点的外部实体/接口定义） |
| **B** | 行为 | 活动、顺序、状态、事件、条件分支、异常路径；包含交互行为（原 C 节点的动态交互） |
| **E** | 技术效果 | 由具体S/B/关系及输出状态进一步产生的`<受影响对象,属性,技术后果,条件,因果路径,证据,类型,可选比较基线>`合同 |

不增加独立O层。`F.Output`是功能规格要求的直接输出，`STATE.OutputState`是具体行为形成的输出状态；二者可对应但均不当然等于E。E若只是换词重复F或其直接输出，应删除、移入F.Output或标`Q`。一般E可为绝对技术后果；只有比较型E及下游区别效果要求明确比较基线。

### 各 Mode 建模差异

| 维度 | disclosure | document | search |
|------|-----------|----------|--------|
| **建模深度** | 中深——识别空缺→发明人问题 | 深——双向追溯+异常路径+接口/参数补充分析 | 浅——仅需驱动检索式 |
| **追溯方向** | 单向 R→F→S→B→OutputState→E | 双向（主链+反向验证） | 无追溯链 |
| **证据标签** | D/I/N/G/Q/X（全六类） | D/I/G/Q/X（不含 N） | 不适用 |
| **补充分析** | 无 | 接口与上下文分析 + 约束与参数分析（强制） | 无 |
| **多文件对照** | 无 | 核心能力 | 无 |
| **审查员逻辑映射** | 无 | 核心能力 | 无 |
| **检索要素/检索块** | 核心能力（阶段三/四） | 不适用 | 核心能力 |

## 统一证据标签

所有需证据标签的 Mode 使用统一的六类标签。详见 `references/unified-evidence-rules.md`。

| 标签 | 含义 | 可作为下游前提？ |
|------|------|-----------------|
| `D` | 原文明确披露（附段落/图号） | ✅ 是 |
| `I` | 受限推断（写明前提和推断范围） | ⚠️ 仅限标注范围 |
| `N` | 发明人确认新增 | ✅ 是（仅 disclosure） |
| `G` | 指向 D/N 的通用专利化表达 | ⚠️ 取决于指向 |
| `Q` | 待确认（缺失或歧义） | ❌ 否 |
| `X` | 排除（无关或误混入） | ❌ 否 |

## 专利证据与论证包（所有 Mode）

当任务进入检索、候选权利要求、可专利性评估或审查意见答复交接时，建立或更新案件专用运行目录中的 `patent_evidence_pack.json`。它是技术模型、文献证据和判断卡的唯一结构化交接件；详细字段、状态和质量门见 `references/patent-evidence-pack.md`。OA交接须使用答审技能的 `v2.1-oa` 活动集合、快照和重算门，并由 document mode 输出完整的权利要求评价台账。

- `disclosure`：可建立候选 `CLM/CF`，并保留 `N/G` 的交底来源状态；不得将其写成现有技术结论。
- `search`：输出 `DOC/EV`、`NB/IS` 所需证据和链接；未完成全文定位时保持 `Q`。
- `document`：仅使用事实状态 `D/I/Q/X`，不得使用 `N`；将审查意见事实核实和组合分析回写至包。

## 通用工作区管理

在写入任何文件之前，在用户指定的目标目录下创建一个专用的运行文件夹。若用户未指定，则在当前工作目录下创建。

文件夹命名模式：

```text
MBSE建模-<mode>-<技术主题>-<YYYYMMDD-HHMMSS>
```

无法识别主题时：

```text
MBSE建模-<mode>-未命名项目-<YYYYMMDD-HHMMSS>
```

## 通用质量门禁

| 检查项 | disclosure | document | search |
|--------|-----------|----------|--------|
| 每个 R 有下游路径或 Q | ✅ | ✅ | — |
| 每个 F 有输入、变换、直接输出及S/B实现 | ✅ | ✅ | — |
| 每个 S 有功能目的和出处 | ✅ | ✅ | — |
| 每个 E 有对象、属性、后果、条件、因果路径和证据，且不重复F/输出 | ✅ | ✅ | — |
| 无商业目标改写为技术问题 | ✅ | ✅ | — |
| Mermaid 节点 ID 与表格匹配 | ✅ | ✅ | — |
| JSON 可解析无 Markdown 注释 | ✅（阶段三） | — | — |
| 无检索前假设写成可专利性结论 | ✅ | ✅ | — |
| 双向追溯链完整 | — | ✅ | — |
| 文件独立性 | — | ✅ | — |
| 检索块至少含中英关键词 | — | — | ✅ |

## 快速路由

- 仅需技术交底书 MBSE 分析与可专利性初判 → 本 skill（`mode=disclosure`）
- 仅需专利文本技术理解与多文件对照 → 本 skill（`mode=document`）
- 仅需检索驱动的轻量建模 → 本 skill（`mode=search`）
- 仅需完整专利申请撰写 → `cn-patent-drafting-workflow` 技能（其 Stage1 调用本 skill mode=disclosure）
- 仅需审查意见答复 → `cn-oa-reexam-opinion-drafting` 技能（其 Phase1 调用本 skill mode=document）
- 仅需独立专利检索 → `patent-search-workflow` 技能（可选 MBSE 环节调用本 skill mode=search）
- 仅需专利附图标注 → `patent-figure-labeling` 技能

## 参考阅读索引

### 核心框架（所有 Mode 共用）

| 文件 | 内容 |
|------|------|
| `references/mbse-framework.md` | R/F/S/B/E 五层统一定义与建模方法 |
| `references/unified-evidence-rules.md` | D/I/N/G/Q/X 统一证据标签体系 |
| `references/sysml-lite-mapping.md` | 关系语义参考（allocate/flow/satisfy 等） |
| `references/visualization-patterns.md` | Mermaid 图表规范 |
| `references/failure-patterns.md` | 常见建模失败模式及修复 |
| `references/patent-evidence-pack.md` | 向后兼容1.0及新版1.1证据包合同、阶段1—3工作流对象、新颖性卡、创造性卡与程序回写 |

### Mode 工作流

| 文件 | 内容 |
|------|------|
| `references/modes/mode-disclosure.md` | disclosure 模式完整工作流（四阶段） |
| `references/modes/mode-document.md` | document 模式完整工作流（六步骤） |
| `references/modes/mode-search.md` | search 模式完整工作流（三视图→检索块） |

### 领域建模规则

| 文件 | 领域 |
|------|------|
| `references/domains/mechanical.md` | 机械/结构（含 disclosure + document 分节） |
| `references/domains/electronics-communication.md` | 电子通信/AI/软件（含 disclosure + document 分节） |
| `references/domains/software-algorithm.md` | 软件/算法（含 disclosure + document 分节） |
| `references/domains/chemistry-material.md` | 化学/材料（含 disclosure + document 分节） |

### 跨 Mode 桥接

| 文件 | 内容 |
|------|------|
| `references/search-bridge-guide.md` | disclosure 模式：模型→检索要素映射 |
| `references/document-comparison-guide.md` | document 模式：多文件对照+审查员逻辑映射 |

### 输出模板

| 文件 | 对应 Mode |
|------|----------|
| `assets/templates/disclosure-output-template.md` | disclosure |
| `assets/templates/document-output-template.md` | document |
| `assets/templates/search-output-template.md` | search |
