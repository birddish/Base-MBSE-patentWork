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
一条独立闭合CHAIN → 一个PU候选
一个准入PU × 一个PST → 一项独立权利要求候选
一个PU可以派生多个PST
独立替代CHAIN → 平行独权或另案候选
非独立强化子链 → 才可作为从属权利要求增量候选
```

`workflow.chains`可以保留`technical_closure=open/Q`的缺口记录，以便补正和统计；但只有`closed`记录满足CHAIN的正式对象定义并可作为通常PU来源。`open`记录只有在明确列出补正条件时，才可形成`conditional`预审PU；不得进入正式母版。PU还须接受来源、检索、客户既有申请、技术性、单一性和撰写准入审查。独立闭合CHAIN不得仅因与另一链共享产品、场景或宽泛效果而降格为该链的从属特征。

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
| `search_maturity` | `检索设计/初筛线索/全文定位/比对完结/Q` | 分别表示已设计、仅有线索、全文已定位、比对已复核或状态待核 |
| `drafting_admission` | `admitted/conditional/paused/excluded/Q` | `admitted`进入；`conditional`满足列明条件后进入；`paused`暂缓；`excluded`排除；`Q`待决 |

`[N]`只能由发明人或有权技术人员确认，并绑定确认主体、日期、确认内容、实施依据和适用CTX。代理师确认法律表达、保护层级和申请策略，不得单独创造技术事实。`[G]`必须指向一个或多个[D]或[N]对象并记录共同技术属性，不得生成新结构、关系、参数或效果。未经技术确认的[I]在撰写采用轴按[Q]控制，不得进入正式母版。

`open`不得对应`drafting_admission=admitted`。只有列明缺口、补正事项、责任主体和完成条件时，才可作为`conditional`预审对象；条件未满足前仍不得进入正式母版。正式母版只消费`admitted`或条件已经满足并留下确认记录的`conditional`。

## 五、检索投影视图

保留现有创新单元`IU`作为PU在特定PST边界下面向`patent-search-workflow-tiered-models`的检索投影视图：

```text
IU(PU,PST) = SearchProjection(PU | PST_boundary)
```

每个IU必须回指PU、PST、来源CHAIN、当前`PST_boundary`签名、检索特征组和检索基准日。IU不是新的保护单元，也不反向决定PU的必要特征。PST变化导致系统边界、必要对象、必要关系或行为条件变化时，旧IU立即失效；必须按新边界重新生成IU，并对变化部分补检和重新确认。

## 六、CTX组合支持门

多个特征分别出现不等于特定组合已经获得支持。拟组合内容必须记录：

| 组合ID | 特征组 | 各自证据 | CTX/交叉引用 | 原文是否允许组合 | 共同属性 | 共同功能或效果 | 互斥条件 | 结论 |
|---|---|---|---|---|---|---|---|---|

CTX组合结论只允许`allowed/conditional/prohibited/Q`：`allowed`可按记录语境采用；`conditional`仅在列明条件满足后采用；`prohibited`不得组合；`Q`保持待核。`prohibited/Q`以及条件未满足的`conditional`不得进入正式母版。

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

## 八、PU准入与落位

PU准入表至少记录：PU、来源CHAIN、必要节点和关系、CTX、PST、三种成熟度、检索风险、客户既有申请影响、单一性风险、准入状态和理由。准入后的业务落位统一为：

```text
独权必要 / 从权强化 / 说明书预留 / 另案候选 / 暂停 / 排除
```

技术闭合不等于证据成熟，证据成熟不等于撰写准入，撰写准入也不等于具有新颖性、创造性或授权前景。暂停或另案PU必须保留技术模型、理由和重新启动条件，不得从模型中静默删除。

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
