# 检索技法指南

工程2(检索策略的构建)・工程3(正式检索与筛选)的工作步骤手册。出处参见末尾的"出处URL集"。

## 0. 六法域覆盖与全球六语优先

所有案件均以中国(CN)、美国(US)、日本(JP)、韩国(KR)、欧洲专利(EP)、PCT国际申请(WO)为一体必须覆盖范围。检索从融入中文、英文、日文、韩文、法文、德文同义词的、不限法域的全球式开始。不得从六法域分别检索开始。仅当全球结果超过工具单次稳定提取上限、且分页或分批获取仍无法完整取得时，方可讨论法域分割检索，并记录总命中数、提取上限、尝试结果和分割理由。除客户明确指示缩小范围并记录理由、未调查范围及对结论的影响外，任何法域均不得从覆盖范围中省略。核心文献通过 MCP 或可信全文渠道核对权利要求、说明书或附图。本地 PDF 的下载、保存和附送均为可选。

| 覆盖法域 | 全球主检索与官方/可信核验 | 统一关键词语言 | 主要分类 |
|----------|---------------------------|------------------|----------|
| CN | Global Core Patent Database；CNIPA 核验 | 中英日韩法德 | IPC/CPC |
| US | Global Core Patent Database；USPTO 核验 | 中英日韩法德 | IPC/CPC |
| JP | Global Core Patent Database；J-PlatPat 核验 | 中英日韩法德 | IPC/FI/F-term |
| KR | Global Core Patent Database；KIPRIS 核验 | 中英日韩法德 | IPC/CPC |
| EP | Global Core Patent Database；Espacenet/European Patent Register 核验 | 中英日韩法德 | IPC/CPC |
| WO/PCT | Global Core Patent Database；PATENTSCOPE 核验 | 中英日韩法德、必要时 CLIR | IPC/CPC |

将一次性全球检索作为主检索，结果按国家/机构代码等对应到六法域。无需对每个法域保留独立检索式。官方渠道用于号码、法律状态和异常空白法域的抽查。仅当满足上述提取上限条件时方可制作法域分别检索式。

标准成果物为经书目解析的公开号/专利号、来源查询、公开法域、确认DB、确认日期的号码清单和报告书。标题和摘要可用于非核心候选的相关性排序。用于实质结论的核心文献通过 MCP 或可信全文渠道读取权利要求、说明书或附图，并记录公开位置。本地 PDF 可不包含在标准成果物中。

## 1. 检索块方式的步骤

1. 从工程1的技术特征分解中选出2~4个检索"观点"(使用全部要件会过度收窄。技术领域+核心特征的组合为基本)
2. 按观点制作块: 同一观点内用 OR(展开同义词・近义词・表记差异・上位/下位概念词・中英日韩法德・缩写・旧用语)，观点间用 AND
3. 仅关键词式和仅分类式并行运行，用 OR 合并(双线并行)。分类付与的偏差和关键词表记的偏差相互补充
4. 文献集过大(无法筛选的件数)则追加观点，过小(基准文献漏检)则追加下位概念词或削减观点进行调整

## 2. 中英日韩法德关键词展开

- 中文: 以简体字为基础，展开繁体字、行业简称、上位/下位概念、译词差异
- 日文: 同义词(例: ねじ/ネジ/螺子)、片假名/汉字表记差异、行业简称
- 英文: 同义词(screw/fastener)、英美拼写差异、有无连字符
- 韩文: 展开谚文同义词、汉字词来源表记、英文音译、行业简称
- 法文: 展开名词・动词形态、性数变化、复合词、英语借用词、技术公报中使用标准译法
- 德文: 展开复合名词的结合・分割表记、词尾变化、英语借用词、技术公报中使用标准译法
- 上位概念(紧固件/fastening means)与下位概念(小螺钉/machine screw)双向展开
- 在支持邻近运算符的 DB 中加以利用
- 通过机器翻译生成的日文、韩文、法文、德文词汇，不得直接作为唯一检索词，须以邻近公报的原文用语、分类、英文对译进行验证

## 3. 分类的逆引き步骤

1. 在 `global_core_patent_database` 的全球统一检索中找到2~5件邻近文献。官方法域渠道用于分类确认或抽查，不作为初始的法域分别检索
2. 将各文献被赋予的分类(IPC/CPC 通过 Google Patents・Espacenet，FI/F-term 通过 J-PlatPat)进行列表化
3. 将多件邻近文献共同被赋予的分类作为主分类候选，通过分类表(Espacenet CPC 浏览器、J-PlatPat 专利地图指南)确认含义和层级
4. 分场景使用: 日本文献的主检索键为 FI/F-term，欧美调查为 CPC(比 IPC 更精细)。F-term 设计为通过目的・材料・结构等多观点的乘法进行收窄

## 4. 召回率与精确率的调整

- 召回率(减少遗漏)与精确率(减少噪声)是权衡关系
- 按模式优先: FTO・无效检索优先召回率(文献集取宽、人工筛选应对)。专利态势分析可偏向精确率
- 提高召回率的手段: 扩大 DB 内检索字段(含全文检索)、上位层级分类、追加上位概念词。使用全文检索也不要求下载文献 PDF
- 提高精确率的手段: 追加观点(AND)、限定为下位分类、限定为权利要求/标题・摘要字段

## 5. 数据库列表与分场景使用

**免费检索 DB(Web UI)**:

| DB | 运营方 | URL | 特点 |
|---|---|---|---|
| CNIPA 专利检索及分析系统 | CNIPA | https://pss-system.cponline.cnipa.gov.cn/ | 中国公报・分类检索。书目・法律状态也可通过官方审查信息确认 |
| J-PlatPat | INPIT/专利局 | https://www.j-platpat.inpit.go.jp/ | 日本公报全文、FI/F-term检索、审查经过信息 |
| KIPRIS | KIPO/KIPI | https://www.kipris.or.kr/ | 韩国公报全文、英韩关键词、审查经过・书目信息 |
| Espacenet | EPO | https://worldwide.espacenet.com/ | 全球1.5亿件以上、CPC 检索、INPADOC 专利族・法律状态 |
| Google Patents | Google | https://patents.google.com/ | 全文跨库・机器翻译・引用关系。`patents.google.com/patent/{号码}` 可直接通过号码访问 |
| PATENTSCOPE | WIPO | https://patentscope.wipo.int/ | PCT 全文+各国集合、多语言跨库检索(CLIR) |
| Lens.org | Cambia | https://www.lens.org/ | 专利+学术文献的关联。个人・非商用免费 |
| USPTO Patent Public Search | USPTO | https://ppubs.uspto.gov/pubwebapp/ | 美国公报的官方检索 |

## 6. 号码的实存确认与回退顺序

**免费 API(专利号码→书目的机械实存确认)**:

| API | 提供方 | 入口 | 免费条件 |
|---|---|---|---|
| EPO OPS | EPO | https://ops.epo.org / https://developers.epo.org/ | 免费注册+OAuth2、每月4GB免费。向 published-data 传入号码获取书目 XML=实存确认的标准方法 |
| PatentsView PatentSearch API | USPTO | https://search.patentsview.org/docs/ | 免费 API 密钥。通过号码 ID 对美国专利/公开公报进行 GET |
| USPTO Open Data Portal | USPTO | https://data.uspto.gov/ | 免费。PatentsView 迁移目标 |
| Google Patents Public Data | Google/IFI | BigQuery 公开数据集 https://cloud.google.com/blog/topics/public-datasets/google-patents-public-datasets-connecting-public-paid-and-private-patent-data | BigQuery 免费额度内 |
| Lens API | Cambia | https://www.lens.org/ | 学术・非商用需申请 |
| 专利局 专利信息取得API | JPO | https://www.jpo.go.jp/system/laws/sesaku/data/api-provision.html | 免费(试行)但已于令和6年8月9日停止新申请受理。J-PlatPat 本身无公开 API |

**专利号码机械实存确认的实务手段(免费)**:
1. EPO OPS `published-data/publication/.../biblio` — 支持世界各国号码，返回书目 XML 即确认实存
2. Google Patents URL 模式(通过 HTTP 200/404 确认，注意抓取条款)
3. PatentsView(仅美国)/ PATENTSCOPE・Espacenet 的号码检索
4. WIPO「Manual on Open Source Patent Analytics」第7章 https://wipo-analytics.github.io/manual/databases.html

**运用规则(回退顺序)**:

- 第1手段: 在 `global_core_patent_database` 中解析候选的号码・书目，记录检索式或号码、实施日期、结果。核心文献通过该服务器的全文・权利要求・附图功能确认技术内容和公开位置。能从服务器读取的，无需取得或保存本地 PDF
- 第2手段: 通过公开国・机构对应的官方渠道(CNIPA、USPTO、J-PlatPat、KIPRIS、European Patent Register/Espacenet、PATENTSCOPE)交叉确认号码和书目
- 第3手段: 通过 EPO OPS、Espacenet、Lens.org、Google Patents 等可信渠道补充同族・翻译・书目
- 全部失败时: 标明"号码实存确认保留"，将该路线的官方渠道确认作为用户分拣任务提示。在保留状态下不得列入确定号码清单(实存门)
- 注意号码的正规化: 国家代码+号码+种类代码(例: JP2020123456A)。不同 DB 的分隔符和位数处理可能不同

## 7. J-PlatPat 核验・附条件分拣任务的提示要领

J-PlatPat 用于 JP 结果的官方核验、FI/F-term 确认、或全球结果超过提取上限且满足法域拆分条件时使用。不得作为初始独立 JP 检索向用户委托。委托时须明确目的并以下列格式提示:

```
【J-PlatPat 检索委托】
1. 打开 https://www.j-platpat.inpit.go.jp/
2. 选择"专利・实用新型检索"
3. 检索式: (以可直接粘贴的逻辑式全文提示。例: [インクジェット/CL] * [B41J2/14@FI])
4. 检索选项: (如有期间・文献种类的指定则明确记载)
5. 请告知命中件数(过多/过少将调整检索式)
6. 将结果 CSV 导出，保存到 docs/patent-search/<案件slug>/sources/
   (CSV 导出为检索结果一览的"CSV出力"按钮。超过上限时分割导出)
7. (仅工程2的覆盖性门验证时)请确认在检索式中 AND 基准文献的公报号后命中件数为1件
```

带回结果作为(用户提供)处理，号码在官方或可信 DB 中完成书目解析后升格为(号级线索)。指定为核心候选的文献通过 MCP 或可信全文渠道与公报原文比对，记录公开位置。

## 8. 出处URL集

以下为 research(`docs/superpowers/specs/2026-07-08-patent-search-research.md`)各节末尾记载的出典、以及"补充: 可信度特别高的一次资料TOP5"的转录。

### 第1章(专利调查的种类与目的)的出典

- 秋山国际专利商标事务所"专利调查的种类" https://www.tectra.jp/akiyama-patent/post-2553/
- 日本IR"专利调查的种类与概要" https://nihon-ir.jp/service/patentsearch-solution/main/patent-search-main/
- 日本IR"专利侵权预防调查(清关调查・FTO调查)" https://nihon-ir.jp/service/patentsearch-solution/purpose/patent-clearance-search/
- JPDS"按调查种类整理调查观点" https://www.jpds.co.jp/info/search/003_1.html
- 日本专利代理人会 关西会 Q&A"专利调查的方法" https://www.kjpaa.jp/qa/46380.html
- TMI综合法律事务所"知产DD中专利调查的类型与注意事项" https://www.tmi.gr.jp/eyes/blog/2022/13596.html
- Spruson & Ferguson: Patentability vs FTO searching 的区别 https://www.spruson.com/understanding-the-differences-between-patentability-novelty-and-freedom-to-operate-prior-art-searching/
- WIPO Toolkit Tool 5: Freedom to Operate https://www.wipo.int/documents/d/tisc/docs-en-tisc-toolkit-freedom-to-operate-description.pdf
- WIPO Magazine: Launching a New Product — Freedom to Operate https://www.wipo.int/en/web/wipo-magazine/articles/ip-and-business-launching-a-new-product-freedom-to-operate-34956
- WIPO「Guidelines for Preparing Patent Landscape Reports」 https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf
- evort「SDI调查(专利的定期调查)」 https://evort.jp/article/sdi
- 恩田国际专利事务所「SDI定期调查」 https://www.ondatechno.com/jp/search_analysis/sdi/
- WIPO 培训资料「Basics of Patent Searching」 https://www.wipo.int/edocs/mdocs/africa/en/wipo_pat_hre_15/wipo_pat_hre_15_t_7.pdf

### 第2章(标准调查流程)的出典

- INPIT 培训教材(PDF) https://www.inpit.go.jp/content/100881807.pdf (同系: http://www.kautm.net/data/pds/k_total.pdf )
- 专利局 审查基准 第I部第2章第2节(PDF) https://www.jpo.go.jp/system/laws/rule/guideline/patent/tukujitu_kijun/document/index/01_0202bm.pdf
- 专利局"关于注册调查机构" https://www.jpo.go.jp/system/patent/gaiyo/sesaku/toroku/touroku_chousa.html
- 日本专利代理人会 会刊"专利信息调查的步骤"(PDF) https://www.jpaa.or.jp/old/activity/publication/patent/patent-library/patent-lib/201401/jpaapatent201401_031-042.pdf
- INPIT J-PlatPat 讲习会教材 https://www.inpit.go.jp/j-platpat_info/lecture/patent.html / https://www.inpit.go.jp/j-platpat_info/lecture/patent_intermediate.html / https://www.inpit.go.jp/j-platpat_info/reference/index.html
- WIPO PCT ISPE Guidelines https://www.wipo.int/en/web/pct-system/texts/ispe/index
- EPO Guidelines Part B 概说 https://en.wikipedia.org/wiki/Guidelines_for_Examination_in_the_European_Patent_Office
- 信息管理研究社"专利调查流程" https://johokanri.co.jp/patentsearch/process/

### 第3章(检索式构建的技法)的出典

- 知产实务信息Lab."检索式的构建方法" https://chizai-jj-lab.com/2022/10/18/1018/
- 角渕由英"检索式的基础・召回率与精确率" https://note.com/tsunobuchi/n/nbd110dd5513a /"专利调查检索式的制作方法" https://note.com/tsunobuchi/n/ne332b05845bb
- 秋山国际专利商标事务所"检索式的基础・召回率与精确率" https://www.tectra.jp/akiyama-patent/post-2382/
- 知产Times"专利分类的种类与使用方法(IPC/FI/F-term)" https://tokkyo-lab.com/co/info-patentsearch02og
- JPDS"检索式制作时应避免的运算" https://www.jpds.co.jp/info/search/005_1.html
- INPIT 培训教材(前掲) https://www.inpit.go.jp/content/100881807.pdf
- WIPO「IPC and CPC Basics」 https://www.wipo.int/edocs/mdocs/africa/en/wipo_ip_pre_16/wipo_ip_pre_16_t_8.pdf
- Espacenet Classification search https://worldwide.espacenet.com/help?locale=en_EP&method=handleHelpTopic&topic=classificationsearch / CPC 浏览器 https://worldwide.espacenet.com/patent/cpc-browser
- 审查官的检索手法解说(专利代理人会刊) https://www.jpaa.or.jp/old/activity/publication/patent/patent-library/patent-lib/201112/jpaapatent201112_051-059.pdf

### 第4章(主要数据库与免费 API・实存确认手段)的其他出典

- python-epo-ops-client https://pypi.org/project/python-epo-ops-client/ / https://github.com/ip-tools/python-epo-ops-client/
- PatentsView → USPTO ODP 迁移指南 https://data.uspto.gov/support/transition-guide/patentsview
- PQAI「Top Patent Search APIs」 https://projectpq.ai/best-patent-search-apis-2025/

### 第5章(评价・判定的技法)的出典

- EPO Guidelines B-X 9.2 https://xepc.eu/node/b_x_9_2
- How to Interpret EPO Search Reports(PDF) https://people.unica.it/liaisonoffice/files/2014/05/How-to-Interpret-EPO-Search-Reports.pdf
- USPTO MPEP 1844 https://www.uspto.gov/web/offices/pac/mpep/s1844.html
- WIPO「Interpreting and using search and examination reports」 https://www.wipo.int/edocs/mdocs/aspac/en/wipo_ip_bkk_12/wipo_ip_bkk_12_www_238945.pdf
- 知产管理 Vol.69 No.6 (2019)"关于制作权利要求对照表(claim chart)的注意事项" http://www.jipa.or.jp/kaiin/kikansi/honbun/2019_06_849.pdf
- 知产实务信息Lab."侵权预防调查 ⑩全部技术特征原则的具体例" https://chizai-jj-lab.com/2023/11/21/1121/
- 知产实务Tips"全部技术特征原则与单一实体规则" https://ip-tips.com/all_emement_rule_single_entity_rule/

### 第6章(报告书的标准构成)的出典

- INPIT「检索的思路与报告书的制作」 https://www.inpit.go.jp/content/100881807.pdf / http://www.kautm.net/data/pds/k_total.pdf
- 角渕由英"专利调查报告书制作" https://note.com/tsunobuchi/n/nee062f8cbf16 /"生成AI时代的专利调查报告书制作" https://note.com/tsunobuchi/n/nbe464973b68a
- WIPO Patent Landscape Report 指南 https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf

### 第7章(调查的限度与品质管理)的出典

- 专利局"关于公报的FAQ" https://www.jpo.go.jp/system/laws/koho/general/koho_faq.html
- 创英国际专利法律事务所"关于公报发行日的冷知识" https://www.soei.com/%EF%BC%BB%E7%89%B9%E8%A8%B1%EF%BC%8Fip5%E3%80%81wipo%EF%BC%BD%EF%BC%9C%E3%82%B3%E3%83%A9%E3%83%A0%EF%BC%9E%E5%85%AC%E5%A0%B1%E7%99%BA%E8%A1%8C%E6%97%A5%E3%81%AB%E9%96%A2%E3%81%99%E3%82%8B%E3%83%88/
- 专利誌"关于专利申请的公开时期" https://jpaa-patent.info/patent/viewPdf/4576
- Logic Meister"效率性、覆盖性、再现性" https://logic-meister.com/pages/74/
- IP调查塾"专利调查的种类与覆盖性" https://www.ip-searcher.co.jp/archives/kensakukouza/more1
- 日本专利代理人会 会刊(前掲) https://www.jpaa.or.jp/old/activity/publication/patent/patent-library/patent-lib/201401/jpaapatent201401_031-042.pdf

### 补充: 可信度特别高的一次资料TOP5

1. INPIT 调查业务实施者培训教材 https://www.inpit.go.jp/content/100881807.pdf
2. 专利局 审查基准 第I部第2章第2节 https://www.jpo.go.jp/system/laws/rule/guideline/patent/tukujitu_kijun/document/index/01_0202bm.pdf
3. WIPO PCT ISPE Guidelines https://www.wipo.int/en/web/pct-system/texts/ispe/index
4. WIPO Patent Landscape Report Guidelines https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf
5. WIPO Manual on Open Source Patent Analytics https://wipo-analytics.github.io/manual/databases.html

注意事项: 专利局"专利信息取得API"已于2024年8月9日停止新申请受理。如需新规机械访问，EPO OPS(免费额度 月4GB)+ PatentsView/USPTO ODP + Google Patents Public Data(BigQuery)的组合是实用的免费方案。

## 9. 补充检索指导

当回退至工程2（复核与回退触发），或因新证据出现需要扩展检索范围时，按以下规则执行补充检索。

### 9.1 触发条件

| 模式 | 典型触发场景 |
|------|------------|
| 查新检索 | MBSE 追溯矩阵发现某技术特征无文献覆盖；审查员引用新对比文件需扩展检索 |
| 无效检索 | Claim Chart 中某特征仅有"部分充足"需补强证据；发现新的公知常识线索需举证 |
| FTO | 产品规格变更新增技术特征；法律状态核验后发现原排除专利已恢复有效 |
| 专利态势分析 | 文献集代表性不足需扩大 IPC 范围；发现新的重要申请人名称变体需回溯 |

### 9.2 保留与调整原则

- 原检索式中通过 benchmark 验证的检索块**保留复用**，不重新设计
- 仅调整触发补充的检索块：追加关键词/扩展分类层级/放宽检索字段（如从权利要求放宽至全文）
- 新增检索块需重新通过 benchmark 验证
- 在 `检索策略与日志.xlsx` Sheet 1 末尾记录调整理由、调整前后的检索式对比

### 9.3 新旧结果合并规则

- 新旧结果按公开号去重，合并到号码清单中
- 补充检索新发现的文献标注来源为"补充检索/日期"
- 原文献的证据等级和 MCP 核验结果**保留继承**，不因补充检索而重复核验
- 若补充检索覆盖了原空白特征，更新 MBSE 追溯矩阵对应行
- 补充检索执行日志追加到 `检索策略与日志.xlsx` Sheet 2 末尾

### 9.4 交付物更新要求

| 需更新的交付物 | 更新内容 |
|--------------|---------|
| 号码清单 | 新增行，标注补充检索来源与日期 |
| 技术特征对比表 / Claim Chart | 补充文献的 MCP 全文核验位置（按正常流程核验后填入） |
| 检索报告 | 结论中注明"经补充检索后…"；报告书限度节标注补充检索的日期、范围与触发原因 |
| MBSE 追溯矩阵（如有） | 补充文献覆盖的模型要素行更新为 ✅ |
