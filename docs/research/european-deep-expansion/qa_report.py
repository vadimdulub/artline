"""Create PDF-review contact sheets from Poppler renders, not artwork assets."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[3]
folder = root / "tmp/pdfs/deep-expansion"
pages = sorted(folder.glob("page-*.png"))
assert len(pages) == 31
for start in range(0, len(pages), 6):
    sheet = Image.new("RGB", (1260, 1260), "#d8d4cd")
    draw = ImageDraw.Draw(sheet)
    for j, path in enumerate(pages[start:start+6]):
        pic = Image.open(path).convert("RGB")
        pic.thumbnail((400, 570))
        x, y = (j % 3) * 420 + 10, (j // 3) * 630 + 35
        sheet.paste(pic, (x, y))
        draw.text((x, y-22), f"Page {start+j+1}", fill="black")
    target = folder / f"contact-{start//6+1}.jpg"
    sheet.save(target, quality=90)
    print(target)
