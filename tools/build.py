"""Gộp dữ liệu thành các tệp xuất bản trong site/data/. Chạy: python tools/build.py"""
import csv, collections, glob, json, os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "data")
os.makedirs(OUT, exist_ok=True)

actors, relations, events, policies = [], [], [], []
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    if not os.path.isdir(region_dir):
        continue
    for path in sorted(glob.glob(os.path.join(region_dir, "actors", "*.yaml"))):
        actors.append(yaml.safe_load(open(path, encoding="utf-8")))
    for name, bucket in (("events.yaml", events), ("policies.yaml", policies)):
        p = os.path.join(region_dir, name)
        if os.path.exists(p):
            bucket.extend(yaml.safe_load(open(p, encoding="utf-8")) or [])
    r = os.path.join(region_dir, "relations.csv")
    if os.path.exists(r):
        relations.extend(csv.DictReader(open(r, encoding="utf-8")))

def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

dump("actors.json", actors)
dump("relations.json", relations)
dump("events.json", events)
dump("policies.json", policies)

cols = ["id", "name_vi", "name_en", "type", "categories", "region", "website", "verification", "sources"]
with open(os.path.join(OUT, "actors.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for a in actors:
        w.writerow([a["id"], a["name"].get("vi", ""), a["name"].get("en", ""), a["type"],
                    "; ".join(a.get("categories", [])), a["region"], a.get("website", ""),
                    a["verification"]["level"], "; ".join(a["sources"])])

features = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": a["coordinates"]},
             "properties": {"id": a["id"], "name": a["name"]["vi"], "type": a["type"]}}
            for a in actors if a.get("coordinates")]
dump("actors.geojson", {"type": "FeatureCollection", "features": features})

stats = {
    "actors": len(actors),
    "by_type": collections.Counter(a["type"] for a in actors),
    "by_region": collections.Counter(a["region"] for a in actors),
    "by_verification": collections.Counter(a["verification"]["level"] for a in actors),
    "relations": len(relations), "events": len(events), "policies": len(policies),
    "with_coordinates": len(features),
}
dump("stats.json", stats)
print(json.dumps(stats, ensure_ascii=False))
