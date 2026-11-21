/* Dùng chung: ngôn ngữ, giao diện sáng/tối, nhãn dữ liệu */
(function () {
  var D = {
    vi: {
      nav_home: "Trang chủ", nav_dir: "Danh bạ", nav_map: "Bản đồ", nav_events: "Sự kiện", nav_policy: "Chính sách", nav_contribute: "Đóng góp",
      theme: "Đổi giao diện sáng, tối", lang: "English",
      foot_data: "Dữ liệu mở theo CC BY 4.0, mã nguồn theo MIT.", foot_src: "Mã nguồn và dữ liệu trên GitHub",
      search_ph: "Tìm tổ chức, startup, quỹ…", search_btn: "Tìm",
      f_type: "Loại", f_region: "Khu vực", f_ver: "Mức xác minh", f_filters: "Bộ lọc", f_clear: "Xoá bộ lọc",
      sort_az: "Tên A–Z", sort_ver: "Đã xác minh trước", view_list: "Danh sách", view_cards: "Thẻ",
      results: "{n} kết quả", none: "Không có kết quả khớp. Thử bỏ bớt bộ lọc, hoặc thêm hồ sơ còn thiếu.", add_missing: "Thêm hồ sơ còn thiếu",
      prev: "Trang trước", next: "Trang sau", page: "Trang {p}/{t}",
      t_startup: "Startup", t_creator: "Dự án sáng tạo xứ Quảng", t_company: "Doanh nghiệp", t_fund: "Quỹ, nhà đầu tư", t_incubator: "Vườn ươm", t_accelerator: "Chương trình tăng tốc", t_space: "Không gian ĐMST", t_university: "Viện, trường", t_government: "Cơ quan nhà nước", t_support_org: "Tổ chức hỗ trợ", t_international: "Đối tác quốc tế", t_community: "Cộng đồng", t_media: "Truyền thông",
      r_da_nang: "Đà Nẵng", r_former_quang_nam: "Khu vực Quảng Nam cũ",
      v_unverified: "Chưa xác minh", v_source_checked: "Đã đối chiếu nguồn", v_org_confirmed: "Tổ chức xác nhận", v_partner_verified: "Đối tác xác minh",
      upcoming: "Sắp diễn ra", past: "Đã diễn ra", organizer: "Đơn vị tổ chức", all_events: "Tất cả sự kiện",
      policy_search: "Tìm văn bản, nội dung…", all_policies: "Tất cả chính sách",
      map_note: "{a} trên {b} hồ sơ đã có vị trí trên bản đồ.", map_help: "Biết địa chỉ chính xác của một tổ chức? Thêm tọa độ để tổ chức đó hiện trên bản đồ.",
      no_place: "Chưa có vị trí", by_ward: "Vị trí theo phường, xã", by_addr: "Vị trí theo địa chỉ"
    },
    en: {
      nav_home: "Home", nav_dir: "Directory", nav_map: "Map", nav_events: "Events", nav_policy: "Policies", nav_contribute: "Contribute",
      theme: "Switch light or dark theme", lang: "Tiếng Việt",
      foot_data: "Open data under CC BY 4.0, code under MIT.", foot_src: "Code and data on GitHub",
      search_ph: "Search organisations, startups, funds…", search_btn: "Search",
      f_type: "Type", f_region: "Area", f_ver: "Verification", f_filters: "Filters", f_clear: "Clear filters",
      sort_az: "Name A–Z", sort_ver: "Verified first", view_list: "List", view_cards: "Cards",
      results: "{n} results", none: "Nothing matches. Remove a filter, or add the profile that is missing.", add_missing: "Add a missing profile",
      prev: "Previous", next: "Next", page: "Page {p} of {t}",
      t_startup: "Startup", t_creator: "Quang Nam creative project", t_company: "Company", t_fund: "Fund, investor", t_incubator: "Incubator", t_accelerator: "Accelerator", t_space: "Innovation space", t_university: "University, institute", t_government: "Government body", t_support_org: "Support organisation", t_international: "International partner", t_community: "Community", t_media: "Media",
      r_da_nang: "Da Nang", r_former_quang_nam: "Former Quang Nam area",
      v_unverified: "Unverified", v_source_checked: "Checked against source", v_org_confirmed: "Confirmed by organisation", v_partner_verified: "Verified by partner",
      upcoming: "Upcoming", past: "Past", organizer: "Organiser", all_events: "All events",
      policy_search: "Search documents, content…", all_policies: "All policies",
      map_note: "{a} of {b} profiles have a location on the map.", map_help: "Know an organisation's exact address? Add coordinates so it shows on the map.",
      no_place: "No location yet", by_ward: "Located by ward or commune", by_addr: "Located by address"
    }
  };
  var store = { get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
                set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
  var lang = store.get("vie-lang") || "vi";
  var theme = store.get("vie-theme");
  if (theme) document.documentElement.setAttribute("data-theme", theme);

  function t(key, vars) {
    var s = (D[lang] && D[lang][key]) || D.vi[key] || key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.replace("{" + k + "}", vars[k]); });
    return s;
  }
  function apply() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) { el.textContent = t(el.getAttribute("data-i18n")); });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) { el.placeholder = t(el.getAttribute("data-i18n-ph")); });
    document.querySelectorAll("[data-i18n-label]").forEach(function (el) { el.setAttribute("aria-label", t(el.getAttribute("data-i18n-label"))); });
    document.querySelectorAll("[data-vi]").forEach(function (el) {
      var v = el.getAttribute("data-" + lang) || el.getAttribute("data-vi"); if (v) el.textContent = v;
    });
    document.dispatchEvent(new CustomEvent("vie:lang"));
  }
  window.VIE = {
    t: t, lang: function () { return lang; },
    typeLabel: function (x) { return t("t_" + x); },
    regionLabel: function (x) { return t("r_" + String(x).replace(/-/g, "_")); },
    verLabel: function (x) { return t("v_" + x); },
    verClass: function (x) { return { unverified: "l0", source_checked: "l1", org_confirmed: "l2", partner_verified: "l3" }[x] || "l0"; },
    name: function (a) { return (lang === "en" && a.name.en) || a.name.vi; },
    root: document.documentElement.getAttribute("data-root") || "/",
    load: function (f) { return fetch((document.documentElement.getAttribute("data-root") || "/") + "data/" + f).then(function (r) { if (!r.ok) throw new Error(f); return r.json(); }); },
    el: function (tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  };
  document.addEventListener("DOMContentLoaded", function () {
    var lb = document.getElementById("lang-toggle");
    if (lb) lb.addEventListener("click", function () { lang = lang === "vi" ? "en" : "vi"; store.set("vie-lang", lang); apply(); });
    var tb = document.getElementById("theme-toggle");
    if (tb) tb.addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = cur === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next); store.set("vie-theme", next);
    });
    apply();
  });
})();
