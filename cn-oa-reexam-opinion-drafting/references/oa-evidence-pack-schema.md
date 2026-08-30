# OA 专利证据包 Schema（v2.1-oa）

## 1. 目的、版本与兼容性

`patent_evidence_pack.json` 是申请文件、MBSE模型、审查意见、权利要求修改和答复之间的唯一结构化交接件。`v2.1-oa` 继承 `v2.0-oa` 的 `DOC/CLM/CF/REL/EV/NB/IS/OA/AMD/RT` 语义，新增活动权利要求集合、分析快照、问题注册表、修改策略和重算门。

- 新任务必须写 `schema_version: "2.1-oa"`。
- `v2.0-oa` 仍可读取，但只能通过兼容性基础校验；应使用 `scripts/normalize_oa_evidence_pack.py` 生成不覆盖的 `v2.1-oa` 副本。
- 升级保留原ID、原文、证据定位和 `D/I/Q/X` 事实语义；活动集合、文献资格或主策略无法唯一确定时必须标 `Q/candidate/blocked`，不得猜测。

## 2. 顶层字段

在 `v2.0-oa` 全部字段基础上，必须增加：

```json
{
  "claim_sets": [],
  "active_claim_set_id": "CLMSET-...",
  "analysis_snapshots": [],
  "active_snapshot_id": "SNAP-...",
  "issue_registry": [],
  "amendment_strategies": [],
  "primary_strategy_id": "STR-...",
  "recalculation_gate": {}
}
```

活动ID只能各指向一个 `status=active/primary` 对象。不能确定时ID置空，相关对象置 `candidate` 或 `blocked`，并使重算门失败。

## 3. 事实状态与文献法律资格双轴

模型节点、关系、证据和事实主张继续使用：

- `D`：材料明确记载；
- `I`：依规则从已记载事实受限推断；
- `Q`：材料不足、冲突或待核验；
- `X`：明确排除或与原文矛盾。

文献对每个评价轴分别使用：

```json
"eligibility": {
  "novelty": "eligible | conditional | Q | ineligible | not_applicable",
  "inventive_step": "eligible | conditional | Q | ineligible | not_applicable",
  "status": "D | I | Q | X",
  "reason": "资格事实、日期和法律角色说明"
}
```

`conditional` 只表示测试材料已明确给出日期或角色、但官方材料尚待核验；日期缺失、互相冲突或抵触申请条件无法判断时必须为 `Q`。仅具抵触申请新颖性资格的文件，其 `inventive_step` 必须为 `ineligible`。

## 4. 权利要求集合与引用路径

`claims` 中每个新版本必须有稳定ID、`version`、完整文本、`feature_group_ids`、`status`；替代旧版本时写 `supersedes` 并由 `claim_amendment_events` 指向。

`claim_sets` 至少记录：

```json
{
  "id": "CLMSET-AMENDED-01",
  "claim_ids": ["CLM-NEW-01", "CLM-NEW-02"],
  "status": "active | candidate | superseded | invalidated",
  "supersedes": "CLMSET-ORIGINAL",
  "fact_status": "D"
}
```

任一时点必须且只能有一组活动权利要求。活动从属项按每条合法引用路径展开；路径记录写入活动快照的 `claim_paths`，不得只评价其新增限定。

## 5. 分析快照

阶段三前冻结：

```json
{
  "id": "SNAP-01",
  "claim_set_id": "CLMSET-AMENDED-01",
  "claim_paths": [
    {"id": "PATH-C2-C1", "claim_id": "CLM-NEW-02", "ancestor_claim_ids": ["CLM-NEW-01"]}
  ],
  "document_eligibility": {
    "DOC-D1": {"novelty": "eligible", "inventive_step": "eligible"}
  },
  "primary_strategy_id": "STR-01",
  "status": "active",
  "frozen_hash": "SHA256..."
}
```

`frozen_hash` 对上述四项冻结内容的规范化JSON计算。全部活动 `NB/IS/RT` 必须引用同一 `active_snapshot_id`；旧快照记录只能为 `superseded/invalidated`。

## 6. 问题注册表

每个OA问题以法律依据、权利要求范围、文献组合路径和主张类型形成稳定指纹：

```json
{
  "id": "IR-01",
  "issue_id": "OA-01",
  "fingerprint": {
    "legal_basis": "专利法第二十二条第三款",
    "claim_ids": ["CLM-NEW-01"],
    "document_path": ["DOC-D1", "DOC-D2"],
    "assertion_type": "inventive_step"
  },
  "status": "active"
}
```

`issue_registry`、`office_action_issues` 与活动 `response_trace.issue_ids` 必须一一对应；OA问题调整颗粒度时新建注册记录并明确替代关系，不得悄然合并或遗漏。

## 7. 主修改策略与原子修改事务

`amendment_strategies` 的 `status` 取 `primary/candidate/blocked/superseded`。必须且只能有一个 `primary_strategy_id`；备选策略使用独立权利要求集合和快照，不得混入当前NB/IS、区别链或答复。

修改必须按以下顺序作为一个事务执行：

```text
新建CLM版本
→ 记录supersedes和支持依据
→ 使旧NB/IS/RT失效
→ 冻结新活动权利要求集合
→ 计算修改影响闭包
→ 重新生成TA
→ 重算全部受影响NB/IS
→ 切换response_trace
→ 通过recalculation_gate
```

修改影响闭包包括直接修改项、其全部引用后代，以及因编号、引用路径或保护主题改变而受影响的权利要求。修改支持为 `Q` 时策略只能是 `candidate/blocked`。

## 8. NB/IS评价记录

每条活动权利要求的每条有效引用路径必须各有NB和IS记录，增加：

```json
{
  "path_id": "PATH-...",
  "assessment_mode": "full | inherited | no_separate_issue",
  "conclusion_status": "confirmed | conditional | undetermined",
  "snapshot_id": "SNAP-01",
  "lifecycle_status": "active | superseded | invalidated"
}
```

- `full`：针对完整展开对象进行完整评价；
- `inherited`：明确引用某一上位路径评价并补充本项新增限定；
- `no_separate_issue`：OA未对该路径单独争议，但仍记录其继承对象、证据资格和为什么无需独立展开。

每个NB仍只允许一个 `document_id`；新颖性不得多文献拼接。创造性候选文献必须在快照的 `inventive_step` 轴具备资格。

## 9. 决定性Q传播

| 决定性对象为Q | 强制结果 |
|---|---|
| 日期或法律资格 | 对应NB/IS `conclusion_status=undetermined`、`risk=undetermined` |
| NB覆盖特征 | 不得认定完整覆盖或明确不覆盖 |
| 修改支持 | 策略只能 `candidate/blocked` |
| 技术启示、动机、接口兼容或成功预期 | IS组合路径不得闭合 |
| 活动集合或主策略 | 不得产生活动快照，重算门失败 |

`Q` 不能被说明文字、风险字段、相似度、模型推断或一般常识补足。文献资格为 `conditional` 时结论至多为 `conditional`，不得为 `confirmed`。

## 10. 重算门

```json
"recalculation_gate": {
  "snapshot_id": "SNAP-01",
  "impact_claim_ids": ["CLM-NEW-01"],
  "impact_path_ids": ["PATH-CLM-NEW-01-SELF"],
  "expected_nb_keys": ["CLM-NEW-01::PATH-CLM-NEW-01-SELF"],
  "expected_is_keys": ["CLM-NEW-01::PATH-CLM-NEW-01-SELF"],
  "completed_nb_keys": ["CLM-NEW-01::PATH-CLM-NEW-01-SELF"],
  "completed_is_keys": ["CLM-NEW-01::PATH-CLM-NEW-01-SELF"],
  "response_trace_switched": true,
  "old_analysis_invalidated": true,
  "passed": true
}
```

阶段四定稿必须要求预期与完成集合相等、答复已切换、旧分析已失效。门禁未通过时，只能生成内部条件性草稿。

## 11. 就绪状态与标准交付

`readiness.content_status` 取 `pass/conditional/fail`；`submission_status` 取 `ready/blocked`。存在材料、日期、修改支持、范围取舍、期限、形式信息或客户确认阻塞时，不得标 `ready`。

验证器直接要求标准文件名 `00`—`09`、`run-metadata.json`，其中：

- `08-模型到答复追溯报告.md`
- `09-质量审计与提交状态.md`

运行：

```powershell
python scripts/validate_oa_delivery.py <run_dir> --report <run_dir>/validation.json
```

结构性判断只读取JSON；文本扫描仅用于对外答复内部ID和少量禁止措辞检查。
