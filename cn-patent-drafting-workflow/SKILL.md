---
name: cn-patent-drafting-workflow
description: 中国专利全领域九阶段撰写工作流，覆盖机械/结构、电子通信/AI/软件、生化/材料发明。引导MBSE建模、保护单元准入、查新检索（委托patent-search-workflow）、权利要求撰写、说明书撰写、可选附图制作、既有申请文件审计及审查程序交接。当Codex收到中文或英文撰写、修改、审计或管理完整中国专利申请工作流的请求时使用。
---

# 中国专利撰写全领域九阶段工作流

将本技能用于中国专利申请的端到端撰写辅助。输出视为执业辅助，不作法律保证。

## 领域类型选择（启动必选）

在开始任何实质性工作前，确认领域类型：

| 代码 | 领域 | 典型发明 |
|------|------|----------|
| **M** | 机械/结构 | 传动机构、装配结构、流体机械、医疗器械结构、建筑构件 |
| **E** | 电子通信/AI/软件 | 信号处理、网络协议、天线、AI模型、算法、数据结构、控制 |
| **C** | 生化/材料 | 组合物、制备方法、材料配方、化学反应路径、基因序列 |

可组合选择（如 M+E 表示机电一体化方案）。领域选择决定各阶段的建模方法、权利要求特征类型、实施方式结构和附图工具链。

## 九阶段主链

默认按“阶段1→阶段2A/2B→阶段3→阶段4→阶段5→阶段8→最终组卷”推进；提交后收到审查意见时启动阶段9。阶段6、阶段7仅在用户明确要求时启动。

| 阶段 | 内容 | 必读通用文件 | 域补充文件 |
|------|------|-------------|-----------|
| 1 | 技术建模 | `references/stage-1-mbse-modeling.md` + `references/protectable-unit-contract.md` | M域/C域补充规则 |
| 2A/2B | 查新检索与PU准入/保护布局（委托 patent-search-workflow） | `references/stage-2-search-and-comparison.md` + `references/protectable-unit-contract.md` | — |
| 3 | 权利要求书撰写 | `references/stage-3-claim-drafting.md` + `references/node-claim-mapping.md` + `references/protectable-unit-contract.md` | `references/domain-rules-{M/E/C}.md` |
| 4 | 背景技术撰写 | `references/stage-4-background-technology.md` | — |
| 5 | 具体实施方式撰写 | `references/stage-5-detailed-description.md` | `references/domain-rules-{M/E/C}.md` |
| 6 | 附图MD生成（可选） | `references/stage-6-figure-markdown.md` | 图源类型按域适配 |
| 7 | VSDX生成与验收（可选） | `references/stage-7-vsdx-production.md` | 图源类型按域适配 |
| 8 | 既有申请文件审计与补强 | `references/stage-8-existing-application-audit.md` | — |
| 9 | 审查程序交接与回写（收到审查意见时） | `references/stage-9-prosecution-handoff.md` | — |

总流程索引和最终组卷规则：`references/full-process.md`。

## 最高优先级红线

1. 每份实质性交付物附注：`本内容仅为执业辅助参考，最终需专利代理师本人审核确认。`（不得写入申请文件正文）
2. 不编造技术事实、对比文献、检索结果、实验数据、附图、标准或法律结论。
3. 保持 `R_problem → F<Input, Transformation, Output> → S/B/STATE → OutputState → E` 闭环；F、直接输出与E不得同义反复。
4. 分开记录事实来源、撰写采用、技术闭合、来源成熟度、文本定位成熟度、法律证据成熟度和撰写准入状态；排除内容只进入排除台账，不得成为PU/PST（详见 `references/protectable-unit-contract.md` 与 `references/common-constraints.md`）。
5. 逐阶段取得专利代理师确认后方可进入下一阶段（详见 `references/confirmation-gates.md`）。
6. 保护保密信息；提示用户不要上传客户身份、无关商业秘密或撰写不需要的非公开材料。

## 通用机制索引

详细规则已下沉到独立 reference 文件，SKILL.md 仅保留路由摘要：

| 机制 | 文件 | 核心内容 |
|------|------|----------|
| 可保护单元对象合同 | `references/protectable-unit-contract.md` | `CHAIN/PU/PST/CTX/STATE`、F/E边界、双状态轴、IU投影、准入与组合支持硬门；阶段1—3、8以此为唯一对象定义来源 |
| 共同约束与状态使用 | `references/common-constraints.md` | 事实来源与撰写采用分轴、主创新点锚定卡、证据闭环、四层映射账本 |
| 版本台账与母本控制 | `references/state-and-version-control.md` | 状态台账、版本母本链、变更影响台账、最终DOCX母本一致性 |
| 工作空间目录与文件编号 | `references/workspace-conventions.md` | 文件夹结构、会话序号规则、版本留存 |
| 确认门与版本回退 | `references/confirmation-gates.md` | 阶段确认单、硬确认门、回退触发条件 |
| 撰写护栏 | `references/drafting-guardrails.md` | 独权必要特征、主创新点前置、母版→提交候选版分配、实施方式三块结构 |
| 交付规则 | `references/delivery-rules.md` | Markdown交付、硬换行、正文与审校分离 |
| 节点-权项四层映射 | `references/node-claim-mapping.md` | MBSE→CHAIN/PU/PST/CTX→CF/REL/CT/INT→权项映射账本、语言转换和变更回写 |
| 证据包与判断卡 | `../mbse-patentability-analysis/references/patent-evidence-pack.md` | 向后兼容1.0/1.1及新版1.2合同；1.2增加CHAIN角色、排除台账、PST权项消费策略门、两轴证据成熟度和分型指标 |
| 工作流回归测试 | `references/workflow-regression-cases.md` | 四个机械/结构主导用例、F-0至F-15阻断场景及对象枚举/从属分支消费回归预期 |

## 领域规则索引

| 域 | 文件 | 状态 |
|---|---|---|
| 机械/结构 | `references/domain-rules-mechanical.md` | 初始骨架，含待确认清单 |
| 电子通信/AI/软件 | `references/domain-rules-electronics.md` | 已确立规则（含AI/软件/算法专项） |
| 生化/材料 | `references/domain-rules-biochemical.md` | 初始骨架，含待确认清单 |

## 快速路由

- 仅需技术交底书 MBSE 分析 → `mbse-patentability-analysis` 技能（`mode=disclosure`）
- 仅需独立查新/无效/FTO/态势检索 → `patent-search-workflow` 技能
- 仅需审查意见答复 → `cn-oa-reexam-opinion-drafting` 技能
- 仅需专利文本 MBSE 建模与多文件对照 → `mbse-patentability-analysis` 技能（`mode=document`）
- 仅需专利附图标注 → `patent-figure-labeling` 技能
