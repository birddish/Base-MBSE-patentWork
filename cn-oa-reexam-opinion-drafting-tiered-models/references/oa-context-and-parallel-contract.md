# OA上下文、并行与原子修改合同

## 1. 覆盖层

模型运行信息不写入`v2.2-oa`法律对象，另建必需的`oa_context_manifest.json`、`routing_ledger.json`和`invalidation_ledger.json`。覆盖层必须引用`active_claim_set_id`、`active_snapshot_id`、`primary_strategy_id`、问题注册表和`recalculation_gate`，并与案件活动快照逐字段、逐哈希一致。

## 2. 问题级上下文切片

每个任务原则上按一个或一组相关`issue_id`切片，且必须包含：活动权利要求的完整引用路径、审查员原始主张、相关申请文件和对比文件原文、文献资格、当前主策略、输入快照哈希及禁止使用的旧快照。

Sol审核时必须可访问完整活动权利要求集合和原始文件，不得只读Luna/Terra摘要。

## 3. 并行

同一`active_snapshot_id`且写入对象不冲突的事实定位、对比和草稿任务可并行。权利要求、文献资格、问题颗粒度或主策略变化时冻结相关任务；旧快照产物标为`stale/invalidated`。

## 4. Sol原子修改事务

```text
Sol提出候选修改
→ 新建CLM版本和支持依据
→ 代理师确认范围取舍
→ 旧NB/IS/RT失效
→ 冻结新活动集合/快照
→ 从真实依赖图计算修改项及引用后代的局部影响闭包
→ 重算闭包内TA、NB、IS，并另行核验全案NB/IS完整覆盖
→ 切换response_trace
→ recalculation_gate通过
```

Luna/Terra可以生成候选红线，但不能设置`active_claim_set_id`、`primary_strategy_id`或使重算门通过。

## 5. 接收与对外输出

来自申请撰写技能的`oa_context.json`必须符合`oa-context/2.0`，含源/目标Skill版本、来源任务、提交版权项及各文件版本/哈希、原文证据位置、证据包哈希、可修改特征、保护边界和待核事项。OA完成后以`oa-handoff/2.0`返回审核任务和执行记录、新旧权项关系、证据包前后哈希、重算门状态、实际/允许写回、失效对象及未决事项。默认必须为候选、未核验、重算门关闭；只有重算通过、哈希一致、Sol审核记录存在且代理师确认后，才可成为活动版本候选。内部任务只使用`task_context.json/task_handoff.json`。对外答复不得显示模型、任务、快照或内部ID。
