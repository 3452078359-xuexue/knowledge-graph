// thai-tourism.schema.v1  —  建库 DDL (FalkorDB / Neo4j openCypher)
// 说明：图库不强制 schema，这里用「唯一约束 + 索引」把类型与主键固化，等价于 schema。

// ---------- 唯一主键约束（id 不可变代理键）----------
CREATE CONSTRAINT admin_id   IF NOT EXISTS FOR (n:AdministrativeArea) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT attr_id    IF NOT EXISTS FOR (n:Attraction)         REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT scenic_id  IF NOT EXISTS FOR (n:ScenicArea)         REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (n:Facility)          REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT dining_id  IF NOT EXISTS FOR (n:DiningVenue)        REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT accom_id   IF NOT EXISTS FOR (n:Accommodation)      REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT retail_id  IF NOT EXISTS FOR (n:RetailVenue)        REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT ent_id     IF NOT EXISTS FOR (n:EntertainmentVenue) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT hub_id     IF NOT EXISTS FOR (n:TransportHub)       REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT source_id  IF NOT EXISTS FOR (n:Source)            REQUIRE n.id IS UNIQUE;

// ---------- 检索索引 ----------
CREATE INDEX admin_dopa  IF NOT EXISTS FOR (n:AdministrativeArea) ON (n.dopaCode);
CREATE INDEX admin_level IF NOT EXISTS FOR (n:AdministrativeArea) ON (n.adminLevel);
CREATE INDEX attr_name   IF NOT EXISTS FOR (n:Attraction)         ON (n.nameZh);
CREATE INDEX dining_name IF NOT EXISTS FOR (n:DiningVenue)        ON (n.nameZh);

// ---------- 关系类型（图库按写入自动建立，这里仅注明允许的 from→to）----------
// (:AdministrativeArea)-[:PART_OF]->(:AdministrativeArea)          子→父，递归到国
// (:Attraction|ScenicArea|Facility|DiningVenue|Accommodation|RetailVenue|EntertainmentVenue|TransportHub)-[:LOCATED_IN]->(:AdministrativeArea)
// (:Attraction|Facility|DiningVenue|RetailVenue|EntertainmentVenue)-[:INSIDE_SCENIC]->(:ScenicArea)
// (:KnowledgeUnit|FAQ)-[:DERIVED_FROM]->(:Source)
