# 泰国行政区划中泰双语与地图边界数据包

生成日期：2026-08-25

## 交付范围

- ADM0 国家：1 条，中心经纬度 + GeoJSON 多边形。
- ADM1 府/特别行政区：77 条，中心经纬度 + 77 个多边形。
- ADM2 县/曼谷区：928 条，中心经纬度 + 928 个多边形。
- ADM3 乡/曼谷分区：7,436 条，中心经纬度 + 7,436 个多边形。
- 村：DOPA 2025-12 人口文件中 75,653 条可用名录，其中 59,509 条匹配到GISTDA历史点位；不提供全国统一村界多边形。

泰国官方统计口径为76府、878县、7,256乡、75,693村；本数据包将曼谷1个特别行政区、50个区、180个分区纳入同一业务层级，因此ADM1/2/3分别为77、928、7,436。

## 本地地图校验

macOS 可双击 `启动地图校验.command`，或者在本目录运行：

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

然后打开 `http://127.0.0.1:8765/地图校验.html`。页面支持切换ADM0—ADM4、按代码或中/泰/英文搜索、点击边界查看属性与来源。该校验页使用无需API Key的OpenStreetMap底图，不会消耗Google Maps配额。

## Google Maps 使用结论

Google Maps Data-driven Styling在泰国原生支持国家和ADM1边界，不支持ADM2。县、乡/分区应加载本包GeoJSON；Google Places/Geocoding返回地点、中心点和视野框，不返回可下载的行政区边界坐标。

```javascript
map.data.loadGeoJson('/data/泰国_ADM2_县区边界.geojson');
map.data.setStyle((feature) => ({
  fillColor: '#2563EB', fillOpacity: 0.18,
  strokeColor: '#1D4ED8', strokeWeight: 1
}));
```

## 重要质量说明

1. ADM1/ADM2及非曼谷ADM3边界为RTSD/OCHA衍生简化边界，边界有效日主要为2019-02-21；中心点/面积来自RTSD/HDX，有效日2022-01-22。
2. 曼谷180个现行分区边界来自OpenStreetMap行政关系，抓取日为2026-08-25，许可为ODbL。若用于法务、土地权属、政府申报或高精度测绘，必须改用泰国主管机关最新权威边界复核。
3. 乡级中文名只保留Wikidata/OSM已有中文标签；其余以英文回退显示并标记“待本地化”，没有生成猜测性中文音译。
4. 村级点位来自GISTDA历史公开图层，只作为旅游搜索和地图标点参考，不应视为现行村中心或法定边界。
5. 所有GeoJSON坐标顺序为 `[经度, 纬度]`；表格中心点列顺序为“纬度、经度”。

## 主要来源

- DOPA：https://www.bora.dopa.go.th/wp-content/uploads/2025/12/tabdb_19122568.pdf
- HDX / Royal Thai Survey Department：https://data.humdata.org/dataset/cod-ab-tha
- Canonical admin names：https://github.com/DevelopedbyWill/thailand-canonical-admin-names
- GISTDA ArcGIS：https://gistdaportal.gistda.or.th/
- OpenStreetMap：https://www.openstreetmap.org/copyright
- Google DDS覆盖：https://developers.google.com/maps/documentation/javascript/dds-boundaries/coverage
