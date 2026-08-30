# 阶段9：审查程序交接与回写

本阶段在提交申请后、收到审查意见通知书或驳回决定时启动。它不替代 `cn-oa-reexam-opinion-drafting` 的五阶段答复流程，而是提供统一输入、版本控制和回写规则。

字段、状态与版本规则读取 `../../mbse-patentability-analysis/references/patent-evidence-pack.md`。

## 输入

1. 已提交的权利要求、说明书、附图及其版本；
2. `patent_evidence_pack.json`、`novelty_assessment.md`、`inventive_step_assessment.md`；
3. 审查意见/驳回决定原文、引用对比文件及审查员的权利要求版本；
4. 后续检索、实验或发明人确认材料（如有）。

## 交接清单

生成 `prosecution_handoff.md`，至少列出：案件基准日、当前 `CLM/CF/EV/DOC/NB/IS` ID、提交版本、审查员主张、引用文献、已核验事实、待核验事项、可修改特征及其原始支持位置。将该清单与原材料交给 `cn-oa-reexam-opinion-drafting`。

## 回写规则

- 审查意见答复中的事实核实、补充全文证据和组合分析回写为 `EV/NB/IS` 更新；
- 修改权利要求时新增 `CLM` 版本并以 `supersedes` 链接旧版，重新核验受影响的 `CF`、说明书支持与 `NB/IS`；
- 新对比文件、实际技术问题或必要特征变化时，回退阶段2A/2B；
- 最终答复书只使用法律语言，不展示内部 ID、状态或 MBSE 节点编号。

## 输出与确认

| 交付物 | 内容 | 确认人 |
|---|---|---|
| `prosecution_handoff.md` | 答复输入和待核实清单 | 代理师 |
| 更新后的证据包 | 版本、证据与判断卡回写 | 代理师 |
| 变更影响表 | 权利要求、说明书、检索和答复的回退范围 | 代理师 |

授权后归档最终权利要求版本、审查历史、证据包和版本链，以供后续无效、FTO 或组合分析复用。
