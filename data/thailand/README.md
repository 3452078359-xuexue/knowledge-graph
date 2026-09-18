# 泰国公开数据快照

## 已公开

- 泰国旅游知识图谱 Schema（JSON / Cypher）；
- 257 个本地整理文件的数据目录和分类统计；
- 各来源的覆盖范围、时效和质量边界；
- ADM0–ADM3 中泰双语行政区 CSV 与 GeoJSON；
- 行政区质量报告和来源说明。

行政区规模：

| 层级 | 记录数 |
| --- | ---: |
| ADM0 国家 | 1 |
| ADM1 府/特别行政区 | 77 |
| ADM2 县/曼谷区 | 928 |
| ADM3 乡/曼谷分区 | 7,436 |

## 未公开

- ADM4 村级 75,653 条名录和 59,509 个历史匹配点位；
- Google Maps / Places 地点、评论和原始响应；
- 携程、Trip.com 酒店与景点详情、房型和动态价格；
- 小红书帖子、作者和点点 AI 原始内容；
- Transitland / NAMTANG 全量 GTFS 明细。

未公开部分已经登记在 `catalog/local-full-data-manifest.json`，可据此在有授权的本地环境中定位和复建，但清单不是对第三方内容的再分发许可。

## 来源与署名

行政区数据综合 DOPA、HDX / Royal Thai Survey Department、OpenStreetMap、GISTDA 和 canonical admin names 项目。不同层级的有效日期、许可和精度并不相同，请先阅读 `administrative/README.zh-CN.md`。

特别注意：曼谷 ADM3 边界来自 OpenStreetMap 行政关系，应遵守 ODbL；RTSD/OCHA 衍生边界不适用于土地权属、法务或高精度测绘。
