# 检索上下文与查询运行合同

## 1. 检索案件清单

`formal` 除通用`case_context_manifest.json`外建立`search_context.json`：模式、基准日、权利判断地域、六法域/六语范围、活动特征集ID及哈希、PU/PST/IU边界签名、benchmark、活动查询版本和证据等级规则。`standard` 使用 `search-context/lightweight-1.0`；`quick` 可只使用 `search_run.md/json`。

## 2. 查询运行

每次实际查询生成不可变`query_run_id`，记录完整检索式及哈希、数据库/工具、日期、分页或分批参数、命中数、结果文件、覆盖法域、输入特征集哈希和实际模型。查询或特征变化必须新建运行，不覆盖旧记录。

Luna只能执行已在`approved_query_ids`中的查询。Terra生成候选查询；Sol 对同一批次进行一次范围批准，并只对基准日/范围冲突、异常结果、补检或法域拆分进行风险复核。未改变正文、特征集或参数的查询不得重复批准。

## 3. 三类结果

| 类别 | 生成者 | 含义 |
|---|---|---|
| `raw_hit` | Luna | 查询返回、书目或文本命中，不表示技术相关 |
| `candidate_match` | Terra | 候选相关性和优先级，不表示特征公开 |
| `verified_finding` | Sol | 已核验书目/全文/法律状态并可进入正式对比 |

核心技术特征结论必须有权利要求、段落或附图定位。摘要级和相似度只能进入候选发现。

## 4. 输出

`search_handoff.json`记录输入快照、活动特征集、查询运行、文献证据等级、全文位置、候选/审核结论、未决Q、写回对象和失效条件。返回申请撰写技能时还必须携带`pst_boundary_signature`。
