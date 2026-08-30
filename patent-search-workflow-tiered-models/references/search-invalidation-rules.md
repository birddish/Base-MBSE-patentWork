# 检索失效与重算规则

| 变化 | 必须失效/重算 |
|---|---|
| 基准日 | 文献时间资格、NB/IS和报告结论 |
| 特征集/权利要求/产品规格 | 检索块、查询、筛选、核心文献、对比和报告 |
| PST或IU边界 | 对应查询运行、全文对比和判断卡 |
| 检索模式或权利地域 | 法律状态、筛选标准、FTO/无效评价 |
| 查询文本、分类或范围 | 命中数、结果集、覆盖统计和下游筛选 |
| 摘要升级为全文 | 该文献的覆盖、X/Y/A及NB/IS候选 |
| 核心文献增删 | 对比表、NB/IS和报告结论 |
| 法律状态更新 | FTO候选和权利风险结论 |

失效事件写入`invalidation_ledger.json`。依赖旧`feature_set_hash/query_version/pst_boundary_signature`的任务和产物不得进入`evidence_ready/final_reviewed`。
