/* Lịch tháng kiểu Luma dùng chung: EVCAL(el, days, today)
   days: {"YYYY-MM-DD": {t: tiêu đề, s: ngày bắt đầu}}. Bấm ngày: chuyển thẻ (nếu có), cuộn tới #d-<ngày bắt đầu>. */
(function () {
  var M = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6","Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"];
  var ME = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var WDV = ["T2","T3","T4","T5","T6","T7","CN"], WDE = ["Mo","Tu","We","Th","Fr","Sa","Su"];
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  window.EVCAL = function (box, EV, TODAY) {
    if (!box) return;
    var en = function () { return window.VIE && VIE.lang && VIE.lang() === "en"; };
    var keys = Object.keys(EV).sort(), next = keys.filter(function (k) { return k >= TODAY; })[0] || keys[keys.length - 1] || TODAY;
    var cur = new Date(next + "T00:00:00"); cur.setDate(1);
    function go(k) {
      var info = EV[k]; if (!info) return;
      var scope = document, target = document.getElementById("d-" + info.s);
      var pane = target && target.closest(".ev-pane");
      var tabs = document.querySelectorAll(".ev-tabs [data-tab]");
      if (tabs.length) {
        var want = pane ? pane.dataset.pane : (info.s >= TODAY ? "up" : "past");
        var t = document.querySelector('.ev-tabs [data-tab="' + want + '"]'); if (t) t.click();
        document.querySelectorAll('.ev-filter .chip[data-v=""]').forEach(function (c) { c.click(); });
        target = document.querySelector('.ev-pane[data-pane="' + want + '"] #d-' + info.s) || target;
      }
      if (target) { target.scrollIntoView({ behavior: "smooth", block: "start" }); target.classList.add("flash"); setTimeout(function () { target.classList.remove("flash"); }, 1600); }
    }
    function draw() {
      var y = cur.getFullYear(), m = cur.getMonth(), first = (new Date(y, m, 1).getDay() + 6) % 7, days = new Date(y, m + 1, 0).getDate();
      var h = '<div class="evcal-h"><button type="button" class="evcal-nav" data-d="-1" aria-label="Tháng trước">‹</button><b>' + (en() ? ME[m] : M[m]) + " " + y + '</b><button type="button" class="evcal-nav" data-d="1" aria-label="Tháng sau">›</button></div><div class="evcal-g">';
      (en() ? WDE : WDV).forEach(function (w) { h += '<span class="evcal-w">' + w + "</span>"; });
      for (var i = 0; i < first; i++) h += "<span></span>";
      for (var d = 1; d <= days; d++) {
        var k = y + "-" + pad(m + 1) + "-" + pad(d), info = EV[k], cls = "evcal-d" + (k === TODAY ? " today" : "") + (info ? " has" : "");
        h += info ? '<button type="button" class="' + cls + '" data-k="' + k + '" title="' + info.t.replace(/"/g, "&quot;") + '">' + d + "<i></i></button>" : '<span class="' + cls + '">' + d + "</span>";
      }
      var cnt = keys.filter(function (k) { return k.slice(0, 7) === y + "-" + pad(m + 1); }).length;
      h += '</div><p class="evcal-c small muted">' + (cnt ? (en() ? cnt + " day(s) with events" : cnt + " ngày có sự kiện") : (en() ? "No events this month" : "Không có sự kiện trong tháng")) + "</p>";
      box.innerHTML = h;
      box.querySelectorAll(".evcal-nav").forEach(function (b) { b.onclick = function () { cur.setMonth(cur.getMonth() + (+b.dataset.d)); draw(); }; });
      box.querySelectorAll(".evcal-d.has").forEach(function (b) { b.onclick = function () { go(b.dataset.k); }; });
    }
    draw(); document.addEventListener("vie:lang", draw);
  };
})();
