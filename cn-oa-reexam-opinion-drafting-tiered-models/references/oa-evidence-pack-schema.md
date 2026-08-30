# OA专利证据包合同（v2.2-oa）

`patent_evidence_pack.json`是申请文件、活动权利要求、MBSE模型、审查意见、修改和答复之间的唯一结构化交接件。新案件必须使用`schema_version: "v2.2-oa"`。旧OA 2.0/2.1包一律拒绝，不提供迁移；申请前1.1包只能作为阶段零来源，由`scripts/normalize_oa_evidence_pack.py`创建全新的v2.2包。

## 1. 必需对象

基础对象：`case/documents/claims/feature_groups/evidence/novelty_assessments/inventive_step_assessments/office_action_issues/claim_amendment_events/response_trace/readiness/version_history`。

V2.2控制对象：

- `claim_sets`与唯一`active_claim_set_id`；
- `claim_dependency_graph`；
- `analysis_snapshots`与唯一`active_snapshot_id`；
- `issue_registry`；
- `amendment_strategies`与唯一`primary_strategy_id`；
- `novelty_summaries`和`inventive_step_summaries`；
- `recalculation_gate`。

## 2. 权利要求依赖图和完整路径

每个活动权利要求必须显式给出：

```json
{
  "id": "CLM-02",
  "claim_type": "dependent",
  "depends_on_claim_ids": ["CLM-01"]
}
```

独立项的`depends_on_claim_ids`必须为空；从属项必须列出直接父项。校验器检查父项存在性、自引用、重复、引用环、文本一致性，并从真实依赖图生成所有从根到本项的完整路径。关系不明时依赖图为`blocked`、活动快照为空，禁止伪造`SELF`路径。

```json
{
  "id": "PATH-CLM-02-01",
  "claim_id": "CLM-02",
  "ancestor_claim_ids": ["CLM-01"]
}
```

## 3. 文献资格与结论强度

每篇文献的`eligibility`必须分别记录`novelty`、`inventive_step`、总`status`和理由。评价轴允许`eligible/conditional/Q/ineligible/not_applicable`；总状态使用`D/I/Q/X`。

- `ineligible/not_applicable/Q`以及总状态`Q`不得支撑确定NB/IS；相应判断必须为`conclusion_status=undetermined`、`risk=undetermined`。
- `conditional`不得支撑`confirmed`。
- 新颖性判断卡只允许一个`document_id`。
- 创造性组合候选必须含`same_function_or_problem/motivation/interface_compatibility/reasonable_expectation_of_success`；任一决定性字段为`Q`时组合路径不得闭合。

## 4. 复合唯一键与汇总结论

活动判断卡唯一键：

- NB：`snapshot_id + claim_id + path_id + document_id`；
- IS：`snapshot_id + claim_id + path_id + closest_document_id`。

每个`claim_id + path_id + snapshot_id`还必须分别存在且仅存在一个活动`novelty_summary`和`inventive_step_summary`。汇总对象必须引用同一路径的底层判断卡，不能用重复卡片掩盖冲突。

## 5. 快照和冻结哈希

活动分析快照冻结：活动权利要求ID、全部完整路径、依赖图、文献资格快照和主策略。`frozen_hash`由这些对象按UTF-8、键排序、无多余空白的确定性JSON计算。活动快照必须唯一；旧快照的NB/IS和答复追溯不得继续`active`。

## 6. 全案覆盖与局部影响闭包

`recalculation_gate`分别记录：

```json
{
  "snapshot_id": "OA-SNAP-01",
  "impact_seed_claim_ids": ["CLM-01"],
  "impact_claim_ids": ["CLM-01", "CLM-02"],
  "impact_path_ids": ["PATH-CLM-01-01", "PATH-CLM-02-01"],
  "full_expected_nb_keys": [],
  "full_expected_is_keys": [],
  "full_completed_nb_keys": [],
  "full_completed_is_keys": [],
  "impact_expected_nb_keys": [],
  "impact_expected_is_keys": [],
  "impact_completed_nb_keys": [],
  "impact_completed_is_keys": [],
  "response_trace_switched": false,
  "old_analysis_invalidated": false,
  "dependency_graph_valid": false,
  "document_qualification_clear": false,
  "passed": false
}
```

全案NB/IS覆盖以全部活动权利要求路径计算；局部影响闭包仅从修改种子经真实依赖图向引用后代传播。二者必须分开校验，不能把影响闭包直接等同全部活动权利要求。

## 7. 正式输出门

`oa_context_manifest.json`是必需文件，必须使用`oa-context-manifest/2.0`并与证据包的案件、活动对象和重算门一致。以下任一情形禁止`approved_draft`：重算门为假、存在决定性Q/无资格文献、依赖图阻断、旧快照仍活动、缺少Sol审核执行记录、哈希不一致或缺少代理师确认。
