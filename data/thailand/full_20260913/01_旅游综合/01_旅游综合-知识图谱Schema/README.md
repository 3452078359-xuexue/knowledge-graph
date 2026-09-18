# 泰国旅游知识图谱 Schema

当前权威版本：**thai_tourism_schema_v4.json**（2026-08-27，经 5 路标准评审+对抗收敛）

| 文件 | 说明 |
|---|---|
| **thai_tourism_schema_v4.json** | ★当前主文件。v3 经 schema.org/Wikidata/SKOS/PROV/属性图 五路评审后收敛 |
| thai_tourism_schema_v3.json | 本体化重构版(对照留存) |
| thai_tourism_schema_v2.json | 荔波扁平风格(对照留存,勿用于建库) |
| thai_tourism_schema.cypher | 建库 DDL,需按 v4 类名/关系名更新后使用 |
| test_mount.cypher | 数据测试产物(5 POI 经 PIP 挂到府/县/分区) |
| thai-schema-spec.html | 可读规格(结构相通) |

## v4 相较 v3 的关键变化（评审共识必改）
1. 新增 **Event/Festival** 一等类（泼水节/水灯节，日期/递归；三种时间语义分离）。
2. **CulturalItem** 从 Concept 提为一等类（Dish/特产/遗产可挂图/坐标/断言）。
3. **PART_OF 拆** PART_OF_ADMIN / CONTAINED_IN / IN_ZONE（对齐 FalkorDB 矩阵引擎与“两套口径永不互推”）。
4. 地点分类**单一真相** Place.category（带索引）；细类经 Concept 派生，去双轨。
5. **半静态信息回收进图**：结构化营业时间、双轨票价(THB+CNY/外国人-本地)、评分快照、图片、联系方式、支付方式；仅实时房价/排队走 businessRefId。
6. **选择性 reify**：仅价/时/名/评分挂 Claim（带 observedAt），其余内联。
7. **SAME_AS→RESOLVES_TO**（有向函数式；非规范记录 :Candidate 隔离；导出 skos:exactMatch）。
8. **ConceptScheme 升一等** + altLabel，真正兑现“加词表零改 schema”。

## 设计铁律
科学规范只落在有回报的接口处；三条落地铁律高于一切：FalkorDB 可查 · 管道能灌 · 游客可用。

## 延后(LATER)
destination/zone 先做角色后升 Collection；Product/Itinerary 精细分工；schema.org JSON-LD crosswalk。
