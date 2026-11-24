"""Оригиналы с телефона -> веб-версии для альбома.

На каждый снимок: full (2000 px по длинной стороне) и thumb (900 px) для показа,
dl (полное разрешение, q92) для скачивания и крошечная размытая заглушка.
EXIF и GPS вырезаются. Пишет photos.json: порядок, размеры, время, заглушка,
и downloads.json: архивы «скачать все».

    python tools/build_web.py <папка-с-оригиналами> <корень-альбома>
"""
import os, sys, glob, json, base64, io, time, math, zipfile
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
import pillow_heif

pillow_heif.register_heif_opener()

ZIP_PREFIX = "evgesha-43-photos"
ZIP_LIMIT = 85 * 1048576     # GitHub не принимает файлы больше 100 МБ
DL_QUALITY = 94              # полное разрешение; 4:2:0 как в самом HEIC

EXTS = (".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def pick_files(src_dir):
    """Все снимки; где айфон сохранил правку (IMG_Ennnn) — берём её, а не оригинал."""
    files = [f for f in glob.glob(os.path.join(src_dir, "*"))
             if os.path.splitext(f)[1].lower() in EXTS]
    stems = {os.path.splitext(os.path.basename(f))[0] for f in files}
    keep = []
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0]
        if stem.startswith("IMG_") and not stem.startswith("IMG_E"):
            if "IMG_E" + stem[4:] in stems:
                continue                      # есть отредактированная версия
        keep.append(f)
    return keep


def shot_time(path):
    try:
        ex = Image.open(path).getexif()
        d = {TAGS.get(k, k): v for k, v in ex.items()}
        return d.get("DateTimeOriginal") or d.get("DateTime") or ""
    except Exception:
        return ""


def main(src_dir, out_root):
    full_dir = os.path.join(out_root, "photos", "full")
    thumb_dir = os.path.join(out_root, "photos", "thumb")
    dl_dir = os.path.join(out_root, "photos", "dl")
    for d in (full_dir, thumb_dir, dl_dir):
        os.makedirs(d, exist_ok=True)

    files = pick_files(src_dir)
    if not files:
        sys.exit("В папке нет снимков: " + src_dir)
    # без времени съёмки — в конец, по имени
    items = sorted(((shot_time(f) or "9999", f) for f in files), key=lambda t: (t[0], t[1]))

    meta, t0, failed = [], time.time(), []
    for i, (when, f) in enumerate(items, 1):
        slug = "%03d" % i
        try:
            im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
        except Exception as e:
            failed.append((os.path.basename(f), str(e)))
            continue
        w, h = im.size

        full = im.copy()
        full.thumbnail((2000, 2000), Image.LANCZOS)
        full.save(os.path.join(full_dir, slug + ".webp"), "WEBP", quality=82, method=5)

        # Для скачивания — полное разрешение оригинала, без уменьшения.
        # JPEG, а не webp или heic: открывается везде.
        im.save(os.path.join(dl_dir, slug + ".jpg"), "JPEG",
                quality=DL_QUALITY, subsampling=2, optimize=True, progressive=True)

        th = im.copy()
        th.thumbnail((900, 900), Image.LANCZOS)
        th.save(os.path.join(thumb_dir, slug + ".webp"), "WEBP", quality=72, method=5)

        tiny = im.copy()
        tiny.thumbnail((20, 20), Image.LANCZOS)
        buf = io.BytesIO()
        tiny.save(buf, "WEBP", quality=40)

        meta.append({
            "id": slug, "w": w, "h": h,
            "time": when.replace(":", "-", 2) if when != "9999" else "",
            "lqip": "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode(),
        })
        if i % 10 == 0 or i == len(items):
            print("%d/%d  %.0fс" % (i, len(items), time.time() - t0), flush=True)

    # убрать кадры, оставшиеся от прошлой, более длинной сборки
    removed = 0
    for d, ext in ((full_dir, ".webp"), (thumb_dir, ".webp"), (dl_dir, ".jpg")):
        keep = {m["id"] + ext for m in meta}
        for name in os.listdir(d):
            if name not in keep:
                os.remove(os.path.join(d, name))
                removed += 1

    # Архивы «скачать все» — статическому хостингу их на лету не собрать.
    # Делим на самостоятельные части: каждая распаковывается сама по себе.
    sizes = [os.path.getsize(os.path.join(dl_dir, m["id"] + ".jpg")) for m in meta]
    total = sum(sizes)
    parts = max(1, math.ceil(total / ZIP_LIMIT))
    target = total / parts

    chunks, cur, cur_size = [], [], 0
    for m, sz in zip(meta, sizes):
        if cur and cur_size + sz > target and len(chunks) < parts - 1:
            chunks.append(cur); cur, cur_size = [], 0
        cur.append(m); cur_size += sz
    if cur:
        chunks.append(cur)

    downloads = []
    for n, chunk in enumerate(chunks, 1):
        name = "%s.zip" % ZIP_PREFIX if len(chunks) == 1 else "%s-%d.zip" % (ZIP_PREFIX, n)
        path = os.path.join(out_root, name)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as z:
            for m in chunk:
                z.write(os.path.join(dl_dir, m["id"] + ".jpg"),
                        arcname="evgesha-43-%s.jpg" % m["id"])
        downloads.append({
            "name": name, "part": n, "parts": len(chunks),
            "from": int(chunk[0]["id"]), "to": int(chunk[-1]["id"]),
            "count": len(chunk),
            "mb": round(os.path.getsize(path) / 1048576),
        })
        print("архив %s: кадры %d-%d, %d МБ"
              % (name, downloads[-1]["from"], downloads[-1]["to"], downloads[-1]["mb"]))

    keep_zips = {d["name"] for d in downloads}
    for name in os.listdir(out_root):
        if name.endswith(".zip") and name not in keep_zips:
            os.remove(os.path.join(out_root, name)); removed += 1

    with open(os.path.join(out_root, "photos.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out_root, "downloads.json"), "w", encoding="utf-8") as fh:
        json.dump(downloads, fh, ensure_ascii=False, separators=(",", ":"))
    print("для скачивания: %d кадров, %.0f МБ, частей %d"
          % (len(meta), total / 1048576, len(chunks)))

    for name, err in failed:
        print("не прочитался:", name, "-", err)
    print("готово: %d кадров, удалено лишних файлов: %d" % (len(meta), removed))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
