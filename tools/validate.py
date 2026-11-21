"""Kiểm tra dữ liệu: schema, trùng lặp, tham chiếu. Chạy: python tools/validate.py"""
import csv, glob, json, os, re, sys
import yaml
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
schema = json.load(open(os.path.join(ROOT, "schema", "actor.schema.json"), encoding="utf-8"))
validator = Draft202012Validator(schema)
errors = []

def norm(s):
    return re.sub(r"\W+", "", (s or "").lower())

ids, names, sites, places = {}, {}, {}, set()
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    if not os.path.isdir(region_dir):
        continue
    pfile = os.path.join(region_dir, "places.yaml")
    if os.path.exists(pfile):
        places |= {p["id"] for p in (yaml.safe_load(open(pfile, encoding="utf-8")) or [])}
    for path in sorted(glob.glob(os.path.join(region_dir, "actors", "*.yaml"))):
        rel = os.path.relpath(path, ROOT)
        rec = yaml.safe_load(open(path, encoding="utf-8"))
        for e in validator.iter_errors(rec):
            errors.append(f"{rel}: {'/'.join(map(str, e.path)) or '(gốc)'}: {e.message}")
        rid = rec.get("id")
        if rid != os.path.splitext(os.path.basename(path))[0]:
            errors.append(f"{rel}: id '{rid}' phải trùng tên tệp")
        if rid in ids:
            errors.append(f"{rel}: id trùng với {ids[rid]}")
        ids[rid] = rel
        n = norm(rec.get("name", {}).get("vi"))
        if n and n in names:
            errors.append(f"{rel}: tên trùng với {names[n]} (nếu là hai tổ chức khác nhau, ghi rõ trong tên)")
        names.setdefault(n, rel)
        w = (rec.get("website") or "").lower().rstrip("/").replace("://www.", "://")
        if w and w in sites:
            errors.append(f"{rel}: website trùng với {sites[w]}")
        if w:
            sites.setdefault(w, rel)
        if rec.get("place") and rec["place"] not in places:
            errors.append(f"{rel}: place '{rec['place']}' không có trong places.yaml")

for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    rfile = os.path.join(region_dir, "relations.csv")
    if os.path.exists(rfile):
        for i, row in enumerate(csv.DictReader(open(rfile, encoding="utf-8")), start=2):
            for side in ("from", "to"):
                if row[side] not in ids:
                    errors.append(f"{os.path.relpath(rfile, ROOT)}:{i}: '{row[side]}' không tồn tại")

if errors:
    print(f"Có {len(errors)} lỗi:\n" + "\n".join(errors))
    sys.exit(1)
print(f"OK: {len(ids)} tác nhân, không có lỗi.")
