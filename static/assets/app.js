/* v2026-11-13 */
/* vian.cz — search, listing filters (incl. width in cm), "does it fit" calculator, gallery, consent + GA4 click events. No dependencies, no tracking without consent. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var cache = {};
  function getJSON(u) {
    if (!cache[u]) cache[u] = fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
    return cache[u];
  }
  function kc(n) { return Math.round(n).toLocaleString("cs-CZ").replace(/\s/g, " ") + " Kč"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fold(s) { return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function words(q) { return fold(q).split(/[^a-z0-9]+/).filter(function (w) { return w.length > 1; }); }
  function shopsIn(n) { return n === 1 ? "v 1 obchodě" : (n < 5 ? "ve " : "v ") + n + " obchodech"; }

  /* ---------- broken shop images -> our placeholder ---------- */
  /* A shop image the browser cannot show (some shops refuse real browsers) never becomes the placeholder while another image exists:
     gallery thumbnail -> hidden; main image -> next gallery image; card -> its alternative image; placeholder only as the very last resort. */
  function viaProxy(u) { return "https://wsrv.nl/?w=480&output=webp&url=" + encodeURIComponent(u); }
  function unproxy(u) { var m = u.match(/[?&]url=([^&]+)/); return u.indexOf("wsrv.nl") >= 0 && m ? decodeURIComponent(m[1]) : u; }
  /* A shop picture the browser cannot show: 1) the other route to the same picture (resized via wsrv <-> the shop's original),
     2) the product's other pictures (gallery / alternative), 3) the box stays empty. Every address is tried at most once. */
  function fixImg(im) {
    if (im.tagName !== "IMG" || !im.src || im.src.indexOf(location.host) >= 0) return;
    var t = im._t = im._t || {}, cur = im.currentSrc || im.src, orig = unproxy(cur);
    t[(cur.indexOf("wsrv.nl") >= 0 ? "p:" : "d:") + orig] = 1;       /* most pictures arrive resized through wsrv: the original is the fallback */
    if (!t["d:" + orig]) { t["d:" + orig] = 1; im.src = orig; return; }
    if (!t["p:" + orig]) { t["p:" + orig] = 1; im.src = viaProxy(orig); return; }
    var th = im.closest ? im.closest(".thumbs button") : null;
    if (th) { th.dataset.bad = "1"; th.hidden = true; var left = $$(".thumbs button").filter(function (b) { return !b.dataset.bad; }); if (left.length < 2) { var st = $(".thumbs"); if (st) st.hidden = true; } return; }
    var cand = im.id === "gmain" ? $$(".thumbs button").map(function (b) { return b.dataset.src; }) : [im.dataset.alt];
    var next = cand.filter(function (c) { return c && !t["d:" + c] && !t["p:" + c]; })[0];
    if (next) { t["d:" + next] = 1; im.src = next; return; }
    im.style.visibility = "hidden";     // nothing works: leave the box empty, never a stand-in picture
  }
  document.addEventListener("error", function (e) { fixImg(e.target); }, true);
  $$("img").forEach(function (im) { if (im.complete && !im.naturalWidth && im.getAttribute("loading") !== "lazy") fixImg(im); });

  /* ---------- product search over the 2-letter buckets ---------- */
  function searchProducts(q, limit) {
    var ws = words(q);
    if (!ws.length) return Promise.resolve([]);
    var key = ws.slice().sort(function (a, b) { return b.length - a.length; })[0].slice(0, 2);
    return getJSON("/data/s/" + key + ".json").then(function (rows) {
      var out = [];
      for (var i = 0; i < rows.length && out.length < limit; i++) {
        var n = fold(rows[i][0]), ok = true;
        for (var j = 0; j < ws.length; j++) if (n.indexOf(ws[j]) < 0) { ok = false; break; }
        if (ok) out.push(rows[i]);
      }
      return out;
    }).catch(function () { return []; });
  }

  var sInput = $("#q"), sBox = $("#sugg");
  if (sInput) {
    var sug = null, sel = -1, hits = [], tmr;
    var loadSug = function () { if (!sug) getJSON("/data/sug.json").then(function (d) { sug = d.map(function (x) { return [fold(x[0]), x]; }); }); };
    var run = function () {
      var q = sInput.value.trim();
      if (q.length < 2) { sBox.style.display = "none"; return; }
      var ws = words(q), cats = [];
      if (sug) for (var i = 0; i < sug.length && cats.length < 5; i++) {
        var ok = ws.length > 0;
        for (var j = 0; j < ws.length; j++) if (sug[i][0].indexOf(ws[j]) < 0) { ok = false; break; }
        if (ok) cats.push({ t: sug[i][1][0], u: sug[i][1][1], s: sug[i][1][2] });
      }
      searchProducts(q, 7).then(function (rows) {
        hits = cats.concat(rows.map(function (r) { return { t: r[0], u: "/produkt/" + r[1] + "/", s: (r[3] > 1 ? "od " : "") + kc(r[2]), img: r[4] }; }));
        hits.push({ t: "Hledat „" + q + "“ v celé nabídce", u: "/hledat/?q=" + encodeURIComponent(q), s: "" });
        sel = -1;
        sBox.innerHTML = hits.map(function (h, i) {
          return '<a href="' + h.u + '" role="option">' + (h.img ? '<img src="' + esc(h.img) + '" alt="" loading="lazy" referrerpolicy="no-referrer">' : "") + "<span>" + esc(h.t) + "</span><small>" + esc(h.s) + "</small></a>";
        }).join("");
        sBox.style.display = "block";
      });
    };
    sInput.addEventListener("focus", loadSug);
    sInput.addEventListener("input", function () { loadSug(); clearTimeout(tmr); tmr = setTimeout(run, 120); });
    sInput.addEventListener("keydown", function (e) {
      var links = $$("a", sBox);
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault(); sel = Math.max(0, Math.min(links.length - 1, sel + (e.key === "ArrowDown" ? 1 : -1)));
        links.forEach(function (a, i) { a.classList.toggle("on", i === sel); });
      } else if (e.key === "Enter" && sel >= 0 && hits[sel]) { e.preventDefault(); location.href = hits[sel].u; }
      else if (e.key === "Escape") sBox.style.display = "none";
    });
    document.addEventListener("click", function (e) { if (!e.target.closest(".search")) sBox.style.display = "none"; });
  }

  /* ---------- /hledat/ page ---------- */
  var sres = $("#sres");
  if (sres) {
    var q = new URLSearchParams(location.search).get("q") || "";
    if (sInput) sInput.value = q;
    if (q) searchProducts(q, 96).then(function (rows) {
      $("#sq").textContent = rows.length ? "Výsledky pro „" + q + "“" + (rows.length >= 96 ? " (prvních 96)" : ": " + rows.length) : "Pro „" + q + "“ jsme nic nenašli. Zkuste kratší slovo nebo značku.";
      sres.innerHTML = rows.map(function (r) { return card([r[0], r[1], r[4], r[2], r[3], -1, [], [], [], 0, 0, 0, [], 0, "", []], []); }).join("");
    });
  }

  /* ---------- listing filters ---------- */
  var SW = { bila: "#FFFFFF", cerna: "#1E1E1E", seda: "#9A9C9A", bezova: "#E3D3B8", hneda: "#7A5236", zelena: "#4F7A5A", modra: "#3F6E9E", ruzova: "#E7B3B8", cervena: "#B3322C", zluta: "#E9C24A", oranzova: "#D8743C", zlata: "#C7A043", stribrna: "#C9CCCF" };
  /* row: [0 name, 1 slug, 2 img, 3 price, 4 shops, 5 brand#, 6 colors, 7 mats, 8 styles, 9 wmin, 10 wmax, 11 discount, 12 shopids, 13 variants, 14 tape, 15 feats,
           16 go (cheapest offer), 17 its shop, 18 height, 19 depth, 20 sizes, 21 shapes, 22 seats, 23 category facets ["key:value"]] */
  function card(it, brands, shops) {
    var sale = it[11] >= 10 ? '<span class="flag">−' + it[11] + " %</span>" : "";
    var tape = it[14] ? '<span class="tape">' + esc(it[14]) + "</span>" : "";
    var brand = '<span class="pc__brand">' + (it[5] >= 0 && brands[it[5]] ? esc(brands[it[5]]) : "") + "</span>";
    var sw = '<span class="sw">' + (it[6] || []).slice(0, 4).map(function (c) { return '<i style="--c:' + (SW[c] || "#ccc") + '"></i>'; }).join("") + "</span>";
    var nv = it[13] || 0, meta = shopsIn(it[4]) + (nv > 1 ? " · " + nv + (nv < 5 ? " varianty" : " variant") : "");
    var detail = "/produkt/" + it[1] + "/";
    /* like Favi: the card goes straight to the shop, "Detail" to our product page (search rows have no shop link: detail) */
    var go = it[16] ? esc(it[16]) : detail;
    var ga = it[16] ? ' rel="sponsored nofollow noopener" target="_blank" data-go="' + esc(it[17]) + '"' : "";
    var sname = it[17] && shops && shops[it[17]] ? shops[it[17]] : "";
    var where = sname ? (it[4] > 1 ? "nejlevněji " : "") + esc(sname) : "";
    return '<li class="pc"><a class="pc__img" href="' + go + '"' + ga + ' tabindex="-1" aria-hidden="true"><img src="' + esc(it[2] || "/img/ui/placeholder.svg") + '" alt="" loading="lazy" referrerpolicy="no-referrer" width="400" height="300">' + sale + tape + "</a>" +
      '<div class="pc__b">' + brand + '<h3><a href="' + go + '"' + ga + ">" + esc(it[0]) + "</a></h3>" + sw + '<div class="pc__f"><span class="ptag">' + ((it[4] > 1 || nv > 1) ? "<small>od</small>" : "") + "<b>" + kc(it[3]) + "</b></span>" +
      '<span class="pc__n">' + meta + "</span></div>" +
      '<div class="pc__a"><span class="pc__w">' + where + '</span><a class="pc__d" href="' + detail + '">Detail</a></div></div></li>';
  }
  var list = $("#plist"), form = $("#filters");
  if (list && form) {
    var data = null, shown = 36, sortSel = $("#sort"), count = $("#count"), pager = $(".pager"), chipsBox = $("#factive"), shade = $(".fshade");
    var RANGES = [["p", "Cena", "Kč"], ["w", "Šířka", "cm"], ["h", "Výška", "cm"], ["d", "Hloubka", "cm"]];
    var LISTS = ["brand", "shop", "colors", "mats", "styles", "feats", "size", "shape", "seats", "fx"];
    var num = function (n) { var el = form.elements[n]; return el ? (+el.value || 0) : 0; };
    var active = function () {
      var f = { multi: false, sale: false };
      LISTS.forEach(function (k) { f[k] = []; });
      $$("input[type=checkbox]:checked", form).forEach(function (c) { if (Array.isArray(f[c.name])) f[c.name].push(c.value); else f[c.name] = true; });
      RANGES.forEach(function (r) { f[r[0] + "min"] = num(r[0] + "min"); f[r[0] + "max"] = num(r[0] + "max"); });
      return f;
    };
    var isEmpty = function (f) {
      return !f.multi && !f.sale && LISTS.every(function (k) { return !f[k].length; }) && RANGES.every(function (r) { return !f[r[0] + "min"] && !f[r[0] + "max"]; });
    };
    var isDefault = function (f) { return isEmpty(f) && sortSel.value === (list.dataset.order || "pop"); };
    var any = function (have, want) { return !want.length || (have || []).some(function (x) { return want.indexOf(String(x)) >= 0; }); };
    var inRange = function (v, lo, hi) { return !(lo || hi) || (v && (!lo || v >= lo) && (!hi || v <= hi)); };
    var fcount = $(".fcount", form);
    var apply = function () {
      var f = active();
      syncUi(f);
      if (isDefault(f) && !data) return;
      (data ? Promise.resolve(data) : getJSON(list.dataset.json)).then(function (d) {
        data = d;
        var items = d.i.filter(function (it) {
          if (f.multi && it[4] < 2) return false;
          if (f.sale && it[11] < 10) return false;
          if (!inRange(it[3], f.pmin, f.pmax)) return false;
          if ((f.wmin || f.wmax) && !it[9]) return false;          /* width unknown: hide it, we cannot promise it fits */
          if (f.wmax && it[9] > f.wmax) return false;              /* the narrowest variant must fit */
          if (f.wmin && it[10] < f.wmin) return false;
          if (!inRange(it[18], f.hmin, f.hmax) || !inRange(it[19], f.dmin, f.dmax)) return false;
          if (f.brand.length && f.brand.indexOf(String(it[5])) < 0) return false;
          if (f.shop.length && !any(it[12], f.shop)) return false;
          if (!any(it[6], f.colors) || !any(it[7], f.mats) || !any(it[8], f.styles) || !any(it[15], f.feats)) return false;
          if (!any(it[20], f.size) || !any(it[21], f.shape)) return false;
          if (f.seats.length && f.seats.indexOf(String(it[22] || "")) < 0) return false;
          if (f.fx.length) {      /* category facets: within one facet any value, across facets all of them */
            var have = it[23] || [], keys = {};
            f.fx.forEach(function (kv) { var k = kv.split(":")[0]; keys[k] = keys[k] || have.indexOf(kv) >= 0; });
            for (var k in keys) if (!keys[k]) return false;
          }
          return true;
        });
        var s = sortSel.value;
        if (s === "price") items.sort(function (a, b) { return a[3] - b[3]; });
        else if (s === "pricedesc") items.sort(function (a, b) { return b[3] - a[3]; });
        else if (s === "sale") items.sort(function (a, b) { return b[11] - a[11]; });
        count.textContent = items.length;
        if (fcount) fcount.textContent = items.length + (items.length === 1 ? " kus" : items.length < 5 && items.length ? " kusy" : " kusů");
        var def = isDefault(f);
        if (pager) pager.style.display = def ? "" : "none";
        if (def) { location.reload(); return; }
        list.innerHTML = items.length ? items.slice(0, shown).map(function (it) { return card(it, d.b, d.s); }).join("") :
          '<li class="empty"><img src="/img/ic/kreslo.webp" alt="" width="120" height="120"><p>Takovou kombinaci teď nemáme. Zkuste uvolnit filtry nebo rozměr.</p></li>';
        var more = $("#lmore");
        if (items.length > shown) {
          if (!more) { more = document.createElement("p"); more.id = "lmore"; more.style.textAlign = "center"; more.innerHTML = '<button class="btn btn--g" type="button">Načíst další</button>'; list.after(more); }
          more.firstChild.onclick = function () { shown += 36; apply(); };
        } else if (more) more.remove();
      });
    };
    /* pill counters + chips of the active filters ("bílá ✕", "Cena do 5 000 Kč ✕", "Zrušit vše") */
    var labelOf = function (c) { var l = c.closest("label"); if (!l) return c.value; var t = l.cloneNode(true); $$(".count", t).forEach(function (x) { x.remove(); }); return t.textContent.trim(); };
    var syncUi = function (f) {
      $$(".fb", form).forEach(function (fb) {
        var n = $$("input[type=checkbox]:checked", fb).length + $$("input[type=number]", fb).filter(function (i) { return +i.value; }).length;
        $(".fb__n", fb).textContent = n ? " · " + n : "";
        fb.classList.toggle("on", !!n);
      });
      $$(".fbt", form).forEach(function (l) { l.classList.toggle("on", $("input", l).checked); });
      if (!chipsBox) return;
      var chips = [];
      $$("input[type=checkbox]:checked", form).forEach(function (c) { chips.push(['<button type="button" data-c="' + esc(c.name) + '|' + esc(c.value) + '">' + esc(labelOf(c)) + " ✕</button>"]); });
      RANGES.forEach(function (r) {
        var lo = f[r[0] + "min"], hi = f[r[0] + "max"];
        if (!lo && !hi) return;
        var fmt = function (v) { return r[2] === "Kč" ? kc(v) : v + " cm"; };
        var t = r[1] + " " + (lo && hi ? fmt(lo).replace(" Kč", "") + "–" + fmt(hi) : lo ? "od " + fmt(lo) : "do " + fmt(hi));
        chips.push(['<button type="button" data-r="' + r[0] + '">' + esc(t) + " ✕</button>"]);
      });
      chipsBox.innerHTML = chips.join("") + (chips.length ? '<button type="button" class="clr" data-all="1">Zrušit vše</button>' : "");
      chipsBox.hidden = !chips.length;
    };
    chipsBox && chipsBox.addEventListener("click", function (e) {
      var b = e.target.closest("button"); if (!b) return;
      if (b.dataset.all) { form.reset(); }
      else if (b.dataset.r) { form.elements[b.dataset.r + "min"].value = ""; form.elements[b.dataset.r + "max"].value = ""; }
      else { var p = b.dataset.c.split("|"); $$('input[name="' + p[0] + '"]', form).forEach(function (c) { if (c.value === p.slice(1).join("|")) c.checked = false; }); }
      shown = 36; apply();
    });
    form.addEventListener("change", function () { shown = 36; apply(); });
    var wt;
    $$("input[type=number]", form).forEach(function (i) { i.addEventListener("input", function () { clearTimeout(wt); wt = setTimeout(function () { shown = 36; apply(); }, 350); }); });
    sortSel && sortSel.addEventListener("change", function () { shown = 36; apply(); });
    $$(".fquick button", form).forEach(function (b) {
      b.addEventListener("click", function () { form.pmax.value = b.classList.contains("on") ? "" : b.dataset.pmax; $$(".fquick button", form).forEach(function (x) { x.classList.toggle("on", x === b && form.pmax.value); }); shown = 36; apply(); });
    });
    $$(".freset", form).forEach(function (r) { r.addEventListener("click", function () { form.reset(); shown = 36; apply(); }); });
    $$(".fsearch", form).forEach(function (fs) {
      fs.addEventListener("input", function () { var w = fold(fs.value); $$(".flinks label", fs.parentNode).forEach(function (l) { l.style.display = fold(l.textContent).indexOf(w) >= 0 ? "" : "none"; }); });
    });
    /* popovers: one open at a time, close on click outside / Esc / "Zobrazit" */
    /* fetch the category data when the visitor reaches for the filters, so the first click filters at once */
    var warmed = false;
    var warm = function () { if (warmed || data) return; warmed = true; getJSON(list.dataset.json).then(function (d) { data = data || d; }); };
    form.addEventListener("pointerenter", warm);
    form.addEventListener("focusin", warm);
    var pills = $$(".fb", form);
    var closePills = function (except) { pills.forEach(function (p) { if (p !== except) p.open = false; }); };
    pills.forEach(function (p) {
      p.addEventListener("toggle", function () {
        if (!p.open || form.classList.contains("all")) return;
        closePills(p);
        /* a pill near the right edge opens its popover leftwards, so it never leaves the screen */
        p.classList.remove("fb--r");
        var pop = $(".fb__pop", p);
        if (pop && pop.getBoundingClientRect().right > document.documentElement.clientWidth - 12) p.classList.add("fb--r");
      });
    });
    $$(".fb__ok", form).forEach(function (b) { b.addEventListener("click", function () { closePills(); }); });
    document.addEventListener("click", function (e) { if (!form.classList.contains("all") && !e.target.closest(".fb")) closePills(); });
    /* "Všechny filtry": the same form as a drawer, every group open */
    var openAll = function () { form.classList.add("all"); pills.forEach(function (p) { p.open = true; }); if (shade) shade.hidden = false; document.body.style.overflow = "hidden"; apply(); };
    var closeAll = function () { form.classList.remove("all"); closePills(); if (shade) shade.hidden = true; document.body.style.overflow = ""; };
    $$(".fall", form).forEach(function (b) { b.addEventListener("click", openAll); });
    $$(".fx, .fclose", form).forEach(function (b) { b.addEventListener("click", closeAll); });
    shade && shade.addEventListener("click", closeAll);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") { if (form.classList.contains("all")) closeAll(); else closePills(); } });
    syncUi(active());
  }

  /* ---------- product page ---------- */
  var gm = $("#gmain");
  $$(".thumbs button").forEach(function (b) {
    b.addEventListener("click", function () { gm.src = b.dataset.src; $$(".thumbs button").forEach(function (x) { x.classList.toggle("on", x === b); }); });
  });
  $$("[data-more]").forEach(function (b) {
    var el = document.getElementById(b.dataset.more);
    if (el && el.scrollHeight <= el.clientHeight + 10) { el.classList.remove("clamp"); b.remove(); return; }
    b.addEventListener("click", function () { el.classList.remove("clamp"); b.remove(); });
  });

  /* ---------- "does it fit?" — computed in the browser only ---------- */
  var fb = $(".fitbox");
  if (fb) {
    var fw = $("#fitw"), fo = $("#fitout"), need = +fb.dataset.w;
    var calc = function () {
      var have = +fw.value;
      if (!have) { fo.textContent = ""; fo.className = ""; return; }
      var d = Math.round((have - need) * 10) / 10;
      if (d >= 0) { fo.textContent = "Vejde se. Zbyde " + String(d).replace(".", ",") + " cm."; fo.className = "ok"; }
      else { fo.textContent = "Nevejde se, chybí " + String(-d).replace(".", ",") + " cm."; fo.className = "no"; }
      store("vian-fitw", fw.value);
    };
    var last = store("vian-fitw");
    if (last) fw.value = last;
    fw.addEventListener("input", calc); calc();
  }

  /* ---------- consent: Consent Mode v2 (GTM itself is in the page head, see render.py; here only the update) ---------- */
  var ga = document.querySelector('meta[name="ga4"]'), cbar = $("#consent"), granted = false;
  window.dataLayer = window.dataLayer || [];
  function setConsent(yes) {
    if (!ga) return;
    granted = yes;
    if (window.gtag) window.gtag("consent", "update", { analytics_storage: yes ? "granted" : "denied" });
  }
  var c = store("vian-consent");
  if (c === "yes") granted = true; else if (!c && ga && cbar) cbar.hidden = false;
  $$("[data-consent]").forEach(function (b) {
    b.addEventListener("click", function () { store("vian-consent", b.dataset.consent); cbar.hidden = true; setConsent(b.dataset.consent === "yes"); });
  });
  var sq = $("#shopq"), sl = $("#shoplist");
  if (sq && sl) sq.addEventListener("input", function () {
    var q = sq.value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    sl.querySelectorAll("li").forEach(function (li) { li.hidden = !!q && (li.dataset.name || "").indexOf(q) < 0; });
  });
  var co = $("#consent-open");
  co && co.addEventListener("click", function (e) { e.preventDefault(); if (cbar) cbar.hidden = false; });
  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-go]");
    if (a && ga) {
      var d = { shop: a.dataset.go, from_path: location.pathname, transport_type: "beacon" };
      if (ga.content.indexOf("GTM-") === 0) { d.event = "click_shop"; window.dataLayer.push(d); }
      else if (window.gtag) window.gtag("event", "click_shop", d);
    }
  });

  /* ---------- 404: send a dead address to the nearest category / brand / topic (the server still answers 404) ---------- */
  var STOP = { pro: 1, nabytek: 1, srovnani: 1, ceny: 1, levne: 1, cena: 1, akce: 1, eshop: 1, a: 1, na: 1, do: 1, od: 1, se: 1, s: 1, the: 1, ve: 1, v: 1, z: 1 };
  function sameWord(a, b) {
    var m = Math.min(a.length, b.length);
    if (m < 4) return a === b;
    var k = Math.max(4, m - 2);
    return a.slice(0, k) === b.slice(0, k) && Math.abs(a.length - b.length) <= 3;
  }
  function nearest(idx, url) {
    var ut = fold(url.replace(/strana-\d+/g, " ").replace(/^\/(produkt|znacky)\//, "/")).split(/[^a-z0-9]+/).filter(function (w) { return w.length > 1 && !/^\d+$/.test(w); });
    var best = null, part = [];
    idx.forEach(function (e, i) {
      var ct = words(e[0]).filter(function (w) { return w.length > 2 && !STOP[w]; });
      if (!ct.length) return;
      var hit = 0, chars = 0, miss = 0;
      ct.forEach(function (w) { if (ut.some(function (u) { return sameWord(w, u); })) { hit++; chars += w.length; } else miss += w.length; });
      if (!hit) return;
      var sc = chars - miss / 2;
      if ((chars >= 5 || (chars >= 4 && !miss)) && (!best || sc > best.s)) best = { s: sc, e: e };
      part.push({ s: sc, e: e, i: i });
    });
    part.sort(function (a, b) { return b.s - a.s || a.i - b.i; });
    return { best: best && best.e, other: part.slice(0, 6).map(function (x) { return x.e; }) };
  }
  var e404 = $(".e404");
  /* A product page that 404s may simply be seconds old (the deploy switches listings and product pages ~2 s apart) or a
     404 the browser still has cached: ask the server once more, bypassing every cache, before sending the visitor away. */
  var recheck = function () {
    if (!/^\/produkt\//.test(location.pathname) || /[?&]r=/.test(location.search)) return Promise.resolve(false);
    return new Promise(function (ok) { setTimeout(ok, 1500); })
      .then(function () { return fetch(location.pathname + "?r=" + Date.now(), { method: "HEAD", cache: "no-store" }); })
      .then(function (res) { if (res.ok) { location.replace(location.pathname + "?r=" + Date.now()); return true; } return false; })
      .catch(function () { return false; });
  };
  if (e404) {
    recheck().then(function (fixed) { return fixed ? Promise.reject("fixed") : getJSON("/data/r404.json"); }).then(function (idx) {
      var r = nearest(idx, location.pathname), looped = false;
      try { looped = !!sessionStorage.getItem("vian-404"); } catch (e) { }
      if (r.best && r.best[1] !== location.pathname && !looped) {
        try { sessionStorage.setItem("vian-404", location.pathname); } catch (e) { }
        location.replace(r.best[1]);
        return;
      }
      try { sessionStorage.removeItem("vian-404"); } catch (e) { }
      var list = r.other.length ? r.other : idx.slice(0, 8), box = $("#nf-sugg");
      if (box && list.length) {
        box.hidden = false;
        box.innerHTML = '<p class="muted">Možná hledáte:</p><ul class="chips">' + list.map(function (e) { return '<li><a href="' + esc(e[1]) + '">' + esc(e[0]) + "</a></li>"; }).join("") + "</ul>";
      }
    }).catch(function () { });
  } else {
    if (/[?&]r=\d/.test(location.search)) { try { history.replaceState(null, "", location.pathname); } catch (e) { } }   /* after a recheck reload */
    var from = null;
    try { from = sessionStorage.getItem("vian-404"); sessionStorage.removeItem("vian-404"); } catch (e) { }
    if (from) {
      var nb = document.createElement("div");
      nb.className = "nf"; nb.setAttribute("role", "status");
      var tx = document.createElement("span"); tx.textContent = "Adresu " + from.slice(0, 80) + " jsme nenašli, tady je nejbližší stránka.";
      var cb = document.createElement("button"); cb.type = "button"; cb.setAttribute("aria-label", "Zavřít"); cb.textContent = "×";
      cb.addEventListener("click", function () { nb.remove(); });
      nb.appendChild(tx); nb.appendChild(cb);
      var host = $("main") || document.body; host.insertBefore(nb, host.firstChild);
    }
  }

})();
