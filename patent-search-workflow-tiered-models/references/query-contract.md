# 查询定义与运行合同

本合同仅适用于 `delivery_profile=formal`。`quick/standard` 将查询、原始结果、六法域分布和风险追加到 `search_run.md/json`；不创建查询定义、运行哈希或批准任务。formal 的每条批准查询保存为不可变`query-definition/1.0`，路径为`queries/definitions/<query_id>.json`，至少记录`query_id`、完整查询正文、模式、特征集哈希、批准任务、批准人、六语和六法域范围及定义哈希。`search_context.approved_query_definitions`同时绑定ID与哈希；正文、特征集或范围变化必须创建新ID。

每次执行保存为不可变`query-run/1.0`，路径为`queries/runs/<run_id>.json`，至少记录`run_id`、所引用的查询定义及哈希、原样查询正文、数据库、工具版本、分页参数、实际模型及来源任务、执行时间、结果文件及哈希、六语/六法域分布、`benchmark_hits`、`benchmark_status`、`follow_up_reason`、`run_status`、`truncation_status`和运行哈希。`benchmark_status` 为 `not_applicable/passed/pending/failed`；未命中基准必须标为 `pending` 或 `failed` 并有后续动作，但不阻断首次执行。`search_handoff.query_run_refs`必须同时绑定`run_id/run_hash`并纳入检索快照；Luna只能执行`search_context.approved_query_ids`中的原样查询。

在正式编排模式中，Luna/Terra的可合并检索输出仅允许受控JSON；Markdown报告由Sol审核后生成，避免低阶候选把X/Y/A或NB/IS写入非结构化文件绕过字段权限。

模式载荷必填字段：

| mode | 必填字段 |
|---|---|
| `novelty` | `solution_or_claim_feature_set_id`、`feature_set_version`、`baseline_date` |
| `invalidity` | `target_patent`、`active_claim_set_id`、`active_claim_set_version`、`baseline_date` |
| `fto` | `product_spec_id`、`product_spec_version`、`rights_territories`、`legal_status_checked_at` |
| `landscape` | `collection_boundary`、`time_window`、`inclusion_rules`、`exclusion_rules`、`cleaning_version` |

缩减六语或六法域范围时，必须引用结构化授权记录；否则不得在最终报告声称完整覆盖。benchmark 范围变更应记录原因和影响，不要求以此阻断原始结果保存或核心文献核验。
