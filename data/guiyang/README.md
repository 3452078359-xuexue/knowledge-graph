# 贵阳公开数据快照

## 已公开

| 文件 | 记录数 | 说明 |
| --- | ---: | --- |
| `spatial/guiyang-city.csv` | 1 | 城市配置 |
| `spatial/guiyang-admin-areas.csv` | 157 | 市、区县、街道乡镇三级行政实体 |
| `spatial/guiyang-admin-registry-review.csv` | 157 | 官方区划核验结果 |
| `spatial/guiyang-h3-cells-r7-r8.csv` | 13,011 | R8 主骨架 11,297 + R7 粗层 1,714 |
| `validation/guiyang-graph-validation.json` | 1 份 | Schema、节点、关系和空间检查 |

## 本地存在但未公开

- 24,238 条高德美食及其原始响应；
- 携程酒店、景区详情和动态业务字段；
- 交通 POI、线路及平台原始数据；
- 40,106 条包含第三方 POI 名称的完整 PlaceAlias 索引；
- 小红书帖子全文、评论、作者信息和点点 AI 原始回答；
- 190MB 标准化全量 JSON 和 268MB 节点关系导入包。

这些数据仍保存在本地知识图谱目录，并通过批次 ID、来源 ID、校验报告和 SHA 摘要管理。未公开不表示数据丢失，而是公开范围受文件体量、平台条款、版权和个人信息治理约束。

## 使用限制

- H3 骨架中的 `poiCount`、类别和来源分布是派生统计，会随数据挂载重算。
- `adminAmbiguous=是` 的格子不能直接用于行政区统计。
- `dataQuality=needs_review` 表示记录尚未达到可直接发布事实的全部条件。
- 当前索引按贵阳项目声明的 GCJ-02 输入生成，不得与 WGS84 H3 混合。
