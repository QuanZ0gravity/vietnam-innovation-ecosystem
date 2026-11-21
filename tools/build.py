"""Dựng trang tĩnh và dữ liệu xuất bản vào site/. Chạy: python tools/build.py

Biến môi trường:
  SITE_ROOT  đường dẫn gốc của trang (mặc định "/")
  SITE_URL   địa chỉ đầy đủ để tạo sitemap (mặc định https://innovation.invietnam.vn)
"""
import collections, csv, datetime, glob, html, json, os, shutil, urllib.parse
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
actors, relations, events, policies, places, refs, mentions = [], [], [], [], [], {}, []
for region_dir in sorted(glob.glob(os.path.join(ROOT, "data", "*"))):
    if not os.path.isdir(region_dir):
        continue
    region = os.path.basename(region_dir)
    for path in sorted(glob.glob(os.path.join(region_dir, "actors", "*.yaml"))):
        a = yaml.safe_load(open(path, encoding="utf-8"))
        a["_file"] = os.path.relpath(path, ROOT).replace(os.sep, "/")
        actors.append(a)
    for name, bucket in (("events.yaml", events), ("policies.yaml", policies), ("places.yaml", places)):
        p = os.path.join(region_dir, name)
        if os.path.exists(p):
            for item in yaml.safe_load(open(p, encoding="utf-8")) or []:
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
    if r["from"] in by_id and r["to"] in by_id:
        related[r["from"]].add(r["to"]); related[r["to"]].add(r["from"])
mentioned = collections.defaultdict(list)
for m in mentions:
    if m["reference"] in refs:
        mentioned[m["actor"]].append(refs[m["reference"]])
events.sort(key=lambda x: str(x.get("date") or ""))
policies.sort(key=lambda x: str(x.get("issued") or ""), reverse=True)

# ---------- khung trang ----------
NAV = [("home", "", "nav_home"), ("dir", "danh-ba/", "nav_dir"), ("map", "ban-do/", "nav_map"),
       ("events", "su-kien/", "nav_events"), ("policy", "chinh-sach/", "nav_policy")]
CUR = ' aria-current="page"'
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
<meta name="description" content="{e(desc or 'Danh bạ mở về startup, vườn ươm, quỹ, không gian sáng tạo và chính sách khởi nghiệp đổi mới sáng tạo Việt Nam, bắt đầu từ Đà Nẵng.')}">
<meta property="og:title" content="{e(full_title)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=swap">
<link rel="stylesheet" href="{SITE_ROOT}assets/style.css">
<link rel="icon" href="{SITE_ROOT}assets/favicon.svg" type="image/svg+xml">
{head}
<script src="{SITE_ROOT}assets/app.js"></script>{sc}
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
<a href="https://github.com/{REPO}" data-i18n="foot_src">Mã nguồn và dữ liệu trên GitHub</a></div></footer>
</body>
</html>
"""

def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(content)

def ver_badge(level):
    return f'<span class="ver {VER_CLASS.get(level, "l0")}"><i aria-hidden="true"></i><span data-i18n="v_{level}">{level}</span></span>'

def type_tag(t):
    return f'<span class="tag" data-i18n="t_{t}">{t}</span>'

def dir_link(**params):
    return f"{SITE_ROOT}danh-ba/?" + urllib.parse.urlencode(params)

# ---------- làm sạch thư mục xuất ----------
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
shutil.copytree(os.path.join(WEB, "assets"), os.path.join(OUT, "assets"))
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

# ---------- dữ liệu xuất bản ----------
def dump(name, obj):
    json.dump(obj, open(os.path.join(OUT, "data", name), "w", encoding="utf-8"), ensure_ascii=False)

public = [{k: v for k, v in a.items() if not k.startswith("_")} for a in actors]
dump("actors.json", public)
dump("relations.json", relations)
dump("events.json", events)
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
         "relations": len(relations), "events": len(events), "policies": len(policies), "mapped": len(features),
         "built": TODAY}
dump("stats.json", stats)

# ---------- trang chủ ----------
def n_of(types):
    return sum(counts.get(t, 0) for t in types)

NEEDS = [
    ("Tôi có một ý tưởng và cần nơi bắt đầu", "I have an idea and need a place to start",
     "Vườn ươm, không gian đổi mới sáng tạo, tổ chức hỗ trợ và chương trình tăng tốc.",
     "Incubators, innovation spaces, support organisations and accelerators.",
     ["incubator", "space", "support_org", "accelerator", "community"]),
    ("Tôi cần vốn", "I need funding",
     "Quỹ đầu tư, nhà đầu tư thiên thần và quỹ nhà nước đang có mặt tại Đà Nẵng.",
     "Venture funds, angel investors and public funds active in Da Nang.", ["fund"]),
    ("Tôi tìm đối tác, khách hàng thử nghiệm", "I am looking for partners and pilot customers",
     "Startup, doanh nghiệp và đối tác quốc tế trong hệ sinh thái.",
     "Startups, companies and international partners in the ecosystem.", ["startup", "company", "international"]),
    ("Tôi làm nghiên cứu, đào tạo hoặc chính sách", "I work in research, education or policy",
     "Viện, trường và cơ quan nhà nước; xem thêm danh mục chính sách.",
     "Universities, institutes and government bodies; see also the policy list.", ["university", "government"]),
    ("Tôi muốn xem các dự án sáng tạo xứ Quảng", "I want to see Quang Nam creative projects",
     "Dự án từ chương trình Bản lĩnh xứ Quảng ở khu vực Quảng Nam cũ.",
     "Projects from the Ban linh xu Quang programme in the former Quang Nam area.", ["creator"]),
]
needs_html = "".join(
    f'<a class="need" href="{dir_link(type=",".join(ts))}"><span class="q" data-vi="{e(q)}" data-en="{e(qe)}">{e(q)}</span>'
    f'<span class="a" data-vi="{e(d)}" data-en="{e(de)}">{e(d)}</span><span class="n">{n_of(ts)}</span></a>'
    for q, qe, d, de, ts in NEEDS)
up = [x for x in events if str(x.get("date") or "") >= TODAY][:4] or events[-4:]
ev_html = "".join(
    f'<li data-date="{e(x.get("date"))}"><span class="date">{e(fmt_date(x.get("date")))}</span><br>'
    + (f'<a href="{e(x["url"])}">{e(x["name"])}</a>' if x.get("url") else e(x["name"]))
    + (f'<br><span class="muted small">{e(x.get("organizer"))}</span>' if x.get("organizer") else "") + "</li>"
    for x in up)
po_html = "".join(
    f'<li><b>{e(x["document"])}</b><br><span class="muted">{e(x.get("summary"))}</span></li>' for x in policies[:5])
verified = sum(1 for a in actors if a["verification"]["level"] != "unverified")
home = f"""
<section class="hero"><div class="wrap">
<h1 data-vi="Ai đang làm gì cho khởi nghiệp ở Đà Nẵng?" data-en="Who is doing what for startups in Da Nang?">Ai đang làm gì cho khởi nghiệp ở Đà Nẵng?</h1>
<p class="lead" data-vi="Danh bạ mở về hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam, do cộng đồng cùng cập nhật. Bắt đầu từ Đà Nẵng và khu vực Quảng Nam cũ." data-en="An open, community-maintained directory of Vietnam's startup and innovation ecosystem. It starts with Da Nang and the former Quang Nam area.">Danh bạ mở về hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam, do cộng đồng cùng cập nhật. Bắt đầu từ Đà Nẵng và khu vực Quảng Nam cũ.</p>
<form class="search" action="{SITE_ROOT}danh-ba/" role="search">
<label class="sr" for="hq" data-i18n="search_ph">Tìm</label>
<input id="hq" name="q" type="search" data-i18n-ph="search_ph" placeholder="Tìm tổ chức, startup, quỹ…">
<button class="btn primary" type="submit" data-i18n="search_btn">Tìm</button>
</form>
<p class="census" data-vi="Hiện có {len(actors)} tổ chức và dự án, {len(policies)} văn bản chính sách và {len(events)} sự kiện. {verified} hồ sơ đã được đối chiếu với nguồn; phần còn lại đang chờ cộng đồng xác minh." data-en="The directory holds {len(actors)} organisations and projects, {len(policies)} policy documents and {len(events)} events. {verified} profiles have been checked against a source; the rest are waiting for the community to verify them.">Hiện có <b>{len(actors)}</b> tổ chức và dự án, <b>{len(policies)}</b> văn bản chính sách và <b>{len(events)}</b> sự kiện.</p>
</div></section>
<section class="needs"><div class="wrap">
<h2 class="sr">Bắt đầu từ việc bạn cần</h2>
{needs_html}
</div></section>
<section class="band"><div class="wrap split">
<div><h2 data-i18n="upcoming">Sắp diễn ra</h2><ul class="list-plain">{ev_html}</ul>
<p style="margin-top:16px"><a href="{SITE_ROOT}su-kien/" data-i18n="all_events">Tất cả sự kiện</a></p></div>
<div><h2 data-vi="Chính sách mới ban hành" data-en="Recently issued policies">Chính sách mới ban hành</h2><ul class="list-plain">{po_html}</ul>
<p style="margin-top:16px"><a href="{SITE_ROOT}chinh-sach/" data-i18n="all_policies">Tất cả chính sách</a></p></div>
</div></section>
<section><div class="wrap" style="padding:56px 24px 72px">
<h2 data-vi="Thấy thiếu hoặc sai?" data-en="Something missing or wrong?">Thấy thiếu hoặc sai?</h2>
<p class="lead" style="margin-top:12px" data-vi="Mỗi hồ sơ có nút đề xuất sửa. Tổ chức của bạn chưa có trong danh bạ? Gửi thông tin qua biểu mẫu, không cần biết Git." data-en="Every profile has a suggest-an-edit button. Not listed yet? Send your details through a form, no Git needed.">Mỗi hồ sơ có nút đề xuất sửa. Tổ chức của bạn chưa có trong danh bạ? Gửi thông tin qua biểu mẫu, không cần biết Git.</p>
<p style="margin-top:20px"><a class="btn primary" href="https://github.com/{REPO}/issues/new?template=them-hoac-sua-ho-so.yml" data-i18n="add_missing">Thêm hồ sơ còn thiếu</a></p>
</div></section>
"""
write("index.html", page("", home, "home"))

# ---------- danh bạ ----------
static_rows = "".join(
    f'<li><a href="{SITE_ROOT}a/{a["id"]}/"><span class="nm">{e(a["name"]["vi"])}</span>'
    f'{type_tag(a["type"])}{ver_badge(a["verification"]["level"])}</a></li>'
    for a in sorted(actors, key=lambda x: x["name"]["vi"].lower()))
dir_body = f"""
<div class="wrap page-head"><h1 data-i18n="nav_dir">Danh bạ</h1>
<p class="lead" data-vi="Lọc theo loại, khu vực và mức xác minh. Đường dẫn trên thanh địa chỉ giữ nguyên bộ lọc, gửi cho người khác là họ thấy đúng kết quả này." data-en="Filter by type, area and verification. The address bar keeps your filters, so a shared link shows the same results.">Lọc theo loại, khu vực và mức xác minh.</p></div>
<div class="wrap dir">
<aside class="filters" aria-label="Bộ lọc"><details open><summary data-i18n="f_filters">Bộ lọc</summary>
<fieldset id="f-type"><legend data-i18n="f_type">Loại</legend></fieldset>
<fieldset id="f-region"><legend data-i18n="f_region">Khu vực</legend></fieldset>
<fieldset id="f-ver"><legend data-i18n="f_ver">Mức xác minh</legend></fieldset>
<button class="btn ghost" id="clear" type="button" data-i18n="f_clear">Xoá bộ lọc</button>
</details></aside>
<section aria-live="polite">
<div class="bar">
<label class="sr" for="q" data-i18n="search_ph">Tìm</label>
<input id="q" type="search" data-i18n-ph="search_ph" placeholder="Tìm tổ chức, startup, quỹ…">
<label class="sr" for="sort">Sắp xếp</label>
<select id="sort"><option value="az" data-i18n="sort_az">Tên A–Z</option><option value="ver" data-i18n="sort_ver">Đã xác minh trước</option></select>
<div class="seg" role="group" aria-label="Kiểu hiển thị"><button type="button" id="v-list" aria-pressed="true" data-i18n="view_list">Danh sách</button><button type="button" id="v-cards" aria-pressed="false" data-i18n="view_cards">Thẻ</button></div>
</div>
<p class="count" id="count"></p>
<div id="results"><ul class="rows">{static_rows}</ul></div>
<nav class="pager" id="pager" aria-label="Phân trang"></nav>
</section></div>
"""
write("danh-ba/index.html", page("Danh bạ", dir_body, "dir", scripts=["directory.js"]))

# ---------- trang từng tác nhân ----------
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
    facts_html = "".join(f'<dt data-vi="{vi}" data-en="{en}">{vi}</dt><dd>{val}</dd>' for vi, en, val in facts)
    desc = a.get("description", {})
    desc_html = (f'<p class="desc" data-vi="{e(desc.get("vi"))}" data-en="{e(desc.get("en") or desc.get("vi"))}">{e(desc.get("vi"))}</p>'
                 if desc.get("vi") else
                 '<p class="desc muted" data-vi="Hồ sơ này chưa có mô tả. Bạn biết về tổ chức này? Đề xuất một đoạn mô tả ngắn." data-en="No description yet. Know this organisation? Suggest a short description.">Hồ sơ này chưa có mô tả.</p>')
    rel_html = ""
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
    lvl = a["verification"]["level"]
    vdate = a["verification"].get("date")
    src = "; ".join(a["sources"])
    src_html = e(src) + (f'<br><a href="{e(a["source_url"])}" rel="noopener" class="small">{e(a["source_url"])}</a>' if a.get("source_url") else "")
    issue_q = urllib.parse.urlencode({"template": "them-hoac-sua-ho-so.yml", "title": f"[Hồ sơ] {name}",
                                      "name": name, "website": a.get("website", ""), "region": "Đà Nẵng"})
    body = f"""
<div class="wrap crumbs"><a href="{SITE_ROOT}danh-ba/" data-i18n="nav_dir">Danh bạ</a> / <a href="{dir_link(type=a['type'])}" data-i18n="t_{a['type']}">{a['type']}</a></div>
<div class="wrap actor">
<article>
<p>{type_tag(a["type"])}</p>
<h1 style="margin-top:8px">{e(name)}</h1>
{f'<p class="muted" style="margin-top:6px">{e(a["name"]["en"])}</p>' if a["name"].get("en") else ""}
{desc_html}
<dl class="facts">{facts_html}</dl>
{rel_html}{men_html}
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
    write(f"a/{aid}/index.html", page(name, body, "dir", desc=(desc.get("vi") or f"{name}: hồ sơ trong danh bạ hệ sinh thái khởi nghiệp ĐMST Việt Nam.")))

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
write("ban-do/index.html", page("Bản đồ", map_body, "map", scripts=["map.js"], head=leaf))

# ---------- sự kiện ----------
def ev_month_sections(items, newest_first):
    groups = collections.OrderedDict()
    for x in sorted(items, key=lambda x: str(x.get("date") or ""), reverse=newest_first):
        groups.setdefault(str(x.get("date") or "")[:7], []).append(x)
    return "".join(
        f'<section class="month"><h3 style="font-size:1.15rem;padding-bottom:8px;border-bottom:1.5px solid var(--ink)">{e(m[5:7])}/{e(m[:4])}</h3><ul class="timeline">' + "".join(
            f'<li class="ev" data-date="{e(x.get("date"))}"><span class="d">{e(str(x.get("date"))[8:10])}</span><div>'
            f'<h3>' + (f'<a href="{e(x["url"])}" rel="noopener">{e(x["name"])}</a>' if x.get("url") else e(x["name"])) + '</h3>'
            + (f'<p class="muted">{e(x.get("summary"))}</p>' if x.get("summary") else "")
            + (f'<p class="small muted"><span data-i18n="organizer">Đơn vị tổ chức</span>: {e(x.get("organizer"))}</p>' if x.get("organizer") else "")
            + '</div></li>' for x in xs) + '</ul></section>'
        for m, xs in groups.items())
upcoming = [x for x in events if str(x.get("date") or "") >= TODAY]
past = [x for x in events if str(x.get("date") or "") < TODAY]
ev_body = (f'<h2 style="margin-top:8px" data-i18n="upcoming">Sắp diễn ra</h2>' + (ev_month_sections(upcoming, False) or '<p class="muted" style="margin-top:12px" data-vi="Chưa có sự kiện sắp tới trong danh sách." data-en="No upcoming events listed yet.">Chưa có sự kiện sắp tới trong danh sách.</p>')
           + f'<h2 style="margin-top:56px" data-i18n="past">Đã diễn ra</h2>' + ev_month_sections(past, True))
ev_script = """<script>document.addEventListener('DOMContentLoaded',function(){var t=new Date().toISOString().slice(0,10);
document.querySelectorAll('.ev').forEach(function(li){if((li.getAttribute('data-date')||'')<t)li.classList.add('past')});});</script>"""
write("su-kien/index.html", page("Sự kiện", f"""
<div class="wrap page-head"><h1 data-i18n="nav_events">Sự kiện</h1>
<p class="lead" data-vi="Sự kiện khởi nghiệp đổi mới sáng tạo tại Đà Nẵng và trong khu vực. Thiếu sự kiện của bạn? Thêm qua GitHub." data-en="Startup and innovation events in and around Da Nang. Missing yours? Add it on GitHub.">Sự kiện khởi nghiệp đổi mới sáng tạo tại Đà Nẵng và trong khu vực.</p></div>
<div class="wrap" style="padding-bottom:72px">{ev_body}</div>{ev_script}""", "events"))

# ---------- chính sách ----------
by_year = collections.OrderedDict()
for x in policies:
    by_year.setdefault(str(x.get("issued") or "")[:4] or "Khác", []).append(x)
po_body = "".join(
    f'<section class="month" data-year="{e(y)}"><h2>{e(y)}</h2><ul class="list-plain">' + "".join(
        f'<li class="po" data-text="{e((x["document"] + " " + str(x.get("summary") or "")).lower())}">'
        + (f'<a href="{e(x["url"])}" rel="noopener"><b>{e(x["document"])}</b></a>' if x.get("url") else f'<b>{e(x["document"])}</b>')
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
<div class="wrap" style="padding-bottom:72px">{po_body}</div>{po_script}""", "policy"))

# ---------- 404, sitemap, robots ----------
write("404.html", page("Không tìm thấy", f"""<div class="wrap page-head"><h1 data-vi="Không có trang này" data-en="This page does not exist">Không có trang này</h1>
<p class="lead" data-vi="Đường dẫn có thể đã đổi. Tìm trong danh bạ, hoặc quay về trang chủ." data-en="The link may have changed. Search the directory, or go back home.">Đường dẫn có thể đã đổi.</p>
<p style="margin-top:20px"><a class="btn primary" href="{SITE_ROOT}danh-ba/" data-i18n="nav_dir">Danh bạ</a></p></div>"""))
urls = [""] + [p for _, p, _ in NAV[1:]] + [f"a/{a['id']}/" for a in actors]
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
cname = os.path.join(ROOT, "CNAME")
if os.path.exists(cname):
    shutil.copy(cname, os.path.join(OUT, "CNAME"))
print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False))
