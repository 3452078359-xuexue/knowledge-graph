# 全量数据快照说明

本目录的全量快照由 `scripts/build_full_data_snapshot.py` 从两个已整理交付包生成：

- 贵阳：`v11.2.0-amap-food-fields`，含 30 类实体、业务结构化表、图谱导入文件、来源备份和验证报告。
- 泰国：`20260913` 按业务分类整理包，含旅游、景点、美食、交通、酒店、购物、休闲及行政区数据。

## H3 版本

贵阳使用当前生产约定：

- POI：R9 细索引与 R7 粗索引。
- 空间骨架：R8 主层与 R7 父层。
- 实现：`h3-py 4.x` 的 `latlng_to_cell`。
- 坐标口径：当前高德运行时使用 GCJ-02。该索引集合只能与同样由 GCJ-02 数值生成的 H3 ID 一起使用，不能和 WGS84 H3 混查。

`scripts/validate_guiyang_h3_index.py` 会重新计算所有 `geoPrecision=exact` 点的 R9/R7，并检查 GeoCell 和 PlaceAlias 的分辨率；结果写入 `data/guiyang/H3_INDEX_VALIDATION.json`。

## GitHub 文件存储

普通 Git 文件不能达到 100 MiB。生成器把 45 MiB 及以上的文件转换为确定性 `.gz`，原始相对路径、压缩前后 SHA-256、文件大小及排除原因记录在 `full-data-manifest.json`。

恢复文件：

```bash
gzip -dk path/to/file.json.gz
```

8 个 XLSX 的 55 个工作表同时以 UTF-8 CSV 形式放在各自目录下的 `csv_export/`。`csv-export-manifest.json` 记录行数、列数、源工作表、字节数和 SHA-256。

## 安全边界

快照不会写入 API Key、Cookie、登录态、浏览器 Profile、本机绝对路径、临时访问令牌、缓存数据库、失败截图或锁文件。结构化文件中的 `xsec_token`、API Key 和类似字段保留表头但将值替换为 `[REDACTED]`；包含其他敏感字符串的 XLSX 不进入快照，相同业务数据保留 CSV/JSON 版本。

本快照已在公开 GitHub 仓库中发布。项目自研成果的开放条款见根目录 `LICENSE` 与 `DATA-LICENSE.md`。社媒帖子、评论、平台字段和动态价格等第三方材料仍受原来源条款、个人信息和内容版权约束；本项目不代替原权利人再授权。
