#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 CityTourism.schema（4 空格缩进 + desc/constraint 语法）"""
import re, json, sys, collections

def parse(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    ns, ents = None, {}
    cur_e = cur_sec = cur_p = cur_r = None
    for ln_no, ln in enumerate(lines, 1):
        if not ln.strip(): continue
        ind = len(ln) - len(ln.lstrip())
        t = ln.strip()
        if t.startswith("namespace "): ns = t.split()[1]; continue
        m = re.match(r"^(\w+)\(([^)]*)\): (EntityType|RelationType)$", t)
        if ind == 0 and m:
            cur_e = {"name": m.group(1), "cn": m.group(2), "kind": m.group(3),
                     "desc": "", "properties": {}, "relations": {}}
            ents[m.group(1)] = cur_e; cur_sec = cur_p = cur_r = None; continue
        if ind == 4 and t.startswith("desc:"): cur_e["desc"] = t[5:].strip(); continue
        if ind == 4 and t in ("properties:", "relations:"): cur_sec = t[:-1]; cur_r = None; continue
        m = re.match(r"^(\w+)\(([^)]*)\): (\w+)$", t)
        if m and ind == 8 and cur_sec == "properties":
            cur_p = {"cn": m.group(2), "type": m.group(3), "desc": "", "index": None, "constraint": None, "chunk": None, "optional": None, "_dups": []}
            cur_e["properties"][m.group(1)] = cur_p; continue
        if m and ind == 8 and cur_sec == "relations":
            cur_r = {"cn": m.group(2), "target": m.group(3), "desc": "", "properties": {}}
            cur_e["relations"][m.group(1)] = cur_r; cur_p = None; continue
        if m and ind == 16 and cur_r is not None:
            cur_p = {"cn": m.group(2), "type": m.group(3), "desc": "", "index": None, "constraint": None, "chunk": None, "optional": None, "_dups": []}
            cur_r["properties"][m.group(1)] = cur_p; continue
        for key in ("desc", "index", "constraint", "chunk", "optional"):
            if t.startswith(key + ":"):
                val = t[len(key)+1:].strip()
                tgt = cur_p if cur_p is not None else (cur_r if cur_r is not None else cur_e)
                if key == "desc" and ind == 12 and cur_r is not None and cur_p is None: tgt = cur_r
                # 同一字段块内重复写同一属性会静默后覆盖前，记下来交自检报错
                if tgt.get(key) not in (None, "") and "_dups" in tgt:
                    tgt["_dups"].append((ln_no, key, tgt[key], val))
                tgt[key] = val
                break
    return {"namespace": ns, "types": ents}

if __name__ == "__main__":
    d = parse(sys.argv[1] if len(sys.argv) > 1 else "CityTourism.schema")
    # 输出路径必须可指定 —— 演进测试拿变异后的 schema 解析时若写回共享的 parsed.json，
    # 会把线上产物悄悄改掉（已踩过：ticketPrice 被改名 admissionFee 泄漏进真库）
    out = sys.argv[2] if len(sys.argv) > 2 else "parsed.json"
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    T = d["types"]
    np_ = sum(len(e["properties"]) for e in T.values())
    nr = sum(len(e["relations"]) for e in T.values())
    nrp = sum(len(r["properties"]) for e in T.values() for r in e["relations"].values())
    print(f"namespace {d['namespace']}")
    print(f"实体 {len(T)} · 属性 {np_} · 关系 {nr} · 关系属性 {nrp}")
    tc = collections.Counter(p["type"] for e in T.values() for p in e["properties"].values())
    print("属性类型:", dict(tc))
    cs = collections.Counter()
    for e in T.values():
        for p in e["properties"].values():
            if p["constraint"]:
                for c in re.findall(r"NotNull|MultiValue|Enum", p["constraint"]): cs[c] += 1
    print("约束:", dict(cs))
