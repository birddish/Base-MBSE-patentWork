# 申请撰写多模型回归用例

1. Terra基于旧PST边界生成权项，Sol已更新PST：旧任务必须失效，不能进入母版。
2. Luna/Terra将`proposed_status=Q`写入正式证据包：必须阻断。
3. Terra把预审草案写入`reviewed/sol`或`confirmed/attorney`：必须阻断。
4. 权利要求变化但阶段4/5/8未标待复核：失效传播失败。
5. 搜索回接的`pst_boundary_signature`不匹配：阶段2拒绝消费。
6. OA交接的提交版权项哈希不匹配：阶段9拒绝交接。
7. `execution_mode=orchestrated`但缺少`actual_model`：路由审计失败。
8. 新会话仅依据聊天摘要继续正式阶段：阻断，要求读取案件清单和任务上下文。
9. 将外部`oa_context/oa_handoff`与内部`task_context/task_handoff`混用，或生产者与消费者字段集合不一致：接口校验失败并拒绝接收。
