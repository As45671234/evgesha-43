"""Собирает index.html альбома из photos.json.

    python tools/gen_index.py <корень-альбома>

Заголовок, дату и место правьте в константах ниже."""
import json, os, sys, hashlib

ROOT = sys.argv[1]
TITLE = "Евгеша"
AGE = "43 года"
DATE_HUMAN = "21 ноября 2026"
VENUE = "Atmosfera Music"
ADDR = "Кабанбай батыра, 49"
ZIP_NAME = "evgesha-43-photos.zip"

photos = json.load(open(os.path.join(ROOT, "photos.json"), encoding="utf-8"))


def ver(rel):
    """Короткий хеш файла — чтобы браузер не отдавал старую версию из кэша."""
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return rel + "?v=" + hashlib.md5(fh.read()).hexdigest()[:8]


def hhmm(t):
    return t[11:16] if len(t) >= 16 else ""


times = [hhmm(p["time"]) for p in photos if p.get("time")]
span = f"{times[0]} — {times[-1]}" if times else ""

zip_path = os.path.join(ROOT, ZIP_NAME)
zip_mb = round(os.path.getsize(zip_path) / 1048576) if os.path.exists(zip_path) else 0

ICON_DL = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" '
           'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<path d="M12 3.5v11.5m0 0 4.2-4.2M12 15l-4.2-4.2"/>'
           '<path d="M4 16.5v2A2 2 0 0 0 6 20.5h12a2 2 0 0 0 2-2v-2"/></svg>')

SPARK = ('<svg class="spark" viewBox="0 0 24 24" width="17" height="17" aria-hidden="true">'
         '<path d="M12 0c.6 6.3 5.1 10.8 12 12-6.9 1.2-11.4 5.7-12 12-.6-6.3-5.1-10.8-12-12'
         'C6.9 10.8 11.4 6.3 12 0z" fill="currentColor"/></svg>')

hero_ids = [photos[i]["id"] for i in (4, 22, 36, 49, 12) if i < len(photos)]
hero_imgs = "\n".join(
    f'        <img src="photos/thumb/{i}.webp" alt="" aria-hidden="true">'
    for i in hero_ids)

tiles = []
for p in photos:
    ar = round(p["w"] / p["h"], 4)
    t = hhmm(p.get("time", ""))
    n = int(p["id"])
    tiles.append(
        f'      <figure class="tile" data-ar="{ar}" data-id="{p["id"]}" '
        f'data-full="photos/full/{p["id"]}.webp" data-time="{t}" '
        f'style="background-image:url({p["lqip"]})" aria-label="Кадр {n}, {t}">'
        f'<img data-src="photos/thumb/{p["id"]}.webp" alt="Кадр {n} — {t}" '
        f'width="{p["w"]}" height="{p["h"]}" loading="lazy" decoding="async"></figure>')
tiles = "\n".join(tiles)

doc = f"""<!doctype html>
<html lang="ru" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TITLE} · {AGE} — {DATE_HUMAN}</title>
<meta name="description" content="Фотоальбом вечеринки {DATE_HUMAN} в {VENUE}. {len(photos)} кадров.">
<meta name="theme-color" content="#0a0a0b">
<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE} · {AGE}">
<meta property="og:description" content="{DATE_HUMAN} · {VENUE} · {len(photos)} кадров">
<meta property="og:image" content="poster.webp">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M12 0c.6 6.3 5.1 10.8 12 12-6.9 1.2-11.4 5.7-12 12-.6-6.3-5.1-10.8-12-12C6.9 10.8 11.4 6.3 12 0z' fill='white'/></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marck+Script&family=Playfair+Display:wght@400;500&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{ver("assets/style.css")}">
<script>document.documentElement.className = "js";</script>
</head>
<body>
<div class="grain" aria-hidden="true"></div>

<header class="hero" id="top">
  <div class="hero__bg" id="heroBg" aria-hidden="true">
{hero_imgs}
  </div>
  <div class="hero__veil" aria-hidden="true"></div>

  <div class="hero__inner">
    <p class="kicker">{DATE_HUMAN} &nbsp;·&nbsp; <b>{VENUE}</b></p>
    <h1 class="chrome">{TITLE}</h1>
    <p class="hero__age chrome">{AGE}</p>

    <div class="rule"><span>{SPARK}</span></div>

    <p class="hero__meta"><strong>{len(photos)} кадров</strong> одного вечера · {span}</p>
    <p class="hero__dress">Дресс-код: чёрно-белый</p>
  </div>

  <div class="scroll-cue" aria-hidden="true"><i></i>вниз</div>
</header>

<main>
  <section class="section section--tight reveal" id="afisha">
    <div class="poster">
      <div class="poster__img" id="posterOpen" role="button" tabindex="0" aria-label="Открыть афишу">
        <img src="poster.webp" alt="Афиша вечеринки" width="1073" height="1600" loading="lazy" decoding="async">
      </div>
      <div class="poster__txt">
        <p class="lead">«Приглашаю отметить свой День Рождения!»</p>
        <p>С этой афиши всё и началось. Ниже — как это было: {len(photos)} кадров, от первых гостей до последнего тоста.</p>
        <ul class="poster__facts">
          <li><b>Когда</b><span>{DATE_HUMAN}, {span}</span></li>
          <li><b>Где</b><span>{VENUE} · {ADDR}</span></li>
          <li><b>Дресс-код</b><span>Чёрно-белый (обязателен)</span></li>
          <li><b>В программе</b><span>Бэк-вокал, конкурсы и много позитива</span></li>
        </ul>
      </div>
    </div>
  </section>

  <section class="section reveal" id="gallery">
    <div class="sec-head">
      <h2>Вечер</h2>
      <p>{len(photos)} кадров · {span}</p>
      <div class="sec-actions">
        <button class="pill" data-toggle-color aria-pressed="true">
          <i aria-hidden="true"></i><span>Цвет</span>
        </button>
        <a class="pill pill--dl" href="{ZIP_NAME}" download>
          {ICON_DL}<span>Скачать все · {zip_mb} МБ</span>
        </a>
      </div>
    </div>

    <div class="grid" id="grid">
{tiles}
    </div>
  </section>
</main>

<footer class="foot">
  <p class="foot__sign chrome">С днём рождения</p>
  <p>{VENUE} · {ADDR}</p>
  <p>{DATE_HUMAN}</p>
  <p class="scorp">{SPARK.replace('width="17" height="17"', 'width="15" height="15"')}</p>
  <a class="up" href="#top">Наверх</a>
</footer>

<div class="lb" id="lb" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Просмотр фото">
  <div class="lb__bar lb__bar--top">
    <span id="lbCount">1 / {len(photos)}</span>
    <span class="lb__tools">
      <a class="lb__dl" id="lbDl" download title="Скачать этот кадр" aria-label="Скачать этот кадр">{ICON_DL}</a>
      <button class="lb__x" aria-label="Закрыть">&times;</button>
    </span>
  </div>
  <div class="lb__stage">
    <img class="lb__img" id="lbImg" alt="">
  </div>
  <button class="lb__nav lb__nav--prev" aria-label="Предыдущее">&#8249;</button>
  <button class="lb__nav lb__nav--next" aria-label="Следующее">&#8250;</button>
  <div class="lb__bar lb__bar--bot"><span id="lbTime"></span></div>
</div>

<script src="{ver("assets/app.js")}" defer></script>
</body>
</html>
"""

with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
    f.write(doc)
print("index.html: %d байт · %d фото · %s · архив %d МБ" % (len(doc), len(photos), span, zip_mb))
