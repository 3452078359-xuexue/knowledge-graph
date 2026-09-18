# 城市旅游知识图谱

面向城市旅游问答、附近检索、行程决策和多来源证据治理的知识图谱工程。当前公开快照覆盖两个数据域：

- 贵阳：城市、行政区、商圈、H3 网格、地名解析、景区、美食、酒店、交通和证据治理。
- 泰国：旅游 Schema、数据目录、质量边界，以及 ADM0–ADM3 中泰双语行政区数据。

> 本仓库是“公开安全快照”，不是本地全量采集盘的镜像。公开仓库保留可复现的 Schema、空间骨架、行政区数据、设计文档、数据目录和质量报告；受平台条款限制的原始 POI、评论、帖子全文、动态价格、浏览器状态和密钥不会上传。

## 当前规模

| 数据域 | 本地成果 | 本仓库公开内容 |
| --- | --- | --- |
| 贵阳 Schema | 30 个实体、1,098 个属性、18 种声明关系 | OpenSPG DSL、解析版和平台版 |
| 贵阳图谱 | 96,753 个节点、398,717 条关系，联合校验 0 error / 0 warning | 设计、验证报告、行政区和 H3 空间骨架 |
| 贵阳空间层 | R8 11,297 格、R7 1,714 格、157 个行政区 | 13,011 个 H3 单元及行政区结构化表 |
| 泰国整理包 | 257 个登记文件，覆盖旅游、景点、美食、交通、酒店和行政区 | Schema、文件清单、质量边界、ADM0–ADM3 数据 |
| 泰国行政区 | ADM0 1、ADM1 77、ADM2 928、ADM3 7,436 | CSV 与 GeoJSON，附来源和质量说明 |

## 总体设计

```text
用户问题
   │
   ├─ 地名 ──> PlaceAlias ──> H3 锚点/格集
   ├─ 用户定位 ──────────────> H3 单元
   └─ “最热门/最适合” ───────> 业务筛选与排序索引
                                  │
                    H3 候选召回（需要空间约束时）
                                  │
                     精确距离、质量和业务精排
                                  │
        POI 事实层 + SourceEvidence 证据层 + 内容检索层
```

核心原则：

1. POI 事实主库与社媒体验证据分层。高德、携程、官方资料负责稳定事实；小红书等内容只作为审核后的体验证据。
2. H3 负责空间候选召回，不负责最终距离、行政区统计或“最热门”结论。
3. 地名、用户定位和无空间边界的“最 XX”查询采用不同路由，不把行政区或附近半径当成永远不能突破的边界。
4. 所有跨源结论必须能追溯到 DataSource、CollectionBatch 和 SourceEvidence。
5. `exact / approx / none` 决定坐标能否进入附近排序；近似中心点不得冒充独立 POI 点位。

完整设计见[贵阳知识图谱技术设计](docs/architecture/guiyang-knowledge-graph-design.zh-CN.md)。

## H3 技术依据

本项目的网格设计参考 Isaac Brodsky 于 2018 年发布的 Uber Engineering 文章 [H3: Uber’s Hexagonal Hierarchical Spatial Index](https://www.uber.com/us/en/blog/h3/)。该资料是官方工程文章，不是同行评审学术论文；本仓库不复制其全文，只保存书目信息、技术摘要和本项目的映射关系。

文章及 H3 官方文档说明了以下关键性质：

- H3 将地球划分为层级六边形单元，便于把海量点事件聚合到稳定的空间桶。
- 六边形相邻中心距离类型单一，比方格更适合近邻、平滑和近似圆形范围分析。
- H3 有 0–15 共 16 个分辨率；每升一级，单元面积约缩小到七分之一。
- 全球每个分辨率都包含 12 个五边形；算法不能假设所有单元都是普通六边形。
- H3 索引可做邻域、父子层级、区域覆盖和集合压缩，但候选召回后仍需计算真实距离。

贵阳采用两套粒度：

- 空间骨架：R8 主层 + R7 父层。
- POI 就近查询：R9 细筛 + R7 大半径粗筛，再做精确距离过滤。

三类典型查询：

| 查询 | 空间策略 |
| --- | --- |
| “甲秀楼附近有什么” | 地名解析到一个 H3 锚点，展开安全 k 环，再按精确距离过滤 |
| “我附近有什么” | 将用户定位转换到项目统一坐标口径后落格，再执行同一邻域流程 |
| “贵阳最值得去/评分最高” | 先走全域业务过滤和排序；H3 只在用户同时指定位置时参与，不作为传统边界限制 |

坐标约束：H3 本身不会执行 GCJ-02、WGS84 或 BD-09 转换。当前贵阳快照以项目声明的 GCJ-02 值保持内部一致，因此其 H3 ID 不得与 WGS84 生成的 H3 ID 混用。跨城市交换建议保留 WGS84 标准 H3，并将 GCJ-02 仅用于中国地图展示；迁移前必须重算并验证全部索引。

更完整的技术记录见 [H3 参考与项目映射](docs/references/h3-spatial-index.md)。

## 数据来源边界

| 来源 | 在图谱中的角色 | 公开策略 |
| --- | --- | --- |
| 官方行政区、开放边界、开放交通 | 空间框架与公共事实 | 按来源许可和署名公开 |
| 高德、Google Maps / Places | POI 发现、坐标与业务字段 | 不公开原始响应或全量平台数据 |
| 携程、Trip.com | 酒店与景点快照 | 不公开受限详情、评论和动态价格 |
| 小红书 / 点点 AI | 需求发现与体验证据 | 不公开帖子全文、作者信息或临时访问参数 |
| 百度百科、官网、政府网站 | 历史文化与事实核验 | 保存引用和证据，不镜像整篇受版权保护内容 |

详见[公开数据与治理策略](docs/governance/publication-policy.zh-CN.md)。

## 仓库目录

```text
docs/
  architecture/        知识图谱与检索设计
  references/          H3 等技术参考
  governance/          公开、来源和证据治理规则
schemas/
  guiyang/             贵阳 OpenSPG Schema
  thailand/            泰国旅游 Schema
data/
  guiyang/spatial/     贵阳城市、行政区和 H3 网格
  guiyang/validation/  图谱验证报告
  thailand/catalog/    泰国本地全量数据目录与质量边界
  thailand/administrative/  泰国 ADM0–ADM3 CSV / GeoJSON
```

## 快速核验

```bash
# 贵阳公开 H3 单元数（含表头应为 13,012 行）
wc -l data/guiyang/spatial/guiyang-h3-cells-r7-r8.csv

# JSON 文件语法检查
find schemas data -name '*.json' -print0 | xargs -0 -n1 jq empty

# 一次完成行数、GeoJSON、文件大小和敏感信息检查
python scripts/validate_public_snapshot.py

# 贵阳 Schema 结构自检（10 条共享词表提示为已知 warning）
python scripts/lint_guiyang_schema.py schemas/guiyang/CityTourism.schema

# 查看当前提交中最大的文件
git ls-files -z | xargs -0 du -h | sort -h | tail
```

## 参考资料

- Isaac Brodsky, “H3: Uber’s Hexagonal Hierarchical Spatial Index,” Uber Engineering, 2018-06-27.
- [H3 官方文档：系统概览](https://h3geo.org/docs/core-library/overview/)
- [H3 官方文档：各分辨率单元统计](https://h3geo.org/docs/core-library/restable/)
- [H3 官方仓库](https://github.com/uber/h3)
