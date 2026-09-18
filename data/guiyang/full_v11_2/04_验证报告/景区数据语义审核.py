# -*- coding: utf-8 -*-
"""
景区数据语义审核 —— 专查既有验证器查不到的。

既有 24 项验证里 18 项是行数/列数/字段顺序，纯结构检查；
只有 6 项涉及语义，且没有一项检查「这条记录说的东西该不该存在」。
「综述」「生聚教训」「牌坊」当年就是这样全过 24 项的。
"""
import json, csv, os, re, collections, math, h3

D = "[LOCAL_HOME]/Desktop/贵州城市知识图谱/02_Data数据/02_贵阳市景区数据"
S = "[LOCAL_HOME]/Desktop/贵州城市知识图谱/01_Schema/CityTourism.schema"
L = lambda f: json.load(open(os.path.join(D, f), encoding='utf-8'))['records']
C = lambda f: list(csv.DictReader(open(os.path.join(D, f), encoding='utf-8-sig')))

sa, ar = L('贵阳市景区数据.json'), L('贵阳市景点数据.json')
fac, rt = L('贵阳市景区设施数据.json'), L('贵阳市游览路线数据.json')
rel = C('贵阳市景区关系明细表.csv')
ku = json.load(open(os.path.join(D,'贵阳市景区百科知识单元_已对齐.json'),encoding='utf-8'))['records']
schema = open(S, encoding='utf-8').read()

R = []
def chk(name, bad, tot, note=""):
    R.append((name, bad, tot, note)); return bad == 0

print("=" * 96); print("景区数据语义审核".center(88)); print("=" * 96)
print(f"\nScenicArea {len(sa)} · Area {len(ar):,} · Facility {len(fac)} · Route {len(rt)} · 关系 {len(rel):,}")

# ── A 实体该不该存在 ──
print("\n[A] 实体存在性")
JUNK = re.compile(r'(错误页|404|页面不存在|综述|概述|简介$|^(牌坊|名人故居|游客服务中心)$)')
junk_sa = [x for x in sa if JUNK.search(x.get('name') or '')]
chk("景区名不含词条结构性内容", len(junk_sa), len(sa),
    f"{[x['name'] for x in junk_sa]}" if junk_sa else "")
# 跨地域：贵阳的数据集里混了外地
OUT = re.compile(r'(深圳|广州|北京|上海|重庆|成都|昆明|遵义|安顺)')
out_sa = [x for x in sa if OUT.search(x.get('name') or '')]
chk("景区不含外地实体", len(out_sa), len(sa), f"{[x['name'] for x in out_sa]}" if out_sa else "")

# ── B Schema 约束 ──
print("\n[B] Schema 约束")
def enum_of(ent, field):
    m = re.search(r'^%s\(.*?\n(?:    .*\n|        .*\n|            .*\n)*' % ent, schema, re.M)
    if not m: return None
    b = m.group(0)
    m2 = re.search(r'        %s\(.*?\n(?:            (?!        ).*\n)*' % field, b)
    if not m2: return None
    m3 = re.search(r'Enum="([^"]+)"', m2.group(0))
    return set(m3.group(1).split(',')) if m3 else None
for ent, recs, field in (('Area', ar, 'areaType'), ('Area', ar, 'geoPrecision'),
                         ('Area', ar, 'dataQuality'), ('Area', ar, 'identityStatus'),
                         ('ScenicArea', sa, 'dataQuality')):
    e = enum_of(ent, field)
    if not e: continue
    bad = [x for x in recs if x.get(field) and x[field] not in e]
    chk(f"{ent}.{field} 取值在枚举内", len(bad), len(recs),
        f"越界值 {sorted({x[field] for x in bad})}" if bad else "")

# ── C 类型纯度：Area 不用于表示餐饮住宿商店 ──
print("\n[C] 实体类型纯度（schema：Area 不用于表示餐饮、住宿、商店）")
def primary(x): return (x.get('amapType') or '').split(';')[0]
BAD_PRIMARY = {'餐饮服务', '住宿服务', '购物服务', '商务住宅', '生活服务'}
# 审核要区分「未处理」与「已决策并记了理由」。地图厂商的主类与「是否可游览」
# 口径本就不同（省博归科教文化、步行街归购物服务），一刀切会把正确保留的也标红。
# 判定依据是有没有留下可追溯的决策记录，不是主类本身。
contaminated = [x for x in ar if primary(x) in BAD_PRIMARY
                and not x.get('_retypeReason') and not x.get('_reviewNote')]
decided = [x for x in ar if primary(x) in BAD_PRIMARY and (x.get('_retypeReason') or x.get('_reviewNote'))]
chk("Area 主类异常者均已决策", len(contaminated), len(ar),
    ("；".join(f"{x['name'][:14]}({primary(x)})" for x in contaminated[:8])
     if contaminated else f"{len(decided)} 条主类非风景名胜但已逐条决策并记录理由（改 areaType 或标待核）"))

# ── D 坐标与 H3 正确性（不只是完整性）──
print("\n[D] 坐标与 H3")
h3bad = []
for x in ar:
    if x.get('geoPrecision') != 'exact' or not x.get('latitude'): continue
    la, lo = float(x['latitude']), float(x['longitude'])
    if x.get('h3Index') and h3.latlng_to_cell(la, lo, 9) != x['h3Index']: h3bad.append((x['name'], 'R9'))
    elif x.get('h3IndexCoarse') and h3.latlng_to_cell(la, lo, 7) != x['h3IndexCoarse']: h3bad.append((x['name'], 'R7'))
chk("H3 与坐标一致（重算比对）", len(h3bad), len(ar),
    f"{h3bad[:5]}" if h3bad else "既有验证器只查 H3 非空，不查算得对不对")
# 坐标落在贵阳范围内
oob = [x for x in ar if x.get('latitude') and not (26.0 <= float(x['latitude']) <= 27.3
                                                   and 106.0 <= float(x['longitude']) <= 107.3)]
chk("坐标落在贵阳经纬范围内", len(oob), len(ar), f"{[(x['name'], x['latitude'], x['longitude']) for x in oob[:5]]}" if oob else "")
# district 与 adcode 一致
ADC = {'520102': '南明区', '520103': '云岩区', '520111': '花溪区', '520112': '乌当区',
       '520113': '白云区', '520115': '观山湖区', '520121': '开阳县', '520122': '息烽县',
       '520123': '修文县', '520181': '清镇市'}
dmis = [x for x in ar if x.get('adcode') in ADC and x.get('district') and x['district'] != ADC[x['adcode']]]
chk("district 与 adcode 一致", len(dmis), len(ar), f"{[(x['name'], x['district'], x['adcode']) for x in dmis[:5]]}" if dmis else "")

# ── E 跨实体层级 ──
print("\n[E] 跨实体层级")
san = {x['name'] for x in sa}
lvl = [x for x in ar if x['name'] in san]
chk("同一名称不同时是 ScenicArea 与 Area", len(lvl), len(ar),
    f"{[x['name'] for x in lvl]}" if lvl else "")
# locatedInScenicArea 指向存在的景区
said = {x['id'] for x in sa}
badref = [x for x in ar if x.get('locatedInScenicArea') and x['locatedInScenicArea'] not in said]
chk("locatedInScenicArea 指向存在的景区", len(badref), len(ar), "")

# ── F 重复 ──
print("\n[F] 重复")
dup_id = [k for k, v in collections.Counter(x['amapPoiId'] for x in ar if x.get('amapPoiId')).items() if v > 1]
chk("amapPoiId 无重复", len(dup_id), len(ar), f"{dup_id[:5]}" if dup_id else "")
# 坐标重合（5 位小数 ≈ 1m）
# 坐标重合不等于重复：地图厂商常给同一建筑群内的相邻对象标同一坐标
# （黔灵山藏经楼/玉佛殿、1958 园区多个表演点）。真重复的按 schema 记 possibleSameAs
# 候选并置 ambiguous，不自动合并。这里只查「重合且未作任何记录」的。
cg = collections.defaultdict(list)
for x in ar:
    if x.get('latitude'):
        cg[(round(float(x['latitude']), 5), round(float(x['longitude']), 5))].append(x)
undecided = [k for k, v in cg.items() if len(v) > 1
             and not any(m.get('possibleSameAs') or m.get('_coordNote') for m in v)]
noted = [k for k, v in cg.items() if len(v) > 1 and any(m.get('possibleSameAs') or m.get('_coordNote') for m in v)]
chk("坐标重合者均已判定", len(undecided), len(ar),
    (f"{len(undecided)} 组重合但未记录判定：" +
     "；".join("/".join(m['name'][:12] for m in cg[k]) for k in undecided[:3])
     if undecided else f"{len(noted)} 组已记 possibleSameAs 待人工确认"))

# ── G 关系语义 ──
print("\n[G] 关系语义")
decl = set(re.findall(r'^        (\w+)\(.*?\):\s*(?:ScenicArea|Area|Facility|Route|Zone|AdminArea|Dish|Product|Transit\w+)',
                      schema, re.M))
rel_types = collections.Counter(r['relationType'] for r in rel)
undecl = {k: v for k, v in rel_types.items() if k not in decl}
chk("关系类型在 schema 声明内", sum(undecl.values()), len(rel),
    f"未声明 {dict(sorted(undecl.items(), key=lambda kv: -kv[1]))}" if undecl else "")
ids = {x['id'] for x in sa} | {x['id'] for x in ar} | {x['id'] for x in fac} | {x['id'] for x in rt}
dang = [r for r in rel if r['sourceId'] not in ids and r['sourceType'] in ('Area', 'ScenicArea', 'Facility', 'Route')]
chk("关系源实体存在", len(dang), len(rel), "")

# ── H 内容质量 ──
print("\n[H] 内容质量")
# 地图厂商 POI 本来就不带描述，全库 100% 无描述是数据源特性不是错误。
# 真正该查的是：有百科知识可挂的实体，有没有把描述补上。
kuhost = {k['targetId'] for k in ku}
should = [x for x in ar if x['id'] in kuhost]
missing = [x for x in should if not (x.get('description') or x.get('shortDesc'))]
chk("有百科知识的实体已补描述", len(missing), max(len(should), 1),
    f"可补 {len(should)} 条 · 已补 {len(should)-len(missing)} 条。"
    f"其余 {len(ar)-len(should):,} 条无百科内容可挂 —— 地图厂商 POI 不带描述，属数据源特性")
saloc = [x for x in sa if not x.get('latitude')]
chk("景区有坐标", len(saloc), len(sa),
    f"{[x['name'] for x in saloc]}" if saloc else "")

print("\n" + "=" * 96)
bad_n = 0
for n, b, t, note in R:
    ok = b == 0
    bad_n += not ok
    print(f"  [{'过' if ok else '问题'}] {n:42s} {b:>5}/{t:<6}")
    if note: print(f"          {note[:150]}")
print("\n" + "=" * 96)
print(f"语义审核 {len(R)} 项 · 通过 {len(R)-bad_n} · 有问题 {bad_n}")
