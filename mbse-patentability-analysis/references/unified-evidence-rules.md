# 统一证据标签体系

本文件定义 `mbse-patentability-analysis` 全 Mode 通用的证据标签体系，合并自原各 skill 的 E/I/Q、D/N/G/Q/X 及文本级 evidence_level 三套体系。

---

## 六类证据标签

| 标签 | 名称 | 含义 | 允许作为下游推理前提？ | 适用 Mode |
|------|------|------|---------------------|----------|
| `D` | 明确公开 (Disclosed) | 原文文字、权利要求或附图无歧义地记载。必须附段落号、权利要求号或附图标记。 | ✅ 是 | disclosure / document |
| `I` | 受限推断 (Inferred) | 由已列明的 D 前提得出的受限工程推断。必须写明"前提→推断"及推断范围。 | ⚠️ 仅限标注范围内 | disclosure / document |
| `N` | 发明人确认新增 (New) | 经发明人明确确认为新增创新点，非源自公开文献。附确认来源（如邮件、会议记录）。 | ✅ 是 | disclosure |
| `G` | 通用专利化表达 (Generalized) | 指向 D 或 N 技术事实的通用专利化表达，非独立事实。必须注明指向的具体 D/N 编号。 | ⚠️ 取决于指向的 D/N | disclosure |
| `Q` | 待确认 (Question) | 来源缺失、歧义或无法从已提供材料核验。纳入待确认问题表。 | ❌ 否 | disclosure / document |
| `X` | 排除 (eXcluded) | 无关、误混入或明确排除的材料。记录来源与排除理由，不进入后续分析。 | ❌ 否 | disclosure / document |
| `—` | 不适用 | search mode 不要求证据标签，模型本身即为检索输入。 | — | search |

---

## 各标签详细使用规则

### D（明确公开）

- 必须精确定位至：权利要求编号、说明书段落号（如 `[0035]`）、附图号/标号
- 可以是一个句子跨越多层，拆为多个 D 节点，各自保留原文
- 附图仅在其内容无歧义时视为 D；模糊图面标注为 Q
- 示例：`D1-R1: "如何在连续行进中实现托盘翻转？" — 说明书[0008] (D)`

### I（受限推断）

- 必须在节点备注中写明前提（指向具体的 D 节点）和推断范围
- 不得将 I 作为另一 I 节点的唯一前提（最多一层推断链）
- 推断范围不得超过原文明确限定的技术领域和工程常识边界
- 示例：`若 D1-S3 为齿轮且 D1-B2 为旋转驱动，则可推断(I)齿轮与轴之间为键连接或过盈配合——仅限常规机械连接方式，具体连接形式待核实`

### N（发明人确认新增）

- 仅适用于 disclosure mode
- 必须单列确认来源和确认日期
- N 节点仍应建立与其他节点的追溯关系
- 后续可被 G 节点引用

### G（通用专利化表达）

- 不引入新事实，仅是对已有 D/N 事实的专利语言包装
- 必须注明指向的具体 D/N 节点编号
- 示例：`"驱动装置" (G) — 指向 D1-S2 "电机"、D1-S3 "齿轮减速器"`
- 如果找不到对应的 D/N 节点，"通用表达"实际上是在虚构事实 → 应标记为 Q

### Q（待确认）

- 标记为 Q 的节点不得作为任何下游关系的事实前提
- 每个 Q 节点必须纳入待确认问题表，写明缺失维度、影响范围和请求确认事项
- 不得以"本领域常规手段"绕过 Q 标记
- 区分"文件已公开但当前未获取"（Q-未获取）和"文件已获取但未公开"（Q-未公开）

### X（排除）

- 记录原始来源和排除理由
- 不进入追溯链、创新点表和最终报告
- 典型场景：交底书中混入的商业描述、明显不属于本方案的现有技术引用、已被发明人确认放弃的实施例

---

## 跨 Mode 差异

| 规则 | disclosure | document | search |
|------|-----------|----------|--------|
| 证据标签 | 必须（D/I/N/G/Q/X） | 必须（D/I/Q/X） | 不需要 |
| I 节点最大推断层数 | 2 层 | 1 层（专利文本要求更严格） | — |
| Q 节点处理 | 转为发明人确认问题 | 转为待核实问题清单 | — |
| 未获取材料的处理 | 标注 Q-未获取，可继续建模 | 标注 Q-未获取，暂停结论 | — |

---

## 证据标签迁移对照

从旧标签体系迁移时使用以下对照：

| 旧体系 | 来源 Skill | 新标签 |
|--------|-----------|--------|
| `E`（明确记载） | patent-text-mbse-rapid-modeling | `D` |
| `I`（受限推断） | patent-text-mbse-rapid-modeling | `I` |
| `Q`（待核实） | patent-text-mbse-rapid-modeling | `Q` |
| `D`（明确公开） | cn-patent-drafting-workflow / cn-oa-reexam-opinion-drafting | `D` |
| `N`（发明人确认新增） | cn-patent-drafting-workflow / cn-oa-reexam-opinion-drafting | `N` |
| `G`（通用专利化表达） | cn-patent-drafting-workflow / cn-oa-reexam-opinion-drafting | `G` |
| `Q`（待确认） | cn-patent-drafting-workflow / cn-oa-reexam-opinion-drafting | `Q` |
| `X`（排除） | cn-patent-drafting-workflow / cn-oa-reexam-opinion-drafting | `X` |
| `evidence_level`（文本描述） | mbse-patentability-analysis（旧版） | 对应上述 D/I/N/G/Q/X |
