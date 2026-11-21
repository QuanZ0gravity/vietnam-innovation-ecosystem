"""Kiểm tra dữ liệu: schema, trùng lặp, tham chiếu. Chạy: python tools/validate.py"""
import csv, difflib, glob, json, os, re, sys, unicodedata
import yaml
from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
schema = json.load(open(os.path.join(ROOT, "schema", "actor.schema.json"), encoding="utf-8"))
validator = Draft202012Validator(schema)
errors = []

def norm(s):
    return re.sub(r"\W+", "", (s or "").lower())

STOP = r"\b(cong ty|co phan|ctcp|tnhh|jsc|co ltd|ltd|pte|llc|inc|group|truong|the|vietnam|viet nam|investment fund|ventures?)\b"
ABBR = {r"\bdh\b": "dai hoc", r"\bdhdn\b": "dai hoc da nang", r"\bdmst\b": "doi moi sang tao", r"\bnc\b": "nghien cuu", r"\bspkt\b": "su pham ky thuat"}

def fold(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()
    for k, v in ABBR.items():
        s = re.sub(k, v, s)
    s = re.sub(STOP, " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())

def similar(a, b):
    if not a or not b:
        return False
    ta, tb = set(a.split()), set(b.split())
    return difflib.SequenceMatcher(None, a, b).ratio() > 0.85 or len(ta & tb) / len(ta | tb) >= 0.75

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

# Tên gần giống nhau: báo lỗi, trừ cặp đã được xác nhận là hai tác nhân khác nhau
allowed = set()
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    nd = os.path.join(region_dir, "not-duplicates.csv")
    if os.path.exists(nd):
        for row in csv.DictReader(open(nd, encoding="utf-8")):
            allowed.add(frozenset((row["a"], row["b"])))
folded = []
for rid, rel in ids.items():
    rec = yaml.safe_load(open(os.path.join(ROOT, rel), encoding="utf-8"))
    names = [rec.get("name", {}).get("vi")] + (rec.get("alt_names") or [])
    folded.append((rid, rel, [fold(n) for n in names if n]))
for i, (ia, ra, na) in enumerate(folded):
    for ib, rb, nb in folded[i + 1:]:
        if frozenset((ia, ib)) in allowed:
            continue
        if any(similar(x, y) for x in na for y in nb):
            errors.append(f"{ra}: có thể trùng với {rb}. Nếu là một, hãy gộp hồ sơ; nếu khác nhau, thêm cặp id vào not-duplicates.csv")

for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    rfile = os.path.join(region_dir, "relations.csv")
    if os.path.exists(rfile):
        for i, row in enumerate(csv.DictReader(open(rfile, encoding="utf-8")), start=2):
            for side in ("from", "to"):
                if row[side] not in ids:
                    errors.append(f"{os.path.relpath(rfile, ROOT)}:{i}: '{row[side]}' không tồn tại")

opp_schema = Draft202012Validator(json.load(open(os.path.join(ROOT, "schema", "opportunity.schema.json"), encoding="utf-8")))
AGGREGATORS = ("startupdanang.vn",)
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    ofile = os.path.join(region_dir, "opportunities.yaml")
    if not os.path.exists(ofile):
        continue
    rel = os.path.relpath(ofile, ROOT)
    seen = set()
    for item in yaml.safe_load(open(ofile, encoding="utf-8")) or []:
        oid = item.get("id")
        for e in opp_schema.iter_errors(item):
            errors.append(f"{rel} [{oid}]: {'/'.join(map(str, e.path)) or '(gốc)'}: {e.message}")
        if oid in seen:
            errors.append(f"{rel}: id '{oid}' bị trùng")
        seen.add(oid)
        for k in ("apply_url", "primary_source"):
            if any(a in (item.get(k) or "") for a in AGGREGATORS):
                errors.append(f"{rel} [{oid}]: {k} phải là trang của đơn vị tổ chức, không phải trang tổng hợp; chuyển liên kết này sang secondary_sources")
        for x in item.get("organizer_ids") or []:
            if x not in ids:
                errors.append(f"{rel} [{oid}]: organizer_ids '{x}' không có trong danh bạ")

if errors:
    print(f"Có {len(errors)} lỗi:\n" + "\n".join(errors))
    sys.exit(1)
print(f"OK: {len(ids)} tác nhân, không có lỗi.")
