# 贵阳高价值 POI 小红书体验补采

本批以当前知识图谱中的标准 POI 为主键，使用小红书点点 AI 发现可追溯的公开帖子，再进入逐帖语义审核。点点 AI 回答不直接覆盖高德、携程、官方来源形成的稳定事实。

## 范围

- 任务总量：216 个标准 POI。
- P0：116 个，优先本轮采集；P1：100 个，在 P0 质量复核后续采。
- 修文县、息烽县、开阳县列为 P2 县域扩展，并非永久排除；先用核心城区 P0 校准问题和审核成本，再单独按县域旅游价值生成任务。
- 业务类型：餐饮美食 120、住宿酒店 80、景区 12、交通枢纽 4。
- 行政范围：云岩区、南明区、观山湖区、花溪区、乌当区、白云区、清镇市。
- 每题只核实一个图谱实体；连锁分店必须依靠分店名、地址、商圈或邻近地标确认。

## 当前进度与停止点

- 严格完成 184/216：P0 116/116；P1 餐饮 60/60；P1 酒店 8/40。
- 已归并 4,031 篇去重小红书帖子；当前生成 2,140 条待复核 `SourceEvidence` 候选、184 个 `ReviewItem`，人工采纳仍为 0。
- 剩余 32 家均为 P1 酒店（问题 0185–0216）。页面断连后连续两次未通过稳定输入门槛，采集器未发送问题并安全暂停；原问题表和 JSONL 可直接断点续采。
- 餐饮 P1 的四层边际收益与酒店样本结论见 `04_处理结果/09_P1分层收益与停止结论.json`。低价值餐饮已到主动采集停止点，后续改由用户查询或字段证据缺口触发。

## 目录与阶段

1. `01_任务设计/`：优先级队列、点点 AI 问题表、生成审计与严格校验。
2. `02_原始采集/`：断点 JSONL、问答 CSV、带 URL 与完整正文的参考帖子 CSV、失败截图。
3. `03_图谱审核暂存/`：采集审计、帖子与 POI 候选关联、`RawSourceAnswer`、`SourceEvidence`、`ReviewItem`、`CollectionBatch` 增量及联合 Schema 校验报告。
4. `04_处理结果/`：统一帖子知识库、逐实体语义审核包、字段级人工审核决定表与审核说明。
5. `05_人工审核入图/`：只有人工明确裁决且通过校验后才生成的 `SourceEvidence` 决定增量、已完成 `ReviewItem` 增量和校验报告；本目录永不改写基础 POI。
6. `贵阳高价值POI点点补采任务与进度.xlsx`：任务、采集审计、收益、帖子候选和 P1 闸门的一体化进度工作簿。

## 质量闸门

- 只接收 `xhs_note + full_post + capture_status=complete` 且有稳定帖子 ID、URL、正文的来源。
- “采集成功”采用严格口径：回答完成且来源追溯完整；回答成功但来源正文未采全的轮次只留原始日志，状态为“来源不完整待重试”，不生成 `RawSourceAnswer`、`ReviewItem` 或 P1 收益。
- 优先近 24 个月；仅在证据不足时接受 24–36 个月；超过 36 个月自动排除。
- 标题或正文必须直接命中标准实体名称；连锁分店缺少位置上下文时进入人工审核，不自动归属。
- 空间型实体增加异地同名排除；所有 POI 都检查行政区冲突。异地同名直接排除，目标行政区冲突只生成核验工单，不据社媒自动改行政区。
- 点点 AI 只作来源发现。所有 `SourceEvidence.decision` 初始为 `待复核`，接受数固定为 0。
- 小红书完整帖子正文保留在本地帖子库；图谱只保存 `xhs:<note_id>`、URL、短引文和 `xhs-post-kb://<note_id>` 快照引用。
- 未完成逐帖语义审核前，不写回 `visitorDemandScenarios`、`ugcPoiSubtype`、`ugcLocationDescription`、`trendingScore` 或 `trendingEvidence`。
- 当前图谱中 `src_xhs.publishable=否`。即使逐帖审核后把 `SourceEvidence.decision` 改为 `采纳`，也只表示证据可供回答 Agent 使用，不代表可直接改写 POI 的稳定事实层或把实体提升为 `ingestable`。
- 回答 Agent 的读取路径为：标准 POI ID → `SourceEvidence(objectId, decision=采纳)` → `externalIds` 中的 `xhs:<note_id>` → 本地帖子知识库正文。用户展示时带帖子 URL、发布日期和短引文。
- 本批是逐实体定向检索，不是全量平台抽样，严禁据此生成 `trendingScore`、热门榜位或“全网最火”结论。
- 人工采纳必须逐帖逐字段完成五项判断：直接指向、分店确认、游客亲历、独立用户、可用体验断言；连续引文还必须能在本地完整正文中定位。
- 机器标记为营销或疑似协同营销的帖子默认不能采纳；只有人工明确判定为误报并写审核说明后，安全入图脚本才允许通过。

## 可重复执行

日常刷新全部派生产物（暂存、收益闸门、帖子知识库、语义审核包、人工审核表、全图联合校验和进度工作簿）优先使用：

```bash
python3 scripts/refresh_guiyang_xhs_batch.py
```

生成任务：

```bash
python3 scripts/build_guiyang_xhs_high_value_tasks.py \
  --output-dir outputs/20260916_贵阳高价值POI点点补采/01_任务设计
```

构建审核暂存：

```bash
python3 scripts/build_guiyang_xhs_graph_staging.py \
  --tasks outputs/20260916_贵阳高价值POI点点补采/01_任务设计/01_高价值POI补采优先级.csv \
  --qa outputs/20260916_贵阳高价值POI点点补采/02_原始采集/贵阳高价值POI体验补采_点点AI问答.csv \
  --sources outputs/20260916_贵阳高价值POI点点补采/02_原始采集/贵阳高价值POI体验补采_点点AI问答_参考帖子.csv \
  --output-dir outputs/20260916_贵阳高价值POI点点补采/03_图谱审核暂存
```

联合校验会把审核增量临时合并到现有全图后检查引用、字段类型、枚举、时间、空间和跨字段约束；不会修改桌面上的正式图谱文件。

生成或续写字段级人工审核表（重复运行会保留已填的审核列）：

```bash
python3 scripts/build_guiyang_xhs_evidence_review_template.py \
  --candidates outputs/20260916_贵阳高价值POI点点补采/03_图谱审核暂存/02_帖子_POI证据候选.csv \
  --output outputs/20260916_贵阳高价值POI点点补采/04_处理结果/07_字段级证据审核决定表.csv \
  --guide outputs/20260916_贵阳高价值POI点点补采/04_处理结果/08_字段级审核操作说明.json
```

应用人工决定（空白行不会被解释；任一已裁决行校验失败时整批拒绝生成可入图证据）：

```bash
python3 scripts/apply_guiyang_xhs_review_decisions.py \
  --decisions outputs/20260916_贵阳高价值POI点点补采/04_处理结果/07_字段级证据审核决定表.csv \
  --candidate-evidence outputs/20260916_贵阳高价值POI点点补采/03_图谱审核暂存/04_SourceEvidence候选增量.json \
  --review-items outputs/20260916_贵阳高价值POI点点补采/03_图谱审核暂存/05_ReviewItem增量.json \
  --sources outputs/20260916_贵阳高价值POI点点补采/02_原始采集/贵阳高价值POI体验补采_点点AI问答_参考帖子.csv \
  --parsed-schema [LOCAL_HOME]/Desktop/贵州城市知识图谱/01_Schema/贵州城市知识图谱Schema解析.json \
  --output-dir outputs/20260916_贵阳高价值POI点点补采/05_人工审核入图
```
