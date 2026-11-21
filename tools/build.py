"""Dựng trang tĩnh và dữ liệu xuất bản vào site/. Chạy: python tools/build.py

Biến môi trường:
  SITE_ROOT  đường dẫn gốc của trang (mặc định "/")
  SITE_URL   địa chỉ đầy đủ để tạo sitemap (mặc định https://innovation.invietnam.vn)
"""
import collections, csv, datetime, glob, html, json, os, re as _re, shutil, urllib.parse
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
WEB = os.path.join(ROOT, "web")
REPO = "chuongnv/vietnam-innovation-ecosystem"
SITE_ROOT = os.environ.get("SITE_ROOT", "/")
SITE_URL = os.environ.get("SITE_URL", "https://innovation.invietnam.vn").rstrip("/")
TODAY = datetime.date.today().isoformat()
e = lambda s: html.escape(str(s or ""), quote=True)

def fmt_date(s):
    s = str(s or "")
    return f"{s[8:10]}/{s[5:7]}/{s[:4]}" if len(s) >= 10 and s[4] == "-" else s

TYPES = ["startup", "fund", "incubator", "accelerator", "space", "support_org", "university",
         "government", "company", "international", "community", "media", "creator"]
VER_ORDER = {"partner_verified": 0, "org_confirmed": 1, "source_checked": 2, "unverified": 3}
VER_CLASS = {"unverified": "l0", "source_checked": "l1", "org_confirmed": "l2", "partner_verified": "l3"}

# ---------- đọc dữ liệu ----------
actors, relations, events, policies, places, refs, mentions, opps, challenges = [], [], [], [], [], {}, [], [], []
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    if not os.path.isdir(region_dir):
        continue
    region = os.path.basename(region_dir)
    for path in sorted(glob.glob(os.path.join(region_dir, "actors", "*.yaml"))):
        a = yaml.safe_load(open(path, encoding="utf-8"))
        a["_file"] = os.path.relpath(path, ROOT).replace(os.sep, "/")
        actors.append(a)
    for name, bucket in (("events.yaml", events), ("policies.yaml", policies), ("places.yaml", places), ("opportunities.yaml", opps), ("challenges.yaml", challenges)):
        p = os.path.join(region_dir, name)
        if os.path.exists(p):
            for item in yaml.safe_load(open(p, encoding="utf-8")) or []:
                if name == "opportunities.yaml":
                    item["_region"] = region
                else:
                    item["region"] = region
                bucket.append(item)
    for name in ("relations.csv", "references.csv", "mentions.csv"):
        p = os.path.join(region_dir, name)
        if not os.path.exists(p):
            continue
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        if name == "relations.csv":
            relations.extend(rows)
        elif name == "references.csv":
            refs.update({r["id"]: r for r in rows})
        else:
            mentions.extend(rows)

by_id = {a["id"]: a for a in actors}
place_by_id = {p["id"]: p for p in places}
related = collections.defaultdict(set)
for r in relations:
    if r["from"] in by_id and r["to"] in by_id and r.get("type") not in ("part_of", "incubated_by"):
        related[r["from"]].add(r["to"]); related[r["to"]].add(r["from"])
mentioned = collections.defaultdict(list)
for m in mentions:
    if m["reference"] in refs:
        mentioned[m["actor"]].append(refs[m["reference"]])
events.sort(key=lambda x: str(x.get("date") or ""))
OPP_TYPES = {"call_for_applications": ("Kêu gọi hồ sơ", "Call for applications"), "competition": ("Cuộc thi", "Competition"),
             "demo_day": ("Demo day", "Demo day"), "investor_matching": ("Kết nối nhà đầu tư", "Investor matching"),
             "accelerator_program": ("Ươm tạo, tăng tốc", "Incubation, acceleration"), "buyer_matching": ("Kết nối khách hàng", "Buyer matching"),
             "pilot_program": ("Thử nghiệm, sandbox", "Pilot, sandbox")}
def opp_key_date(o):
    return o.get("deadline") or o.get("event_date") or o.get("opens") or ""
def opp_status(o):
    if o.get("deadline") and o["deadline"] >= TODAY:
        return "open"
    if o.get("opens") and not o.get("deadline") and not o.get("event_date") and o["opens"] <= TODAY:
        age = (datetime.date.fromisoformat(TODAY) - datetime.date.fromisoformat(o["opens"])).days
        return "open" if age <= 120 else "closed"
    if (o.get("event_date") or "") >= TODAY or (o.get("opens") or "") > TODAY:
        return "upcoming"
    return "closed"
def opp_missing(o):
    m = []
    if not o.get("deadline"): m.append(("hạn nộp", "deadline"))
    if not (o.get("benefits") or o.get("funding")): m.append(("quyền lợi", "benefits"))
    if not o.get("eligibility"): m.append(("đối tượng", "eligibility"))
    if not (o.get("apply_url") or o.get("primary_source")): m.append(("liên kết của đơn vị tổ chức", "organiser link"))
    if opp_status(o) == "closed" and not o.get("outcome"): m.append(("kết quả", "outcome"))
    return m
opps_by_org = collections.defaultdict(list)
for o in opps:
    for x in (o.get("organizer_ids") or []) + (o.get("participants") or []):
        opps_by_org[x].append(o)
policies.sort(key=lambda x: str(x.get("issued") or ""), reverse=True)

# ---------- khung trang ----------
NAV = [("dir", "danh-ba/", "nav_dir"),
       ("cities", "thanh-pho/", "nav_cities"), ("sectors", "linh-vuc/", "nav_sectors"), ("opps", "co-hoi/", "nav_opps"), ("policy", "chinh-sach/", "nav_policy"), ("data", "du-lieu/", "nav_data")]
CUR = ' aria-current="page"'
LEAF = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>')
LOGO = ('<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><circle cx="8" cy="9" r="4" fill="var(--sea)"/>'
        '<circle cx="22" cy="8" r="3" fill="var(--ink)"/><circle cx="15" cy="22" r="5" fill="var(--sun)"/>'
        '<path d="M8 9 22 8M8 9l7 13M22 8l-7 14" stroke="var(--ink)" stroke-width="1.5" fill="none"/></svg>')

def page(title, body, active="", desc="", scripts=(), head=""):
    nav = "".join(
        f'<a href="{SITE_ROOT}{href}" data-i18n="{key}"{CUR if k == active else ""}>{key}</a>'
        for k, href, key in NAV)
    sc = "".join(f'<script src="{SITE_ROOT}assets/{s}" defer></script>' for s in scripts)
    full_title = f"{title} | Bản đồ hệ sinh thái ĐMST Việt Nam" if title else "Bản đồ hệ sinh thái khởi nghiệp ĐMST Việt Nam"
    return f"""<!doctype html>
<html lang="vi" data-root="{SITE_ROOT}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc or 'Danh bạ mở về startup, vườn ươm, quỹ, không gian sáng tạo và chính sách khởi nghiệp đổi mới sáng tạo Việt Nam.')}">
<meta property="og:title" content="{e(full_title)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=swap">
<link rel="stylesheet" href="{SITE_ROOT}assets/style.css">
<link rel="icon" href="{SITE_ROOT}assets/favicon.svg" type="image/svg+xml">
{head}
<script src="{SITE_ROOT}assets/icons.js"></script><script src="{SITE_ROOT}assets/app.js"></script>{sc}
</head>
<body>
<a class="sr" href="#main">Bỏ qua thanh điều hướng</a>
<header class="top"><div class="wrap">
<a class="brand" href="{SITE_ROOT}">{LOGO}<span>Hệ sinh thái ĐMST</span></a>
<nav class="nav" aria-label="Chính">{nav}</nav>
<div class="tools">
<a class="btn ghost contrib" href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md" data-i18n="nav_contribute">Đóng góp</a>
<button class="btn ghost" id="lang-toggle" type="button" data-i18n="lang">English</button>
<button class="btn ghost icon" id="theme-toggle" type="button" data-i18n-label="theme" aria-label="Đổi giao diện sáng, tối"><svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 3a7 7 0 0 1 0 14z" fill="currentColor"/></svg></button>
</div></div></header>
<main id="main">{body}</main>
<footer class="foot"><div class="wrap"><p data-i18n="foot_data">Dữ liệu mở theo CC BY 4.0, mã nguồn theo MIT.</p>
<nav class="foot-nav" aria-label="Chân trang"><a href="{SITE_ROOT}gioi-thieu/" data-vi="Giới thiệu" data-en="About">Giới thiệu</a><a href="{SITE_ROOT}gioi-thieu/phuong-phap/" data-vi="Phương pháp" data-en="Methodology">Phương pháp</a><a href="{SITE_ROOT}gioi-thieu/dong-gop/" data-vi="Đóng góp" data-en="Contribute">Đóng góp</a><a href="{SITE_ROOT}du-lieu/" data-vi="Dữ liệu" data-en="Data">Dữ liệu</a><a href="https://github.com/{REPO}" data-i18n="foot_src">Mã nguồn và dữ liệu trên GitHub</a></nav></div></footer>
</body>
</html>
"""

PAGES = []   # (đường dẫn, lastmod) của các trang được lập chỉ mục
def _git_dates():
    """Ngày sửa gần nhất của từng tệp dữ liệu theo git; không có git thì trả về rỗng."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "--format=@%cs", "--name-only", "--", "data"],
                             capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return {}
    dates, cur = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            cur = line[1:]
        elif line.strip() and cur:
            dates.setdefault(line.strip(), cur)
    return dates
GIT_DATES = _git_dates()

def write(rel, content, lastmod=None):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if rel.endswith(".html") and "</head>" in content:
        url_path = "" if rel == "index.html" else rel[:-len("index.html")] if rel.endswith("index.html") else rel
        full = f"{SITE_URL}/{url_path}"
        redirect = 'http-equiv="refresh"' in content
        m = _re.search(r'<meta name="description" content="([^"]*)"', content)
        d = m.group(1) if m else ""
        t = _re.search(r"<title>(.*?)</title>", content, _re.S)
        tags = [f'<link rel="canonical" href="{full}">', f'<meta property="og:url" content="{full}">',
                '<meta property="og:site_name" content="Hệ sinh thái khởi nghiệp ĐMST Việt Nam">', '<meta property="og:locale" content="vi_VN">',
                f'<meta property="og:description" content="{d}">']
        if 'property="og:type"' not in content:
            tags.append('<meta property="og:type" content="website">')
        if 'property="og:image"' not in content:
            tags += [f'<meta property="og:image" content="{SITE_URL}/assets/og-default.png">', '<meta property="og:image:width" content="1200">',
                     '<meta property="og:image:height" content="630">', '<meta name="twitter:card" content="summary_large_image">']
        if t:
            tags.append(f'<meta name="twitter:title" content="{t.group(1).strip()}">')
        if redirect or rel == "404.html":
            tags = ['<meta name="robots" content="noindex">'] + tags[1:]
        else:
            PAGES.append((url_path, lastmod or TODAY))
        content = content.replace("</head>", "\n".join(tags) + "\n</head>", 1)
    open(path, "w", encoding="utf-8").write(content)

def ver_badge(level):
    return f'<span class="ver {VER_CLASS.get(level, "l0")}"><i aria-hidden="true"></i><span data-i18n="v_{level}">{level}</span></span>'

def type_tag(t):
    return f'<span class="tag" data-i18n="t_{t}">{t}</span>'

def dir_link(**params):
    return f"{SITE_ROOT}danh-ba/?" + urllib.parse.urlencode(params)


# ---------- lĩnh vực (tính khi dựng trang, không sửa dữ liệu gốc) ----------
import unicodedata as _ud, re as _re
def _fold(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in _ud.normalize("NFKD", s) if not _ud.combining(c)).lower()
SECTORS = [(s["id"], s["vi"], s["en"], s.get("keywords", "")) for s in yaml.safe_load(open(os.path.join(ROOT, "schema", "sectors.yaml"), encoding="utf-8"))]
LOGO_DIR = os.path.join(ROOT, "logos")
for a in actors:
    a["sectors"] = a.get("sectors") or []
    if os.path.exists(os.path.join(LOGO_DIR, a["id"] + ".webp")):
        a["logo"] = f"logos/{a['id']}.webp"


def icon_svg(k, size=18):
    P = {"incubator": '<path d="M12 21v-8"/><path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z"/><path d="M12 15c0-3-2.5-5-6-5 0 3 2.5 5 6 5z"/><path d="M7 21h10"/>',
         "fund": '<ellipse cx="9" cy="6" rx="6" ry="2.5"/><path d="M3 6v5c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5V6"/><path d="M3 11v5c0 1.4 2.7 2.5 6 2.5 1 0 2-.1 2.8-.3"/><circle cx="17" cy="16" r="4"/>',
         "company": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
         "university": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v6"/>'}
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{P.get(k, "")}</svg>'

def logo_img(a, size=40, cls="lg"):
    if a.get("logo"):
        return f'<img class="{cls}" src="{SITE_ROOT}{a["logo"]}" alt="" width="{size}" height="{size}" loading="lazy">'
    ini = "".join(w[0] for w in _re.sub(r"[^\w\s]", " ", a["name"]["vi"]).split()[:2]).upper() or "?"
    return f'<span class="{cls} ini" aria-hidden="true" style="width:{size}px;height:{size}px">{e(ini)}</span>'

# ---------- làm sạch thư mục xuất ----------
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
shutil.copytree(os.path.join(WEB, "assets"), os.path.join(OUT, "assets"))
if os.path.isdir(LOGO_DIR):
    shutil.copytree(LOGO_DIR, os.path.join(OUT, "logos"), ignore=shutil.ignore_patterns("*.md"))
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

# ---------- dữ liệu xuất bản ----------
def dump(name, obj):
    json.dump(obj, open(os.path.join(OUT, "data", name), "w", encoding="utf-8"), ensure_ascii=False)

public = [{k: v for k, v in a.items() if not k.startswith("_")} for a in actors]
dump("actors.json", public)
dump("sectors.json", [{"id": k, "vi": vi, "en": en} for k, vi, en, _ in SECTORS])
dump("relations.json", relations)
dump("opportunities.json", [{k: v for k, v in o.items() if not k.startswith("_")} | {"status": opp_status(o)} for o in opps])
dump("policies.json", policies)
dump("places.json", places)
with open(os.path.join(OUT, "data", "actors.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "name_vi", "name_en", "type", "categories", "region", "website", "longitude", "latitude", "verification", "sources"])
    for a in actors:
        c = a.get("coordinates") or ["", ""]
        w.writerow([a["id"], a["name"].get("vi", ""), a["name"].get("en", ""), a["type"], "; ".join(a.get("categories", [])),
                    a["region"], a.get("website", ""), c[0], c[1], a["verification"]["level"], "; ".join(a["sources"])])
features = []
for a in actors:
    coord, prec = a.get("coordinates"), "address"
    if not coord and a.get("place") in place_by_id and place_by_id[a["place"]].get("coordinates"):
        coord, prec = place_by_id[a["place"]]["coordinates"], "ward"
    if coord:
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": coord},
                         "properties": {"id": a["id"], "name": a["name"]["vi"], "type": a["type"],
                                        "verification": a["verification"]["level"], "precision": prec}})
dump("actors.geojson", {"type": "FeatureCollection", "features": features})
counts = collections.Counter(a["type"] for a in actors)
stats = {"actors": len(actors), "by_type": counts, "by_region": collections.Counter(a["region"] for a in actors),
         "by_verification": collections.Counter(a["verification"]["level"] for a in actors),
         "relations": len(relations), "opportunities": len(opps), "policies": len(policies), "mapped": len(features),
         "built": TODAY}
dump("stats.json", stats)

# ---------- thẻ cơ hội ----------
STATUS = {"open": ("Đang nhận hồ sơ", "Open for applications"), "upcoming": ("Sắp diễn ra", "Upcoming"), "closed": ("Đã kết thúc", "Closed")}
def opp_card(o, compact=False):
    st = opp_status(o)
    tv, te = OPP_TYPES[o["type"]]
    sv, se = STATUS[st]
    if st == "open" and not o.get("deadline"):
        sv, se = sv + " (chưa rõ hạn)", se + " (deadline unknown)"
    dates = []
    if o.get("opens"): dates.append(("Mở nhận hồ sơ", "Opens", o["opens"]))
    if o.get("deadline"): dates.append(("Hạn nộp", "Deadline", o["deadline"]))
    if o.get("event_date"): dates.append(("Ngày diễn ra", "Date", o["event_date"]))
    date_html = "".join(f'<span><span data-vi="{a}" data-en="{b}">{a}</span>: <b>{e(fmt_date(d))}</b></span>' for a, b, d in dates)
    org = e(o["organizer"])
    if o.get("organizer_ids"):
        org = ", ".join(f'<a href="{SITE_ROOT}a/{x}/">{e(by_id[x]["name"]["vi"])}</a>' for x in o["organizer_ids"] if x in by_id)
    rows = []
    if o.get("eligibility"): rows.append(("Đối tượng", "Who can apply", e(o["eligibility"])))
    if o.get("benefits") or o.get("funding"): rows.append(("Quyền lợi", "Benefits", e(" ".join(filter(None, [o.get("funding"), o.get("benefits")])))))
    if o.get("focus"): rows.append(("Lĩnh vực", "Focus", e(", ".join(o["focus"]))))
    oc = o.get("outcome") or {}
    if oc:
        parts = []
        for k, vi, en in (("applicants", "hồ sơ", "applications"), ("finalists", "vào chung kết", "finalists"), ("selected", "được chọn", "selected"),
                          ("investors", "nhà đầu tư", "investors"), ("deals", "thỏa thuận đầu tư, hợp tác", "deals")):
            if oc.get(k) is not None: parts.append(f"{oc[k]} {vi}")
        txt = "; ".join(parts) + (". " if parts else "") + (oc.get("note") or "")
        if oc.get("source"): txt = txt + f' <a href="{e(oc["source"])}" rel="noopener" class="small">nguồn</a>'
        rows.append(("Kết quả", "Outcome", txt))
    if o.get("participants"):
        ps = [x for x in o["participants"] if x in by_id]
        shown = ", ".join(f'<a href="{SITE_ROOT}a/{x}/">{e(by_id[x]["name"]["vi"])}</a>' for x in ps[:12])
        more = f' <span class="muted">+{len(ps) - 12}</span>' if len(ps) > 12 else ""
        rows.append((f"Tham gia, được chọn ({len(ps)})", f"Participants ({len(ps)})", shown + more))
    rows_html = "" if compact else "".join(f'<dt data-vi="{a}" data-en="{b}">{a}</dt><dd>{c}</dd>' for a, b, c in rows)
    links = []
    if o.get("apply_url"): links.append(f'<a class="btn primary" href="{e(o["apply_url"])}" rel="noopener" data-vi="Đăng ký" data-en="Apply">Đăng ký</a>')
    if o.get("primary_source"): links.append(f'<a class="btn ghost" href="{e(o["primary_source"])}" rel="noopener" data-vi="Trang đơn vị tổ chức" data-en="Organiser page">Trang đơn vị tổ chức</a>')
    elif o.get("secondary_sources"): links.append(f'<a class="btn ghost" href="{e(o["secondary_sources"][0])}" rel="noopener" data-vi="Bài viết liên quan" data-en="Related article">Bài viết liên quan</a>')
    miss = opp_missing(o)
    miss_html = ""
    if miss and not compact:
        mv = ", ".join(a for a, _ in miss); me = ", ".join(b for _, b in miss)
        miss_html = (f'<p class="gap small"><span data-vi="Còn thiếu: {mv}." data-en="Missing: {me}.">Còn thiếu: {mv}.</span> '
                     f'<a href="https://github.com/{REPO}/edit/main/data/{o["_region"]}/opportunities.yaml" data-vi="Bổ sung" data-en="Add it">Bổ sung</a></p>')
    return (f'<article class="opp {st}" data-type="{o["type"]}" data-status="{st}">'
            f'<p class="opp-meta"><span class="pill {st}" data-vi="{sv}" data-en="{se}">{sv}</span><span class="tag" data-vi="{tv}" data-en="{te}">{tv}</span><span class="tag" data-i18n="r_{o["_region"].replace("-", "_")}">{o["_region"]}</span></p>'
            f'<h3><a class="opp-t" href="{SITE_ROOT}co-hoi/{o["id"].removeprefix("opp-")}/">{e(o["title"])}</a></h3><p class="small muted">{org}</p><p class="opp-dates small">{date_html}</p>'
            + (f'<dl class="facts opp-facts">{rows_html}</dl>' if rows_html else "")
            + (f'<p class="opp-links">{"".join(links)}</p>' if links and not compact else "") + miss_html + '</article>')

# (trang chủ được dựng sau mục thành phố)


# ---------- danh bạ ----------
static_rows = "".join(
    f'<li><a href="{SITE_ROOT}a/{a["id"]}/"><span class="nm">{e(a["name"]["vi"])}</span>'
    f'{type_tag(a["type"])}{ver_badge(a["verification"]["level"])}</a></li>'
    for a in sorted(actors, key=lambda x: x["name"]["vi"].lower()))
dir_body = f"""
<div class="wrap page-head dir-head"><h1 data-i18n="nav_dir">Danh bạ</h1>
<p class="lead" data-vi="{len(actors)} tổ chức, startup, quỹ, trường và cơ quan trong hệ sinh thái. Gõ để tìm, chọn biểu tượng để lọc; đường dẫn giữ nguyên bộ lọc để gửi cho người khác." data-en="{len(actors)} organisations, startups, funds, universities and agencies. Type to search, tap an icon to filter; the link keeps your filters.">{len(actors)} tổ chức, startup, quỹ, trường và cơ quan trong hệ sinh thái.</p>
<div class="bigsearch" role="search"><span class="bs-ico" id="bs-ico"></span>
<label class="sr" for="q" data-i18n="search_ph">Tìm</label>
<input id="q" type="search" autocomplete="off" data-i18n-ph="search_ph2" placeholder="Tìm theo tên, lĩnh vực, mô tả…" aria-controls="sugg" aria-expanded="false">
<ul id="sugg" class="sugg" role="listbox" hidden></ul></div></div>
<div class="wrap">
<div class="chiprow" id="c-type" role="group" aria-label="Loại tác nhân"></div>
<div class="chiprow sm" id="c-sector" role="group" aria-label="Lĩnh vực"></div>
<div class="dir-tools">
<button type="button" class="btn ghost" id="more" aria-expanded="false" aria-controls="morepanel"><span id="more-ico"></span> <span data-vi="Bộ lọc khác" data-en="More filters">Bộ lọc khác</span> <span class="badge" id="more-n" hidden></span></button>
<div class="pills" id="pills"></div>
<span class="spacer"></span>
<label class="sr" for="sort">Sắp xếp</label>
<select id="sort"><option value="rich" data-vi="Thông tin đầy đủ trước" data-en="Most complete first">Thông tin đầy đủ trước</option><option value="az" data-i18n="sort_az">Tên A–Z</option><option value="ver" data-i18n="sort_ver">Đã xác minh trước</option></select>
<div class="seg" role="group" aria-label="Kiểu hiển thị"><button type="button" id="v-cards" aria-pressed="true" data-i18n="view_cards">Thẻ</button><button type="button" id="v-list" aria-pressed="false" data-i18n="view_list">Danh sách</button><button type="button" id="v-map" aria-pressed="false" data-vi="Bản đồ" data-en="Map">Bản đồ</button></div>
<button type="button" class="btn ghost" id="csv" title="Tải CSV theo bộ lọc hiện tại"><span data-vi="Tải CSV" data-en="Download CSV">Tải CSV</span></button>
</div>
<div class="morepanel" id="morepanel" hidden>
<fieldset id="f-region"><legend data-i18n="f_region">Khu vực</legend></fieldset>
<fieldset id="f-status"><legend data-i18n="f_status">Tình trạng</legend></fieldset>
<fieldset id="f-ver"><legend data-i18n="f_ver">Mức xác minh</legend></fieldset>
<fieldset id="f-has"><legend data-vi="Có thông tin" data-en="Has">Có thông tin</legend></fieldset>
<button class="btn ghost" id="clear" type="button" data-i18n="f_clear">Xoá bộ lọc</button>
</div>
<p class="count" id="count" aria-live="polite"></p>
<div id="mapwrap" hidden><div id="mapbox" class="mapbox"></div><p class="small muted" id="mapnote" style="margin-top:8px"></p></div>
<div id="results"><ul class="rows">{static_rows}</ul></div>
<nav class="pager" id="pager" aria-label="Phân trang"></nav>
</div>
"""
write("danh-ba/index.html", page("Danh bạ", dir_body, "dir", scripts=["map.js", "directory.js"], head=LEAF, desc=f"Danh bạ {len(actors)} startup, quỹ đầu tư, vườn ươm, trường, cơ quan trong hệ sinh thái khởi nghiệp Việt Nam. Lọc theo loại, lĩnh vực, địa phương; xem bản đồ; tải CSV miễn phí."))

# ---------- trang từng tác nhân ----------
VIE_TYPE = {"startup": "Startup", "fund": "Quỹ đầu tư", "incubator": "Vườn ươm", "accelerator": "Chương trình tăng tốc", "space": "Không gian đổi mới sáng tạo", "support_org": "Tổ chức hỗ trợ khởi nghiệp", "university": "Trường, viện", "government": "Cơ quan nhà nước", "company": "Doanh nghiệp", "international": "Đối tác quốc tế", "community": "Cộng đồng", "media": "Truyền thông", "creator": "Dự án sáng tạo"}
REGION_VI = {"da-nang": "Đà Nẵng", "former-quang-nam": "Khu vực Quảng Nam cũ", "ha-noi": "Hà Nội", "ho-chi-minh": "TP. Hồ Chí Minh",
             "hai-phong": "Hải Phòng", "viet-nam": "Việt Nam", "quoc-te": "Quốc tế"}
SECT_VI = {k: vi for k, vi, _, _ in SECTORS}
def richness(x):
    return (2 if x.get("logo") else 0) + (2 if (x.get("description") or {}).get("vi") else 0) + (1 if x.get("website") else 0) - (5 if x.get("status") == "inactive" else 0)
by_sector = collections.defaultdict(list)
by_region_type = collections.defaultdict(list)
for x in actors:
    for s in x.get("sectors") or []:
        by_sector[s].append(x)
    by_region_type[(x["region"], x["type"])].append(x)
def similar(a, pool, n=6, exclude=()):
    seen = {a["id"], *exclude}
    out = []
    ranked = sorted(pool, key=lambda x: (-(x["region"] == a["region"]), -richness(x), x["name"]["vi"].lower()))
    for x in ranked:
        if x["id"] not in seen:
            seen.add(x["id"]); out.append(x)
        if len(out) >= n - 2: break
    # thêm hàng xóm theo thứ tự tên để hồ sơ ít thông tin cũng được liên kết tới
    alpha = sorted(pool, key=lambda x: x["name"]["vi"].lower())
    i = next((k for k, x in enumerate(alpha) if x["id"] == a["id"]), 0)
    for x in alpha[i + 1:] + alpha[:i]:
        if len(out) >= n: break
        if x["id"] not in seen:
            seen.add(x["id"]); out.append(x)
    return out
def mini_cards(xs):
    return '<div class="fsgrid">' + "".join(
        f'<a class="fs" href="{SITE_ROOT}a/{x["id"]}/">{logo_img(x, 44)}<span class="nm">{e(x["name"]["vi"])}</span>'
        f'<span class="muted small" data-i18n="t_{x["type"]}">{x["type"]}</span></a>' for x in xs) + "</div>"

issue_base = f"https://github.com/{REPO}/issues/new?"
for a in actors:
    aid, name = a["id"], a["name"]["vi"]
    facts = []
    if a.get("categories"):
        facts.append(("Lĩnh vực, phân loại", "Categories", e("; ".join(a["categories"]))))
    facts.append(("Khu vực", "Area", f'<span data-i18n="r_{a["region"].replace("-", "_")}">{e(a["region"])}</span>'))
    if a.get("place") in place_by_id:
        facts.append(("Phường, xã", "Ward", e(place_by_id[a["place"]]["name"])))
    if a.get("address"):
        facts.append(("Địa chỉ", "Address", e(a["address"])))
    if a.get("website"):
        facts.append(("Website", "Website", f'<a href="{e(a["website"])}" rel="noopener">{e(a["website"])}</a>'))
    if a.get("linkedin"):
        facts.append(("LinkedIn", "LinkedIn", f'<a href="{e(a["linkedin"])}" rel="noopener">{e(a["linkedin"])}</a>'))
    if a.get("founded"):
        facts.append(("Năm thành lập", "Founded", e(a["founded"])))
    if a.get("status") in ("active", "inactive"):
        sv = {"active": ("Đang hoạt động", "Active"), "inactive": ("Đã ngừng hoạt động", "No longer active")}[a["status"]]
        facts.append(("Tình trạng", "Status", f'<span data-vi="{sv[0]}" data-en="{sv[1]}">{sv[0]}</span>'))
    if a.get("contact_email"):
        facts.append(("Email", "Email", f'<a href="mailto:{e(a["contact_email"])}">{e(a["contact_email"])}</a>'))
    if a.get("contact_phone"):
        facts.append(("Điện thoại", "Phone", e(a["contact_phone"])))
    facts_html = "".join(f'<dt data-vi="{vi}" data-en="{en}">{vi}</dt><dd>{val}</dd>' for vi, en, val in facts)
    desc = a.get("description", {})
    desc_html = (f'<p class="desc" data-vi="{e(desc.get("vi"))}" data-en="{e(desc.get("en") or desc.get("vi"))}">{e(desc.get("vi"))}</p>'
                 if desc.get("vi") else
                 '<p class="desc muted" data-vi="Hồ sơ này chưa có mô tả. Bạn biết về tổ chức này? Đề xuất một đoạn mô tả ngắn." data-en="No description yet. Know this organisation? Suggest a short description.">Hồ sơ này chưa có mô tả.</p>')
    rel_html = ""
    if a.get("alt_names"):
        facts.append(("Tên khác", "Other names", e("; ".join(a["alt_names"]))))
        facts_html = "".join(f'<dt data-vi="{vi}" data-en="{en}">{vi}</dt><dd>{val}</dd>' for vi, en, val in facts)
    if related.get(aid):
        items = "".join(f'<li><a href="{SITE_ROOT}a/{r}/">{e(by_id[r]["name"]["vi"])}</a> {type_tag(by_id[r]["type"])}</li>'
                        for r in sorted(related[aid]))
        rel_html = f'<div class="section"><h2 data-vi="Liên quan" data-en="Related">Liên quan</h2><ul class="list-plain">{items}</ul></div>'
    men = sorted(mentioned.get(aid, []), key=lambda r: r.get("date") or "", reverse=True)[:12]
    men_html = ""
    if men:
        items = "".join(
            f'<li><span class="date">{e(fmt_date(r.get("date")))}</span> '
            + (f'<a href="{e(r["url"])}" rel="noopener">{e(r["title"])}</a>' if r.get("url") else e(r["title"]))
            + f' <span class="muted small">{e(r.get("source"))}</span></li>' for r in men)
        men_html = f'<div class="section"><h2 data-vi="Được nhắc tới trong" data-en="Mentioned in">Được nhắc tới trong</h2><ul class="list-plain">{items}</ul></div>'
    org_opps = opps_by_org.get(aid, [])
    opp_html = ""
    if org_opps:
        opp_html = ('<div class="section"><h2 data-vi="Cơ hội liên quan" data-en="Related opportunities">Cơ hội liên quan</h2><div class="opp-list" style="margin-top:12px">'
                    + "".join(opp_card(o, compact=True) for o in sorted(org_opps, key=opp_key_date, reverse=True)) + "</div></div>")
    parents = [r["to"] for r in relations if r["from"] == aid and r.get("type") == "part_of" and r["to"] in by_id]
    children = [r["from"] for r in relations if r["to"] == aid and r.get("type") == "part_of" and r["from"] in by_id]
    lvl = a["verification"]["level"]
    incubators = [r["to"] for r in relations if r["from"] == aid and r.get("type") == "incubated_by" and r["to"] in by_id]
    alumni = sorted({r["from"] for r in relations if r["to"] == aid and r.get("type") == "incubated_by" and r["from"] in by_id}, key=lambda x: by_id[x]["name"]["vi"].lower())
    if incubators:
        items = "".join(f'<li><a href="{SITE_ROOT}a/{x}/">{e(by_id[x]["name"]["vi"])}</a> {type_tag(by_id[x]["type"])}</li>' for x in dict.fromkeys(incubators))
        rel_html = f'<div class="section"><h2 data-vi="Được ươm tạo, hỗ trợ bởi" data-en="Supported by">Được ươm tạo, hỗ trợ bởi</h2><ul class="list-plain">{items}</ul></div>' + rel_html
    if alumni:
        act = [x for x in alumni if by_id[x].get("status") != "inactive"]
        ina = [x for x in alumni if by_id[x].get("status") == "inactive"]
        items = "".join(f'<li><a href="{SITE_ROOT}a/{x}/">{e(by_id[x]["name"]["vi"])}</a></li>' for x in act)
        items += "".join(f'<li><a href="{SITE_ROOT}a/{x}/">{e(by_id[x]["name"]["vi"])}</a> <span class="muted small" data-vi="(đã ngừng hoạt động)" data-en="(no longer active)">(đã ngừng hoạt động)</span></li>' for x in ina)
        rel_html += (f'<div class="section"><h2 data-vi="Startup đã ươm tạo, hỗ trợ ({len(alumni)})" data-en="Startups supported ({len(alumni)})">Startup đã ươm tạo, hỗ trợ ({len(alumni)})</h2>'
                     f'<ul class="list-plain alumni">{items}</ul></div>')
    if parents or children:
        items = "".join(f'<li><span class="muted small" data-vi="Thuộc" data-en="Part of">Thuộc</span> <a href="{SITE_ROOT}a/{p_}/">{e(by_id[p_]["name"]["vi"])}</a></li>' for p_ in parents)
        items += "".join(f'<li><a href="{SITE_ROOT}a/{c_}/">{e(by_id[c_]["name"]["vi"])}</a> {type_tag(by_id[c_]["type"])}</li>' for c_ in sorted(children))
        rel_html = f'<div class="section"><h2 data-vi="Đơn vị liên quan" data-en="Related units">Đơn vị liên quan</h2><ul class="list-plain">{items}</ul></div>' + rel_html
    vdate = a["verification"].get("date")
    src = "; ".join(a["sources"])
    src_html = e(src) + (f'<br><a href="{e(a["source_url"])}" rel="noopener" class="small">{e(a["source_url"])}</a>' if a.get("source_url") else "")
    issue_q = urllib.parse.urlencode({"template": "them-hoac-sua-ho-so.yml", "title": f"[Hồ sơ] {name}",
                                      "name": name, "website": a.get("website", ""), "region": REGION_VI.get(a["region"], "")})
    linked = set(related.get(aid, [])) | {r["to"] for r in relations if r["from"] == aid} | {r["from"] for r in relations if r["to"] == aid}
    sim_html = ""
    sec0 = (a.get("sectors") or [None])[0]
    if sec0:
        xs = similar(a, by_sector[sec0], exclude=linked)
        if xs:
            sim_html += (f'<div class="section"><h2 data-vi="Cùng lĩnh vực: {e(SECT_VI.get(sec0, sec0))}" data-en="Same sector">Cùng lĩnh vực: {e(SECT_VI.get(sec0, sec0))}</h2>'
                         f'{mini_cards(xs)}<p class="small" style="margin-top:10px"><a href="{dir_link(sector=sec0)}" data-vi="Xem tất cả" data-en="See all">Xem tất cả</a></p></div>')
            linked |= {x["id"] for x in xs}
    xs = similar(a, by_region_type[(a["region"], a["type"])], exclude=linked)
    if xs:
        rv = REGION_VI.get(a["region"], a["region"])
        sim_html += (f'<div class="section"><h2 data-vi="Cùng địa phương: {e(rv)}" data-en="Same area: {e(rv)}">Cùng địa phương: {e(rv)}</h2>'
                     f'{mini_cards(xs)}<p class="small" style="margin-top:10px"><a href="{dir_link(type=a["type"], region=a["region"])}" data-vi="Xem tất cả" data-en="See all">Xem tất cả</a></p></div>')
    ld = {"@context": "https://schema.org", "@type": "EducationalOrganization" if a["type"] == "university" else "GovernmentOrganization" if a["type"] == "government" else "Organization",
          "name": name, "url": f"{SITE_URL}/a/{aid}/"}
    if (a.get("description") or {}).get("vi"): ld["description"] = a["description"]["vi"]
    if a.get("logo"): ld["logo"] = f"{SITE_URL}/{a['logo']}"
    same = [u for u in (a.get("website"), a.get("linkedin")) if u]
    if same: ld["sameAs"] = same
    if a.get("founded"): ld["foundingDate"] = str(a["founded"])
    if a.get("alt_names"): ld["alternateName"] = a["alt_names"][:5]
    if a["region"] not in ("viet-nam", "quoc-te"):
        ld["address"] = {"@type": "PostalAddress", "addressRegion": REGION_VI.get(a["region"], ""), "addressCountry": "VN"}
    if a.get("sectors"): ld["knowsAbout"] = [SECT_VI[s] for s in a["sectors"] if s in SECT_VI]
    a_head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    a_head += '<meta property="og:type" content="profile">'
    a_last = GIT_DATES.get(a["_file"], TODAY)
    body = f"""
<div class="wrap crumbs"><a href="{SITE_ROOT}danh-ba/" data-i18n="nav_dir">Danh bạ</a> / <a href="{dir_link(type=a['type'])}" data-i18n="t_{a['type']}">{a['type']}</a></div>
<div class="wrap actor">
<article>
<p>{type_tag(a["type"])}</p>
{logo_img(a, 72, "lg alogo")}<h1 style="margin-top:8px">{e(name)}</h1>
{f'<p class="muted" style="margin-top:6px">{e(a["name"]["en"])}</p>' if a["name"].get("en") else ""}
{desc_html}
<dl class="facts">{facts_html}</dl>
{rel_html}{opp_html}{sim_html}{men_html}
</article>
<aside class="side">
<div class="box"><h2 data-vi="Độ tin cậy" data-en="Reliability">Độ tin cậy</h2>
<p>{ver_badge(lvl)}{f' <span class="muted small">{e(vdate)}</span>' if vdate else ""}</p>
<p class="small muted" style="margin-top:10px" data-vi="Nguồn: {e(src)}" data-en="Source: {e(src)}">Nguồn: {e(src)}</p>
{f'<p class="small" style="margin-top:6px"><a href="{e(a["source_url"])}" rel="noopener" data-vi="Xem nguồn" data-en="View source">Xem nguồn</a></p>' if a.get("source_url") else ""}
</div>
<div class="box"><h2 data-vi="Thông tin chưa đúng?" data-en="Something wrong?">Thông tin chưa đúng?</h2>
<p class="small muted" data-vi="Gửi đề xuất qua biểu mẫu, hoặc sửa thẳng tệp dữ liệu trên GitHub." data-en="Send a suggestion through the form, or edit the data file on GitHub.">Gửi đề xuất qua biểu mẫu, hoặc sửa thẳng tệp dữ liệu trên GitHub.</p>
<p style="margin-top:14px;display:flex;flex-direction:column;gap:8px">
<a class="btn primary" href="{issue_base}{issue_q}" data-vi="Đề xuất sửa" data-en="Suggest an edit">Đề xuất sửa</a>
<a class="btn ghost" href="https://github.com/{REPO}/edit/main/{a['_file']}" data-vi="Sửa trên GitHub" data-en="Edit on GitHub">Sửa trên GitHub</a></p>
</div>
</aside></div>
"""
    auto_desc = f"{name}: {VIE_TYPE.get(a['type'], a['type']).lower()} tại {REGION_VI.get(a['region'], 'Việt Nam')}" + (f", lĩnh vực {', '.join(SECT_VI[s].lower() for s in a['sectors'] if s in SECT_VI)}" if a.get("sectors") else "") + ". Hồ sơ trong danh bạ mở hệ sinh thái khởi nghiệp Việt Nam."
    write(f"a/{aid}/index.html", page(name, body, "dir", desc=((desc.get("vi") + " " + auto_desc) if desc.get("vi") and len(desc["vi"]) < 70 else (desc.get("vi") or auto_desc))[:300], head=a_head), lastmod=a_last)

# ---------- bản đồ ----------
leaf = ('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" defer></script>')
map_body = f"""
<div class="wrap page-head"><h1 data-i18n="nav_map">Bản đồ</h1>
<p class="lead" id="map-note"></p></div>
<div class="wrap mapwrap">
<div id="map" role="region" aria-label="Bản đồ các tổ chức"></div>
<aside><div class="box"><h2 data-vi="Giúp bản đồ đầy đủ hơn" data-en="Help complete the map">Giúp bản đồ đầy đủ hơn</h2>
<p class="small muted" data-i18n="map_help"></p>
<p style="margin-top:14px"><a class="btn primary" href="https://github.com/{REPO}/blob/main/docs/data-model.md" data-vi="Cách thêm tọa độ" data-en="How to add coordinates">Cách thêm tọa độ</a></p></div>
<h2 style="font-size:1.1rem;margin:24px 0 8px" data-vi="Đang hiện trên bản đồ" data-en="On the map">Đang hiện trên bản đồ</h2>
<p class="legend"><span><i style="background:var(--sea)"></i><span data-i18n="by_addr">Vị trí theo địa chỉ</span></span><span><i style="background:var(--sun)"></i><span data-i18n="by_ward">Vị trí theo phường, xã</span></span></p>
<ul class="maplist" id="map-list" style="margin-top:12px"></ul></aside>
</div>
"""
write("ban-do/index.html", page("Bản đồ", f'<div class="wrap page-head"><h1>Bản đồ đã chuyển</h1><p class="lead">Bản đồ nay nằm trong <a href="{SITE_ROOT}danh-ba/?view=map">Danh bạ</a> và trang từng thành phố.</p></div>', head=f'<meta http-equiv="refresh" content="0; url={SITE_ROOT}danh-ba/?view=map">'))

# ---------- cơ hội ----------
groups = [("open", "Đang nhận hồ sơ", "Open for applications"), ("upcoming", "Sắp diễn ra", "Upcoming"), ("closed", "Đã kết thúc", "Closed")]
blocks = ""
for key, vi, en in groups:
    items = [o for o in opps if opp_status(o) == key]
    items.sort(key=opp_key_date, reverse=(key == "closed"))
    empty = {"open": ("Chưa có cơ hội nào đang mở trong danh sách. Biết một chương trình đang nhận hồ sơ? Thêm vào để mọi người cùng thấy.",
                      "Nothing open in the list yet. Know a programme taking applications? Add it so others can see it."),
             "upcoming": ("Chưa có cơ hội sắp diễn ra trong danh sách.", "No upcoming opportunities listed yet.")}.get(key)
    body_items = "".join(opp_card(o) for o in items) or (f'<p class="muted" data-vi="{empty[0]}" data-en="{empty[1]}">{empty[0]}</p>' if empty else "")
    blocks += f'<section class="opp-group" data-group="{key}"><h2 data-vi="{vi}" data-en="{en}">{vi} <span class="muted">({len(items)})</span></h2><div class="opp-list">{body_items}</div></section>'
ch_html = ""
if challenges:
    ch_html = ('<section class="opp-group"><h2 data-vi="Bài toán thành phố đang cần giải pháp" data-en="Problems the city needs solved">Bài toán thành phố đang cần giải pháp</h2>'
               '<p class="muted" style="margin-top:10px" data-vi="Không phải kêu gọi hồ sơ, mà là các hướng có nhu cầu thật để startup cân nhắc." data-en="Not calls for applications, but areas of real demand for startups to consider.">Không phải kêu gọi hồ sơ, mà là các hướng có nhu cầu thật để startup cân nhắc.</p>'
               '<div class="cards" style="margin-top:16px">' + "".join(
                   f'<article class="card"><p class="nm" data-vi="{e(c["title"]["vi"])}" data-en="{e(c["title"].get("en") or c["title"]["vi"])}">{e(c["title"]["vi"])}</p>'
                   f'<p class="small muted" data-vi="{e(c["summary"]["vi"])}" data-en="{e(c["summary"].get("en") or c["summary"]["vi"])}">{e(c["summary"]["vi"])}</p></article>' for c in challenges) + '</div></section>')
type_opts = "".join(f'<option value="{k}" data-vi="{v[0]}" data-en="{v[1]}">{v[0]}</option>' for k, v in OPP_TYPES.items())
opp_script = """<script>document.addEventListener('DOMContentLoaded',function(){var s=document.getElementById('otype');
s.addEventListener('change',function(){var v=s.value;document.querySelectorAll('.opp').forEach(function(a){a.hidden=v&&a.getAttribute('data-type')!==v});});});</script>"""
write("co-hoi/index.html", page("Cơ hội", f"""
<div class="wrap page-head"><h1 data-vi="Cơ hội" data-en="Opportunities">Cơ hội</h1>
<p class="lead" data-vi="Kêu gọi hồ sơ, cuộc thi, demo day, kết nối nhà đầu tư và khách hàng, chương trình ươm tạo và thử nghiệm: những hoạt động có thể dẫn tới vốn, khách hàng hoặc hợp đồng. Hội thảo và tin ký kết không nằm ở đây." data-en="Calls for applications, competitions, demo days, investor and buyer matching, incubation and pilot programmes: activities that can lead to funding, customers or contracts. Conferences and signing news are not listed here.">Kêu gọi hồ sơ, cuộc thi, demo day, kết nối nhà đầu tư và khách hàng, chương trình ươm tạo và thử nghiệm.</p>
<div class="bar" style="margin-top:20px"><label for="otype" data-vi="Loại cơ hội" data-en="Type">Loại cơ hội</label>
<select id="otype"><option value="" data-vi="Tất cả" data-en="All">Tất cả</option>{type_opts}</select>
<a class="btn primary" href="https://github.com/{REPO}/edit/main/data/da-nang/opportunities.yaml" data-vi="Thêm cơ hội" data-en="Add an opportunity">Thêm cơ hội</a></div></div>
<div class="wrap" style="padding-bottom:72px">{blocks}{ch_html}</div>{opp_script}""", "opps", desc=f"{len(opps)} cơ hội gọi vốn, cuộc thi, demo day, chương trình ươm tạo và kết nối khách hàng cho startup Việt Nam, kèm hạn nộp, quyền lợi và kết quả."))
write("su-kien/index.html", page("Cơ hội", f'<div class="wrap page-head"><h1>Trang đã chuyển</h1><p class="lead">Mục sự kiện nay là <a href="{SITE_ROOT}co-hoi/">Cơ hội</a>.</p></div>', head=f'<meta http-equiv="refresh" content="0; url={SITE_ROOT}co-hoi/">'))


# ---------- thành phố ----------
BENCH = {}
_bp = os.path.join(ROOT, "data", "benchmarks", "startupblink-2026.yaml")
if os.path.exists(_bp):
    BENCH = yaml.safe_load(open(_bp, encoding="utf-8"))
CITY_REGIONS = {"ho-chi-minh": ["ho-chi-minh"], "ha-noi": ["ha-noi"], "da-nang": ["da-nang", "former-quang-nam"], "hai-phong": ["hai-phong"]}

def money(v):
    if v is None: return "–"
    v = float(v)
    if v >= 1e9: return f"{v/1e9:.2f} tỷ USD".replace(".", ",")
    if v >= 1e6: return f"{v/1e6:.1f} triệu USD".replace(".", ",")
    return f"{int(v):,} USD".replace(",", ".")

def chg(v):
    if v is None: return '<span class="muted small">mới</span>'
    if v == 0: return '<span class="muted small">giữ nguyên</span>'
    return f'<span class="up small">{"+" if v > 0 else ""}{v}</span>'

def kpi(label_vi, label_en, value, note=""):
    return (f'<div class="kpi"><p class="kv">{value}</p><p class="kl" data-vi="{label_vi}" data-en="{label_en}">{label_vi}</p>'
            + (f'<p class="kn small muted">{note}</p>' if note else "") + "</div>")

def city_table(active=None):
    rows = ""
    for c in BENCH.get("cities", []):
        cur = ' class="cur"' if c["id"] == active else ""
        rows += (f'<tr{cur}><td>{c["national_rank"]}</td><td><a href="{SITE_ROOT}thanh-pho/{c["id"]}/">{e(c["name"])}</a></td>'
                 f'<td>#{c["global_rank"]} {chg(c.get("rank_change"))}</td><td>#{c.get("regional_rank","–")}</td>'
                 f'<td>{c["total_score"]:.3f}'.replace(".", ",") + f'</td><td>{str(c["national_share"]).replace(".", ",")}%</td>'
                 f'<td>{sum(1 for a in actors if a["region"] in CITY_REGIONS.get(c["id"], [c["id"]]))}</td></tr>')
    return ('<div class="tbl-wrap"><table class="tbl"><thead><tr><th data-vi="Hạng QG" data-en="National">Hạng QG</th><th data-vi="Thành phố" data-en="City">Thành phố</th>'
            '<th data-vi="Hạng thế giới" data-en="Global rank">Hạng thế giới</th><th data-vi="Hạng Đông Nam Á" data-en="SEA rank">Hạng Đông Nam Á</th>'
            '<th data-vi="Điểm" data-en="Score">Điểm</th><th data-vi="Tỷ trọng QG" data-en="National share">Tỷ trọng QG</th>'
            '<th data-vi="Tác nhân trong danh bạ" data-en="Actors in this directory">Tác nhân trong danh bạ</th></tr></thead><tbody>' + rows + '</tbody></table></div>')

def ind_table(inds):
    if not inds: return '<p class="muted">Chưa có dữ liệu.</p>'
    rows = "".join(f'<tr><td>{e(i["name"])}</td><td>#{i["rank"]}</td><td>{i["startups"]}</td></tr>' for i in inds)
    return ('<div class="tbl-wrap"><table class="tbl"><thead><tr><th data-vi="Ngành" data-en="Industry">Ngành</th><th data-vi="Hạng thế giới" data-en="Global rank">Hạng thế giới</th>'
            '<th data-vi="Số startup" data-en="Startups">Số startup</th></tr></thead><tbody>' + rows + '</tbody></table></div>')

SB_NOTE = ('<p class="small muted src-note" data-vi="Số liệu xếp hạng, startup, vốn và ngành: StartupBlink, Global Startup Ecosystem Index 2026 (trang công khai, truy cập 21/11/2026). Số tác nhân, cơ hội: danh bạ mở này." '
           'data-en="Rankings, startups, funding and industries: StartupBlink Global Startup Ecosystem Index 2026 (public pages, accessed 21 Nov 2026). Actors and opportunities: this open directory.">'
           'Số liệu xếp hạng, startup, vốn và ngành: StartupBlink, Global Startup Ecosystem Index 2026 (trang công khai, truy cập 21/11/2026). Số tác nhân, cơ hội: danh bạ mở này.</p>')

if BENCH:
    co = BENCH["country"]
    kp = "".join([kpi("Hạng thế giới", "Global rank", f'#{co["global_rank"]} {chg(co["rank_change"])}'),
                  kpi("Hạng Đông Nam Á", "SEA rank", f'#{co["regional_rank"]}'),
                  kpi("Startup (StartupBlink)", "Startups (StartupBlink)", f'{co["startups"]:,}'.replace(",", ".")),
                  kpi("Giá trị hệ sinh thái", "Ecosystem value", money(co["ecosystem_value_usd"])),
                  kpi("Vốn đầu tư 2017–2025", "Funding 2017–2025", money(co["funding_2017_2025_usd"])),
                  kpi("Vốn năm 2025", "Funding 2025", money(co["funding_2025_usd"]), f'{co["deals_2025"]} thương vụ'),
                  kpi("Tác nhân trong danh bạ", "Actors in this directory", f'{len(actors)}'),
                  kpi("Cơ hội đang theo dõi", "Opportunities tracked", f'{len(opps)}')])
    write("thanh-pho/index.html", page("Thành phố", f"""
<div class="wrap page-head"><p class="crumb small"><span data-vi="Việt Nam" data-en="Vietnam">Việt Nam</span></p>
<h1 data-vi="Hệ sinh thái khởi nghiệp Việt Nam theo thành phố" data-en="Vietnam's startup ecosystem by city">Hệ sinh thái khởi nghiệp Việt Nam theo thành phố</h1>
<p class="lead" data-vi="Tổng quan quốc gia, bảng xếp hạng các thành phố và trang riêng cho từng thành phố." data-en="Country overview, city ranking and a page for each city.">Tổng quan quốc gia, bảng xếp hạng các thành phố và trang riêng cho từng thành phố.</p></div>
<div class="wrap" style="padding-bottom:72px">
<nav class="onpage small"><a href="#tong-quan" data-vi="Tổng quan" data-en="Overview">Tổng quan</a><a href="#thanh-pho" data-vi="Các thành phố" data-en="Cities">Các thành phố</a><a href="#nganh" data-vi="Ngành" data-en="Industries">Ngành</a></nav>
<section id="tong-quan" class="sec"><h2 data-vi="Tổng quan" data-en="Overview">Tổng quan</h2><div class="kpis">{kp}</div></section>
<section id="thanh-pho" class="sec"><h2 data-vi="Các thành phố khởi nghiệp hàng đầu" data-en="Top startup cities">Các thành phố khởi nghiệp hàng đầu</h2>{city_table()}</section>
<section id="nganh" class="sec"><h2 data-vi="Ngành nổi bật của Việt Nam" data-en="Vietnam's top industries">Ngành nổi bật của Việt Nam</h2>{ind_table(co.get("industries"))}</section>
{SB_NOTE}</div>""", "cities", desc="Hệ sinh thái khởi nghiệp Việt Nam theo thành phố: xếp hạng, số startup, vốn đầu tư và ngành nổi bật của TP.HCM, Hà Nội, Đà Nẵng, Hải Phòng."))

    for c in BENCH["cities"]:
        regs = CITY_REGIONS.get(c["id"], [c["id"]])
        acts = [a for a in actors if a["region"] in regs]
        tc = collections.Counter(a["type"] for a in acts)
        kp = [kpi("Hạng trong nước", "National rank", f'#{c["national_rank"]}'),
              kpi("Hạng thế giới", "Global rank", f'#{c["global_rank"]} {chg(c.get("rank_change"))}'),
              kpi("Hạng Đông Nam Á", "SEA rank", f'#{c.get("regional_rank","–")} {chg(c.get("regional_change")) if "regional_change" in c else ""}'),
              kpi("Startup (StartupBlink)", "Startups (StartupBlink)", f'{c["startups"]}'),
              kpi("Giá trị hệ sinh thái", "Ecosystem value", money(c["ecosystem_value_usd"])),
              kpi("Vốn đầu tư 2017–2025", "Funding 2017–2025", money(c.get("funding_2017_2025_usd")))]
        if c.get("funding_2025_usd") is not None:
            kp.append(kpi("Vốn năm 2025", "Funding 2025", money(c["funding_2025_usd"]), f'{c.get("deals_2025", 0)} thương vụ'))
        if c.get("coworking_spaces") or c.get("accelerators"):
            kp.append(kpi("Không gian làm việc chung, tăng tốc", "Coworking, accelerators", f'{c.get("coworking_spaces","–")} / {c.get("accelerators","–")}'))
        ours = [kpi("Tác nhân trong danh bạ", "Actors here", str(len(acts))), kpi("Startup", "Startups", str(tc["startup"])),
                kpi("Quỹ, nhà đầu tư", "Funds, investors", str(tc["fund"])),
                kpi("Tổ chức hỗ trợ, vườn ươm", "Support orgs, incubators", str(tc["support_org"] + tc["incubator"] + tc["accelerator"] + tc["space"])),
                kpi("Trường, viện", "Universities", str(tc["university"])), kpi("Cơ quan nhà nước", "Government", str(tc["government"]))]
        def lst(t, n=24):
            xs = sorted([a for a in acts if a["type"] == t], key=lambda a: (not a.get("logo"), not a.get("description"), VER_ORDER.get(a["verification"]["level"], 9), a["name"]["vi"].lower()))
            if not xs: return '<p class="muted small" data-vi="Chưa có trong danh bạ." data-en="None listed yet.">Chưa có trong danh bạ.</p>'
            items = "".join(f'<li><a href="{SITE_ROOT}a/{a["id"]}/">{logo_img(a, 22)}{e(a["name"]["vi"])}</a></li>' for a in xs[:n])
            more = f'<p class="small"><a href="{dir_link(type=t, region=",".join(regs))}" data-vi="Xem tất cả {len(xs)}" data-en="See all {len(xs)}">Xem tất cả {len(xs)}</a></p>' if len(xs) > n else ""
            return f'<ul class="list-plain alumni">{items}</ul>{more}'
        copps = sorted([o for o in opps if o["_region"] in regs], key=lambda o: opp_key_date(o), reverse=True)
        opp_html = "".join(opp_card(o, compact=True) for o in copps[:6]) or '<p class="muted small" data-vi="Chưa có cơ hội nào." data-en="No opportunities yet.">Chưa có cơ hội nào.</p>'
        corp = ", ".join(e(x) for x in c.get("corporations") or []) or "–"
        body = f"""
<div class="wrap page-head"><p class="crumb small"><a href="{SITE_ROOT}thanh-pho/" data-vi="Việt Nam" data-en="Vietnam">Việt Nam</a> / {e(c["name"])}</p>
<h1>{e(c["name"])}</h1>
<p class="lead" data-vi="Hệ sinh thái khởi nghiệp {e(c['name'])}: xếp hạng, ngành, vốn, danh bạ tác nhân và cơ hội." data-en="The {e(c['name'])} startup ecosystem: ranking, industries, funding, actors and opportunities.">Hệ sinh thái khởi nghiệp {e(c["name"])}: xếp hạng, ngành, vốn, danh bạ tác nhân và cơ hội.</p></div>
<div class="wrap" style="padding-bottom:72px">
<nav class="onpage small"><a href="#tong-quan" data-vi="Tổng quan" data-en="Overview">Tổng quan</a><a href="#nganh" data-vi="Ngành" data-en="Industries">Ngành</a><a href="#danh-ba" data-vi="Danh bạ" data-en="Directory">Danh bạ</a><a href="#ban-do" data-vi="Bản đồ" data-en="Map">Bản đồ</a><a href="#co-hoi" data-vi="Cơ hội" data-en="Opportunities">Cơ hội</a><a href="#xep-hang" data-vi="Xếp hạng" data-en="Ranking">Xếp hạng</a></nav>
<section id="tong-quan" class="sec"><h2 data-vi="Tổng quan" data-en="Overview">Tổng quan</h2><div class="kpis">{"".join(kp)}</div>
<h3 style="margin-top:28px" data-vi="Trong danh bạ mở này" data-en="In this open directory">Trong danh bạ mở này</h3><div class="kpis">{"".join(ours)}</div></section>
<section id="nganh" class="sec"><h2 data-vi="Ngành nổi bật" data-en="Top industries">Ngành nổi bật</h2>{ind_table(c.get("industries"))}
<p class="small" style="margin-top:12px"><span class="muted" data-vi="Doanh nghiệp lớn tích cực làm việc với startup:" data-en="Corporations active with startups:">Doanh nghiệp lớn tích cực làm việc với startup:</span> {corp}</p></section>
<section id="danh-ba" class="sec"><h2 data-vi="Danh bạ" data-en="Directory">Danh bạ</h2>
<div class="cols2"><div><h3 data-vi="Startup" data-en="Startups">Startup</h3>{lst("startup")}</div>
<div><h3 data-vi="Quỹ, nhà đầu tư" data-en="Funds, investors">Quỹ, nhà đầu tư</h3>{lst("fund", 12)}
<h3 style="margin-top:20px" data-vi="Tổ chức hỗ trợ" data-en="Support organisations">Tổ chức hỗ trợ</h3>{lst("support_org", 12)}{lst("incubator", 12) if tc["incubator"] else ""}
<h3 style="margin-top:20px" data-vi="Trường, viện" data-en="Universities">Trường, viện</h3>{lst("university", 12)}</div></div></section>
<section id="ban-do" class="sec"><h2 data-vi="Bản đồ" data-en="Map">Bản đồ</h2><div class="mapbox" id="citymap" data-ids="{",".join(a["id"] for a in acts)}"></div><p class="small muted" id="citymapnote" style="margin-top:8px"></p>
<p class="small"><a href="{dir_link(region=",".join(regs), view="map")}" data-vi="Mở bản đồ trong danh bạ để lọc thêm" data-en="Open the map in the directory to filter further">Mở bản đồ trong danh bạ để lọc thêm</a></p></section>
<section id="co-hoi" class="sec"><h2 data-vi="Cơ hội" data-en="Opportunities">Cơ hội</h2><div class="opp-list">{opp_html}</div>
<p class="small" style="margin-top:12px"><a href="{SITE_ROOT}co-hoi/" data-vi="Tất cả cơ hội" data-en="All opportunities">Tất cả cơ hội</a></p></section>
<section id="xep-hang" class="sec"><h2 data-vi="So với các thành phố khác" data-en="Compared with other cities">So với các thành phố khác</h2>{city_table(c["id"])}
<p class="small" style="margin-top:10px"><a href="{e(c["url"])}" rel="noopener" data-vi="Trang {e(c['name'])} trên StartupBlink" data-en="{e(c['name'])} on StartupBlink">Trang {e(c["name"])} trên StartupBlink</a></p></section>
{SB_NOTE}</div>"""
        body += """<script>document.addEventListener("DOMContentLoaded",function(){var el=document.getElementById("citymap");VIEMAP.render(el,el.dataset.ids.split(","),document.getElementById("citymapnote"));});</script>"""
        write(f"thanh-pho/{c['id']}/index.html", page(f"Khởi nghiệp {c['name']}", body, "cities", scripts=["map.js"], head=LEAF,
            desc=f"Hệ sinh thái khởi nghiệp {c['name']}: hạng #{c['global_rank']} thế giới, {len(acts)} tác nhân, {tc['startup']} startup, {tc['fund']} quỹ, bản đồ và cơ hội."))


# ---------- trang chủ ----------
def n_of(types):
    return sum(counts.get(t, 0) for t in types)
NEEDS = [
    ("Tôi có ý tưởng và cần nơi bắt đầu", "I have an idea and need a place to start", "Vườn ươm, không gian đổi mới sáng tạo, tổ chức hỗ trợ, chương trình tăng tốc.", "Incubators, innovation spaces, support organisations, accelerators.", ["incubator", "space", "support_org", "accelerator", "community"], "incubator"),
    ("Tôi cần vốn", "I need funding", "Quỹ đầu tư mạo hiểm, nhà đầu tư thiên thần, quỹ nhà nước.", "Venture funds, angel investors, public funds.", ["fund"], "fund"),
    ("Tôi tìm đối tác, khách hàng thử nghiệm", "I'm looking for partners and pilot customers", "Startup, doanh nghiệp, đối tác quốc tế.", "Startups, companies, international partners.", ["startup", "company", "international"], "company"),
    ("Tôi làm nghiên cứu, đào tạo, chính sách", "I work in research, education or policy", "Trường, viện, cơ quan nhà nước và văn bản chính sách.", "Universities, institutes, government and policy documents.", ["university", "government"], "university"),
]
needs_html = "".join(
    f'<a class="need" href="{dir_link(type=",".join(ts))}"><span class="nico">{icon_svg(ic, 26)}</span><span class="q" data-vi="{e(q)}" data-en="{e(qe)}">{e(q)}</span>'
    f'<span class="a" data-vi="{e(d)}" data-en="{e(de)}">{e(d)}</span><span class="n">{n_of(ts)}</span></a>'
    for q, qe, d, de, ts, ic in NEEDS)
st_rank = {"open": 0, "upcoming": 1, "closed": 2}
live = sorted([o for o in opps if opp_status(o) in ("open", "upcoming")], key=lambda o: (st_rank[opp_status(o)], o.get("deadline") or o.get("event_date") or ""))
recent = sorted([o for o in opps if opp_status(o) == "closed"], key=opp_key_date, reverse=True)
show = (live + recent)[:4]
n_open = sum(1 for o in opps if opp_status(o) == "open")
opp_title_vi = "Cơ hội đang mở" if live else "Cơ hội gần đây"
opp_title_en = "Open opportunities" if live else "Recent opportunities"
home_opps = "".join(opp_card(o, compact=True) for o in show)
city_cards = f'<a class="city all" href="{SITE_ROOT}danh-ba/"><span class="cn" data-vi="Toàn quốc" data-en="All of Vietnam">Toàn quốc</span><span class="cm">{len(actors)} <span data-vi="tác nhân" data-en="actors">tác nhân</span></span><span class="cr" data-vi="Hạng thế giới #{BENCH.get("country", {}).get("global_rank", "–")}" data-en="Global rank #{BENCH.get("country", {}).get("global_rank", "–")}">Hạng thế giới #{BENCH.get("country", {}).get("global_rank", "–")}</span></a>'
for c in BENCH.get("cities", []):
    n = sum(1 for a in actors if a["region"] in CITY_REGIONS.get(c["id"], [c["id"]]))
    no = sum(1 for o in opps if o["_region"] in CITY_REGIONS.get(c["id"], [c["id"]]))
    city_cards += (f'<a class="city" href="{SITE_ROOT}thanh-pho/{c["id"]}/"><span class="cn">{e(c["name"])}</span>'
                   f'<span class="cm">{n} <span data-vi="tác nhân" data-en="actors">tác nhân</span> · {no} <span data-vi="cơ hội" data-en="opportunities">cơ hội</span></span>'
                   f'<span class="cr" data-vi="Hạng thế giới #{c["global_rank"]}" data-en="Global rank #{c["global_rank"]}">Hạng thế giới #{c["global_rank"]}</span></a>')
feat = sorted([a for a in actors if a["type"] == "startup" and a.get("logo") and (a.get("description") or {}).get("vi") and a.get("status") != "inactive"],
              key=lambda a: (VER_ORDER.get(a["verification"]["level"], 9), a["name"]["vi"].lower()))[:12]
feat_html = "".join(f'<a class="fs" href="{SITE_ROOT}a/{a["id"]}/">{logo_img(a, 44)}<span class="nm">{e(a["name"]["vi"])}</span><span class="muted small">{e(", ".join(s[1] for s in SECTORS if s[0] in a["sectors"][:1]))}</span></a>' for a in feat)
po_html = "".join(f'<li><b>{e(x["document"])}</b><br><span class="muted">{e(x.get("summary"))}</span></li>' for x in policies[:4])
verified = sum(1 for a in actors if a["verification"]["level"] != "unverified")
home = f"""
<section class="hero"><div class="wrap">
<h1 data-vi="Ai đang làm gì cho khởi nghiệp Việt Nam?" data-en="Who is doing what for startups in Vietnam?">Ai đang làm gì cho khởi nghiệp Việt Nam?</h1>
<p class="lead" data-vi="Danh bạ mở về startup, quỹ, vườn ươm, trường, cơ quan và cơ hội trong hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam, do cộng đồng cùng cập nhật." data-en="An open, community-maintained directory of startups, funds, incubators, universities, agencies and opportunities in Vietnam's innovation ecosystem.">Danh bạ mở về startup, quỹ, vườn ươm, trường, cơ quan và cơ hội trong hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam, do cộng đồng cùng cập nhật.</p>
<form class="search" action="{SITE_ROOT}danh-ba/" role="search">
<label class="sr" for="hq" data-i18n="search_ph">Tìm</label>
<input id="hq" name="q" type="search" data-i18n-ph="search_ph2" placeholder="Tìm theo tên, lĩnh vực, mô tả…">
<button class="btn primary" type="submit" data-i18n="search_btn">Tìm</button>
</form>
<div class="cities" role="list" aria-label="Chọn thành phố">{city_cards}</div>
</div></section>
<section class="band first"><div class="wrap">
<div class="sec-h"><h2 data-vi="{opp_title_vi}" data-en="{opp_title_en}">{opp_title_vi}</h2><a href="{SITE_ROOT}co-hoi/" data-vi="Tất cả {len(opps)} cơ hội" data-en="All {len(opps)} opportunities">Tất cả {len(opps)} cơ hội</a></div>
{"" if live else '<p class="muted small" data-vi="Chưa có chương trình nào đang nhận hồ sơ trong danh sách; dưới đây là các cơ hội vừa kết thúc. Biết một chương trình đang mở? Thêm vào để mọi người cùng thấy." data-en="No programme in the list is taking applications right now; below are recent ones. Know an open programme? Add it.">Chưa có chương trình nào đang nhận hồ sơ trong danh sách; dưới đây là các cơ hội vừa kết thúc.</p>'}
<div class="opp-grid">{home_opps}</div>
</div></section>
<section class="needs"><div class="wrap">
<h2 class="sr">Bắt đầu từ việc bạn cần</h2>
{needs_html}
</div></section>
<section><div class="wrap" style="padding:48px 24px 8px">
<div class="sec-h"><h2 data-vi="Startup có hồ sơ đầy đủ" data-en="Startups with complete profiles">Startup có hồ sơ đầy đủ</h2><a href="{dir_link(type="startup")}" data-vi="Xem tất cả startup" data-en="See all startups">Xem tất cả startup</a></div>
<div class="fsgrid">{feat_html}</div>
</div></section>
<section class="band"><div class="wrap split">
<div><h2 data-vi="Chính sách mới (Đà Nẵng)" data-en="New policies (Da Nang)">Chính sách mới (Đà Nẵng)</h2><ul class="list-plain">{po_html}</ul>
<p style="margin-top:16px"><a href="{SITE_ROOT}chinh-sach/" data-i18n="all_policies">Tất cả chính sách</a></p></div>
<div><h2 data-vi="Dữ liệu mở, tải về miễn phí" data-en="Open data, free to download">Dữ liệu mở, tải về miễn phí</h2>
<p class="muted" style="margin-top:12px" data-vi="{len(actors)} hồ sơ, {verified} đã đối chiếu nguồn. Lọc trong danh bạ rồi bấm Tải CSV để lấy đúng phần bạn cần; dữ liệu dùng giấy phép CC BY 4.0." data-en="{len(actors)} profiles, {verified} checked against a source. Filter the directory and press Download CSV to get exactly what you need; data is CC BY 4.0.">{len(actors)} hồ sơ, {verified} đã đối chiếu nguồn. Lọc trong danh bạ rồi bấm Tải CSV để lấy đúng phần bạn cần; dữ liệu dùng giấy phép CC BY 4.0.</p>
<p style="margin-top:16px"><a class="btn primary" href="{SITE_ROOT}danh-ba/" data-vi="Mở danh bạ" data-en="Open the directory">Mở danh bạ</a> <a class="btn ghost" href="https://github.com/{REPO}/issues/new?template=them-hoac-sua-ho-so.yml" data-i18n="add_missing">Thêm hồ sơ còn thiếu</a></p></div>
</div></section>
"""
home_ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "Hệ sinh thái khởi nghiệp ĐMST Việt Nam", "url": f"{SITE_URL}/", "inLanguage": "vi",
           "potentialAction": {"@type": "SearchAction", "target": f"{SITE_URL}/danh-ba/?q={{search_term_string}}", "query-input": "required name=search_term_string"}}
write("index.html", page("", home, "home", desc=f"Danh bạ mở về {len(actors)} startup, quỹ, vườn ươm, trường, cơ quan và {len(opps)} cơ hội trong hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam: TP.HCM, Hà Nội, Đà Nẵng, Hải Phòng.",
      head='<script type="application/ld+json">' + json.dumps(home_ld, ensure_ascii=False) + "</script>"))

# ---------- chính sách ----------
by_year = collections.OrderedDict()
for x in policies:
    by_year.setdefault(str(x.get("issued") or "")[:4] or "Khác", []).append(x)
po_body = "".join(
    f'<section class="month" data-year="{e(y)}"><h2>{e(y)}</h2><ul class="list-plain">' + "".join(
        f'<li class="po" data-text="{e((x["document"] + " " + str(x.get("summary") or "")).lower())}">'
        + f'<a href="{SITE_ROOT}chinh-sach/{x["id"].removeprefix("policy-")}/"><b>{e(x["document"])}</b></a>'
        + (f' <span class="muted small">{e(fmt_date(x.get("issued")))}</span>' if x.get("issued") else "")
        + (f'<br>{e(x.get("summary"))}' if x.get("summary") else "") + '</li>' for x in xs) + '</ul></section>'
    for y, xs in by_year.items())
po_script = """<script>document.addEventListener('DOMContentLoaded',function(){var q=document.getElementById('pq');
q.addEventListener('input',function(){var v=q.value.trim().toLowerCase();document.querySelectorAll('.po').forEach(function(li){li.hidden=v&&li.getAttribute('data-text').indexOf(v)<0});
document.querySelectorAll('[data-year]').forEach(function(s){s.hidden=!s.querySelector('.po:not([hidden])')});});});</script>"""
write("chinh-sach/index.html", page("Chính sách", f"""
<div class="wrap page-head"><h1 data-i18n="nav_policy">Chính sách</h1>
<p class="lead" data-vi="Văn bản hỗ trợ khởi nghiệp, đổi mới sáng tạo và chuyển đổi số tại Đà Nẵng, theo năm ban hành." data-en="Documents supporting startups, innovation and digital transformation in Da Nang, by year issued.">Văn bản hỗ trợ khởi nghiệp, đổi mới sáng tạo và chuyển đổi số tại Đà Nẵng, theo năm ban hành.</p>
<div class="bar" style="margin-top:20px"><label class="sr" for="pq" data-i18n="policy_search">Tìm</label><input id="pq" type="search" data-i18n-ph="policy_search" placeholder="Tìm văn bản, nội dung…"></div></div>
<div class="wrap" style="padding-bottom:72px">{po_body}</div>{po_script}""", "policy", desc=f"{len(policies)} văn bản chính sách về khởi nghiệp, đổi mới sáng tạo, khoa học công nghệ và chuyển đổi số, tra cứu theo loại và năm."))


# ================= ĐỢT 2: trang đích, trang chi tiết, dữ liệu, giới thiệu =================
def kp(label_vi, label_en, value, note=""):
    return kpi(label_vi, label_en, value, note)

def rich_sorted(xs):
    return sorted(xs, key=lambda x: (-richness(x), VER_ORDER.get(x["verification"]["level"], 9), x["name"]["vi"].lower()))

def dist_rows(counter, label):
    total = sum(counter.values()) or 1
    rows = "".join(f'<tr><td>{label(k)}</td><td>{v}</td><td><span class="bar-in" style="width:{max(2, round(100 * v / total))}%"></span></td></tr>'
                   for k, v in counter.most_common(8))
    return f'<div class="tbl-wrap"><table class="tbl dist"><tbody>{rows}</tbody></table></div>'

REG_L = lambda k: f'<span data-i18n="r_{k.replace("-", "_")}">{e(REGION_VI.get(k, k))}</span>'
TYPE_L = lambda k: f'<span data-i18n="t_{k}">{e(VIE_TYPE.get(k, k))}</span>'
SEC_L = lambda k: e(SECT_VI.get(k, "Chưa phân loại"))

def landing(path, title, title_en, intro, intro_en, xs, dir_params, extra="", desc=""):
    rc = collections.Counter(x["region"] for x in xs)
    sc = collections.Counter(s for x in xs for s in (x.get("sectors") or ["_none"]))
    tc = collections.Counter(x["type"] for x in xs)
    k = [kp("Hồ sơ", "Profiles", str(len(xs))),
         kp("Có logo", "With logo", f'{sum(1 for x in xs if x.get("logo"))}'),
         kp("Có mô tả", "With description", f'{sum(1 for x in xs if (x.get("description") or {}).get("vi"))}'),
         kp("Đã xác minh", "Verified", f'{sum(1 for x in xs if x["verification"]["level"] != "unverified")}')]
    top = rich_sorted(xs)[:24]
    dist = (f'<div class="cols2"><div><h3 data-vi="Theo địa phương" data-en="By place">Theo địa phương</h3>{dist_rows(rc, REG_L)}</div>'
            + (f'<div><h3 data-vi="Theo lĩnh vực" data-en="By sector">Theo lĩnh vực</h3>{dist_rows(sc, SEC_L)}</div>' if "sector" not in dir_params
               else f'<div><h3 data-vi="Theo loại" data-en="By type">Theo loại</h3>{dist_rows(tc, TYPE_L)}</div>') + "</div>")
    body = f"""
<div class="wrap page-head"><p class="crumb small">{extra and ""}</p>
<h1 data-vi="{e(title)}" data-en="{e(title_en)}">{e(title)}</h1>
<p class="lead" data-vi="{e(intro)}" data-en="{e(intro_en)}">{e(intro)}</p>
<p style="margin-top:18px"><a class="btn primary" href="{dir_link(**dir_params)}" data-vi="Lọc và tải CSV trong danh bạ" data-en="Filter and download CSV in the directory">Lọc và tải CSV trong danh bạ</a>
<a class="btn ghost" href="{dir_link(view="map", **dir_params)}" data-vi="Xem trên bản đồ" data-en="View on map">Xem trên bản đồ</a></p></div>
<div class="wrap" style="padding-bottom:72px">
<section class="sec"><div class="kpis">{"".join(k)}</div></section>
<section class="sec"><h2 data-vi="Hồ sơ nổi bật" data-en="Featured profiles">Hồ sơ nổi bật</h2>{mini_cards(top)}
<p class="small" style="margin-top:12px"><a href="{dir_link(**dir_params)}" data-vi="Xem tất cả {len(xs)}" data-en="See all {len(xs)}">Xem tất cả {len(xs)}</a></p></section>
<section class="sec"><h2 data-vi="Phân bố" data-en="Distribution">Phân bố</h2>{dist}</section>
{extra}
</div>"""
    write(path, page(title, body, "dir" if path.startswith("danh-ba") else "sectors", desc=desc or intro))

# ---- trang đích theo loại ----
TYPE_PAGES = [
    ("startup", ["startup"], "Startup", "Startups", "Startup đổi mới sáng tạo tại Việt Nam, từ dự án sinh viên đến doanh nghiệp đã gọi vốn.", "Innovative startups in Vietnam, from student projects to funded companies."),
    ("quy-dau-tu", ["fund"], "Quỹ đầu tư, nhà đầu tư", "Funds and investors", "Quỹ đầu tư mạo hiểm, quỹ đầu tư thiên thần, quỹ nhà nước và quỹ doanh nghiệp đầu tư vào startup Việt Nam.", "Venture, angel, public and corporate funds investing in Vietnamese startups."),
    ("ho-tro-khoi-nghiep", ["incubator", "accelerator", "space", "support_org", "community"], "Tổ chức hỗ trợ khởi nghiệp", "Startup support organisations", "Vườn ươm, chương trình tăng tốc, không gian đổi mới sáng tạo, cộng đồng và tổ chức hỗ trợ khởi nghiệp.", "Incubators, accelerators, innovation spaces, communities and support organisations."),
    ("truong-vien", ["university"], "Trường, viện", "Universities and institutes", "Trường đại học, cao đẳng, viện nghiên cứu và trung tâm khởi nghiệp trong trường.", "Universities, colleges, research institutes and campus startup centres."),
    ("co-quan-nha-nuoc", ["government"], "Cơ quan nhà nước", "Government bodies", "Cơ quan quản lý, đơn vị sự nghiệp và trung tâm đổi mới sáng tạo của nhà nước.", "Public agencies, public service units and state innovation centres."),
    ("doanh-nghiep", ["company"], "Doanh nghiệp", "Companies", "Doanh nghiệp công nghệ, doanh nghiệp lớn và đối tác thương mại làm việc với startup.", "Technology firms, corporates and commercial partners working with startups."),
    ("doi-tac-quoc-te", ["international"], "Đối tác quốc tế", "International partners", "Tổ chức quốc tế, cơ quan phát triển và đối tác nước ngoài hoạt động trong hệ sinh thái Việt Nam.", "International organisations, development agencies and foreign partners active in Vietnam."),
    ("du-an-sang-tao", ["creator"], "Dự án sáng tạo", "Creative projects", "Dự án sáng tạo cộng đồng, chủ yếu từ chương trình Bản lĩnh xứ Quảng.", "Community creative projects, mostly from the Ban linh xu Quang programme."),
]
for slug, ts, t, te, i, ie in TYPE_PAGES:
    xs = [a for a in actors if a["type"] in ts]
    if xs:
        landing(f"danh-ba/{slug}/index.html", t, te, i, ie, xs, {"type": ",".join(ts)},
                desc=f"{len(xs)} {t.lower()} trong danh bạ mở hệ sinh thái khởi nghiệp Việt Nam. {i}")

# ---- lĩnh vực ----
SECT_INTRO = {
    "ai": ("Trí tuệ nhân tạo, phần mềm, dữ liệu và chuyển đổi số.", "AI, software, data and digital transformation."),
    "fintech": ("Thanh toán, ví điện tử, ngân hàng số, bảo hiểm và kế toán.", "Payments, wallets, digital banking, insurance and accounting."),
    "web3": ("Blockchain, tài sản số, stablecoin và hạ tầng Web3.", "Blockchain, digital assets, stablecoins and Web3 infrastructure."),
    "commerce": ("Thương mại điện tử, bán lẻ, công cụ cho người bán.", "E-commerce, retail and seller tools."),
    "agrifood": ("Nông nghiệp, thủy sản, thực phẩm, dược liệu, sản phẩm OCOP.", "Agriculture, aquaculture, food, medicinal plants, OCOP products."),
    "health": ("Y tế, công nghệ sinh học, chăm sóc sức khỏe, mỹ phẩm.", "Health, biotech, care and cosmetics."),
    "edu": ("Giáo dục, đào tạo, học ngoại ngữ, STEM.", "Education, training, language learning, STEM."),
    "tourism": ("Du lịch, lưu trú, văn hóa, di sản, làng nghề.", "Tourism, hospitality, culture, heritage, craft villages."),
    "climate": ("Năng lượng tái tạo, pin, kinh tế tuần hoàn, xử lý chất thải, giảm phát thải.", "Renewables, batteries, circular economy, waste, decarbonisation."),
    "deeptech": ("Bán dẫn, robot, drone, IoT, vật liệu mới và phần cứng.", "Semiconductors, robotics, drones, IoT, new materials and hardware."),
    "mobility": ("Logistics, vận tải, giao hàng, xe điện, chuỗi cung ứng.", "Logistics, transport, delivery, EVs, supply chain."),
    "marketing": ("Truyền thông, quảng cáo, nội dung, giải trí, game.", "Media, advertising, content, entertainment, games."),
    "property": ("Bất động sản, xây dựng, kiến trúc, nội thất.", "Property, construction, architecture, interiors."),
}
sec_cards = ""
for k, vi, en, _ in SECTORS:
    xs = by_sector.get(k, [])
    iv, ie = SECT_INTRO.get(k, ("", ""))
    sec_cards += (f'<a class="city" href="{SITE_ROOT}linh-vuc/{k}/"><span class="cn" data-vi="{e(vi)}" data-en="{e(en)}">{e(vi)}</span>'
                  f'<span class="cm">{len(xs)} <span data-vi="hồ sơ" data-en="profiles">hồ sơ</span></span><span class="cr" data-vi="{e(iv)}" data-en="{e(ie)}">{e(iv)}</span></a>')
    if xs:
        sopps = [o for o in opps if any(_fold(f) and _fold(vi.split(",")[0]) in _fold(f) for f in (o.get("focus") or []))]
        extra = ""
        if sopps:
            extra = ('<section class="sec"><h2 data-vi="Cơ hội liên quan" data-en="Related opportunities">Cơ hội liên quan</h2><div class="opp-list">'
                     + "".join(opp_card(o, compact=True) for o in sopps[:6]) + "</div></section>")
        landing(f"linh-vuc/{k}/index.html", vi, en, iv, ie, xs, {"sector": k}, extra=extra,
                desc=f"{len(xs)} startup, doanh nghiệp, quỹ lĩnh vực {vi.lower()} tại Việt Nam: {iv}")
unclassified = sum(1 for a in actors if a["type"] in ("startup", "company", "fund", "creator") and not a.get("sectors"))
write("linh-vuc/index.html", page("Lĩnh vực", f"""
<div class="wrap page-head"><h1 data-vi="Lĩnh vực" data-en="Sectors">Lĩnh vực</h1>
<p class="lead" data-vi="13 lĩnh vực của startup, doanh nghiệp và quỹ trong danh bạ. Lĩnh vực do tổ chức tự chọn; một số hồ sơ đang mang gợi ý tự động chờ xác nhận." data-en="13 sectors across startups, companies and funds. Organisations choose their own sectors; some profiles still carry automatic suggestions awaiting confirmation.">13 lĩnh vực của startup, doanh nghiệp và quỹ trong danh bạ.</p></div>
<div class="wrap" style="padding-bottom:72px"><div class="cities secgrid">{sec_cards}</div>
<p class="small muted" style="margin-top:20px" data-vi="{unclassified} hồ sơ chưa có lĩnh vực. Tổ chức của bạn chưa đúng lĩnh vực? Sửa hồ sơ hoặc gửi biểu mẫu." data-en="{unclassified} profiles have no sector yet.">{unclassified} hồ sơ chưa có lĩnh vực. Tổ chức của bạn chưa đúng lĩnh vực? Sửa hồ sơ hoặc gửi biểu mẫu.</p></div>""", "sectors",
      desc="Startup, doanh nghiệp và quỹ đầu tư Việt Nam theo 13 lĩnh vực: AI, tài chính số, Web3, nông nghiệp, y tế, giáo dục, du lịch, năng lượng, bán dẫn, logistics và hơn nữa."))

# ---- chi tiết cơ hội ----
for o in opps:
    slug = o["id"].removeprefix("opp-")
    parts = [by_id[x] for x in dict.fromkeys(o.get("participants") or []) if x in by_id]
    orgs = [by_id[x] for x in o.get("organizer_ids") or [] if x in by_id]
    same = [x for x in opps if x is not o and x["type"] == o["type"]][:4]
    body = f"""
<div class="wrap crumbs" style="max-width:920px"><a href="{SITE_ROOT}co-hoi/" data-i18n="nav_opps">Cơ hội</a> / {e(o["title"])}</div>
<div class="wrap" style="padding-bottom:72px;max-width:920px">
<div class="opp-list opp-detail">{opp_card(o)}</div>
{('<section class="sec"><h2 data-vi="Đơn vị tổ chức" data-en="Organisers">Đơn vị tổ chức</h2>' + mini_cards(orgs) + '</section>') if orgs else ""}
{(f'<section class="sec"><h2 data-vi="Tham gia, được chọn ({len(parts)})" data-en="Participants ({len(parts)})">Tham gia, được chọn ({len(parts)})</h2>' + mini_cards(rich_sorted(parts)) + '</section>') if parts else ""}
{('<section class="sec"><h2 data-vi="Cơ hội cùng loại" data-en="Similar opportunities">Cơ hội cùng loại</h2><div class="opp-list">' + "".join(opp_card(x, compact=True) for x in same) + '</div></section>') if same else ""}
</div>"""
    ev = {"@context": "https://schema.org", "@type": "Event", "name": o["title"], "url": f"{SITE_URL}/co-hoi/{slug}/",
          "eventStatus": "https://schema.org/EventScheduled", "organizer": {"@type": "Organization", "name": o["organizer"]}}
    if o.get("event_date"): ev["startDate"] = o["event_date"]
    elif o.get("deadline"): ev["startDate"] = o["deadline"]
    ev["location"] = {"@type": "Place", "name": REGION_VI.get(o["_region"], "Việt Nam"), "address": {"@type": "PostalAddress", "addressRegion": REGION_VI.get(o["_region"], ""), "addressCountry": "VN"}}
    if o.get("primary_source") or o.get("apply_url"): ev["sameAs"] = o.get("primary_source") or o.get("apply_url")
    tv = OPP_TYPES[o["type"]][0]
    d = f'{o["title"]}: {tv.lower()} tại {REGION_VI.get(o["_region"], "Việt Nam")}' + (f', ngày {fmt_date(o["event_date"])}' if o.get("event_date") else "") + (f', hạn nộp {fmt_date(o["deadline"])}' if o.get("deadline") else "") + (f". {len(parts)} đơn vị tham gia, được chọn." if parts else ".")
    write(f"co-hoi/{slug}/index.html", page(o["title"], body, "opps", desc=d,
          head='<script type="application/ld+json">' + json.dumps(ev, ensure_ascii=False) + "</script>"), lastmod=GIT_DATES.get(f"data/{o['_region']}/opportunities.yaml", TODAY))

# ---- chi tiết chính sách ----
DOC_KIND = [("NQ", "Nghị quyết"), ("QĐ", "Quyết định"), ("KH", "Kế hoạch"), ("CT", "Chỉ thị"), ("TT", "Thông tư"), ("NĐ", "Nghị định"), ("Luật", "Luật"), ("CV", "Công văn"), ("ĐA", "Đề án")]
def doc_kind(d):
    for k, v in DOC_KIND:
        if d.startswith(k): return v
    return "Văn bản"
def doc_issuer(d):
    for k, v in (("HĐND", "Hội đồng nhân dân thành phố"), ("UBND", "Ủy ban nhân dân thành phố"), ("TTg", "Thủ tướng Chính phủ"), ("BKHCN", "Bộ Khoa học và Công nghệ"), ("CP", "Chính phủ"), ("QH", "Quốc hội")):
        if k in d: return v
    return ""
for x in policies:
    slug = x["id"].removeprefix("policy-")
    kind, issuer = doc_kind(x["document"]), doc_issuer(x["document"])
    yr = str(x.get("issued") or "")[:4]
    near = [y for y in policies if y is not x and str(y.get("issued") or "")[:4] == yr and doc_kind(y["document"]) == kind][:8]
    facts = [("Số hiệu", "Number", e(x["document"])), ("Loại văn bản", "Type", e(kind))]
    if issuer: facts.append(("Cơ quan ban hành", "Issued by", e(issuer)))
    if x.get("issued"): facts.append(("Ngày ban hành", "Issued", e(fmt_date(x["issued"]))))
    facts.append(("Địa phương", "Place", "Đà Nẵng"))
    if x.get("source"): facts.append(("Nguồn", "Source", e(x["source"])))
    fh = "".join(f'<dt data-vi="{a}" data-en="{b}">{a}</dt><dd>{c}</dd>' for a, b, c in facts)
    body = f"""
<div class="wrap crumbs"><a href="{SITE_ROOT}chinh-sach/" data-i18n="nav_policy">Chính sách</a> / {e(x["document"])}</div>
<div class="wrap actor"><article>
<p><span class="tag">{e(kind)}</span></p>
<h1 style="margin-top:8px">{e(x["document"])}</h1>
<p class="desc">{e(x.get("summary") or "")}</p>
<dl class="facts">{fh}</dl>
{f'<p style="margin-top:18px"><a class="btn primary" href="{e(x["url"])}" rel="noopener" data-vi="Đọc toàn văn" data-en="Read the full text">Đọc toàn văn</a></p>' if x.get("url") else '<p class="small muted" style="margin-top:14px" data-vi="Chưa có đường dẫn toàn văn. Biết nguồn chính thức? Bổ sung vào dữ liệu." data-en="No link to the full text yet.">Chưa có đường dẫn toàn văn. Biết nguồn chính thức? Bổ sung vào dữ liệu.</p>'}
{('<div class="section"><h2 data-vi="Cùng loại, cùng năm" data-en="Same type, same year">Cùng loại, cùng năm</h2><ul class="list-plain">' + "".join(f'<li><a href="{SITE_ROOT}chinh-sach/{y["id"].removeprefix("policy-")}/">{e(y["document"])}</a> <span class="muted small">{e(y.get("summary") or "")}</span></li>' for y in near) + '</ul></div>') if near else ""}
</article>
<aside class="side"><div class="box"><h2 data-vi="Thông tin chưa đúng?" data-en="Something wrong?">Thông tin chưa đúng?</h2>
<p style="margin-top:12px"><a class="btn ghost" href="https://github.com/{REPO}/edit/main/data/da-nang/policies.yaml" data-vi="Sửa trên GitHub" data-en="Edit on GitHub">Sửa trên GitHub</a></p></div></aside></div>"""
    ld = {"@context": "https://schema.org", "@type": "Legislation", "name": x["document"], "legislationIdentifier": x["document"],
          "legislationType": kind, "url": f"{SITE_URL}/chinh-sach/{slug}/", "spatialCoverage": "Đà Nẵng, Việt Nam"}
    if x.get("issued"): ld["legislationDate"] = x["issued"]
    if x.get("summary"): ld["description"] = x["summary"]
    if issuer: ld["legislationPassedBy"] = {"@type": "GovernmentOrganization", "name": issuer}
    write(f"chinh-sach/{slug}/index.html", page(f'{x["document"]}: {x.get("summary") or kind}', body, "policy",
          desc=f'{kind} {x["document"]}' + (f' ngày {fmt_date(x["issued"])}' if x.get("issued") else "") + (f': {x["summary"]}' if x.get("summary") else "") + ". Đà Nẵng.",
          head='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>"), lastmod=GIT_DATES.get("data/da-nang/policies.yaml", TODAY))

# ---- dữ liệu ----
csv_cols = ["id", "name", "type", "sectors", "region", "status", "founded", "website", "linkedin", "description", "verification", "sources"]
import io
buf = io.StringIO(); w = csv.writer(buf)
w.writerow(csv_cols)
for a in actors:
    w.writerow([a["id"], a["name"]["vi"], a["type"], "; ".join(a.get("sectors") or []), a["region"], a.get("status", ""), a.get("founded", ""),
                a.get("website", ""), a.get("linkedin", ""), (a.get("description") or {}).get("vi", ""), a["verification"]["level"], "; ".join(a["sources"])])
open(os.path.join(OUT, "data", "actors.csv"), "w", encoding="utf-8-sig", newline="").write(buf.getvalue())
def pct(n, d): return f"{round(100 * n / d) if d else 0}%"
q_rows = ""
for r in ["da-nang", "former-quang-nam", "ho-chi-minh", "ha-noi", "hai-phong", "viet-nam", "quoc-te"]:
    xs = [a for a in actors if a["region"] == r]
    if not xs: continue
    n = len(xs)
    q_rows += (f'<tr><td>{REG_L(r)}</td><td>{n}</td><td>{pct(sum(1 for a in xs if a.get("logo")), n)}</td><td>{pct(sum(1 for a in xs if (a.get("description") or {}).get("vi")), n)}</td>'
               f'<td>{pct(sum(1 for a in xs if a.get("website")), n)}</td><td>{pct(sum(1 for a in xs if a.get("linkedin")), n)}</td><td>{pct(sum(1 for a in xs if a.get("sectors")), n)}</td>'
               f'<td>{pct(sum(1 for a in xs if a.get("coordinates") or a.get("place")), n)}</td><td>{pct(sum(1 for a in xs if a["verification"]["level"] != "unverified"), n)}</td></tr>')
N = len(actors)
q_rows += (f'<tr class="cur"><td data-vi="Tổng" data-en="Total">Tổng</td><td>{N}</td><td>{pct(sum(1 for a in actors if a.get("logo")), N)}</td><td>{pct(sum(1 for a in actors if (a.get("description") or {}).get("vi")), N)}</td>'
           f'<td>{pct(sum(1 for a in actors if a.get("website")), N)}</td><td>{pct(sum(1 for a in actors if a.get("linkedin")), N)}</td><td>{pct(sum(1 for a in actors if a.get("sectors")), N)}</td>'
           f'<td>{pct(sum(1 for a in actors if a.get("coordinates") or a.get("place")), N)}</td><td>{pct(sum(1 for a in actors if a["verification"]["level"] != "unverified"), N)}</td></tr>')
files = [("actors.csv", "Toàn bộ tác nhân, CSV (mở bằng Excel)", "All actors, CSV"), ("actors.json", "Toàn bộ tác nhân, JSON", "All actors, JSON"),
         ("actors.geojson", "Tác nhân có tọa độ, GeoJSON", "Actors with coordinates, GeoJSON"), ("opportunities.json", "Cơ hội, JSON", "Opportunities, JSON"),
         ("relations.json", "Quan hệ giữa tác nhân, JSON", "Relations, JSON"), ("sectors.json", "Danh mục lĩnh vực, JSON", "Sector list, JSON"), ("stats.json", "Số liệu tổng hợp, JSON", "Summary statistics, JSON")]
f_rows = "".join(f'<li><a href="{SITE_ROOT}data/{f}" download><b>{f}</b></a> <span class="muted" data-vi="{vi}" data-en="{en}">{vi}</span></li>' for f, vi, en in files)
write("du-lieu/index.html", page("Dữ liệu", f"""
<div class="wrap page-head"><h1 data-vi="Dữ liệu mở" data-en="Open data">Dữ liệu mở</h1>
<p class="lead" data-vi="Toàn bộ dữ liệu của bản đồ được tải về miễn phí, không cần tài khoản, theo giấy phép CC BY 4.0: được dùng, chỉnh sửa, thương mại hóa, chỉ cần ghi nguồn." data-en="All map data is free to download, no account needed, under CC BY 4.0: use, adapt and commercialise with attribution.">Toàn bộ dữ liệu của bản đồ được tải về miễn phí, không cần tài khoản, theo giấy phép CC BY 4.0.</p></div>
<div class="wrap" style="padding-bottom:72px">
<section class="sec"><h2 data-vi="Tải về" data-en="Download">Tải về</h2><ul class="list-plain">{f_rows}</ul>
<p class="small muted" style="margin-top:10px" data-vi="Muốn một phần dữ liệu? Lọc trong Danh bạ rồi bấm Tải CSV. Các tệp JSON được cập nhật mỗi lần dữ liệu thay đổi và có thể đọc trực tiếp từ ứng dụng khác." data-en="Need a subset? Filter the directory and press Download CSV. JSON files update with every data change and can be read directly by other apps.">Muốn một phần dữ liệu? Lọc trong Danh bạ rồi bấm Tải CSV.</p></section>
<section class="sec"><h2 data-vi="Chất lượng dữ liệu" data-en="Data quality">Chất lượng dữ liệu</h2>
<div class="tbl-wrap"><table class="tbl"><thead><tr><th data-vi="Địa phương" data-en="Place">Địa phương</th><th data-vi="Hồ sơ" data-en="Profiles">Hồ sơ</th><th>Logo</th><th data-vi="Mô tả" data-en="Description">Mô tả</th><th>Website</th><th>LinkedIn</th><th data-vi="Lĩnh vực" data-en="Sector">Lĩnh vực</th><th data-vi="Vị trí" data-en="Location">Vị trí</th><th data-vi="Đã xác minh" data-en="Verified">Đã xác minh</th></tr></thead><tbody>{q_rows}</tbody></table></div>
<p class="small muted" style="margin-top:10px" data-vi="Cập nhật {TODAY}. Cách tính mức xác minh xem ở trang Phương pháp." data-en="Updated {TODAY}. See Methodology for verification levels.">Cập nhật {TODAY}. Cách tính mức xác minh xem ở trang <a href="{SITE_ROOT}gioi-thieu/phuong-phap/">Phương pháp</a>.</p></section>
<section class="sec"><h2 data-vi="Cấu trúc và giấy phép" data-en="Structure and licence">Cấu trúc và giấy phép</h2>
<ul class="list-plain"><li><a href="https://github.com/{REPO}/blob/main/docs/data-model.md" data-vi="Mô hình dữ liệu: các trường và ý nghĩa" data-en="Data model: fields and meaning">Mô hình dữ liệu: các trường và ý nghĩa</a></li>
<li><a href="https://github.com/{REPO}/tree/main/schema" data-vi="Schema JSON dùng để kiểm tra tự động" data-en="JSON schemas used for validation">Schema JSON dùng để kiểm tra tự động</a></li>
<li><a href="https://github.com/{REPO}/blob/main/data/LICENSE.md" data-vi="Giấy phép dữ liệu CC BY 4.0 và cách ghi nguồn" data-en="CC BY 4.0 data licence and attribution">Giấy phép dữ liệu CC BY 4.0 và cách ghi nguồn</a></li>
<li><a href="https://github.com/{REPO}/blob/main/logos/README.md" data-vi="Logo là nhãn hiệu của tổ chức, không thuộc CC BY" data-en="Logos are trademarks, not CC BY">Logo là nhãn hiệu của tổ chức, không thuộc CC BY</a></li>
<li><a href="https://github.com/{REPO}/commits/main/data" data-vi="Lịch sử thay đổi dữ liệu" data-en="Data change history">Lịch sử thay đổi dữ liệu</a></li></ul></section>
</div>""", "data", desc=f"Tải miễn phí dữ liệu {len(actors)} tác nhân, {len(opps)} cơ hội trong hệ sinh thái khởi nghiệp Việt Nam: CSV, JSON, GeoJSON, giấy phép CC BY 4.0, kèm số liệu chất lượng dữ liệu."))

# ---- giới thiệu ----
def info_page(path, title, title_en, html_body, desc):
    write(path, page(title, f'<div class="wrap page-head"><h1 data-vi="{e(title)}" data-en="{e(title_en)}">{e(title)}</h1></div><div class="wrap prose" style="padding-bottom:72px;max-width:820px">{html_body}</div>', "", desc=desc))
src_counts = collections.Counter(s.split(" (")[0] for a in actors for s in a["sources"])
src_list = "".join(f"<li>{e(s)} <span class='muted small'>({n} hồ sơ)</span></li>" for s, n in src_counts.most_common(12))
info_page("gioi-thieu/index.html", "Giới thiệu", "About", f"""
<p class="lead">Bản đồ hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam là danh bạ mở, do cộng đồng cùng cập nhật: ai đang làm gì, ở đâu, và cơ hội nào đang mở cho startup.</p>
<h2>Vì sao có bản đồ này</h2>
<p>Thông tin về hệ sinh thái nằm rải rác ở trang của từng tổ chức, bài báo, danh sách sự kiện và báo cáo trả phí. Bản đồ gom lại thành một chỗ, ghi rõ nguồn từng dòng, và cho phép tải về miễn phí để ai cũng dùng được: founder tìm nơi hỗ trợ và vốn, nhà đầu tư tìm dự án, cơ quan nhà nước và nhà nghiên cứu nhìn toàn cảnh.</p>
<h2>Hiện có gì</h2>
<p>{len(actors)} tác nhân (startup, quỹ, vườn ươm, trường, cơ quan, doanh nghiệp, đối tác quốc tế), {len(opps)} cơ hội và {len(policies)} văn bản chính sách. Dữ liệu bắt đầu từ Đà Nẵng và đang mở rộng ra TP.HCM, Hà Nội, Hải Phòng.</p>
<h2>Nguồn dữ liệu chính</h2><ul>{src_list}</ul>
<p>Mỗi hồ sơ ghi nguồn riêng. Cách chọn và kiểm tra nguồn xem ở trang <a href="{SITE_ROOT}gioi-thieu/phuong-phap/">Phương pháp</a>.</p>
<h2>Ai vận hành</h2>
<p>Dự án mã nguồn mở trên GitHub. Mọi thay đổi đi qua Pull Request và được kiểm tra tự động trước khi lên trang. Vai trò điều phối, duyệt và quy trình gỡ thông tin được mô tả trong <a href="https://github.com/{REPO}/blob/main/GOVERNANCE.md">GOVERNANCE.md</a>.</p>
<h2>Giấy phép</h2>
<p>Dữ liệu theo CC BY 4.0, mã nguồn theo MIT. Logo thuộc chủ sở hữu tương ứng.</p>
""", "Giới thiệu bản đồ hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam: mục tiêu, nguồn dữ liệu, cách vận hành và giấy phép.")
info_page("gioi-thieu/phuong-phap/index.html", "Phương pháp", "Methodology", f"""
<h2>Mức xác minh</h2>
<ul><li>{ver_badge("unverified")}: thông tin lấy từ nguồn công khai hoặc cộng đồng gửi, chưa ai đối chiếu.</li>
<li>{ver_badge("source_checked")}: đã đối chiếu với ít nhất một nguồn đáng tin (website chính thức, văn bản, bài báo).</li>
<li>{ver_badge("org_confirmed")}: chính tổ chức đã xác nhận hoặc tự cập nhật hồ sơ.</li>
<li>{ver_badge("partner_verified")}: một tổ chức hỗ trợ đã làm việc trực tiếp với đơn vị này xác nhận (ví dụ vườn ươm xác nhận startup đã ươm tạo).</li></ul>
<h2>Nguồn</h2>
<p>Mỗi hồ sơ ghi nguồn trong trường <code>sources</code>. Mô tả được viết lại ngắn gọn từ phần tự giới thiệu của tổ chức, không sao chép nguyên văn. Không thu thập dữ liệu bằng cách quét tự động các nền tảng cấm việc này (như LinkedIn); liên kết LinkedIn chỉ lấy khi tổ chức tự đặt trên website của mình.</p>
<h2>Thông tin cá nhân</h2>
<p>Không đăng hồ sơ cá nhân khi người đó chưa đồng ý. Thông tin liên hệ chỉ dùng kênh chung của tổ chức, không dùng email hay số di động cá nhân.</p>
<h2>Lĩnh vực</h2>
<p>13 lĩnh vực trong <code>schema/sectors.yaml</code>. Tổ chức tự chọn tối đa 3. Hồ sơ chưa chọn có thể mang gợi ý tự động theo từ khóa, cần tổ chức xác nhận.</p>
<h2>Cơ hội</h2>
<p>Chỉ ghi các hoạt động có thể dẫn tới vốn, khách hàng hoặc hợp đồng: kêu gọi hồ sơ, cuộc thi, demo day, kết nối nhà đầu tư, kết nối khách hàng, ươm tạo, thử nghiệm. Đường dẫn đăng ký phải là trang của đơn vị tổ chức. Trạng thái (đang mở, sắp diễn ra, đã kết thúc) tính tự động theo ngày.</p>
<h2>Số liệu xếp hạng thành phố</h2>
<p>Lấy từ trang công khai của StartupBlink Global Startup Ecosystem Index 2026, ghi nguồn và ngày truy cập; không dùng dữ liệu thuộc gói trả phí.</p>
<h2>Trùng lặp</h2>
<p>Kiểm tra tự động so tên gần đúng (kể cả viết tắt) và chặn hồ sơ trùng. Tên cũ, tên pháp lý giữ trong <code>alt_names</code> để tìm được.</p>
""", "Phương pháp của bản đồ hệ sinh thái khởi nghiệp Việt Nam: mức xác minh, nguồn dữ liệu, thông tin cá nhân, lĩnh vực, cơ hội và kiểm tra trùng lặp.")
info_page("gioi-thieu/dong-gop/index.html", "Đóng góp", "Contribute", f"""
<p class="lead">Không cần biết lập trình. Có ba cách, chọn cách bạn thấy tiện.</p>
<h2>1. Gửi biểu mẫu</h2>
<p>Thêm tổ chức mới, sửa thông tin, chọn lĩnh vực, gửi logo hoặc yêu cầu gỡ thông tin qua biểu mẫu trên GitHub. Người duyệt sẽ cập nhật giúp.</p>
<p><a class="btn primary" href="https://github.com/{REPO}/issues/new?template=them-hoac-sua-ho-so.yml">Mở biểu mẫu</a></p>
<h2>2. Sửa trực tiếp hồ sơ</h2>
<p>Mỗi trang hồ sơ có nút <b>Sửa trên GitHub</b>. Bạn sửa tệp, GitHub tự tạo đề xuất thay đổi; kiểm tra tự động báo ngay nếu có lỗi.</p>
<h2>3. Thêm cơ hội</h2>
<p>Chương trình đang nhận hồ sơ, cuộc thi, demo day: thêm vào tệp <code>opportunities.yaml</code> của địa phương, ghi hạn nộp, quyền lợi và đường dẫn đăng ký của đơn vị tổ chức.</p>
<h2>Logo</h2>
<p>Tệp vuông 128 × 128 px, nền trong suốt, định dạng WebP hoặc PNG, đặt tên trùng mã hồ sơ.</p>
<h2>Gỡ thông tin</h2>
<p>Tổ chức hoặc cá nhân muốn gỡ thông tin về mình: gửi biểu mẫu, ghi rõ hồ sơ và lý do. Yêu cầu được xử lý theo quy trình trong <a href="https://github.com/{REPO}/blob/main/GOVERNANCE.md">GOVERNANCE.md</a>.</p>
<p>Hướng dẫn kỹ thuật đầy đủ: <a href="https://github.com/{REPO}/blob/main/CONTRIBUTING.md">CONTRIBUTING.md</a>.</p>
""", "Cách đóng góp cho bản đồ hệ sinh thái khởi nghiệp Việt Nam: gửi biểu mẫu, sửa hồ sơ, thêm cơ hội, gửi logo, yêu cầu gỡ thông tin.")

# ---------- 404, sitemap, robots ----------
write("404.html", page("Không tìm thấy", f"""<div class="wrap page-head"><h1 data-vi="Không có trang này" data-en="This page does not exist">Không có trang này</h1>
<p class="lead" data-vi="Đường dẫn có thể đã đổi. Tìm trong danh bạ, hoặc quay về trang chủ." data-en="The link may have changed. Search the directory, or go back home.">Đường dẫn có thể đã đổi.</p>
<p style="margin-top:20px"><a class="btn primary" href="{SITE_ROOT}danh-ba/" data-i18n="nav_dir">Danh bạ</a></p></div>"""))
urls = [""] + [p for _, p, _ in NAV[1:]] + [f"thanh-pho/{c['id']}/" for c in (BENCH.get("cities", []) if "BENCH" in globals() else [])] + [f"a/{a['id']}/" for a in actors]
def _urlset(items):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in items) + "</urlset>\n")
groups = collections.OrderedDict([("trang", []), ("thanh-pho", []), ("linh-vuc", []), ("co-hoi", []), ("chinh-sach", []), ("to-chuc", [])])
for u, d in PAGES:
    g = "to-chuc" if u.startswith("a/") else next((k for k in ("thanh-pho", "linh-vuc", "co-hoi", "chinh-sach") if u.startswith(k + "/") and u != k + "/"), "trang")
    groups[g].append((u, d))
files = []
for g, items in groups.items():
    items.sort()
    chunks = [items[i:i + 500] for i in range(0, len(items), 500)] or []
    for k, ch in enumerate(chunks, 1):
        name = f"sitemap-{g}{'-' + str(k) if len(chunks) > 1 else ''}.xml"
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(_urlset(ch))
        files.append((name, max(d for _, d in ch)))
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"<sitemap><loc>{SITE_URL}/{n}</loc><lastmod>{d}</lastmod></sitemap>\n" for n, d in files) + "</sitemapindex>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
cname = os.path.join(ROOT, "CNAME")
if os.path.exists(cname):
    shutil.copy(cname, os.path.join(OUT, "CNAME"))
print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False))
