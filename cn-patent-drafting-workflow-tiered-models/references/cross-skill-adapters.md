# 检索与OA跨技能适配器

## 1. 检索适配器

阶段2向`patent-search-workflow-tiered-models`发送符合`search-context/2.0`的`search_context.json`，至少包含：

- 源/目标Skill及版本、来源任务、案件、上游快照ID/哈希、基准日和检索模式；
- `CHAIN/PU/PST/IU`及`pst_boundary_signature`；
- 检索特征组、不可检索内容、六法域/六语范围；
- 逐文件版本/哈希、原文证据位置、允许写回对象和旧结果失效条件。

检索技能返回符合`search-handoff/2.0`的`search_handoff.json`：来源/审核任务、控制器执行记录、查询运行来源、候选文献、证据等级、全文定位、`DOC/EV/NB/IS`候选或审核记录、实际/允许写回、失效对象、未决Q及输入哈希。每个`verified_finding`必须独立携带Sol审核任务、全文证据与查询运行来源；否则保持`candidate/unverified`。

## 2. OA适配器

阶段9向`cn-oa-reexam-opinion-drafting-tiered-models`发送符合`oa-context/2.0`的`oa_context.json`，至少包含：

- 源/目标Skill及版本、来源任务、上游快照、已提交权利要求、说明书、附图版本和逐文件哈希；
- `CLM/CF/EV/DOC/NB/IS`、提交基准日和支持位置；
- 审查意见/驳回决定、审查员使用的权项版本；
- 允许修改特征、禁止改变边界和待核事项。

OA技能以`oa-handoff/2.0`回写：来源任务、Sol审核任务和执行记录、新的权利要求集合、答复稿、重算门结果、证据包前后哈希、实际写回、失效对象和未决事项。安全默认值为`candidate/unverified/recalculation_gate_passed=false`且正式新对象为空。仅在重算门通过、哈希一致、Sol审核记录存在且代理师确认后，才能成为活动版本候选。回写时新增版本，不覆盖申请前对象。

外部边界文件与内部模型文件严格分名：跨技能使用`search_context.json → search_handoff.json`、`oa_context.json → oa_handoff.json`；单个模型任务仅使用`task_context.json → task_handoff.json`。

## 3. 接收校验

任何适配器存在以下情形即拒绝接收：Schema不是V2、缺少源/目标Skill版本或来源/审核任务、快照/逐文件哈希不匹配、活动版本不唯一、证据无原文位置、候选输出冒充已核验、写回范围超出授权、开放失效事件命中或失效对象仍被标为活动。校验不得只比较顶层键集合。
