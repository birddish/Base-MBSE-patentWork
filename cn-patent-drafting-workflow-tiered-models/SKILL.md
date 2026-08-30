---
name: cn-patent-drafting-workflow-tiered-models
description: 按Luna、Terra、Sol分层执行的中国专利九阶段撰写工作流。用于需要在MBSE、检索、撰写、审计与审查交接之间明确模型权限、交接与升级条件的案件。
---

# 中国专利撰写全流程：Luna / Terra / Sol 分工版

将本技能用于中国专利申请的端到端撰写辅助。它保留原工作流的九阶段、对象合同、证据包和代理师确认门，仅新增模型分工与升级规则；不取代原版工作流。输出视为执业辅助，不作法律保证。

## 模型路由（启动必选）

本版本仅接受`multi-model-orchestration/2.0`运行目录；所有1.x编排数据必须明确拒绝并新建V2目录，不提供迁移。每个案件先选择`execution_mode=advisory/orchestrated`，每个工作项再指定`assigned_tier=Luna/Terra/Sol`。当前发布状态为`orchestration_status=enabled`；正式`orchestrated`输出仍须通过控制器执行记录、活动快照、Sol审核和代理师确认门。进入任一阶段时，必须同时读取`references/model-routing-contract.md`、`references/context-and-handoff-contract.md`、`references/stage-model-io-contract.md`及该阶段原有参考文件。跨技能任务另读`references/cross-skill-adapters.md`。

- **Luna**：仅做可复核的提取、转写、整理、格式化和静态检查；不能确认技术或法律事实。
- **Terra**：基于已定位证据形成候选模型、初稿和问题清单；输出默认是候选或预审，不能越过确认门。
- **Sol**：负责跨证据技术推理、MBSE/权利要求架构、NB/IS、保护布局和正式交付前的实质审核。
- **专利代理师**：确认技术/法律结论、阶段门和提交决定。Sol不得替代代理师或有权技术人员的确认。

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
| 2A/2B | 查新检索与PU准入/保护布局（委托 patent-search-workflow-tiered-models） | `references/stage-2-search-and-comparison.md` + `references/protectable-unit-contract.md` | — |
| 3 | 权利要求书撰写 | `references/stage-3-claim-drafting.md` + `references/node-claim-mapping.md` + `references/protectable-unit-contract.md` | `references/domain-rules-{M/E/C}.md` |
| 4 | 背景技术撰写 | `references/stage-4-background-technology.md` | — |
| 5 | 具体实施方式撰写 | `references/stage-5-detailed-description.md` | `references/domain-rules-{M/E/C}.md` |
| 6 | 附图MD生成（可选） | `references/stage-6-figure-markdown.md` | 图源类型按域适配 |
| 7 | VSDX生成与验收（可选） | `references/stage-7-vsdx-production.md` | 图源类型按域适配 |
| 8 | 既有申请文件审计与补强 | `references/stage-8-existing-application-audit.md` | — |
| 9 | 审查程序交接与回写（收到审查意见时） | `references/stage-9-prosecution-handoff.md` | — |

总流程索引和最终组卷规则：`references/full-process.md`。

### 九阶段模型路由摘要

| 阶段 | Luna | Terra | Sol |
|---|---|---|---|
| 1 技术建模 | 材料索引、原文定位、术语归一 | 节点/追溯链候选、待确认问题 | 模型边界、CHAIN独立性、PU/PST/CTX与技术闭合 |
| 2A 查新接口 | 生成/检查`search_context`材料清单 | 整理检索请求候选，不执行检索 | 冻结请求边界、接收并审核`search_handoff`；实际检索全部由检索Skill完成 |
| 2B 布局 | 判断卡骨架、证据索引和台账 | 候选区别关系、风险问题清单 | NB/IS、单一性、PU准入和保护布局 |
| 3 权利要求 | 编号/引用/术语检查、依赖图静态检查 | 冻结特征的预审草案、从权候选 | 必要特征、PST、概括边界、母版与提交候选版 |
| 4 背景技术 | 已确认术语和格式检查 | 基于冻结事实的初稿 | 技术问题边界、泄露检查和实质审核 |
| 5 实施方式 | 模板、交叉引用、图文编号检查 | 基于确认特征的初稿与一致性分析 | 充分公开、效果因果、支持范围和实质审核 |
| 6/7 附图 | Mermaid/VSDX初稿、标号同步 | 节点/图元与原文对齐 | 结构、状态、分支和技术关系完整性 |
| 8 审计 | 文本比对、矩阵预填、版本差异扫描 | 缺口和不一致问题清单 | 支持性、问题等级、补强和可提交性意见 |
| 9 交接 | 文件清单、版本链、ID索引 | 生成`oa_context`和待核问题 | 审核`oa_handoff`并回写版本；OA策略、修改和答复全部由OA Skill完成 |

固定执行顺序：阶段1为`Luna提取 → Terra候选模型 → Sol冻结工程边界`；阶段3—5为`Sol冻结输入边界 → Terra起草 → Luna静态检查 → Terra一致性复核 → Sol实质终审`。阶段2和阶段9的父Skill只负责请求、接收、阶段门与回写，不承接子Skill的检索或OA实质职责。

## 最高优先级红线

1. 每份实质性交付物附注：`本内容仅为执业辅助参考，最终需专利代理师本人审核确认。`（不得写入申请文件正文）
2. 不编造技术事实、对比文献、检索结果、实验数据、附图、标准或法律结论。
3. 保持 `R_problem → F<Input, Transformation, Output> → S/B/STATE → OutputState → E` 闭环；F、直接输出与E不得同义反复。
4. 分开记录事实来源、撰写采用、技术闭合、来源成熟度、检索成熟度和撰写准入状态（详见 `references/protectable-unit-contract.md` 与 `references/common-constraints.md`）。
5. 逐阶段取得专利代理师确认后方可进入下一阶段（详见 `references/confirmation-gates.md`）。
6. 保护保密信息；提示用户不要上传客户身份、无关商业秘密或撰写不需要的非公开材料。
7. Luna和Terra不得把候选内容写入正式`fact_status`、`drafting_status`、`technical_closure`、`search_maturity`、`drafting_admission`、`NB`或`IS`结论；无法精确定位的内容默认`Q`并升级。
8. 对话历史不得替代案件事实源；新会话、模型切换或上下文压缩后，必须从`case_context_manifest.json`和当前`task_context.json`恢复。
9. 每个模型任务必须生成`task_handoff.json`；下游只能读取其中声明的交付物、输入快照哈希和未决问题，不得凭对话补齐缺失事实。
10. 跨技能边界固定为`search_context.json → search_handoff.json`和`oa_context.json → oa_handoff.json`；不得与内部任务文件混名。

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
| 证据包与判断卡 | `../mbse-patentability-analysis/references/patent-evidence-pack.md` | 向后兼容1.0及新版1.1合同；1.1承载模型、CHAIN/PU/PST/CTX/IU、准入、映射、依赖图及`CLM/CF/EV/DOC/NB/IS` |
| 工作流回归测试 | `references/workflow-regression-cases.md` | 四个跨领域用例与三个阻断性失败场景的验收预期 |
| 模型路由合同 | `references/model-routing-contract.md` | Luna/Terra/Sol权限、阶段分工、路由记录、升级和审校规则；每个工作项必读 |
| 上下文与交接合同 | `references/context-and-handoff-contract.md` | 执行模式、上下文切片、暂存目录、交接、失效与并行规则 |
| 阶段模型I/O | `references/stage-model-io-contract.md` | 九阶段各模型的输入、输出及失效触发 |
| 跨技能适配器 | `references/cross-skill-adapters.md` | 检索和OA的机器可读交接及回写边界 |
| 多模型回归 | `references/model-orchestration-regression-cases.md` | 越权、旧快照、跨技能哈希和会话恢复阻断用例；由`scripts/validate_model_orchestration.py`和`scripts/validate_cross_skill_contracts.py`校验 |

## 领域规则索引

| 域 | 文件 | 状态 |
|---|---|---|
| 机械/结构 | `references/domain-rules-mechanical.md` | 初始骨架，含待确认清单 |
| 电子通信/AI/软件 | `references/domain-rules-electronics.md` | 已确立规则（含AI/软件/算法专项） |
| 生化/材料 | `references/domain-rules-biochemical.md` | 初始骨架，含待确认清单 |

## 快速路由

- 仅需技术交底书 MBSE 分析 → `mbse-patentability-analysis` 技能（`mode=disclosure`）
- 仅需独立查新/无效/FTO/态势检索并要求模型分工 → `patent-search-workflow-tiered-models` 技能
- 仅需审查意见答复并要求模型分工 → `cn-oa-reexam-opinion-drafting-tiered-models` 技能
- 仅需专利文本 MBSE 建模与多文件对照 → `mbse-patentability-analysis` 技能（`mode=document`）
- 仅需专利附图标注 → `patent-figure-labeling` 技能
