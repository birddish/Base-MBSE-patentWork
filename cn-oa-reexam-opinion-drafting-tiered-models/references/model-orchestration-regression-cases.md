# OA多模型回归用例

1. Luna/Terra试图修改`active_claim_set_id`：阻断并保留暂存候选。
2. Luna“未找到”直接写“无记载”：阻断，改为Q/当前范围未定位。
3. Terra基于旧快照生成答复：标记`stale`，不得进入对外稿。
4. 权利要求修改后只重算独权、不覆盖引用后代：`recalculation_gate=false`。
5. 不同主策略的NB/IS和段落拼接：五方一致性失败。
6. 修改支持为Q却激活策略：阻断。
7. `recalculation_gate=false`却输出`approved_draft`或“可提交”：阻断。
8. `execution_mode=orchestrated`但未记录`actual_model`：路由审计失败。
9. 对外答复残留模型名、任务ID、快照ID或D/I/Q/X：交付审计失败。
10. 外部`oa_context/oa_handoff`与内部`task_context/task_handoff`复用文件名或字段：接口校验失败，不得切换活动权项版本。
