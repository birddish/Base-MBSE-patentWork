# 多模型上下文、交接与失效合同 V2

本合同仅适用于 `delivery_profile=formal`，采用`multi-model-orchestration/2.0`、`multi-model-task/2.0`、`multi-model-handoff/2.0`、`multi-model-routing/2.0`和`multi-model-invalidation/2.0`。所有1.x正式运行目录一律拒绝；须新建V2目录，不提供迁移器。`quick/standard` 改按 `delivery-profiles.md` 的轻量交接规则运行。

## 1. 发布门与执行模式

- `execution_mode=advisory`：只建议模型层级；`actual_model_id/actual_model_tier/execution_record_id`必须为空，`authority_class=unverified`，不得产生`verified_finding/approved_draft`。
- `orchestrated`：必须读取控制器写入`execution_records/<id>.json`的真实执行记录，并与不可变模型映射、路由账本及案件目录外的控制器签名收据核对。信任存储通过`--trust-store`传入且不得位于可写案件目录；收据必须由本Skill内置固定公钥验证，并校验固定`issuer/key_id`、有效期、nonce及吊销状态。模型自报身份、案件内自改注册表、任意外部普通JSON或仅重算SHA-256均不构成证明。
- `orchestration_status=enabled`允许正式编排，但`verified_finding/approved_draft`及正式回写仍须同时满足控制器执行记录、活动快照、Sol权限和代理师确认要求。

## 2. 运行目录

```text
case_context_manifest.json
model_registry.json
routing_ledger.json
invalidation_ledger.json
execution_records/<execution_record_id>.json
tasks/<task_id>/task_context.json
tasks/<task_id>/task_handoff.json
staging/luna/
staging/terra/
reviewed/sol/
confirmed/attorney/
```

控制器另维护案件目录外的`controller-trust/1.0`存储，记录固定模型映射、签名执行收据、签名跨Skill授权、签名发布收据和吊销清单。执行收据必须同时绑定`task_context_hash`、`task_handoff_hash`、`output_hash`及适用时的`cross_handoff_hash`。`assets/orchestration/controller-trust-store.template.json`只定义格式，不是运行时信任根；私钥不得保存于Skill或案件目录。

OA案件还必须有`oa_context_manifest.json`。模板及本地Schema目录位于`assets/orchestration/`。

## 3. V2任务合同

`task_context.json`固定包含：`case_id/task_id/workflow/stage/execution_mode`、`assigned_tier`、`task_context_hash`、活动快照ID/哈希、逐输入文件版本/哈希、允许和禁止动作、预期输出/结果类别、合并目录白名单、依赖及失效触发。

`task_handoff.json`固定包含：相同身份和快照字段、`actual_model_id/actual_model_tier/execution_record_id`、`task_handoff_hash`、权限类别、生命周期`active/stale/invalidated/superseded`、输出文件及哈希、证据、合并目标、依赖、升级/失效原因和阻断标记。上下文与交接的共享字段及`input_snapshot_hash`必须逐字段一致。缺失或含糊内容仅允许`proposed_status=Q`或`unverified`。

## 4. 确定性哈希

- JSON对象按UTF-8、键排序、无多余空白序列化；对象自身的目标哈希字段不参与该对象哈希。
- 普通源文件按原始字节计算SHA-256。
- 案件活动快照由快照ID和逐输入文件记录规范化后计算；任务必须锚定案件当前活动快照。
- 任务`source_inputs`和跨Skill`source_files`只能是活动快照逐文件记录的子集，不得私自引入新材料。
- `task_context_hash`、`task_handoff_hash`、执行记录哈希、跨Skill`context_hash/handoff_hash`、目标活动快照、检索快照和输出集合哈希均由校验器重算，不能只比较字符串。

## 5. 权限和目录

| 层级 | 输出类别 | 允许目录 | 明确禁止 |
|---|---|---|---|
| Luna | `extraction/raw_hit` | `staging/luna/` | 正式事实、NB/IS、活动权项、确认目录 |
| Terra | `candidate/review/candidate_match` | `staging/terra/` | 正式NB/IS、正式状态、活动权项、确认目录 |
| Sol | `review/approved_draft/verified_finding` | `reviewed/sol/` | 代理师确认、无证据补全 |
| 代理师 | `confirmed` | `confirmed/attorney/` | 以策略确认创造技术事实 |

校验器同时检查`merge_target`和每个生成文件均落在任务白名单及不可修改的层级固定根目录内，并要求实际文件集合与`expected_outputs`一致；不得用任务自授白名单或路径字符串模糊匹配代替目录边界。

## 6. 路由、失效和并行

路由账本记录控制器分配、改派、执行记录和状态；失效台账记录影响任务、对象、快照及输出路径的事件。开放失效事件命中当前任务或其依赖时失败关闭。旧产物必须标为`stale/invalidated/superseded`，不得回流。

仅在输入快照一致且写入目标不冲突时并行。上游边界、活动权利要求、核心证据或主策略变化时，冻结受影响任务并按真实依赖图传播失效。

## 7. 跨Skill接口

请求和返回必须记录源/目标Skill及版本、来源任务、审核任务、控制器执行记录、源案件、上游/目标活动快照、逐文件版本和哈希、原文证据位置、允许/实际写回和失效对象、权限、审核状态及代理师确认引用。编排请求的写回范围必须由上游签名授权收据绑定；正式写回必须有可重算的文件路径和原始字节哈希。检索结论必须精确引用已登记的`DOC/EV`，且返回特征集、PST边界和检索快照必须与签名请求及Sol签名输出一致。

安全默认值固定为`output_class=candidate`、`authority_class=unverified`、`recalculation_gate_passed=false`，新版本和正式写回对象为空。跨Skill对象使用`search-context/2.0`、`search-handoff/2.0`、`oa-context/2.0`、`oa-handoff/2.0`并进行嵌套语义校验。

## 8. 对外交付

对外申请文件、检索报告和OA答复不得显示模型名称、路由账本、任务ID或内部状态。内部合同与对外交付分文件保存。
