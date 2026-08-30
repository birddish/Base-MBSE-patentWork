# Mode: disclosure — 技术交底书可专利性建模

## 适用范围

以发明人提供的申请前技术交底书及可选背景材料为输入。不得在本 mode 中对正式申请文件、引用对比文件、审查意见或驳回决定进行建模——这些材料交给 mode=document 处理。

## 工作流程（四阶段）

### 阶段一：R/F/S/B/E 四视角模型

1. 提取技术问题、提出的解决方案、声称的效果、术语、实施例和附图。
2. 构建五层模型：
   - **R（需求）**：技术需求、工程约束或验收目标，以"如何……"开头
   - **F（功能）**：系统应完成的输入—技术变换—直接输出合同，必要时记录系统边界和触发
   - **S（结构）**：组件、模块、连接关系、空间布局
   - **B（行为）**：活动、顺序、状态、事件、条件分支
   - **E（效果）**：由具体S/B/关系及输出状态进一步造成的对象属性变化或技术后果
3. 将每个实质性节点链接到其来源段落或附图。
4. 构建追溯链 `R → F → S → B/STATE → OutputState → E`；OutputState只是F与E之间的链路字段，不是新增模型层。将缺失或模糊信息标注为 `Q`；不得虚构效果、参数或工作关系。
5. 输出节点表、追溯链表、待确认问题表、Mermaid 图。
6. 暂停等待用户确认。

#### 交付物规格

| 表格 | 列 |
|------|-----|
| R/F/S/B/E 节点表 | `id`、`view`、`node`、`source`、`evidence_level`、`notes` |
| F功能合同表 | `id`、`system_boundary`、`input`、`transformation`、`output`、`precondition_or_trigger`、`allocated_S`、`realizing_B` |
| E效果合同表 | `id`、`affected_object`、`affected_attribute`、`consequence`、`applicable_condition`、`causal_path`、`effect_type`、`comparison_baseline`、`evidence` |
| 追溯链表 | `chain_id`、`R`、`F`、`S`、`B`、`E`、`gap_or_question` |
| 待确认问题表 | `question_id`、`missing_dimension`、`why_it_matters`、`requested_confirmation` |

Mermaid 结构图、行为图和追溯链图，其节点 ID 与表格匹配。

### 阶段二：候选创新点

从结构新颖性、功能协同、操作时序或跨视角交互中识别候选创新点。将其描述为初步技术假设，而非授权结论。

使用包含列 `innovation_id`、`R`、`F`、`S`、`B`、`E`、`source_support`、`evidence_level`、`confidence`、`inventor_question` 的表格。

筛选标准：候选创新点至少有一条完整或明确标注了断点的追溯链，否则不得输出。

暂停等待用户确认。

### 阶段三：检索要素

将已确认的创新点转换为检索要素。

仅对机器可读块输出有效的 JSON。不得在 JSON 内部包含注释。每个 JSON 对象必须包含：

- `innovation_id`、`innovation_name`
- `technical_problem`、`technical_solution`、`technical_effect`
- `evidence_level`、`search_priority`
- `search_elements`（核心术语、同义词、必要组合、可选排除词、初步 IPC 起点）
- `novelty_indicators`
- `related_patents_from_search`

暂停等待用户确认。

### 阶段四（可选）：公开资料初筛及 Google Patents 补充

仅当阶段三确认后且用户明确要求检索时才执行。

#### 4A：公开资料初筛

使用公开搜索引擎查找非专利文献、技术文档、标准、开源文档和权威技术综述。记录每条结果：

| 字段 | 说明 |
|------|------|
| `innovation_id` | 对应创新点编号 |
| `source_tier` | A(官方标准)/B(同行评审)/C(开源项目)/D(通用网络) |
| `engine_or_database` | 检索引擎或数据库 |
| `query` | 检索式 |
| `search_date` | 检索日期 |
| `title` | 文献标题 |
| `URL` | 链接 |
| `disclosed_features` | 公开的技术特征 |
| `relevance` | 相关性判断 |
| `limitation` | 局限说明 |

D 级结果不得作为技术结论的唯一依据。

输出：（1）术语和技术成熟度摘要；（2）每个创新点的风险观察；（3）正式专利检索交接文件。

#### 4B：Google Patents 补充检索

当 Google Patents 可访问时执行。记录：

| 字段 | 说明 |
|------|------|
| `innovation_id` | 对应创新点 |
| `engine_or_database` | 固定为 Google Patents |
| `query`、`filters` | 检索式及筛选条件 |
| `search_date` | 检索日期 |
| `publication_number`、`title` | 专利号及标题 |
| `applicant_or_assignee` | 申请人 |
| `earliest_priority_date`、`publication_date` | 日期 |
| `jurisdiction` | 法域 |
| `family_or_related_documents` | 同族 |
| `disclosed_features`、`feature_location` | 公开特征及位置 |
| `relevance`、`limitation` | 相关性及局限 |
| `source_URL` | 来源链接 |

对于实质性中国文献，在依赖之前应在 CNIPA 或其他权威专利数据库中核实公开号、法律状态和家族信息。

#### 4C：初步新颖性评估

对每个创新点产出评估表：

| 列 | 说明 |
|-----|------|
| `innovation_id`、`innovation_name` | 标识 |
| `public_source_evidence` | 公开资料证据摘要 |
| `Google_Patents_evidence` | Google Patents 证据摘要 |
| `same_or_corresponding_features` | 相同或对应特征 |
| `missing_or_distinguishing_features` | 缺失或区别特征 |
| `preliminary_novelty_risk` | 高/中/低/无法判断 |
| `assessment_reason` | 评估理由（文献特定的特征映射） |
| `evidence_boundary` | 证据边界声明 |
| `next_verification` | 下一步验证建议 |

**风险评级标准**：

- `高`：一篇可访问的专利文献似乎在同一技术方案中公开了所有实质性技术特征（有待权威验证）
- `中`：公开来源或专利文献公开了实质性基础或部分特征，但同一方案组合、特征位置或文献状态需进一步验证
- `低`：检索范围内未识别出公开了实质性组合的单一文献，且检索日志记录充分
- `无法判断`：Google Patents 不可访问、查询覆盖不充分或创新点缺乏稳定的特征定义

不得使用多篇文献组合来断言某创新点不具备新颖性；仅记录为需要单独分析的创造性或组合风险线索。

每条评估理由必须说明：所比较的实质性特征、支持性公开来源或专利公开号、特征位置（如有）及关键差异或缺失证据。声明该评估仅限于所记录的检索引擎、查询式、筛选条件、日期和可访问文献。

## 领域特定规则

根据交底书技术领域，读取对应的域参考文件：
- 机械/结构 → `references/domains/mechanical.md`
- 电子通信/AI/软件 → `references/domains/electronics-communication.md`
- 软件/算法 → `references/domains/software-algorithm.md`
- 化学/材料 → `references/domains/chemistry-material.md`

## 质量门禁

在提交每个阶段之前验证：

- 每个 `R` 都有下游的 `F/S/B/E` 路径或明确的 `Q`
- 每个 `S` 都有功能目的和出处引用
- 每个F具有输入、技术变换和直接输出，并能分配到S、由B核验
- 每个E具有受影响对象、属性、后果、条件、因果路径和证据，不重复F或OutputState
- 没有商业目标在缺乏技术框架的情况下被改写为技术问题
- 没有检索前的假设被写成新颖性或可专利性结论
- Mermaid 节点 ID 与 R/F/S/B/E 表格匹配
- 检索要素 JSON 可解析且不包含 Markdown 注释
- 已适用领域特定的证据规则（如相关）
- 每条实际检索发现标识其来源层级、查询式、日期和 URL
- 没有公开资料初筛结果被描述为专利数据库检索结果或最终的新颖性/创造性结论
- 每条 Google Patents 结果记录其查询式、筛选条件、公开号、日期、特征位置和来源 URL
- 每个创新点都有初步新颖性评估、文献特定的理由、证据边界和下一步验证步骤
