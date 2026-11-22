/* Bản đồ dùng chung: VIEMAP.render(phần tử, danh sách id được phép hoặc null) */
(function () {
  var geoP = null;
  function geo() { return geoP || (geoP = VIE.load("actors.geojson")); }
  window.VIEMAP = {
    render: function (el, ids, note) {
      return geo().then(function (g) {
        if (!window.L) { el.textContent = ""; return 0; }
        var allow = ids ? new Set(ids) : null;
        var feats = g.features.filter(function (f) { return !allow || allow.has(f.properties.id); });
        if (!el._map) {
          el._map = L.map(el, { scrollWheelZoom: false }).setView([16.0, 108.2], 6);
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(el._map);
          el._layer = L.layerGroup().addTo(el._map);
        }
        var map = el._map; el._layer.clearLayers();
        var css = getComputedStyle(document.documentElement);
        var sea = css.getPropertyValue("--sea").trim() || "#0B6E69", sun = css.getPropertyValue("--sun").trim() || "#E9A800";
        var b = [];
        feats.forEach(function (f) {
          var c = f.geometry.coordinates, p = f.properties, ll = [c[1], c[0]];
          var m = L.circleMarker(ll, { radius: p.precision === "ward" ? 7 : 9, weight: 2, color: "#102A2C", fillColor: p.precision === "ward" ? sun : sea, fillOpacity: .9 });
          var d = document.createElement("div"), a = document.createElement("a"); a.href = VIE.root + (p.url || ("to-chuc/" + p.id + "/")); a.textContent = p.name;
          d.append(a, document.createElement("br"), VIE.el("span", "muted", VIE.typeLabel(p.type) + (p.precision === "ward" ? " (" + VIE.t("by_ward") + ")" : "")));
          m.bindPopup(d); m.addTo(el._layer); b.push(ll);
        });
        setTimeout(function () { map.invalidateSize(); if (b.length) map.fitBounds(b, { padding: [40, 40], maxZoom: 13 }); }, 50);
        if (note) note.textContent = VIE.lang() === "en"
          ? feats.length + " of " + (ids ? ids.length : g.features.length) + " results have a location. Add an address to a profile to put it on the map."
          : feats.length + " trên " + (ids ? ids.length : g.features.length) + " kết quả có vị trí. Bổ sung địa chỉ vào hồ sơ để hiện trên bản đồ.";
        return feats.length;
      });
    }
  };
})();
