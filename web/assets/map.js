/* Bản đồ: các hồ sơ có tọa độ, theo địa chỉ hoặc theo phường, xã */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    Promise.all([VIE.load("actors.geojson"), VIE.load("stats.json")]).then(function (r) {
      var geo = r[0], stats = r[1];
      var note = document.getElementById("map-note");
      var setNote = function () { note.textContent = VIE.t("map_note", { a: geo.features.length, b: stats.actors }); };
      setNote(); document.addEventListener("vie:lang", setNote);
      var map = L.map("map", { scrollWheelZoom: false }).setView([15.8, 108.2], 9);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      }).addTo(map);
      var css = getComputedStyle(document.documentElement);
      var sea = css.getPropertyValue("--sea").trim() || "#0B6E69", sun = css.getPropertyValue("--sun").trim() || "#E9A800";
      var bounds = [], list = document.getElementById("map-list");
      geo.features.forEach(function (f) {
        var c = f.geometry.coordinates, p = f.properties, ll = [c[1], c[0]];
        var m = L.circleMarker(ll, { radius: p.precision === "ward" ? 7 : 9, weight: 2, color: "#102A2C",
          fillColor: p.precision === "ward" ? sun : sea, fillOpacity: .9 }).addTo(map);
        var div = document.createElement("div"), a = document.createElement("a");
        a.href = VIE.root + "a/" + p.id + "/"; a.textContent = p.name;
        div.append(a, document.createElement("br"), VIE.el("span", "muted", VIE.typeLabel(p.type) + (p.precision === "ward" ? " (" + VIE.t("by_ward") + ")" : "")));
        m.bindPopup(div); bounds.push(ll);
        var li = document.createElement("li"), b = document.createElement("button");
        b.type = "button";
        b.textContent = p.name; b.onclick = function () { map.setView(ll, 15); m.openPopup(); };
        li.append(b); list.append(li);
      });
      if (bounds.length) map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
    });
  });
})();
