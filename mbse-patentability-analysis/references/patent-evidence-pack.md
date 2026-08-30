# 专利证据与论证包合同

本合同是申请前 MBSE、查新检索、申请撰写与审查意见答复之间的唯一结构化交接件。它记录技术事实和证据，不替代专利代理师的法律判断。每个案件在专用运行目录中维护 `patent_evidence_pack.json`；报告型交付物引用其中 ID，不重复改写事实。

## 一、状态与 ID

| 类别 | 允许值 | 含义 |
|---|---|---|
| 事实证据状态 | `D` / `I` / `Q` / `X` | 明确核验 / 受限推断 / 待核验 / 排除 |
| 交底来源状态 | `D` / `N` / `G` / `Q` / `X` | 仅 disclosure 可使用 `N`（发明人确认新增）和 `G`（指向 D/N 的概括） |
| 判断状态 | `draft` / `reviewed` / `agreed` | 草稿 / 已复核 / 代理师确认 |

使用稳定 ID：`CLM`（候选权利要求）、`CF`（特征组）、`REL`（必要关系）、`EV`（证据）、`DOC`（文献）、`NB`（新颖性判断卡）、`IS`（创造性判断卡）。不得重用已废止 ID；通过 `supersedes` 记录替代关系。

## 二、版本策略

- `schema_version=1.0`和`1.1`继续兼容只读校验，不得原地迁移或覆盖。
- 新成果统一生成`schema_version=1.2`。1.2保留1.1的技术模型、阶段1—3工作流和权利要求映射对象，并增加CHAIN角色、排除台账、PST权项消费策略门、组合消费状态、两轴证据成熟度和分型指标。
- 1.0、1.1与1.2均不把模型或判断卡作为法律结论；版本变化通过新文件和`version_history`记录。

## 三、1.0最小JSON结构

```json
{
  "schema_version": "1.0",
  "case": {
    "case_id": "CASE-001",
    "jurisdiction": "CN",
    "reference_date": "YYYY-MM-DD",
    "status": "draft"
  },
  "claims": [{"id": "CLM-01", "version": "v0.1", "text": "候选权利要求", "feature_group_ids": ["CF-01"]}],
  "feature_groups": [{"id": "CF-01", "text": "技术特征组", "node_ids": ["S1", "B1"], "relation_ids": ["REL-01"], "source_refs": ["EV-01"], "description_support_refs": [], "status": "D"}],
  "documents": [{"id": "DOC-D1", "publication_number": "", "publication_date": "YYYY-MM-DD", "role": "prior_art_candidate", "bibliographic_source": "", "status": "D"}],
  "evidence": [{"id": "EV-01", "document_id": "DOC-D1", "location": "权利要求1/段落[0001]/图1", "excerpt_or_summary": "", "fact_status": "D"}],
  "novelty_assessments": [],
  "inventive_step_assessments": [],
  "prosecution_events": [],
  "version_history": []
}
```

`CF` 必须同时指向：至少一个模型节点或必要关系、至少一条交底/申请来源证据，以及已撰写时的说明书支持位置。没有完整来源的 `CF` 标记为 `Q`，不得进入正式独立权利要求。

## 四、1.1基础扩展与1.2增量

1.1在1.0结构上增加：

```json
{
  "schema_version": "1.1",
  "case": {
    "case_id": "CASE-001",
    "jurisdiction": "CN",
    "reference_date": "YYYY-MM-DD|Q",
    "status": "draft|reviewed|agreed",
    "draft_mode": "prereview|formal",
    "target_claim_count": null
  },
  "model": {
    "R": [], "F": [], "S": [], "B": [], "E": [],
    "IF": [], "CV": [], "STATE": []
  },
  "workflow": {
    "chains": [],
    "protectable_units": [],
    "protection_subjects": [],
    "contexts": [],
    "innovation_units": [],
    "combination_support": [],
    "admission_records": [],
    "claim_mappings": [],
    "dependency_graph": {"nodes": [], "edges": [], "formal_audit": "passed|failed|Q", "semantic_audit": "passed|failed|Q"},
    "compression": {"performed": false, "before_count": 0, "after_count": 0, "reason": ""},
    "metrics": {
      "v1_master_claim_count": 0,
      "v2_master_claim_count": 0,
      "v2_independent_claim_count": 0,
      "closed_chain_count": 0,
      "open_chain_count": 0,
      "pu_candidate_count": 0
    }
  }
}
```

### 1.2可观察接口

1.2沿用上面的1.1字段，并至少增加：

```json
{
  "schema_version": "1.2",
  "workflow": {
    "chains": [{
      "id": "CHAIN-01",
      "chain_role": "main_chain|open_candidate|strengthening_subchain"
    }],
    "exclusion_records": [{
      "id": "EXC-01",
      "source_node_ids": ["S-X"],
      "fact_status": "[X]",
      "drafting_status": "[X]",
      "reason": "非技术广告或其他排除理由",
      "evidence_ids": ["EV-01"]
    }],
    "claim_branch_inventory": [{
      "id": "BR-01",
      "semantic_key": "稳定技术回退语义",
      "pu_id": "PU-01",
      "pst_id": "PST-01",
      "feature_group_ids": ["CF-02"],
      "relation_ids": ["REL-02"],
      "source_refs": ["EV-01"],
      "fallback_value": "passed|failed|Q",
      "non_redundancy": "passed|failed|Q",
      "source_support": "passed|failed|Q",
      "pst_compatibility": "passed|failed|Q",
      "claim_consumption_status": "consumed_dependent|reserved|paused|excluded|Q",
      "consumption_reason": "消费或不消费理由",
      "claim_id": "CLM-02|null"
    }],
    "protection_subjects": [{
      "id": "PST-01",
      "claim_consumption_status": "consumed_independent|consumed_dependent|reserved|paused|excluded|Q",
      "consumption_reason": "消费或不消费理由",
      "strategy_gate": {
        "independent_value": "passed|failed|Q",
        "implementation_actor": "passed|failed|Q",
        "source_support": "passed|failed|Q",
        "search_boundary": "passed|failed|Q",
        "filing_layout": "passed|failed|Q",
        "status": "passed|confirmed|failed|Q"
      }
    }],
    "metrics": {
      "closed_main_chain_count": 0,
      "open_candidate_count": 0,
      "strengthening_subchain_count": 0,
      "excluded_record_count": 0,
      "pu_candidate_count": 0
    }
  }
}
```

排除记录与PU/PST集合互斥，不占用PU或PST编号。`technicality=failed`或`drafting_admission=excluded`的对象必须移入排除台账，不能继续保留为PU。报告中的对象结论必须与证据包集合一致。

`claim_branch_inventory`是从属权项的唯一消费台账。每个`consumed_dependent`分支的四项门必须均为passed，并回指唯一从属权利要求；每项进入母版的从权也必须恰好回指一条已消费分支。同一PST下相同`semantic_key`不得拆成多项。未消费分支须保留理由和去向。

### 1. 模型节点

`model`中的每个节点至少记录`id/text/fact_status/drafting_status/source_refs`。状态分别只允许`[D]/[I]/[Q]/[X]`和`[D]/[N]/[G]/[Q]/[X]`。F节点还须记录`system_boundary/input/transformation/output/trigger`；E节点还须记录`affected_object/affected_attribute/result/conditions/causal_source_ids`。E的因果来源须回指S、B、IF、CV或STATE节点，且E不得与F或F.Output同义反复。`[N]`节点增加：

```json
"technical_confirmation": {
  "subject": "发明人或有权技术人员",
  "date": "YYYY-MM-DD",
  "content": "确认内容",
  "basis": "实施或文件依据",
  "ctx_ids": ["CTX-01"]
}
```

`[G]`节点增加`generalizes_from_ids`，且其来源节点必须为`drafting_status=[D]`或`[N]`。

### 2. CHAIN、PU、PST、CTX和IU

```json
{
  "chains": [{
    "id": "CHAIN-01", "r_ids": ["R-01"], "f_ids": ["F-01"],
    "s_ids": ["S-01"], "b_ids": ["B-01"], "e_ids": ["E-01"],
    "ctx_ids": ["CTX-01"], "state_ids": ["STATE-01"],
    "if_ids": [], "cv_ids": [], "technical_closure": "closed|open|Q",
    "chain_role": "main_chain|open_candidate|strengthening_subchain",
    "relationship_type": "independent-of|alternative-to|depends-on|strengthened-by|none",
    "strengthens_pu_id": null, "gaps": []
  }],
  "protectable_units": [{
    "id": "PU-01", "chain_ids": ["CHAIN-01"],
    "source_maturity": "mature|partial|Q",
    "search_maturity": "检索设计|初筛线索|全文定位|比对完结|Q",
    "text_location_maturity": "线索|说明书片段|说明书全文|权利要求全文|附图定位|Q",
    "legal_evidence_maturity": "书目未核|公开日未核|基准日前资格已核|单文献覆盖已核|Q",
    "drafting_admission": "admitted|conditional|paused|excluded|Q",
    "technicality": "passed|failed|Q", "unity_review": "passed|risk|Q",
    "existing_application_review": "clear|risk|Q", "conditions": []
  }],
  "protection_subjects": [{
    "id": "PST-01", "pu_id": "PU-01", "type": "部件|产品|组合产品|方法|装置|其他",
    "semantic_key": "稳定对象边界语义",
    "enumeration_basis": "原始材料中的独立对象或步骤来源",
    "boundary_difference": "相对同PU其他PST的对象、主体或STATE边界差异",
    "textual_mirror": false,
    "boundary_signature": "稳定边界摘要", "external_objects": [],
    "core_state_actor": "对象", "object_integrity": "passed|failed|Q",
    "integrity_reason": "结论依据",
    "claim_consumption_status": "consumed_independent|consumed_dependent|reserved|paused|excluded|Q",
    "consumption_reason": "消费或不消费理由",
    "strategy_gate": {
      "independent_value": "passed|failed|Q",
      "implementation_actor": "passed|failed|Q",
      "source_support": "passed|failed|Q",
      "search_boundary": "passed|failed|Q",
      "filing_layout": "passed|failed|Q",
      "status": "passed|confirmed|failed|Q"
    }
  }],
  "contexts": [{"id": "CTX-01", "text": "方案语境", "source_refs": ["EV-01"], "status": "[D]|[I]|[Q]|[X]"}],
  "innovation_units": [{
    "id": "IU-01", "pu_id": "PU-01", "pst_id": "PST-01",
    "chain_ids": ["CHAIN-01"], "pst_boundary_signature": "与PST一致",
    "search_maturity": "初筛线索",
    "text_location_maturity": "说明书片段",
    "legal_evidence_maturity": "Q",
    "valid": true, "supersedes": null
  }]
}
```

`workflow.chains`的1.2角色分型为：闭合`main_chain`通常形成PU；`open_candidate`只保存补正后可能独立形成PU的路线；`strengthening_subchain`只强化既有PU，不得形成PU或独权，也不得计入开放候选。`IU(PU,PST)=SearchProjection(PU|PST_boundary)`；边界签名改变时，旧IU必须失效并新建IU。

`search_maturity`在1.2中只作兼容字段。技术文本定位深度记录于`text_location_maturity`，书目、公开日、基准日前资格和单文献覆盖的法律证据成熟度记录于`legal_evidence_maturity`；前者较高不得自动提升后者。

### 3. 组合、准入、映射和依赖图

`combination_support.conclusion`只允许`allowed/conditional/prohibited/Q`。`conditional`须记录`conditions`及`satisfied`；`prohibited/Q`不得关联进入母版的权利要求。1.2还须记录`source_support_status/boundary_compatibility/unity_status/claim_consumption_status/consumption_reason`。`allowed`不当然等于必须生成组合权项；任何实际进入权利要求的组合必须记录已消费状态和非空理由，未消费组合须记录其他去向。

`admission_records`至少回指PU/PST，记录`technical_closure/source_maturity/text_location_maturity/legal_evidence_maturity/search_maturity/drafting_admission`、阶段2是否完成、条件和理由。`open_candidate`不得进入正式母版；只有列明条件时可作为`conditional/paused`预审对象。

`claim_mappings`至少记录`claim_id/claim_type/chain_ids/pu_id/pst_id/ctx_ids/feature_group_ids/relation_ids/evidence_ids/master_included`。独权必须反向定位至`main_chain`、准入PU、客体完整PST、通过的权项消费策略门、CTX、CF/REL和证据。`strengthening_subchain`不得成为独权来源；PST消费状态不是`consumed_independent`时不得映射为独权。

`dependency_graph`的节点记录`claim_id/claim_type/multiple_dependent`，边记录`from_claim_id/to_claim_id/alternative`。多项从权不得引用另一多项从权；每条路径还须通过语义兼容审计。

`case.target_claim_count=null`时，`workflow.compression.performed`必须为`false`且`before_count=after_count`。

`workflow.metrics`是回归统计快照，而非另一个判断对象。1.2校验器必须重新计算母版权项数、独权数、闭合主链、开放候选、强化子链、排除记录和PU候选数并与快照核对；`pu_candidate_count`不得包含排除记录，`open_candidate_count`不得包含强化子链。`v1_master_claim_count`只记录未被覆盖的旧版基线。不得仅凭权项数量减少推导方法质量提高。

## 五、新颖性判断卡（NB）

每张卡只允许一个 `claim_id` 和一个 `document_id`。文献公开日必须早于案件基准日，或明确标为“抵触申请待核验”。逐一记录每个必要 `CF` 的公开位置与 `D/I/Q/X` 状态。

```json
{
  "id": "NB-01",
  "claim_id": "CLM-01",
  "document_id": "DOC-D1",
  "date_status": "prior_art_confirmed",
  "feature_coverage": [{"feature_group_id": "CF-01", "evidence_id": "EV-01", "disclosure": "explicit", "status": "D"}],
  "single_document_rule": true,
  "risk": "high|medium|low|undetermined",
  "reason": "仅说明已核验的单文献覆盖情况",
  "status": "reviewed"
}
```

只有同一文献对全部必要 `CF` 有明确披露，或对技术人员可直接、无歧义确定的必然隐含披露，才可记录“高新颖性风险”。不得用多文献拼接、可能性推测、相似度分数或摘要级线索填写完整覆盖。未检得文献只能表述为“在记录的检索范围内未见”，不得写成具有新颖性。

## 六、创造性三步法判断卡（IS）

每张卡以一个权利要求和一篇最接近现有技术为主线；可引用第二文献或公知常识，但必须分别提供证据。

```json
{
  "id": "IS-01",
  "claim_id": "CLM-01",
  "closest_document_id": "DOC-D1",
  "distinguishing_feature_group_ids": ["CF-02"],
  "technical_effects": [{"effect_node_id": "E1", "evidence_ids": ["EV-02"], "status": "D"}],
  "objective_technical_problem": "不包含区别特征或其解决手段的技术任务",
  "combination_candidates": [{
    "document_id": "DOC-D2",
    "teaching_evidence_ids": ["EV-03"],
    "same_function_or_problem": "D|I|Q|X",
    "motivation": "D|I|Q|X",
    "interface_compatibility": "D|I|Q|X",
    "reasonable_expectation_of_success": "D|I|Q|X"
  }],
  "engineering_analysis_refs": ["兼容性/融合失败分析编号"],
  "risk": "high|medium|low|undetermined",
  "status": "reviewed"
}
```

在 `IS` 中，MBSE 的接口冲突、时序冲突、效果抵消和问题消解只作为工程分析证据；结论必须转换为“缺少技术启示”“存在适配障碍”“不能合理预期该效果”或“事实待核验”。缺少结合动机、兼容性或合理成功预期之一时，风险状态至少为 `undetermined`，不得写成创造性被否定。

## 七、审查程序交接与回写

`prosecution_events` 至少记录审查意见/驳回决定版本、引用文献、权利要求版本、事实核实 ID、答复草案版本及变更影响。审查意见答复可以新增证据或替代 `CLM/CF`，但必须保留旧 ID 与 `supersedes` 链；影响必要特征、实际技术问题或检索范围时，回退至检索和创造性判断卡复核。

进入OA场景时，按答审技能的 `v2.1-oa` 合同扩展但不改写本包原ID：建立 `claim_sets/active_claim_set_id`、`analysis_snapshots/active_snapshot_id`、`issue_registry`、`amendment_strategies/primary_strategy_id` 和 `recalculation_gate`。同时输出权利要求评价台账：`权利要求版本→引用路径→TA→NB→IS/IC→OA问题→答复段落`。

文献事实来源状态和法律资格必须分轴：`D/I/Q/X` 只表示材料事实强度，`eligible/conditional/Q/ineligible/not_applicable` 分别表示新颖性或创造性用途。仅具新颖性资格的抵触申请候选不得进入创造性路径。

权利要求修改后按影响闭包重新生成TA及区别链；闭包包括直接修改项、所有引用后代和因编号、主题或路径变化受影响的权项。活动集合的每个有效引用路径均须有NB，以及 `full/inherited/no_separate_issue` 之一的IS/IC记录。主策略与备选策略使用不同集合及快照，禁止混入同一活动区别链。

## 八、质量门

- 每个 `DOC` 有公开号、公开日、书目来源与核验状态；
- 每个核心 `EV` 有权利要求、段落或附图定位；
- 每个 `NB` 只引用一个文献；
- 每个 `IS` 的技术问题不含区别特征表述；
- `I` 必须列明明确前提，`Q/X` 不得作为结论前提；
- 最终法律文书不展示内部 ID 或状态标签。
- 1.0/1.1包继续通过`scripts/validate_patent_evidence_pack.py`只读校验；1.2包还须通过CHAIN角色、排除互斥、PST消费策略门、两轴成熟度、组合消费、分型指标及报告一致性检查。

## 九、最小验证情景

每次更新流程后，使用下列脱敏情景检查模板与交接：

| 情景 | 必须观察到的结果 |
|---|---|
| 机械：单一 D1 覆盖全部必要 `CF` | `NB` 可记录高新颖性风险，且每个 `CF` 有定位证据 |
| 电子/软件：D1 与 D2 分别覆盖不同特征 | 不得写入 `NB` 完整覆盖；只建立 `IS`，缺少动机/兼容性/成功预期时保持“无法判断” |
| 生化/材料：区别效果只有主张无验证 | 效果标记 `Q`，不得作为 `IS` 的优越效果前提 |
| 审查意见：修改独立权利要求 | 新建 `CLM` 版本并保留 `supersedes`；受影响的 `NB/IS` 回到复核状态 |
