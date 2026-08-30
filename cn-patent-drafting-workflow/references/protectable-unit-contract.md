# 保护单元、保护主题与撰写准入合同

本文件是阶段1至阶段3、阶段8共同使用的唯一对象与状态合同。各阶段只记录或消费本文件定义的对象，不得另设同义对象或把技术闭合直接等同于独立权利要求候选。

## 一、核心对象

```text
CHAIN = 在确定CTX中，由R_problem经F、S/B及必要IF/CV到达E，且功能与效果均闭合的候选技术链
PU    = 经证据、检索和撰写准入审查的最小保护单元
PST   = 由PU派生的部件、产品、组合产品、方法、装置等候选保护主题
CTX   = 保存实施例、选择分支、互斥条件和组合依据的方案语境
STATE = <InitialState, Trigger, PrimaryPowerSource,
         ActionInterface, Transition, OutputState>
EXC   = 不满足技术性或明确不进入保护布局的排除记录；只保留来源、理由和证据，不是PU或PST
```

`R_problem`记录需要技术手段解决的核心工程问题；`R_context`记录工况、环境和使用对象。数值、材料、几何、比例、时序窗口和逻辑守卫进入CV，不得混写为新的技术问题。

`IF`（Interface）表示结构、对象、信号、能量或数据之间的必要接口；`CV`（Constraint Variable）表示数值、材料、几何、比例、时序、阈值、环境及逻辑守卫等约束变量。

| 基础符号 | 定义 |
|---|---|
| `R` | Requirement，需求层；在本合同中拆为`R_problem`和`R_context` |
| `F` | Function，`<SystemBoundary, Input, Transformation, Output, PreconditionOrTrigger>`；描述系统应完成的技术变换及直接输出 |
| `S` | Structure，承载功能的结构、组成、模块、对象及配置关系 |
| `B` | Behavior，输入、触发、处理、动作、时序、分支及状态迁移 |
| `E` | Effect，`<AffectedObject, AffectedAttribute, Consequence, ApplicableCondition, CausalPath, Evidence, EffectType, ComparisonBaseline?>`；描述输出状态进一步造成的对象属性变化或技术后果 |

CHAIN、PU、PST和CTX均为由R/F/S/B/E技术模型派生的撰写中间对象，不构成新的MBSE核心层，也不替代单一性、支持、新颖性、创造性或最终保护策略判断。

### F与E边界合同

不新增独立O层。`F.Output`是功能规格中的预期直接输出；`STATE.OutputState`是具体B执行后形成的可观察状态。二者可以对应，但都不当然等于E。E必须说明该输出状态在确定条件下进一步改变了哪个技术对象的何种属性，并回指具体的S/B/REL/CV因果路径和证据。

```text
R_problem
→ requires → F<Input, Transformation, Output>
→ allocated-to → S
→ realized-by → B/STATE
→ produces → OutputState
→ contributes-to → E
→ addresses → R_problem
```

E若与F使用相同动作和对象、仅表述“实现了F”、直接复制`F.Output/OutputState`，或者脱离S/B/REL/CV仍被宣称成立，应删除、改列为`F.Output`或按Q控制。`EffectType=absolute`时不强制比较；`EffectType=comparative`时必须记录比较基线、差异方向和适用范围。同一条CHAIN内，同一句技术陈述不得同时作为F和E。

## 二、统一映射规则

```text
一条独立闭合main_chain → 一个PU候选
一个准入PU × 一个客体完整PST × 一个通过的权项消费策略门 → 一项独立权利要求候选
一个PU可以派生多个PST
独立替代CHAIN → 平行独权或另案候选
非独立强化子链 → 才可作为从属权利要求增量候选
```

`workflow.chains[*].chain_role`只允许`main_chain/open_candidate/strengthening_subchain`。`main_chain`须为`closed`并可形成通常PU来源；`open_candidate`保存补正后可能独立形成PU的技术路线，只有明确列出补正条件时才可形成`conditional/paused`预审对象；`strengthening_subchain`只强化既有PU，不得形成PU或独权，也不得计入`open_candidate_count`。广告、纯信息表达、商业规则和其他双轴`[X]`内容不进入`workflow.chains`，只进入`workflow.exclusion_records`。PU还须接受来源、检索、客户既有申请、技术性、单一性和撰写准入审查。独立闭合CHAIN不得仅因与另一链共享产品、场景或宽泛效果而降格为该链的从属特征。

CHAIN按技术作用拓扑而不是按实施例数量拆分。两个实施例若具有相同的R_problem、F变换、必要S/REL、B/STATE迁移和E因果路径，只是执行件形态、动力来源、安装位置或参数不同，应共享同一`main_chain`，差异进入从属分支；只有删除其他路线后仍保有不同的最低必要结构/关系、状态迁移或效果因果路径，才形成新的`main_chain`。材料、合金、参数或性能目标不能因名称和预期效果齐全就标为closed；缺少组成/范围、作用机制、适用条件或效果因果证据时必须作为`open_candidate`并列出补正条件。

### 排除记录合同

`workflow.exclusion_records`用于保存已经分析但不得进入保护对象集合的内容。每条记录至少包含`id/source_node_ids/fact_status/drafting_status/reason/evidence_ids`；其中事实轴和撰写轴均须为`[X]`。排除记录不得占用PU或PST编号，不得出现在`protectable_units/protection_subjects/innovation_units/admission_records/claim_mappings`中。`technicality=failed`或`drafting_admission=excluded`的对象不得保留为PU；应移动至排除记录并保留退出理由。报告声称某对象已经排除时，证据包必须同步不存在相应PU/PST。

## 三、关系类型

| 关系 | 适用对象 | 处理规则 |
|---|---|---|
| `independent-of` | CHAIN—CHAIN | 删除另一链后仍能独立形成技术闭环，分别形成PU候选 |
| `alternative-to` | CHAIN/PU—CHAIN/PU | 两条完整路线相互替代，原则上形成平行主题或另案候选 |
| `depends-on` | CHAIN/PU—CHAIN/PU | 当前链需要另一链的输入、状态或核心手段才能工作 |
| `strengthened-by` | PU—特征组/子链 | 附加内容强化效果或稳定性，但不是PU最低闭合条件；不得单独形成PU或独权 |
| `shares-interface-with` | CHAIN/PU/PST—CHAIN/PU/PST | 共享接口不当然构成同一发明构思 |
| `supported-in-context-by` | PU/PST/特征组—CTX | 特定组合在相应方案语境中获得支持 |
| `candidate-for-unity-with` | PU—PU | 仅提示可能共享同一或相应特别技术特征，须继续接受法律审查 |

## 四、状态合同

以下状态彼此独立，不得合并为一个总状态：

| 状态字段 | 允许值 | 含义 |
|---|---|---|
| `fact_status` | `[D]/[I]/[Q]/[X]` | `[D]`原始材料明确记载；`[I]`单层受限工程推断；`[Q]`待核实；`[X]`排除 |
| `drafting_status` | `[D]/[N]/[G]/[Q]/[X]` | `[D]`以明确记载采用；`[N]`经有权技术确认的新增事实；`[G]`专利化概括；`[Q]`暂不准入；`[X]`排除 |
| `technical_closure` | `closed/open/Q` | `closed`须同时通过功能闭合与效果闭合；`open`存在已识别缺口；`Q`材料不足以判断 |
| `source_maturity` | `mature/partial/Q` | `mature`来源完整；`partial`部分有据且缺口已定位；`Q`来源边界不明 |
| `search_maturity` | `检索设计/初筛线索/全文定位/比对完结/Q` | 1.0/1.1兼容字段；1.2不得单独依靠该字段作证据资格判断 |
| `text_location_maturity` | `线索/说明书片段/说明书全文/权利要求全文/附图定位/Q` | 技术文本定位深度，可与法律资格不同步 |
| `legal_evidence_maturity` | `书目未核/公开日未核/基准日前资格已核/单文献覆盖已核/Q` | 先前技术法律资格和证据核验程度 |
| `drafting_admission` | `admitted/conditional/paused/excluded/Q` | `admitted`进入；`conditional`满足列明条件后进入；`paused`暂缓；`excluded`排除；`Q`待决 |

`[N]`只能由发明人或有权技术人员确认，并绑定确认主体、日期、确认内容、实施依据和适用CTX。代理师确认法律表达、保护层级和申请策略，不得单独创造技术事实。`[G]`必须指向一个或多个[D]或[N]对象并记录共同技术属性，不得生成新结构、关系、参数或效果。未经技术确认的[I]在撰写采用轴按[Q]控制，不得进入正式母版。

`open`不得对应`drafting_admission=admitted`。只有列明缺口、补正事项、责任主体和完成条件时，才可作为`conditional`预审对象；条件未满足前仍不得进入正式母版。正式母版只消费`admitted`或条件已经满足并留下确认记录的`conditional`。

## 五、检索投影视图

保留现有创新单元`IU`作为PU在特定PST边界下面向`patent-search-workflow`的检索投影视图：

```text
IU(PU,PST) = SearchProjection(PU | PST_boundary)
```

每个IU必须回指PU、PST、来源CHAIN、当前`PST_boundary`签名、检索特征组和检索基准日。IU不是新的保护单元，也不反向决定PU的必要特征。PST变化导致系统边界、必要对象、必要关系或行为条件变化时，旧IU立即失效；必须按新边界重新生成IU，并对变化部分补检和重新确认。

## 六、CTX组合支持门

多个特征分别出现不等于特定组合已经获得支持。拟组合内容必须记录：

| 组合ID | 特征组 | 各自证据 | CTX/交叉引用 | 原文是否允许组合 | 共同属性 | 共同功能或效果 | 互斥条件 | 结论 |
|---|---|---|---|---|---|---|---|---|

CTX组合结论只允许`allowed/conditional/prohibited/Q`：`allowed`可按记录语境采用；`conditional`仅在列明条件满足后采用；`prohibited`不得组合；`Q`保持待核。`prohibited/Q`以及条件未满足的`conditional`不得进入正式母版。

组合记录还须分别保存`source_support_status/boundary_compatibility/unity_status/claim_consumption_status/consumption_reason`。`allowed`只表示原始语境允许组合，不等于必须消费为权项；未消费的允许组合应记为`reserved/paused`并说明去向。任何关联母版权项的组合必须把`claim_consumption_status`记为`consumed_dependent`或`consumed_independent`；字段缺失或理由为空时不得进入母版。

## 七、PST客体完整性门

每个PST至少核查：保护对象及系统边界、外部对象、STATE完整迁移、主要执行主体和可观察实施路径。外部对象若直接完成核心状态迁移，不得作为未写明的环境条件静默补足；应比较部件主题与组合产品主题，或者调整方法/装置主题。

```text
确定保护对象边界
→ 识别外部对象
→ 检查核心STATE迁移由谁完成
→ 外部对象完成核心迁移？
  是：比较部件、组合产品、方法或装置PST，并重建IU
  否：继续必要特征测试
```

### PST权项消费策略门

客体完整性通过只说明PST构成完整候选保护主题，不当然产生独权。每个PST还须记录：

| 字段 | 要求 |
|---|---|
| `claim_consumption_status` | `consumed_independent/consumed_dependent/reserved/paused/excluded/Q` |
| `consumption_reason` | 说明进入独权、从权或不消费的具体理由 |
| `strategy_gate.independent_value` | 相对同一PU其他PST是否具有独立保护价值：`passed/failed/Q` |
| `strategy_gate.implementation_actor` | 是否具有可识别的单一实施主体和可观察实施路径：`passed/failed/Q` |
| `strategy_gate.source_support` | 对象、步骤、顺序、触发和输出是否获得支持：`passed/failed/Q` |
| `strategy_gate.search_boundary` | 是否已经建立独立IU或明确补检边界：`passed/failed/Q` |
| `strategy_gate.filing_layout` | 共案、分案、另案或不消费布局是否明确：`passed/failed/Q` |
| `strategy_gate.status` | `passed/confirmed/failed/Q`；`confirmed`须记录代理师确认主体和日期 |

只有`object_integrity=passed`、`claim_consumption_status=consumed_independent`且`strategy_gate.status=passed/confirmed`时，PST才可映射为独权。方法或装置PST若只是产品正常操作的文字镜像、实施主体不清、步骤支持不完整、检索边界未建立或共案布局待决，应保留为`reserved/Q`并记录重启条件。一个PU存在多个PST不要求全部消费；未消费PST不得静默删除。

### PST枚举完备性与去重

PST不是“每个PU自动乘以产品、方法、装置”的笛卡尔积。每个PST须具有原始材料支持的独立对象边界和可观察实施路径；方法PST还须具有可单独执行的步骤序列，而不是把产品正常使用改写成动作句。对同一PU先建立`pst_enumeration`：记录候选边界、来源、客体完整性、与其他PST的边界差异、是否仅为文字镜像及最终去向。具有相同对象边界、实施主体和核心STATE迁移的候选必须合并；失败边界重建为组合产品后，不得在无独立步骤支持时再派生重复方法PST。每个原始材料明确支持的独立PST候选必须被记录为有效、失败、保留或排除之一，不得漏记或重复计数。

### 从属权项分支消费门

在生成从属权利要求前建立`workflow.claim_branch_inventory`。一条分支不是一句话或一个参数，而是可独立选择的技术回退命题；同一命题的结构、关系和必要行为应作为一个不可分割分支，不得按措辞拆成多项。每条分支至少记录：

| 字段 | 要求 |
|---|---|
| `semantic_key` | 与编号和措辞无关的稳定技术语义 |
| `pu_id/pst_id` | 回指准入PU和兼容PST |
| `feature_group_ids/relation_ids/source_refs` | 回指特征、必要关系和原始证据 |
| `fallback_value` | 能否在修改、无效或授权回退中独立保留技术意义：`passed/failed/Q` |
| `non_redundancy` | 是否不是独权重述、正常使用说明、同义结构细化或另一分支的重复：`passed/failed/Q` |
| `source_support` | 组合、概括和效果是否有据：`passed/failed/Q` |
| `pst_compatibility` | 与所引用PST及CTX是否兼容：`passed/failed/Q` |
| `claim_consumption_status` | `consumed_dependent/reserved/paused/excluded/Q` |
| `consumption_reason/claim_id` | 记录消费或不消费理由；已消费时回指唯一从权 |

只有四项门均为passed的分支才可标为`consumed_dependent`。每个已消费分支恰好对应一项从权，每项从权恰好对应一条已消费分支；同一PST下相同`semantic_key`不得拆成多项。未消费分支必须保留去向。母版权项数由通过独权消费门的PST数与通过从属分支消费门的分支数共同决定，不得由模型任意详略或固定项数反推。

## 八、PU准入与落位

PU准入表至少记录：PU、来源CHAIN、必要节点和关系、CTX、PST、来源成熟度、文本定位成熟度、法律证据成熟度、兼容检索成熟度、检索风险、客户既有申请影响、单一性风险、准入状态和理由。准入后的业务落位统一为：

```text
独权必要 / 从权强化 / 说明书预留 / 另案候选 / 暂停 / 排除
```

技术闭合不等于证据成熟，证据成熟不等于撰写准入，撰写准入也不等于具有新颖性、创造性或授权前景。暂停或另案PU必须保留技术模型、理由和重新启动条件，不得从模型中静默删除。

`workflow.metrics`分别统计`closed_main_chain_count/open_candidate_count/strengthening_subchain_count/excluded_record_count/pu_candidate_count`。其中`pu_candidate_count`只统计`protectable_units`中的正向保护对象，不含排除记录；`open_candidate_count`不含强化子链。

`technical_closure=closed`至少要求：其一，F具有系统边界、输入、技术变换、直接输出和触发/前提，并由S及B/STATE实现；其二，至少存在一个非同义反复的E，能够识别受影响对象、属性、后果、条件、因果来源和证据。仅有输出状态而没有上述E时，技术闭合不得标为`closed`。

```text
F合同完整
→ S及B/STATE能够实现
→ 形成OutputState
→ 存在非同义E及因果证据
→ technical_closure=closed
```

## 九、预审草案与正式母版

`case.draft_mode`只允许`prereview/formal`。阶段2尚未完成证据化比对和PU准入确认时，只能设置`prereview`并生成醒目标记“预审草案”的不限项母版；不得形成正式阶段3交付。`formal`要求阶段2完成、每个进入母版的PU已正式准入、PST完整性通过、CTX组合允许或条件已满足，并完成依赖图和四层反向定位。
