#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema 自身结构校验。数据校验管「数据符不符合 schema」，本文件管「schema 自己合不合法」。

存在的理由：TransitLine 的 relations 块曾放在维护字段之前，导致 8 个字段被解析成关系，
而数据校验依然报 0 error —— 结构坏了查不出来。这类错误人眼审 1300 行也发现不了。
"""
import re, sys, json, collections

FIELD_LIKE = {"sourceId","batchId","externalIds","dataQuality","contentHash",
              "createdAt","updatedAt","lastSeenAt","id","name","description"}

def lint(path):
    raw = open(path, encoding="utf-8").read()
    lines = raw.split("\n")
    E, W = [], []
    def err(ln, m): E.append((ln, m))
    def warn(ln, m): W.append((ln, m))

    # ── 逐行结构检查 ──
    cur_ent = cur_sec = None
    ent_line = {}
    seen_ent, seen_field = set(), collections.defaultdict(set)
    for i, ln in enumerate(lines, 1):
        if not ln.strip() or ln.strip().startswith("namespace"): continue
        ind = len(ln) - len(ln.lstrip())
        if ind % 4: err(i, f"缩进 {ind} 不是 4 的倍数")
        t = ln.strip()

        m = re.match(r"^(\w+)\(([^)]*)\): (EntityType|RelationType)$", t)
        if ind == 0:
            if not m: err(i, f"顶层行不是合法类型声明: {t[:40]}"); continue
            if not m.group(2).strip(): err(i, f"{m.group(1)} 缺中文名")
            if m.group(1) in seen_ent: err(i, f"实体重复定义 {m.group(1)}")
            seen_ent.add(m.group(1)); cur_ent = m.group(1); cur_sec = None
            ent_line[cur_ent] = i
            continue
        if ind == 4:
            if t in ("properties:", "relations:"):
                # relations 块之后不得再出现 properties 块
                if t == "properties:" and cur_sec == "relations":
                    err(i, f"{cur_ent}: properties 出现在 relations 之后，其字段会被误解析为关系")
                cur_sec = t[:-1]; continue
            if t.startswith("desc:"):
                if cur_sec: err(i, f"{cur_ent}: 实体级 desc 出现在 {cur_sec} 块内")
                continue
            err(i, f"{cur_ent}: 4 缩进层出现意外内容 {t[:40]}"); continue

        if ind == 8:
            m2 = re.match(r"^(\w+)\(([^)]*)\): (\w+)$", t)
            if m2:
                fn = m2.group(1)
                if not m2.group(2).strip(): err(i, f"{cur_ent}.{fn} 缺中文名")
                if fn in seen_field[(cur_ent, cur_sec)]:
                    err(i, f"{cur_ent}.{fn} 在同一块内重复")
                seen_field[(cur_ent, cur_sec)].add(fn)
                # 关系块里出现明显是字段的名字 → 位置错乱
                if cur_sec == "relations" and (fn in FIELD_LIKE or m2.group(3) in ("Text","Float","Integer")):
                    err(i, f"{cur_ent}: 「{fn}」出现在 relations 块内但看起来是属性 —— relations 块位置错误")
                continue
            if t.startswith(("desc:","index:","constraint:","chunk:","optional:")):
                err(i, f"{cur_ent}: {t.split(':')[0]} 缩进错误，应为 12"); continue
            err(i, f"{cur_ent}: 8 缩进层出现意外内容 {t[:40]}"); continue

        if ind in (12, 16, 20):
            if not t.startswith(("desc:","index:","constraint:","chunk:","optional:","properties:")) and \
               not re.match(r"^\w+\([^)]*\): \w+$", t):
                err(i, f"{cur_ent}: {ind} 缩进层出现意外内容 {t[:40]}")

    # ── 语义检查（用解析结果）──
    sys.path.insert(0, ".")
    from parse_schema import parse
    T = parse(path)["types"]

    for n, e in T.items():
        if e["kind"] != "EntityType": continue
        if not e["desc"]: warn(ent_line.get(n,0), f"{n} 缺 desc")
        if "id" not in e["properties"]: err(ent_line.get(n,0), f"{n} 未声明 id")
        for pn, p in e["properties"].items():
            if p["type"] == "Text" and not p.get("index"):
                warn(ent_line.get(n,0), f"{n}.{pn} 是 Text 但无 index")
            if p["type"] not in ("Text","Float","Integer") and p["type"] not in T:
                err(ent_line.get(n,0), f"{n}.{pn} 指向不存在的实体 {p['type']}")
            c = (p.get("constraint") or "").strip()
            if c:
                # 逐个吃掉合法 token，剩余非空即非法（Enum 值里含逗号，不能简单 split）
                rest = c
                for _ in range(6):
                    m2 = re.match(r'^(NotNull|MultiValue|Enum="[^"]*")\s*,?\s*', rest)
                    if not m2: break
                    rest = rest[m2.end():]
                if rest.strip():
                    err(ent_line.get(n,0), f"{n}.{pn} 未知约束片段 {rest.strip()!r}")
        for rn, r in e["relations"].items():
            if r["target"] not in T:
                err(ent_line.get(n,0), f"{n}.{rn} 目标 {r['target']} 不存在")

        props = e["properties"]
        if "geoPrecision" in props:
            required_spatial = {
                "latitude", "longitude", "coordinateSystem", "h3Index", "h3IndexCoarse",
            }
            missing = sorted(required_spatial - set(props))
            if missing:
                err(ent_line.get(n,0), f"{n} 有 geoPrecision 但缺空间字段 {missing}")
            if "NotNull" not in (props["geoPrecision"].get("constraint") or ""):
                err(ent_line.get(n,0), f"{n}.geoPrecision 必须 NotNull，空值会绕过空间闸门")
        identity_fields = {"identityStatus", "identityResolutionMethod", "possibleSameAs"}
        present_identity = identity_fields & set(props)
        if present_identity and present_identity != identity_fields:
            err(ent_line.get(n,0),
                f"{n} 身份治理字段不完整，缺 {sorted(identity_fields - present_identity)}")
        if "possibleSameAs" in props and props["possibleSameAs"]["type"] != n:
            err(ent_line.get(n,0), f"{n}.possibleSameAs 必须引用同类型 {n}")

    city_props = T.get("City", {}).get("properties", {})
    for field in ("spatialCoordinateSystem", "h3FineResolution", "h3CoarseResolution"):
        if field not in city_props:
            err(ent_line.get("City", 0), f"City 缺项目级空间策略字段 {field}")

    # ── 枚举重复 ──
    ev = collections.Counter()
    for n, e in T.items():
        for pn, p in e["properties"].items():
            m = re.search(r'Enum="([^"]+)"', p.get("constraint") or "")
            if m: ev[m.group(1)] += 1
    # 共享词表：同名字段在不同实体的枚举取值必须逐字相同，否则是漂移
    byfield = collections.defaultdict(set)
    for n, e in T.items():
        for pn, p in e["properties"].items():
            m = re.search(r'Enum="([^"]+)"', p.get("constraint") or "")
            if m: byfield[pn].add(m.group(1))
    # 只有真正的共享词表才要求一致。type/level/status 这类通用名在不同实体
    # 本就承载不同语义（餐饮类型 vs 菜品类型 vs 枢纽类型），不是漂移。
    SHARED = {"dataQuality", "geoPrecision", "coordinateSystem", "identityStatus",
              "identityResolutionMethod", "reviewStatus", "authorityLevel",
              "sourceType", "indoorOutdoor", "decision", "stability", "topic"}
    for pn, vs in byfield.items():
        if pn in SHARED and len(vs) > 1:
            err(0, f"共享词表漂移：{pn} 在不同实体取值不一致 —— {[v[:30] for v in sorted(vs)]}")
        elif pn not in SHARED and len(vs) > 1:
            warn(0, f"同名字段 {pn} 在 {len(vs)} 个实体有不同枚举 —— 若属同一概念应加入 SHARED 白名单")
    shared = {pn: len([1 for n,e in T.items() if pn in e["properties"]
                       and 'Enum' in (e["properties"][pn].get("constraint") or "")])
              for pn in byfield}
    for pn, c in sorted(shared.items(), key=lambda x:-x[1]):
        if pn in SHARED and c >= 3:
            warn(0, f"共享词表 {pn} 在 {c} 个实体重复声明 —— 一致性已由本工具强制，改动须同步全部 {c} 处")

    # ── 同一字段块内重复写同一属性（后者静默覆盖前者，改 schema 时最难发现）──
    for en, e in T.items():
        pairs = list(e["properties"].items()) + [
            (f"{rn}.{ppn}", pp) for rn, r in e["relations"].items()
            for ppn, pp in r["properties"].items()]
        for pn, p in pairs:
            for lno, k, old, new in (p.get("_dups") or []):
                err(lno, f"{en}.{pn} 重复声明 {k}：{old!r} 被 {new!r} 静默覆盖")

    return E, W, len(T)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "CityTourism.schema"
    E, W, n = lint(path)
    print(f"schema 自检：实体 {n} · error {len(E)} · warn {len(W)}")
    for ln, m in E[:20]: print(f"  [E] 行{ln:>5}  {m}")
    if len(E) > 20: print(f"  … 另有 {len(E)-20} 条")
    for ln, m in W[:12]: print(f"  [W] 行{ln:>5}  {m}")
    if len(W) > 12: print(f"  … 另有 {len(W)-12} 条")
    sys.exit(1 if E else 0)
