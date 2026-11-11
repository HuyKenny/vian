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
  /* A shop picture the browser cannot show: 1) the same picture through an image proxy, 2) the product's other pictures
     (gallery / alternative), each also direct then proxied, 3) the box stays empty. Every address is tried at most once. */
  function fixImg(im) {
    if (im.tagName !== "IMG" || !im.src || im.src.indexOf(location.host) >= 0) return;
    var t = im._t = im._t || {}, orig = unproxy(im.currentSrc || im.src);
    t["d:" + orig] = 1;
    if (!t["p:" + orig] && (im.currentSrc || im.src).indexOf("wsrv.nl") < 0) { t["p:" + orig] = 1; im.src = viaProxy(orig); return; }
    t["p:" + orig] = 1;
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
  /* row: [name, slug, img, price, shops, brand#, colors, mats, styles, wmin, wmax, discount, shopids, variants, tape, feats] */
  function card(it, brands) {
    var sale = it[11] >= 10 ? '<span class="flag">−' + it[11] + " %</span>" : "";
    var tape = it[14] ? '<span class="tape">' + esc(it[14]) + "</span>" : "";
    var brand = it[5] >= 0 && brands[it[5]] ? '<span class="pc__brand">' + esc(brands[it[5]]) + "</span>" : "";
    var sw = it[6] && it[6].length ? '<span class="sw">' + it[6].slice(0, 4).map(function (c) { return '<i style="--c:' + (SW[c] || "#ccc") + '"></i>'; }).join("") + "</span>" : "";
    var nv = it[13] || 0, meta = shopsIn(it[4]) + (nv > 1 ? " · " + nv + (nv < 5 ? " varianty" : " variant") : "");
    var href = "/produkt/" + it[1] + "/";
    return '<li class="pc"><a class="pc__img" href="' + href + '" tabindex="-1" aria-hidden="true"><img src="' + esc(it[2] || "/img/ui/placeholder.svg") + '" alt="" loading="lazy" referrerpolicy="no-referrer" width="320" height="320">' + sale + tape + "</a>" +
      '<div class="pc__b">' + brand + '<h3><a href="' + href + '">' + esc(it[0]) + "</a></h3>" + sw + '<div class="pc__f"><span class="ptag">' + ((it[4] > 1 || nv > 1) ? "<small>od</small>" : "") + "<b>" + kc(it[3]) + "</b></span>" +
      '<span class="pc__n">' + meta + "</span></div></div></li>";
  }
  var list = $("#plist"), form = $("#filters");
  if (list && form) {
    var data = null, shown = 36, sortSel = $("#sort"), count = $("#count"), pager = $(".pager"), reset = $(".freset", form);
    var active = function () {
      var f = { brand: [], shop: [], colors: [], mats: [], styles: [], feats: [], multi: false, sale: false, pmin: 0, pmax: 0, wmin: 0, wmax: 0 };
      $$("input[type=checkbox]:checked", form).forEach(function (c) { if (Array.isArray(f[c.name])) f[c.name].push(c.value); else f[c.name] = true; });
      f.pmin = +form.pmin.value || 0; f.pmax = +form.pmax.value || 0;
      if (form.wmin) { f.wmin = +form.wmin.value || 0; f.wmax = +form.wmax.value || 0; }
      return f;
    };
    var isDefault = function (f) { return !f.brand.length && !f.shop.length && !f.colors.length && !f.mats.length && !f.styles.length && !f.feats.length && !f.multi && !f.sale && !f.pmin && !f.pmax && !f.wmin && !f.wmax && sortSel.value === (list.dataset.order || "pop"); };
    var any = function (have, want) { return !want.length || (have || []).some(function (x) { return want.indexOf(x) >= 0; }); };
    var apply = function () {
      var f = active();
      if (isDefault(f) && !data) return;
      (data ? Promise.resolve(data) : getJSON(list.dataset.json)).then(function (d) {
        data = d;
        var items = d.i.filter(function (it) {
          if (f.multi && it[4] < 2) return false;
          if (f.sale && it[11] < 10) return false;
          if (f.pmin && it[3] < f.pmin) return false;
          if (f.pmax && it[3] > f.pmax) return false;
          if ((f.wmin || f.wmax) && !it[9]) return false;          /* width unknown: hide it, we cannot promise it fits */
          if (f.wmax && it[9] > f.wmax) return false;              /* the narrowest variant must fit */
          if (f.wmin && it[10] < f.wmin) return false;
          if (f.brand.length && f.brand.indexOf(String(it[5])) < 0) return false;
          if (f.shop.length && !any(it[12], f.shop)) return false;
          if (!any(it[6], f.colors) || !any(it[7], f.mats) || !any(it[8], f.styles) || !any(it[15], f.feats)) return false;
          return true;
        });
        var s = sortSel.value;
        if (s === "price") items.sort(function (a, b) { return a[3] - b[3]; });
        else if (s === "pricedesc") items.sort(function (a, b) { return b[3] - a[3]; });
        else if (s === "sale") items.sort(function (a, b) { return b[11] - a[11]; });
        count.textContent = items.length;
        var def = isDefault(f);
        if (pager) pager.style.display = def ? "" : "none";
        reset.hidden = def;
        if (def) { location.reload(); return; }
        list.innerHTML = items.length ? items.slice(0, shown).map(function (it) { return card(it, d.b); }).join("") :
          '<li class="empty"><img src="/img/ic/kreslo.webp" alt="" width="120" height="120"><p>Takovou kombinaci teď nemáme. Zkuste uvolnit filtry nebo rozměr.</p></li>';
        var more = $("#lmore");
        if (items.length > shown) {
          if (!more) { more = document.createElement("p"); more.id = "lmore"; more.style.textAlign = "center"; more.innerHTML = '<button class="btn btn--g" type="button">Načíst další</button>'; list.after(more); }
          more.firstChild.onclick = function () { shown += 36; apply(); };
        } else if (more) more.remove();
      });
    };
    form.addEventListener("change", function () { shown = 36; apply(); });
    var wt;
    $$('input[name="wmin"], input[name="wmax"], input[name="pmin"], input[name="pmax"]', form).forEach(function (i) { i.addEventListener("input", function () { clearTimeout(wt); wt = setTimeout(function () { shown = 36; apply(); }, 350); }); });
    sortSel && sortSel.addEventListener("change", function () { shown = 36; apply(); });
    $$(".fquick button", form).forEach(function (b) {
      b.addEventListener("click", function () { form.pmax.value = b.classList.contains("on") ? "" : b.dataset.pmax; $$(".fquick button", form).forEach(function (x) { x.classList.toggle("on", x === b && form.pmax.value); }); apply(); });
    });
    var qf = $$(".qf button");
    var qsync = function () {
      qf.forEach(function (b) {
        var q = b.dataset.q, on = q === "pmax" ? +form.pmax.value === +b.dataset.v : q === "sort" ? sortSel.value === b.dataset.v : form.elements[q].checked;
        b.classList.toggle("on", on); b.setAttribute("aria-pressed", on);
      });
    };
    qf.forEach(function (b) {
      b.addEventListener("click", function () {
        var q = b.dataset.q, on = b.classList.contains("on");
        if (q === "pmax") form.pmax.value = on ? "" : b.dataset.v;
        else if (q === "sort") sortSel.value = on ? (list.dataset.order || "pop") : b.dataset.v;
        else form.elements[q].checked = !on;
        shown = 36; qsync(); apply();
      });
    });
    form.addEventListener("change", qsync); sortSel && sortSel.addEventListener("change", qsync);
    reset.addEventListener("click", function () { form.reset(); sortSel.value = list.dataset.order || "pop"; location.reload(); });
    $$(".fsearch", form).forEach(function (fs) {
      fs.addEventListener("input", function () { var w = fold(fs.value); $$(".flinks label, .flinks a", fs.parentNode).forEach(function (l) { l.style.display = fold(l.textContent).indexOf(w) >= 0 ? "" : "none"; }); });
    });
    var tg = $(".ftoggle"), close = $(".fclose", form);
    tg && tg.addEventListener("click", function () { form.classList.add("open"); document.body.style.overflow = "hidden"; });
    close && close.addEventListener("click", function () { form.classList.remove("open"); document.body.style.overflow = ""; });
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
})();
