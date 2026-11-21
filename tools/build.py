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
NAV = [("home", "", "nav_home"), ("dir", "danh-ba/", "nav_dir"), ("map", "ban-do/", "nav_map"),
       ("cities", "thanh-pho/", "nav_cities"), ("opps", "co-hoi/", "nav_opps"), ("policy", "chinh-sach/", "nav_policy")]
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
            f'<h3>{e(o["title"])}</h3><p class="small muted">{org}</p><p class="opp-dates small">{date_html}</p>'
            + (f'<dl class="facts opp-facts">{rows_html}</dl>' if rows_html else "")
            + (f'<p class="opp-links">{"".join(links)}</p>' if links and not compact else "") + miss_html + '</article>')

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
ranked = sorted(opps, key=lambda o: ({"open": 0, "upcoming": 1, "closed": 2}[opp_status(o)], opp_key_date(o) if opp_status(o) != "closed" else "~" + "".join(chr(255 - ord(c)) for c in opp_key_date(o))))
home_opps = "".join(opp_card(o, compact=True) for o in ranked[:4])
n_open = sum(1 for o in opps if opp_status(o) == "open")
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
<p class="census" data-vi="Hiện có {len(actors)} tổ chức và dự án, {len(policies)} văn bản chính sách và {len(opps)} cơ hội gọi vốn, thi đấu, ươm tạo. {verified} hồ sơ đã được đối chiếu với nguồn; phần còn lại đang chờ cộng đồng xác minh." data-en="The directory holds {len(actors)} organisations and projects, {len(policies)} policy documents and {len(opps)} funding, competition and programme opportunities. {verified} profiles have been checked against a source; the rest are waiting for the community to verify them.">Hiện có <b>{len(actors)}</b> tổ chức và dự án, <b>{len(policies)}</b> văn bản chính sách và <b>{len(opps)}</b> cơ hội.</p>
</div></section>
<section class="needs"><div class="wrap">
<h2 class="sr">Bắt đầu từ việc bạn cần</h2>
{needs_html}
</div></section>
<section class="band"><div class="wrap split">
<div><h2 data-vi="Cơ hội gọi vốn, thi đấu, ươm tạo" data-en="Funding, competitions, programmes">Cơ hội gọi vốn, thi đấu, ươm tạo</h2>
<div class="opp-list" style="margin-top:16px">{home_opps}</div>
<p style="margin-top:16px"><a href="{SITE_ROOT}co-hoi/" data-vi="Tất cả cơ hội" data-en="All opportunities">Tất cả cơ hội</a></p></div>
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
<fieldset id="f-status"><legend data-i18n="f_status">Tình trạng</legend></fieldset>
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
{rel_html}{opp_html}{men_html}
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
<div class="wrap" style="padding-bottom:72px">{blocks}{ch_html}</div>{opp_script}""", "opps"))
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
{SB_NOTE}</div>""", "cities"))

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
            xs = sorted([a for a in acts if a["type"] == t], key=lambda a: (VER_ORDER.get(a["verification"]["level"], 9), not a.get("description"), a["name"]["vi"].lower()))
            if not xs: return '<p class="muted small" data-vi="Chưa có trong danh bạ." data-en="None listed yet.">Chưa có trong danh bạ.</p>'
            items = "".join(f'<li><a href="{SITE_ROOT}a/{a["id"]}/">{e(a["name"]["vi"])}</a></li>' for a in xs[:n])
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
<nav class="onpage small"><a href="#tong-quan" data-vi="Tổng quan" data-en="Overview">Tổng quan</a><a href="#nganh" data-vi="Ngành" data-en="Industries">Ngành</a><a href="#danh-ba" data-vi="Danh bạ" data-en="Directory">Danh bạ</a><a href="#co-hoi" data-vi="Cơ hội" data-en="Opportunities">Cơ hội</a><a href="#xep-hang" data-vi="Xếp hạng" data-en="Ranking">Xếp hạng</a></nav>
<section id="tong-quan" class="sec"><h2 data-vi="Tổng quan" data-en="Overview">Tổng quan</h2><div class="kpis">{"".join(kp)}</div>
<h3 style="margin-top:28px" data-vi="Trong danh bạ mở này" data-en="In this open directory">Trong danh bạ mở này</h3><div class="kpis">{"".join(ours)}</div></section>
<section id="nganh" class="sec"><h2 data-vi="Ngành nổi bật" data-en="Top industries">Ngành nổi bật</h2>{ind_table(c.get("industries"))}
<p class="small" style="margin-top:12px"><span class="muted" data-vi="Doanh nghiệp lớn tích cực làm việc với startup:" data-en="Corporations active with startups:">Doanh nghiệp lớn tích cực làm việc với startup:</span> {corp}</p></section>
<section id="danh-ba" class="sec"><h2 data-vi="Danh bạ" data-en="Directory">Danh bạ</h2>
<div class="cols2"><div><h3 data-vi="Startup" data-en="Startups">Startup</h3>{lst("startup")}</div>
<div><h3 data-vi="Quỹ, nhà đầu tư" data-en="Funds, investors">Quỹ, nhà đầu tư</h3>{lst("fund", 12)}
<h3 style="margin-top:20px" data-vi="Tổ chức hỗ trợ" data-en="Support organisations">Tổ chức hỗ trợ</h3>{lst("support_org", 12)}{lst("incubator", 12) if tc["incubator"] else ""}
<h3 style="margin-top:20px" data-vi="Trường, viện" data-en="Universities">Trường, viện</h3>{lst("university", 12)}</div></div></section>
<section id="co-hoi" class="sec"><h2 data-vi="Cơ hội" data-en="Opportunities">Cơ hội</h2><div class="opp-list">{opp_html}</div>
<p class="small" style="margin-top:12px"><a href="{SITE_ROOT}co-hoi/" data-vi="Tất cả cơ hội" data-en="All opportunities">Tất cả cơ hội</a></p></section>
<section id="xep-hang" class="sec"><h2 data-vi="So với các thành phố khác" data-en="Compared with other cities">So với các thành phố khác</h2>{city_table(c["id"])}
<p class="small" style="margin-top:10px"><a href="{e(c["url"])}" rel="noopener" data-vi="Trang {e(c['name'])} trên StartupBlink" data-en="{e(c['name'])} on StartupBlink">Trang {e(c["name"])} trên StartupBlink</a></p></section>
{SB_NOTE}</div>"""
        write(f"thanh-pho/{c['id']}/index.html", page(c["name"], body, "cities"))

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
urls = [""] + [p for _, p, _ in NAV[1:]] + [f"thanh-pho/{c['id']}/" for c in (BENCH.get("cities", []) if "BENCH" in globals() else [])] + [f"a/{a['id']}/" for a in actors]
open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"<url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
cname = os.path.join(ROOT, "CNAME")
if os.path.exists(cname):
    shutil.copy(cname, os.path.join(OUT, "CNAME"))
print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False))
