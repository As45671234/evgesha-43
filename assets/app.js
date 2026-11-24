/* Евгеша · 43 — галерея */
(function () {
  "use strict";

  var grid   = document.getElementById("grid");
  var tiles  = grid ? Array.prototype.slice.call(grid.querySelectorAll(".tile")) : [];
  var ROW    = 6; // grid-auto-rows, px — см. style.css

  /* ——— masonry: высота плитки = её пропорции ——— */
  function layout() {
    if (!grid) return;
    var cs  = getComputedStyle(grid);
    var gap = parseFloat(cs.rowGap) || 0;
    var cw  = tiles.length ? tiles[0].getBoundingClientRect().width : 0;
    if (!cw) return;
    for (var i = 0; i < tiles.length; i++) {
      var t  = tiles[i];
      var ar = parseFloat(t.dataset.ar) || 1;           // width / height
      var h  = (t.getBoundingClientRect().width || cw) / ar;
      t.style.gridRowEnd = "span " + Math.max(1, Math.round((h + gap) / (ROW + gap)));
    }
  }

  var rafId;
  function relayout() { cancelAnimationFrame(rafId); rafId = requestAnimationFrame(layout); }

  /* ——— ленивая подгрузка превью ——— */
  var io = "IntersectionObserver" in window
    ? new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          var img = e.target;
          io.unobserve(img);
          img.src = img.dataset.src;
          if (img.complete) img.classList.add("ready");
          else img.addEventListener("load", function () { img.classList.add("ready"); }, { once: true });
        });
      }, { rootMargin: "700px 0px" })
    : null;

  tiles.forEach(function (t) {
    var img = t.querySelector("img");
    if (!img) return;
    if (io) io.observe(img);
    else { img.src = img.dataset.src; img.classList.add("ready"); }
  });

  /* ——— фон героя: медленное перелистывание ——— */
  (function heroBg() {
    var box = document.getElementById("heroBg");
    if (!box) return;
    var imgs = Array.prototype.slice.call(box.querySelectorAll("img"));
    if (imgs.length < 2) { if (imgs[0]) imgs[0].classList.add("on"); return; }
    var n = 0;
    imgs[0].classList.add("on");
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setInterval(function () {
      imgs[n].classList.remove("on");
      n = (n + 1) % imgs.length;
      imgs[n].classList.add("on");
    }, 6500);
  })();

  /* ——— появление блоков ——— */
  (function reveal() {
    var els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      Array.prototype.forEach.call(els, function (el) { el.classList.add("in"); });
      return;
    }
    var ro = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); ro.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(els, function (el) { ro.observe(el); });
  })();

  /* ——— цвет / ч-б ——— */
  (function colorToggle() {
    var btns = document.querySelectorAll("[data-toggle-color]");
    Array.prototype.forEach.call(btns, function (b) {
      b.addEventListener("click", function () {
        var on = document.body.classList.toggle("in-color");
        Array.prototype.forEach.call(btns, function (x) {
          x.setAttribute("aria-pressed", on ? "true" : "false");
          var lbl = x.querySelector("span");
          if (lbl) lbl.textContent = on ? "Цвет" : "Ч/Б";
        });
      });
    });
  })();

  /* ——— лайтбокс ——— */
  var lb      = document.getElementById("lb");
  if (!lb) return;
  var lbImg   = document.getElementById("lbImg");
  var lbCount = document.getElementById("lbCount");
  var lbTime  = document.getElementById("lbTime");
  var items   = tiles.map(function (t) {
    return { full: t.dataset.full, time: t.dataset.time || "" };
  });
  var cur = -1, lastFocus = null;

  function preload(i) {
    if (i < 0 || i >= items.length) return;
    var p = new Image();
    p.src = items[i].full;
  }

  function show(i) {
    if (!items.length) return;
    cur = (i + items.length) % items.length;
    var it = items[cur];
    lbImg.classList.remove("ready");
    lbImg.src = it.full;
    lbImg.alt = "Кадр " + (cur + 1) + " из " + items.length;
    if (lbImg.complete) lbImg.classList.add("ready");
    lbCount.textContent = (cur + 1) + " / " + items.length;
    lbTime.textContent = it.time;
    preload(cur + 1); preload(cur - 1);
  }

  lbImg.addEventListener("load", function () { lbImg.classList.add("ready"); });

  function open(i) {
    lastFocus = document.activeElement;
    lb.classList.add("on");
    lb.setAttribute("aria-hidden", "false");
    document.body.classList.add("lb-open");
    show(i);
    var x = lb.querySelector(".lb__x");
    if (x) x.focus();
  }

  function close() {
    lb.classList.remove("on");
    lb.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lb-open");
    lbImg.removeAttribute("src");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  tiles.forEach(function (t, i) {
    t.addEventListener("click", function () { open(i); });
    t.setAttribute("tabindex", "0");
    t.setAttribute("role", "button");
    t.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(i); }
    });
  });

  var posterEl = document.getElementById("posterOpen");
  if (posterEl) {
    posterEl.addEventListener("click", function () {
      lastFocus = document.activeElement;
      lb.classList.add("on");
      lb.setAttribute("aria-hidden", "false");
      document.body.classList.add("lb-open");
      cur = -1;
      lbImg.classList.remove("ready");
      lbImg.src = "poster.webp";
      lbImg.alt = "Афиша вечеринки";
      lbCount.textContent = "Афиша";
      lbTime.textContent = "";
      var x = lb.querySelector(".lb__x");
      if (x) x.focus();
    });
  }

  lb.addEventListener("click", function (e) {
    if (e.target === lb || e.target.classList.contains("lb__stage")) close();
  });
  lb.querySelector(".lb__x").addEventListener("click", close);
  lb.querySelector(".lb__nav--prev").addEventListener("click", function () { show(cur - 1); });
  lb.querySelector(".lb__nav--next").addEventListener("click", function () { show(cur + 1); });

  document.addEventListener("keydown", function (e) {
    if (!lb.classList.contains("on")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowRight") show(cur + 1);
    else if (e.key === "ArrowLeft") show(cur - 1);
  });

  /* свайп на телефоне */
  var sx = 0, sy = 0, moved = false;
  lb.addEventListener("touchstart", function (e) {
    sx = e.touches[0].clientX; sy = e.touches[0].clientY; moved = false;
  }, { passive: true });
  lb.addEventListener("touchmove", function () { moved = true; }, { passive: true });
  lb.addEventListener("touchend", function (e) {
    if (!moved) return;
    var dx = e.changedTouches[0].clientX - sx;
    var dy = e.changedTouches[0].clientY - sy;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy)) show(cur + (dx < 0 ? 1 : -1));
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
  }, { passive: true });

  /* ——— раскладка ——— */
  window.addEventListener("load", relayout);
  window.addEventListener("resize", relayout);
  if ("ResizeObserver" in window && grid) new ResizeObserver(relayout).observe(grid);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(relayout);
  relayout();
})();
