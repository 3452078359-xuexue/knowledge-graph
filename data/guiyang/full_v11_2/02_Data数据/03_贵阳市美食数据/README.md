# 贵阳市美食数据

来源口径：仅高德 POI；`business.rating >= 3.5`；不与大众点评、小红书对齐。

当前使用高德 POI 搜索 2.0（v5）的 `show_fields=business,children,indoor,navi,photos`。电话、特色菜、商圈、照片、父 POI 等只写入接口真实返回值；缺失值不从地址或店名推断。街道乡镇由每个唯一 GCJ-02 精确坐标调用逆地理编码取得。`parent` 与 `indoor.cpid` 是不同层级，分别保存。

| 中文数据名 | Schema 实体 | 记录数 | 文件 |
|---|---|---:|---|
| 美食POI | `FoodAndBeverage` | 24,238 | `贵阳市美食POI数据.json` |
| 美食POI关键字段补全表 | `FoodAndBeverage` | 24,238 | `贵阳市美食POI_评分3.5以上_关键字段补全_24238家.xlsx` |
| 菜品 | `Dish` | 5 | `贵阳市菜品数据.json` |

字段覆盖率、父 POI 未返回清单、区县口径冲突及 API 实调结果见 `../../04_验证报告/贵阳市高德美食关键字段补全报告.json`。高德公开接口没有可靠的营业/倒闭状态，实体继续保持 `needs_review`，不得仅凭本数据断言商家当前仍营业。
