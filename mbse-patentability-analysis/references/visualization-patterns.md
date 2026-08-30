# Mermaid 可视化图表模板库

本文件为 `mbse-patentability-analysis` skill 提供 Mermaid 语法模板，用于生成四视角系统模型的可视化图表。

每个模板包含：语法说明、建模要点、完整示例。

---

## 模板1：结构视角 - 系统架构图（graph TD）

**适用场景**：展示系统的分层模块架构、组件组成及数据流/控制流关系。

**语法**：`graph TD`（Top-Down）或 `graph LR`（Left-Right），配合 `subgraph` 分层。

**建模要点**：
- 按系统层次划分子图（如应用层、解析层、数据层、分析层）
- 每个结构模块用方框 `[模块名]` 表示
- 模块间的数据流/控制流用 `-->|标签|` 标注
- 数据库/存储用 `[(存储名)]` 圆柱体表示
- 外部实体/用户用 `{{外部实体}}` 表示
- 决策点用 `{决策条件}` 菱形表示（可选）

**通用模板**：

```mermaid
graph TD
    subgraph 应用层
        S1[用户交互界面]
        S2[裁决执行模块]
    end
    subgraph 解析层
        S3[内容解析引擎]
        S4[脱敏引擎]
        S5[策略决策引擎]
    end
    subgraph 数据层
        S6[(文档库)]
        S7[(策略库)]
        S8[(日志库)]
    end
    subgraph 分析层
        S9[行为分析引擎]
    end
    S1 -->|访问请求| S5
    S5 -->|裁决指令| S2
    S2 -->|脱敏指令| S4
    S3 -->|标签索引| S6
    S5 -->|规则查询| S7
    S2 -->|日志写入| S8
    S8 -->|基线更新| S9
    S9 -->|风险分值| S5
```

**变体 - 软件系统分层架构**：

```mermaid
graph TD
    subgraph 表示层
        UI[Web界面/API网关]
    end
    subgraph 业务逻辑层
        A[模块A]
        B[模块B]
        C[模块C]
    end
    subgraph 数据访问层
        DAO1[数据访问对象1]
        DAO2[数据访问对象2]
    end
    subgraph 数据层
        DB1[(数据库1)]
        DB2[(数据库2)]
    end
    UI --> A
    UI --> B
    A --> DAO1
    B --> DAO1
    B --> DAO2
    C --> DAO2
    DAO1 --> DB1
    DAO2 --> DB2
```

**变体 - 包含外部实体的系统架构**：

```mermaid
graph TD
    User{{用户}} -->|上传文件| S1[预处理模块]
    S1 -->|解析请求| S2[LLM引擎]
    S2 -->|标签结果| S3[索引构建模块]
    S3 -->|存储| DB[(文档库)]
    External{{外部认证服务}} -->|身份验证| S4[访问控制模块]
    S4 -->|查询| DB
    S4 -->|返回| User
```

---

## 模板2：行为视角 - 核心流程时序图（sequenceDiagram）

**适用场景**：展示系统运行时各模块间的交互时序、消息传递及分支逻辑。

**语法**：`sequenceDiagram`，配合 `alt/else/end`、`loop/end`、`opt/end`。

**建模要点**：
- 每个关键结构模块作为一个 `participant`
- 使用 `participant 别名 as 显示名称` 自定义显示名（可含编号）
- 消息传递用 `->>`（实线箭头）或 `-->>`（虚线箭头）
- 用 `alt/else/end` 标注分支逻辑（如裁决结果分支）
- 用 `loop/end` 标注循环流程
- 用 `opt/end` 标注可选流程
- 用 `Note over 参与者: 备注` 或 `Note right of 参与者: 备注` 添加说明
- 用 `activate/deactivate` 标注生命周期（可选）

**通用模板 - 请求裁决流程**：

```mermaid
sequenceDiagram
    participant U as 用户
    participant UI as 用户交互界面(S1)
    participant UEBA as UEBA引擎(S9)
    participant AGG as 属性聚合(F5)
    participant ABAC as ABAC引擎(S5)
    participant LLM as LLM脱敏引擎(S4)
    participant LOG as 行为日志库(S8)
    U->>UI: 发起访问请求(用户ID/文件ID/操作类型/环境属性)
    UI->>UEBA: 传递请求上下文
    activate UEBA
    UEBA->>UEBA: 比对行为基线，计算偏离程度
    UEBA->>AGG: 输出风险分值(0-1)
    deactivate UEBA
    activate AGG
    AGG->>AGG: 聚合用户属性+文件标签+环境属性+风险分值
    AGG->>ABAC: 输出事实元组
    deactivate AGG
    activate ABAC
    ABAC->>ABAC: Rete规则匹配，双重冲突消解
    alt 裁决=允许
        ABAC->>UI: 直接返回请求内容
    else 裁决=脱敏后允许
        ABAC->>LLM: 脱敏指令(超出权限区段)
        LLM->>UI: 返回脱敏后内容
    else 裁决=拒绝
        ABAC->>UI: 返回拒绝通知
    end
    deactivate ABAC
    UI->>LOG: 记录完整上下文及裁决结果
    LOG->>UEBA: 供基线自优化(闭环)
```

**变体 - 文件入库预处理流程**：

```mermaid
sequenceDiagram
    participant U as 用户/系统
    participant PRE as 入库模块
    participant LLM as LLM解析引擎(S3)
    participant IDX as 索引构建模块
    participant DB as 项目文档库(S6)
    U->>PRE: 上传项目文件
    PRE->>LLM: 请求全文语义解析
    activate LLM
    LLM->>LLM: 识别工程专业类别
    LLM->>LLM: 识别项目阶段、功能分区
    LLM->>LLM: 提取段落/表格/图签级涉密标签
    LLM->>PRE: 返回解析结果
    deactivate LLM
    PRE->>IDX: 构建三级索引结构
    IDX->>DB: 存储文件-段落-标签索引
    PRE->>U: 入库完成通知
```

**变体 - 包含循环的后台优化流程**：

```mermaid
sequenceDiagram
    participant LOG as 行为日志库(S8)
    participant UEBA as UEBA引擎(S9)
    participant BASE as 基线模型
    loop 定时批量处理
        LOG->>UEBA: 读取历史访问记录
        UEBA->>BASE: 更新用户行为基线
        BASE->>UEBA: 返回更新后基线
        UEBA->>UEBA: 优化异常检测阈值
        UEBA->>UEBA: 自适应行为模式漂移
    end
    Note over UEBA: 应对用户职务变化、项目变更
```

---

## 模板3：创新点 - 技术方案图解（flowchart LR + subgraph）

**适用场景**：对比展示"现有技术问题 → 本方案解决路径 → 技术效果"的完整链路。

**语法**：`flowchart LR`（横向）或 `flowchart TD`（纵向），配合 `subgraph` 分区。

**建模要点**：
- 左侧/上方 subgraph：`subgraph 现有技术问题` — 用红色/虚线标注缺陷
- 中间 subgraph：`subgraph 本方案解决路径` — 用蓝色/实线标注技术步骤
- 右侧/下方 subgraph：`subgraph 技术效果` — 用绿色标注效果
- 用虚线 `-.->` 连接现有技术问题到效果，标注"问题/缺陷"
- 用实线 `-->` 连接方案路径到效果，标注"解决/实现"
- 步骤用 `A[步骤名]` 方框，决策用 `B{判断条件}` 菱形

**通用模板 - 问题方案效果对比**：

```mermaid
flowchart LR
    subgraph 现有技术问题[现有技术缺陷]
        A1[缺陷步骤1]
        A2[缺陷步骤2]
        A3[缺陷步骤3]
    end
    subgraph 本方案解决路径[本方案技术路径]
        B1[技术步骤1]
        B2[技术步骤2]
        B3[技术步骤3]
    end
    subgraph 技术效果[达到的技术效果]
        C1[效果1]
        C2[效果2]
    end
    A1 --> A2 --> A3
    B1 --> B2 --> B3
    A3 -.->|问题：...| C1
    B3 -->|解决：...| C1
    C1 --> C2
```

**示例 - 创新点1：LLM语义解析与三级索引**：

```mermaid
flowchart LR
    subgraph 现有技术问题[现有技术缺陷]
        A1[RBAC静态权限模型]
        A2[文件级粗粒度控制]
        A3[人工拆分与脱敏]
    end
    subgraph 本方案解决路径[本方案技术路径]
        B1[LLM全文语义解析]
        B2[段落级涉密标签提取]
        B3[文件-段落-标签三级索引]
    end
    subgraph 技术效果[达到的技术效果]
        C1[权限控制单元细化至信息片段级]
        C2[无需人工预处理]
    end
    A1 --> A2 --> A3
    B1 --> B2 --> B3
    A2 -.->|问题：无法差异化授权| C1
    A3 -.->|问题：耗时易错| C2
    B3 -->|解决：段落级标签驱动| C1
    B3 -->|解决：自动索引构建| C2
```

**示例 - 创新点2：ABAC动态访问控制**：

```mermaid
flowchart LR
    subgraph 现有技术问题[现有技术缺陷]
        A1[用户-角色-权限静态查表]
        A2[角色为唯一授权依据]
        A3[权限变更需人工审批]
    end
    subgraph 本方案解决路径[本方案技术路径]
        B1[多维属性集定义]
        B2[Rete算法规则匹配]
        B3[请求时实时裁决]
    end
    subgraph 技术效果[达到的技术效果]
        C1[权限从事先分配变实时评估]
        C2[消除审批时滞]
    end
    A1 --> A2 --> A3
    B1 --> B2 --> B3
    A2 -.->|问题：无法描述动态风险| C1
    A3 -.->|问题：紧急协调停滞| C2
    B3 -->|解决：实时动态决策| C1
    B3 -->|解决：即时授权裁决| C2
```

**变体 - 多方案对比（本方案 vs 替代方案）**：

```mermaid
flowchart TD
    subgraph 现有技术
        A[问题X]
    end
    subgraph 替代方案
        B1[步骤A] --> B2[步骤B]
        B2 --> B3[效果有限]
    end
    subgraph 本方案
        C1[步骤C] --> C2[步骤D]
        C2 --> C3[效果显著]
    end
    A -.->|问题| B1
    A -.->|问题| C1
    B3 -.->|不足：...| C3
```

---

## 模板4：追溯链 - 端到端链路图（flowchart LR）

**适用场景**：展示从需求到效果的完整追溯链，多条追溯链并列展示。

**语法**：`flowchart LR` 或 `flowchart TD`。

**建模要点**：
- 展示完整的 R → F → S → B → 效果 链条
- 多条追溯链用多个 `subgraph` 并列展示
- 核心追溯链（覆盖独立权利要求必备特征）可标注为"核心"
- 跨视角协同创新点用虚线连接标注
- 用不同颜色或标注区分核心链与辅助链（通过文字标注）

**通用模板**：

```mermaid
flowchart LR
    subgraph 追溯链1[追溯链1：XXX主线]
        R1[需求R1：...]
        F1[功能F1：...]
        S1[结构S1：...]
        B1[行为B1：...]
        E1[效果：...]
        R1 --> F1 --> S1 --> B1 --> E1
    end
    subgraph 追溯链2[追溯链2：YYY主线]
        R2[需求R2：...]
        F2[功能F2：...]
        S2[结构S2：...]
        B2[行为B2：...]
        E2[效果：...]
        R2 --> F2 --> S2 --> B2 --> E2
    end
    E1 -.->|跨层联动| E2
```

**示例 - 三条技术链及其协同关系**：

```mermaid
flowchart LR
    subgraph 链1[追溯链1：内容片段建模]
        R1[需求：区分文档中的不同控制对象] --> F1[功能：将输入文本变换为带标签片段]
        F1 --> S1[结构：语义解析引擎]
        S1 --> B1[行为：解析并标记文本片段]
        B1 --> OS1[输出状态：形成带标签的片段集合]
        OS1 --> E1[效果：降低无关片段随受控片段一并处理的范围]
    end
    subgraph 链2[追溯链2：上下文裁决]
        R2[需求：避免不满足当前条件的内容被返回] --> F2[功能：将请求上下文变换为访问决定]
        F2 --> S2[结构：属性裁决引擎]
        S2 --> B2[行为：读取属性并执行规则]
        B2 --> OS2[输出状态：形成允许、遮蔽或拒绝决定]
        OS2 --> E2[效果：减少不满足当前上下文条件的内容被返回]
    end
    subgraph 链3[追溯链3：风险输入生成]
        R3[需求：使异常行为进入访问控制输入] --> F3[功能：将行为记录变换为风险状态]
        F3 --> S3[结构：行为分析引擎]
        S3 --> B3[行为：计算行为偏离程度]
        B3 --> OS3[输出状态：形成请求主体的风险状态]
        OS3 --> E3[效果：减少高风险请求沿用普通风险状态的情形]
    end
    subgraph 协同[跨链协同]
        OS1 -.->|提供片段对象| B2
        OS3 -.->|提供风险属性| B2
        OS2 -.->|约束返回内容| E4[组合后果：减少非授权片段随授权片段一并返回]
    end
```

**变体 - 含分支条件的追溯链**：

```mermaid
flowchart LR
    R[需求：XXX] --> F[功能：YYY]
    F --> S[结构：ZZZ]
    S --> B[行为：开始流程]
    B --> C{条件判断}
    C -->|条件A| B1[分支行为A]
    C -->|条件B| B2[分支行为B]
    B1 --> E1[效果A]
    B2 --> E2[效果B]
```

---

## 模板使用速查表

| 视角/场景 | 推荐语法 | 推荐模板 | 关键元素 |
|----------|---------|---------|---------|
| 结构视角（系统架构） | `graph TD` + `subgraph` | 模板1 | 模块、分层、数据流 |
| 行为视角（运行时序） | `sequenceDiagram` | 模板2 | participant、消息、alt分支 |
| 创新点（问题→方案→效果） | `flowchart LR` + `subgraph` | 模板3 | 现有技术/方案/效果三分区 |
| 追溯链（端到端链路） | `flowchart LR` + `subgraph` | 模板4 | R→F→S→B→效果链条 |
| 多方案对比 | `flowchart TD` + `subgraph` | 模板3变体 | 并列子图对比 |
| 含分支的流程 | `flowchart LR` + `{条件}` | 模板4变体 | 菱形决策节点 |
| 后台循环流程 | `sequenceDiagram` + `loop` | 模板2变体 | loop/end |

---

## Mermaid 语法限制与注意事项

1. **节点命名**：避免中文特殊字符（如顿号、书名号），用方括号 `[...]` 包裹中文节点名
2. **子图嵌套**：Mermaid 支持子图嵌套，但建议不超过两层以保证可读性
3. **箭头标注**：`-->|标签|` 中的标签不宜过长，超过8个中文字建议拆分为两个节点
4. **图表大小**：每个图表控制在 15 个节点以内，超过则拆分为多个图表或简化
5. **颜色支持**：Mermaid 支持 `classDef` 定义样式，但部分渲染器不支持，建议以结构清晰为主，不依赖颜色
6. **兼容性**：使用标准 Mermaid 语法，避免使用实验性功能，确保在大多数 Markdown 渲染器和工具中可正常显示
