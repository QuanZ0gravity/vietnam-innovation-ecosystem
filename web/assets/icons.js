/* Bộ biểu tượng nét 24px (tự vẽ, cùng phong cách), dùng cho loại tác nhân và lĩnh vực */
(function () {
  var P = {
    all: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    startup: '<path d="M5 15c-1.5 1.5-2 4-2 6 2 0 4.5-.5 6-2"/><path d="M9 15l-3-3c1.5-4 5-9 12-9 0 7-5 10.5-9 12z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    fund: '<ellipse cx="9" cy="6" rx="6" ry="2.5"/><path d="M3 6v5c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5V6"/><path d="M3 11v5c0 1.4 2.7 2.5 6 2.5 1 0 2-.1 2.8-.3"/><circle cx="17" cy="16" r="4"/>',
    incubator: '<path d="M12 21v-8"/><path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z"/><path d="M12 15c0-3-2.5-5-6-5 0 3 2.5 5 6 5z"/><path d="M7 21h10"/>',
    accelerator: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    space: '<path d="M4 21V5l8-3 8 3v16"/><path d="M9 21v-5h6v5"/><path d="M8 8h1M12 8h1M16 8h-1M8 12h1M12 12h1M15 12h1"/>',
    support_org: '<path d="M11 17l-2 2a2.8 2.8 0 0 1-4-4l4-4a2.8 2.8 0 0 1 4 0"/><path d="M13 7l2-2a2.8 2.8 0 0 1 4 4l-4 4a2.8 2.8 0 0 1-4 0"/>',
    university: '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/><path d="M22 9v6"/>',
    government: '<path d="M3 21h18M4 10h16M12 3l9 5H3z"/><path d="M6 10v8M10 10v8M14 10v8M18 10v8"/>',
    company: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
    international: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    community: '<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><path d="M15 14.5c3 0 6 2 6 5.5"/>',
    media: '<path d="M3 11v2a1 1 0 0 0 1 1h3l6 5V5L7 10H4a1 1 0 0 0-1 1z"/><path d="M17 8a5 5 0 0 1 0 8"/>',
    creator: '<path d="M12 3l1.8 4.7L18.5 9.5 13.8 11.3 12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    ai: '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    fintech: '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M2 10h20"/><path d="M16 15h2"/>',
    web3: '<path d="M12 2l8 4.5v9L12 20l-8-4.5v-9z"/><path d="M12 11l8-4.5M12 11v9M12 11 4 6.5"/>',
    commerce: '<path d="M3 4h2l2.5 11h11L21 7H6.2"/><circle cx="9" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/>',
    agrifood: '<path d="M11 20c-4 0-7-3-7-8 5 0 8 3 8 8"/><path d="M12 20V10"/><path d="M12 13c0-5 3-8 8-8 0 6-3 8-8 8z"/>',
    health: '<path d="M20.8 6.6a5 5 0 0 0-8.8-2.4 5 5 0 0 0-8.8 2.4C2.4 11.6 12 20 12 20s9.6-8.4 8.8-13.4z"/><path d="M6 12h3l1.5-2.5 2 5L14 12h4"/>',
    edu: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20"/>',
    tourism: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    climate: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    deeptech: '<path d="M9 3v4M15 3v4M9 17v4M15 17v4"/><rect x="5" y="7" width="14" height="10" rx="2"/><path d="M9 11h6M9 13h3"/>',
    mobility: '<path d="M3 16V7a1 1 0 0 1 1-1h10v10"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="17.5" r="2"/><circle cx="17" cy="17.5" r="2"/>',
    marketing: '<path d="M4 19V5"/><path d="M4 19h16"/><path d="M8 15l3-4 3 2 5-6"/>',
    property: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    expert: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/><path d="M15.5 3.5l1 1.5 1.8.3-1.3 1.2.3 1.8-1.8-.9"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    pin: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    repeat: '<path d="M17 2l3 3-3 3"/><path d="M4 11V9a4 4 0 0 1 4-4h12"/><path d="M7 22l-3-3 3-3"/><path d="M20 13v2a4 4 0 0 1-4 4H4"/>',
    other: '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    filter: '<path d="M3 5h18M6 12h12M10 19h4"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>'
  };
  window.ICON = function (k, size) {
    var s = size || 18;
    return '<svg class="ico" width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (P[k] || P.other) + '</svg>';
  };
})();
