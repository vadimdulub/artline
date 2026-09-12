"""Render and structurally verify the canonical catalogue continuation report."""

from html import escape
from pathlib import Path
import hashlib
import json
import re

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "output/pdf/catalogue-expansion-september-10.pdf"
checks = json.loads((ROOT / "output/continuation-applied-verification.json").read_text())
replay = json.loads((ROOT / "output/continuation-replay-verification.json").read_text())
before = json.loads((ROOT / "output/continuation-before-verification.json").read_text())
preview = json.loads((ROOT / "output/continuation-preview-verification.json").read_text())
api = json.loads((ROOT / "output/continuation-api-verification.json").read_text())
assert checks["counts"]["artworks"] == 63073
assert checks["counts"]["artworks"] - before["counts"]["artworks"] == 28809
assert checks["invalid"] == 0
assert checks["fingerprints"] == replay["fingerprints"]
assert before["fingerprints"] == preview["fingerprints"]
assert checks["types"] == {"painting": 9985, "drawing": 24133, "print": 28950, "fresco": 5}
assert len(api["requests"]) == 26
assert [row["status"] for row in api["requests"]] == [200] * 24 + [401, 404]

fonts = Path("/System/Library/Fonts/Supplemental")
for name, filename in [
    ("AtlasSans", "Arial.ttf"),
    ("AtlasBold", "Arial Bold.ttf"),
    ("AtlasSerif", "Georgia.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))

INK = colors.HexColor("#211d18")
MUTED = colors.HexColor("#645d53")
ACCENT = colors.HexColor("#91402d")
LINE = colors.HexColor("#d0c9be")
styles = {
    "title": ParagraphStyle("title", fontName="AtlasSerif", fontSize=27, leading=32,
                            spaceAfter=11, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="AtlasSerif", fontSize=20, leading=26,
                         spaceAfter=13, keepWithNext=True, textColor=INK),
    "body": ParagraphStyle("body", fontName="AtlasSans", fontSize=9.3, leading=13.4,
                           spaceAfter=10, textColor=INK),
    "small": ParagraphStyle("small", fontName="AtlasSans", fontSize=8, leading=11.5,
                            spaceAfter=15, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="AtlasSans", fontSize=8.6, leading=12,
                           textColor=INK),
    "label": ParagraphStyle("label", fontName="AtlasBold", fontSize=8.5, leading=12,
                            spaceAfter=12, textColor=ACCENT),
}


def markup(value):
    value = re.sub("[\u2010-\u2015]", "-", str(value))
    parts, pos = [], 0
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", value):
        parts.append(escape(value[pos:match.start()]))
        parts.append(
            f'<link href="{escape(match[2], quote=True)}" color="#91402d">'
            f'<u>{escape(match[1])}</u></link>'
        )
        pos = match.end()
    return "".join(parts) + escape(value[pos:])


def paragraph(value, kind="body"):
    return Paragraph(markup(value), styles[kind])


def table(lines):
    rows = [
        [paragraph(cell.strip(), "cell") for cell in row.strip("|").split("|")]
        for row in lines if not re.match(r"^\|[-: |]+\|$", row)
    ]
    result = Table(rows, colWidths=[149, 73, A4[0] - 314], repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7dfd2")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(46, 43, A4[0] - 46, 43)
    canvas.setFont("AtlasSans", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(46, 29, "ARTLINE / VERIFIED LOCAL EXPANSION / 10 SEPTEMBER 2026")
    canvas.drawRightString(A4[0] - 46, 29, str(doc.page))
    canvas.restoreState()


source = (HERE / "report-source.md").read_text()
story = [paragraph("RESEARCH + IMPLEMENTATION / PROGRESS REPORT", "label")]
sections = 0
for block in re.split(r"\n\s*\n", source.strip()):
    line = re.sub(r"\s*\n\s*", " ", block).strip()
    if line.startswith("# "):
        story.append(paragraph(line[2:], "title"))
    elif line.startswith("Audience:"):
        story.append(paragraph(line, "small"))
    elif line.startswith("## "):
        if sections:
            story.append(PageBreak())
        story.append(paragraph(line[3:], "h2"))
        sections += 1
    elif line.startswith("|"):
        story.extend([table(block.splitlines()), Spacer(1, 13)])
    else:
        story.append(paragraph(line))

if OUT.exists():
    raise FileExistsError(OUT)
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(
    str(OUT), pagesize=A4, leftMargin=46, rightMargin=46, topMargin=44,
    bottomMargin=60, title="Artline - Catalogue expansion, 10 September 2026",
    author="Artline research",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
pdf = PdfReader(OUT)
extracted = "\n".join(page.extract_text() or "" for page in pdf.pages)
links = [
    annotation.get_object().get("/A", {}).get("/URI")
    for page in pdf.pages for annotation in page.get("/Annots", [])
]
expected = re.findall(r"\[[^\]]+\]\((https?://[^\s)]+)\)", source)
assert set(expected) <= set(links), "A source hyperlink was lost"
for phrase in ["63,073", "28,809", "26,295", "2,075", "439", "9,985", "63,071", "54,484"]:
    assert phrase in extracted, phrase
assert not re.search(r"turn\d+(view|search)|tool_call|\u25a0", extracted)
assert len(pdf.pages) == 2, f"Unexpected page count: {len(pdf.pages)}"
print(json.dumps({
    "path": str(OUT), "pages": len(pdf.pages), "links": len(links),
    "bytes": OUT.stat().st_size, "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
}))
