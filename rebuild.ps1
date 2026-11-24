# Пересборка альбома: веб-версии фото -> страница -> публикация.
#
#   .\rebuild.ps1                        — берёт фото из ..\фотки
#   .\rebuild.ps1 -Src "D:\другая\папка" — из своей папки
#   .\rebuild.ps1 -NoPush                — собрать локально, без выкладки
#
# Что делает: читает ВСЕ снимки из папки (HEIC, JPG, PNG), пересчитывает
# веб-версии, заново нумерует кадры по времени съёмки, вырезает EXIF и GPS,
# пересобирает index.html и выкладывает на GitHub Pages.

param(
    [string] $Src = (Join-Path (Split-Path $PSScriptRoot -Parent) "фотки"),
    [switch] $NoPush
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# -X utf8=1, а не PYTHONIOENCODING: флаг -I игнорирует переменные окружения
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

if (-not (Test-Path -LiteralPath $Src)) { throw "Папка с фото не найдена: $Src" }

$n = (Get-ChildItem -LiteralPath $Src -File |
      Where-Object { $_.Extension -match '^\.(heic|heif|jpg|jpeg|png|webp|tif|tiff)$' }).Count
"Исходных снимков в папке: $n"
""

"[1/3] Веб-версии фото"
python -X utf8=1 -I tools\build_web.py $Src .
if ($LASTEXITCODE -ne 0) { throw "build_web.py упал" }

""
"[2/3] Страница"
python -X utf8=1 -I tools\gen_index.py .
if ($LASTEXITCODE -ne 0) { throw "gen_index.py упал" }

if ($NoPush) {
    ""
    "Готово локально. Выложить: git add -A, затем git commit и git push"
    return
}

""
"[3/3] Публикация"
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { "Изменений нет, публиковать нечего."; return }

$count = (Get-Content photos.json -Raw | ConvertFrom-Json).Count
git commit -q -m "Альбом пересобран: $count кадров"
git push -q origin main
if ($LASTEXITCODE -ne 0) { throw "git push не прошёл" }

""
"Готово: $count кадров -> https://as45671234.github.io/evgesha-43/"
"Обновление доезжает примерно за минуту."
