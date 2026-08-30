# 专利检索多模型回归用例

1. 摘要级文献由Luna/Terra标X/Y：必须阻断，保持`raw_hit/candidate_match`。
2. Luna或Terra填写正式NB/IS：必须阻断并移回暂存区。
3. NB引用两篇文献：必须阻断新颖性结论。
4. IS缺少实际技术问题、动机、兼容性或成功预期：保持Q/无法判断。
5. 特征集哈希变化后沿用旧查询命中数：旧运行失效，重做筛选和报告。
6. PST边界改变但沿用旧IU结果：拒绝回接申请撰写技能。
7. 六法域覆盖不全且无缩减授权：不得进入报告确认。
8. `execution_mode=orchestrated`但无`actual_model`：路由审计失败。
9. `search_context/search_handoff`在申请撰写端与检索端字段或版本不一致：接口校验失败，不启动查询或回写。
