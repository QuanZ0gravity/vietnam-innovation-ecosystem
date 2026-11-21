/* Danh bạ: lọc, tìm, sắp xếp, phân trang; trạng thái lưu trên đường dẫn */
(function () {
  var PER = 30, all = [], st = { q: "", type: [], region: [], ver: [], status: [], sort: "az", view: "list", page: 1 };
  var TYPES = ["startup", "fund", "incubator", "accelerator", "space", "support_org", "university", "government", "company", "international", "community", "media", "creator"];
  var REGIONS = ["da-nang", "former-quang-nam", "ha-noi", "ho-chi-minh", "viet-nam", "quoc-te"];
  var VERS = ["partner_verified", "org_confirmed", "source_checked", "unverified"];
  var STATUSES = ["active", "inactive", "unknown"];
  var $ = function (id) { return document.getElementById(id); };
  var norm = function (s) { return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase(); };

  function readURL() {
    var p = new URLSearchParams(location.search);
    st.q = p.get("q") || "";
    ["type", "region", "ver", "status"].forEach(function (k) { st[k] = (p.get(k) || "").split(",").filter(Boolean); });
    st.sort = p.get("sort") || "az"; st.view = p.get("view") || "list"; st.page = +p.get("page") || 1;
  }
  function writeURL() {
    var p = new URLSearchParams();
    if (st.q) p.set("q", st.q);
    ["type", "region", "ver", "status"].forEach(function (k) { if (st[k].length) p.set(k, st[k].join(",")); });
    if (st.sort !== "az") p.set("sort", st.sort);
    if (st.view !== "list") p.set("view", st.view);
    if (st.page > 1) p.set("page", st.page);
    var s = p.toString(); history.replaceState(null, "", location.pathname + (s ? "?" + s : ""));
  }
  function matches(a, skip) {
    if (st.q) { var q = norm(st.q); if (norm(a.name.vi).indexOf(q) < 0 && norm(a.name.en).indexOf(q) < 0 && norm((a.categories || []).join(" ")).indexOf(q) < 0) return false; }
    if (skip !== "type" && st.type.length && st.type.indexOf(a.type) < 0) return false;
    if (skip !== "region" && st.region.length && st.region.indexOf(a.region) < 0) return false;
    if (skip !== "ver" && st.ver.length && st.ver.indexOf(a.verification.level) < 0) return false;
    if (skip !== "status" && st.status.length && st.status.indexOf(a.status || "unknown") < 0) return false;
    return true;
  }
  function facet(id, key, values, label) {
    var fs = $(id); fs.querySelectorAll(".check").forEach(function (n) { n.remove(); });
    var base = all.filter(function (a) { return matches(a, key); });
    values.forEach(function (v) {
      var n = base.filter(function (a) { return (key === "ver" ? a.verification.level : key === "status" ? (a.status || "unknown") : a[key]) === v; }).length;
      if (!n && st[key].indexOf(v) < 0) return;
      var lb = VIE.el("label", "check"), cb = document.createElement("input");
      cb.type = "checkbox"; cb.checked = st[key].indexOf(v) >= 0;
      cb.addEventListener("change", function () {
        st[key] = cb.checked ? st[key].concat(v) : st[key].filter(function (x) { return x !== v; });
        st.page = 1; render();
      });
      lb.append(cb, VIE.el("span", null, label(v)), VIE.el("span", "c", String(n)));
      fs.append(lb);
    });
  }
  function verBadge(level) {
    var s = VIE.el("span", "ver " + VIE.verClass(level)), i = document.createElement("i");
    i.setAttribute("aria-hidden", "true"); s.append(i, VIE.el("span", null, VIE.verLabel(level))); return s;
  }
  function render() {
    writeURL();
    facet("f-type", "type", TYPES, VIE.typeLabel);
    facet("f-region", "region", REGIONS, VIE.regionLabel);
    facet("f-ver", "ver", VERS, VIE.verLabel);
    facet("f-status", "status", STATUSES, function (x) { return VIE.t("s_" + x); });
    var list = all.filter(function (a) { return matches(a); });
    var collator = new Intl.Collator(VIE.lang() === "en" ? "en" : "vi");
    list.sort(function (a, b) {
      if (st.sort === "ver") { var d = VERS.indexOf(a.verification.level) - VERS.indexOf(b.verification.level); if (d) return d; }
      return collator.compare(VIE.name(a), VIE.name(b));
    });
    var pages = Math.max(1, Math.ceil(list.length / PER));
    if (st.page > pages) st.page = pages;
    $("count").textContent = VIE.t("results", { n: list.length });
    var box = $("results"); box.replaceChildren();
    if (!list.length) {
      var em = VIE.el("div", "empty"); em.append(VIE.el("p", null, VIE.t("none")));
      var a = VIE.el("a", "btn primary", VIE.t("add_missing"));
      a.href = "https://github.com/chuongnv/vietnam-innovation-ecosystem/issues/new?template=them-hoac-sua-ho-so.yml";
      a.style.marginTop = "16px"; em.append(a); box.append(em);
    } else {
      var wrap = st.view === "cards" ? VIE.el("div", "cards") : VIE.el("ul", "rows");
      list.slice((st.page - 1) * PER, st.page * PER).forEach(function (x) {
        var link = VIE.el("a", st.view === "cards" ? "card" : null); link.href = VIE.root + "a/" + x.id + "/";
        link.append(VIE.el("span", "nm", VIE.name(x)), VIE.el("span", "tag", VIE.typeLabel(x.type)), verBadge(x.verification.level));
        if (st.view === "cards") { wrap.append(link); } else { var li = document.createElement("li"); li.append(link); wrap.append(li); }
      });
      box.append(wrap);
    }
    var pg = $("pager"); pg.replaceChildren();
    if (pages > 1) {
      var prev = VIE.el("button", "btn ghost", VIE.t("prev")); prev.type = "button"; prev.disabled = st.page === 1;
      prev.onclick = function () { st.page--; render(); scrollTo(0, 0); };
      var next = VIE.el("button", "btn ghost", VIE.t("next")); next.type = "button"; next.disabled = st.page === pages;
      next.onclick = function () { st.page++; render(); scrollTo(0, 0); };
      pg.append(prev, VIE.el("span", "muted", VIE.t("page", { p: st.page, t: pages })), next);
    }
    $("v-list").setAttribute("aria-pressed", st.view === "list"); $("v-cards").setAttribute("aria-pressed", st.view === "cards");
    $("sort").value = st.sort;
  }
  document.addEventListener("DOMContentLoaded", function () {
    readURL();
    $("q").value = st.q;
    var timer;
    $("q").addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { st.q = $("q").value.trim(); st.page = 1; render(); }, 150); });
    $("sort").addEventListener("change", function () { st.sort = $("sort").value; render(); });
    $("v-list").addEventListener("click", function () { st.view = "list"; render(); });
    $("v-cards").addEventListener("click", function () { st.view = "cards"; render(); });
    $("clear").addEventListener("click", function () { st.type = []; st.region = []; st.ver = []; st.status = []; st.q = ""; $("q").value = ""; st.page = 1; render(); });
    if (window.matchMedia("(max-width:860px)").matches) document.querySelector(".filters details").removeAttribute("open");
    VIE.load("actors.json").then(function (d) { all = d; render(); document.addEventListener("vie:lang", render); })
      .catch(function () { $("count").textContent = ""; });
  });
})();
