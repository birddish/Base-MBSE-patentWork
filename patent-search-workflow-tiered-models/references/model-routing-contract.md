# 专利检索模型路由合同

本合同按 `delivery_profile` 适用：`quick` 仅允许 Luna/Terra 候选发现，`standard` 允许轻量证据交接，`formal` 才与`context-and-handoff-contract.md`共同适用并启用完整模型权限和验证门。

| 阶段 | Luna | Terra | Sol |
|---|---|---|---|
| 1 | 登记材料、日期、术语和原文位置 | 技术特征、F/S/B及问题候选 | 冻结模式、范围、基准日和正式特征集 |
| 2 | 六语词表整理、执行已批准查询并保存最小运行记录 | 检索块、分类号、候选查询和异常标记 | 对同批查询一次范围批准；仅处理基准日、范围或异常等高风险事项 |
| 3 | 日志、号码去重、同族归并 | 标题摘要筛选和核心文献建议 | 核心候选集、全文核验范围和补检决定；不重复审核未变化查询 |
| 4 | 全文摘录、段落/权项/图号定位、矩阵预填 | 差异、候选覆盖和待核问题 | 公开认定、X/Y/A、NB/IS、FTO/无效风险 |
| 5 | 号码、引用、覆盖表和格式检查 | 报告候选初稿 | 结论强度、限制条件和审核稿 |

`quick/standard` 中，Sol 仅处理范围、基准日、核心证据或 FTO 法律状态冲突；不得生成 X/Y/A、NB、IS 或正式风险结论。只有 `formal` 的第4–5阶段采用表中 Sol 的完整结论职责。

## 权限边界

- Luna只输出`raw_hit/extraction`；命中只表示查询返回或文本匹配。
- Terra只输出`candidate_match/candidate/review`；相关性不表示公开、有效或侵权覆盖。
- Sol输出`verified_finding/review/approved_draft`；必须回到可信全文、法律状态或官方书目证据。
- 代理师/律师确认重大FTO、无效、侵权或法律意见。

Luna/Terra遇到缺失或冲突时写`proposed_status=Q`或`unverified`并升级，不得修改正式文献资格、X/Y/A或NB/IS。`orchestrated`模式必须由控制器执行记录证明`actual_model_id/actual_model_tier`；模型自报身份不构成证明，否则使用`advisory`。
