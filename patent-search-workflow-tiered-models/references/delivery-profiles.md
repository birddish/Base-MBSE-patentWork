# 交付档位

新案件默认 `delivery_profile=standard`。所有档位均保持中文、英文、日文、韩文、法文、德文的全球检索，以及 CN、US、JP、KR、EP、WO/PCT 的结果分布或范围限制记录；档位只决定交付深度和编排强度，不缩减检索范围。

| 档位 | 适用场景 | 最小交付 | 分层编排 |
|---|---|---|---|
| `quick` | 首轮候选发现、范围探索 | 范围/基准日、六语查询、原始结果位置、候选清单、`risk_register` | Luna/Terra 候选发现；无需 V2 运行目录或脚本 |
| `standard` | 常规内部检索或轻量跨 Skill 交接 | quick 内容、核心文献全文定位、公开日；FTO 风险候选的法律状态、特征证据矩阵、初步报告 | 使用轻量 `search_context.json` 和 `search_handoff.json`；无需任务、签名、快照或哈希 |
| `formal` | 正式交接、申请布局、无效或 FTO 论证 | standard 内容、正式报告、号码清单、完整策略/日志、适用的证据包、代理师确认 | 维持 `multi-model-orchestration/2.0`、Sol 审核与现有 V2 校验 |

`quick` 和 `standard` 禁止 X/Y/A、NB/IS、无效/侵权/新颖性/创造性结论及可交接 FTO 结论；只有 `formal` 的查新/无效案件可以填写正式判断对象。

## 推进与状态

案件仅使用 `working`、`evidence_ready`、`final_reviewed` 三个进度状态。待补检、异常法域分布、疑似截断、证据缺口和范围限制统一写入 `risk_register`。

`quick` 和 `standard` 可将阶段 1–3 合并为 `search_run.md/json`；其中必须保留范围、查询、原始结果、六法域分布、候选与风险。只有 `formal` 使用不可变 `query-definition/1.0`、`query-run/1.0`、完整任务合同和正式工作簿。

## 轻量交接

轻量 `search_context.json` 必填 `schema_version=search-context/lightweight-1.0`、`delivery_profile`、`case_id`、`mode`、`mode_payload`、六语/六法域范围、特征集标识和输入范围。轻量 `search_handoff.json` 必填 `schema_version=search-handoff/lightweight-1.0`、`delivery_profile`、`case_id`、查询、原始结果位置、六法域分布、文献、证据和 `risk_register`。

正式 V2 交接保持 `search-context/2.0` 与 `search-handoff/2.0`。既有 V2 目录默认视为 `formal`；不迁移、不降级。

核心文献的特征公开必须始终有可定位全文；无效证据必须核验公开日；FTO 风险专利必须核验指定权利地域的法律状态。只有报告主张完整提取或完整覆盖、或运行出现截断/异常时，才要求分页、分批、法域拆分及完整工作簿证明。
