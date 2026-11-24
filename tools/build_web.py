"""Оригиналы с телефона -> веб-версии для альбома.

На каждый снимок: full (2000 px по длинной стороне), thumb (900 px)
и крошечная размытая заглушка для плавной загрузки.
EXIF и GPS вырезаются. Пишет photos.json: порядок, размеры, время, заглушка.

    python tools/build_web.py <папка-с-оригиналами> <корень-альбома>
"""
import os, sys, glob, json, base64, io, time, zipfile
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
import pillow_heif

pillow_heif.register_heif_opener()

ZIP_NAME = "evgesha-43-photos.zip"

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

        # JPEG для скачивания: webp открывается не везде, JPEG — везде
        full.save(os.path.join(dl_dir, slug + ".jpg"), "JPEG",
                  quality=85, subsampling=0, optimize=True, progressive=True)

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

    # архив «скачать все» — статическому хостингу его на лету не собрать
    zip_path = os.path.join(out_root, ZIP_NAME)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for m in meta:
            z.write(os.path.join(dl_dir, m["id"] + ".jpg"),
                    arcname="evgesha-43-%s.jpg" % m["id"])
    print("архив: %s, %.0f МБ" % (ZIP_NAME, os.path.getsize(zip_path) / 1048576))

    with open(os.path.join(out_root, "photos.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, separators=(",", ":"))

    for name, err in failed:
        print("не прочитался:", name, "-", err)
    print("готово: %d кадров, удалено лишних файлов: %d" % (len(meta), removed))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
