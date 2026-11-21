"""Gợi ý lĩnh vực cho các hồ sơ chưa có trường `sectors`, dựa trên phân loại, tên và mô tả.

Chạy: python3 tools/suggest_sectors.py          (chỉ in gợi ý)
      python3 tools/suggest_sectors.py --write  (ghi vào hồ sơ chưa có `sectors`)
Gợi ý chỉ là điểm khởi đầu; tổ chức tự sửa lại trong hồ sơ của mình.
"""
import glob, os, re, sys, unicodedata
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTORS = yaml.safe_load(open(os.path.join(ROOT, "schema", "sectors.yaml"), encoding="utf-8"))
RX = [(s["id"], re.compile(s["keywords"])) for s in SECTORS]
TYPES = ("startup", "company", "creator", "fund")

def fold(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

def suggest(a):
    txt = " " + fold(" ".join((a.get("categories") or []) + [(a.get("description") or {}).get("vi", "") or "", a["name"]["vi"]])) + " "
    return [k for k, rx in RX if rx.search(txt)][:3]

if __name__ == "__main__":
    write = "--write" in sys.argv
    n = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "*", "actors", "*.yaml"))):
        a = yaml.safe_load(open(p, encoding="utf-8"))
        if a.get("sectors") or a["type"] not in TYPES:
            continue
        s = suggest(a)
        if not s:
            continue
        n += 1
        if write:
            out = {}
            for k, v in a.items():
                out[k] = v
                if k == "categories" or (k == "type" and "categories" not in a):
                    out["sectors"] = s
            if "sectors" not in out:
                out["sectors"] = s
            yaml.safe_dump(out, open(p, "w", encoding="utf-8"), allow_unicode=True, sort_keys=False, width=1000)
        else:
            print(a["id"], s)
    print(f"{n} hồ sơ {'đã ghi' if write else 'có gợi ý'}")
