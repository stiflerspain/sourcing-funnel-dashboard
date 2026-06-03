"""Genera los JSON estaticos del dashboard desde los datos del scraper.

Lee  meli-market-scraper/experimentos/sourcing-funnel/data/weeks/<week>/competitors.jsonl
     + data/categories.json (arbol)
Escribe  ./data/weeks.json  y  ./data/<week>/{results,roots,subs,categories}.json

NO scrapea. Solo transforma datos ya scrapeados en JSON listos para el HTML estatico.
Uso: python build_static.py
"""
from __future__ import annotations
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
SRC = Path("/Users/alvaro/Dev/Proyectos/meli-market-scraper/experimentos/sourcing-funnel")
WEEKS_DIR = SRC / "data" / "weeks"
CATS_PATH = SRC / "data" / "categories.json"
OUT = HERE / "data"


def load_tree() -> dict:
    if not CATS_PATH.exists():
        return {}
    return {c["id"]: c for c in json.loads(CATS_PATH.read_text()).get("categories", [])}


def resolve_root(cat_id, by_id):
    c = by_id.get(cat_id) if cat_id else None
    if not c:
        return (None, "Otras")
    if c.get("level") == 1 or not c.get("parent_id"):
        return (c["id"], c["name"])
    parent = by_id.get(c["parent_id"])
    return (parent["id"], parent["name"]) if parent else (c.get("parent_id"), "Otras")


def load_week_rows(week, by_id):
    comp = WEEKS_DIR / week / "competitors.jsonl"
    rows = []
    with comp.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            n = r.get("n_competidores")
            if not isinstance(n, (int, float)):
                continue
            sub_id = r.get("categoria_id")
            sub_name = r.get("categoria") or (by_id.get(sub_id, {}).get("name") if sub_id else None) or "GLOBAL"
            root_id, root_name = resolve_root(sub_id, by_id)
            rows.append({"keyword": r["keyword"], "sub_id": sub_id, "categoria": sub_name,
                         "root_id": root_id, "root_name": root_name, "n_competidores": int(n)})
    return rows


def quintiles(sorted_ns):
    return statistics.quantiles(sorted_ns, n=5) if len(sorted_ns) >= 5 else []


def score_1_5(n, thr):
    if not thr:
        return 3
    if n <= thr[0]: return 5
    if n <= thr[1]: return 4
    if n <= thr[2]: return 3
    if n <= thr[3]: return 2
    return 1


def aggregate(rows, key_id, key_name):
    buckets, names, roots = defaultdict(list), {}, {}
    for r in rows:
        k = r.get(key_id) or "__none__"
        buckets[k].append(r["n_competidores"])
        names[k] = r.get(key_name) or "—"
        roots[k] = r.get("root_name") or "—"
    pre = []
    for k, ns in buckets.items():
        pre.append({"id": k, "nombre": names[k], "root_name": roots[k],
                    "n_keywords": len(ns), "median_competidores": round(statistics.median(ns), 1),
                    "min_competidores": min(ns), "max_competidores": max(ns)})
    thr = quintiles(sorted(c["median_competidores"] for c in pre))
    for c in pre:
        c["score"] = score_1_5(c["median_competidores"], thr)
    pre.sort(key=lambda c: (-c["score"], c["median_competidores"]))
    return pre


def list_weeks():
    return sorted(d.name for d in WEEKS_DIR.iterdir() if (d / "competitors.jsonl").exists())


def build():
    by_id = load_tree()
    weeks_meta = []
    for week in list_weeks():
        rows = load_week_rows(week, by_id)
        wdir = OUT / week
        wdir.mkdir(parents=True, exist_ok=True)

        # results (keywords) con score
        ns = sorted(r["n_competidores"] for r in rows)
        thr = quintiles(ns)
        results = [{**r, "score": score_1_5(r["n_competidores"], thr)} for r in rows]
        (wdir / "results.json").write_text(json.dumps(results, ensure_ascii=False, separators=(",", ":")))

        # roots
        roots = aggregate(rows, "root_id", "root_name")
        subs_by_root = defaultdict(set)
        for r in rows:
            subs_by_root[r.get("root_id") or "__none__"].add(r.get("sub_id"))
        for c in roots:
            c["root_id"], c["root_name"] = c["id"], c["nombre"]
            c["n_subs"] = len(subs_by_root.get(c["id"], set()))
        (wdir / "roots.json").write_text(json.dumps(roots, ensure_ascii=False, separators=(",", ":")))

        # subs (mapa root_id -> [subs])
        subs_map = {}
        for root in roots:
            rid = root["id"]
            sub_rows = [r for r in rows if (r.get("root_id") or "__none__") == rid]
            agg = aggregate(sub_rows, "sub_id", "categoria")
            for c in agg:
                c["sub_id"], c["categoria"] = c["id"], c["nombre"]
            subs_map[rid] = agg
        (wdir / "subs.json").write_text(json.dumps(subs_map, ensure_ascii=False, separators=(",", ":")))

        # categories (flat subs)
        cats = aggregate(rows, "sub_id", "categoria")
        for c in cats:
            c["sub_id"], c["categoria"] = c["id"], c["nombre"]
        (wdir / "categories.json").write_text(json.dumps(cats, ensure_ascii=False, separators=(",", ":")))

        comp = WEEKS_DIR / week / "competitors.jsonl"
        weeks_meta.append({"week": week, "rows": len(rows),
                           "mtime": comp.stat().st_mtime})
        print(f"  {week}: {len(rows)} filas, {len(roots)} raices, {len(cats)} subcats")

    weeks_meta.sort(key=lambda x: x["week"], reverse=True)
    (OUT / "weeks.json").write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weeks": weeks_meta,
    }, ensure_ascii=False, indent=2))
    print(f"[ok] {len(weeks_meta)} semanas -> {OUT}")


if __name__ == "__main__":
    build()
