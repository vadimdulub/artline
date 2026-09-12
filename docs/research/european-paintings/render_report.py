"""Render the canonical research narrative and complete candidate inventory.

Run from the repository root:
  uv run --with reportlab --with pypdf python docs/research/european-paintings/render_report.py
"""
from collections import Counter
from html import escape
from pathlib import Path
import json
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from pypdf import PdfReader

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
OUT = ROOT / "output/pdf/european-painting-collections.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
data = json.loads((SOURCE / "inventory.json").read_text())
works, institutions = data["works"], data["institutions"]
assert len(works) == 59 and len(institutions) == 26
assert len({item["country"] for item in institutions}) == 12
assert len({item["url"] for item in works}) == len(works)
assert all(item["institution"] in {i["id"] for i in institutions} for item in works)
assert data["defaults"]["image_download_authorized"] is False

font_dir = Path("/System/Library/Fonts/Supplemental")
for name, filename in [("AtlasSans", "Arial.ttf"), ("AtlasSansBold", "Arial Bold.ttf"), ("AtlasSerif", "Georgia.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily("AtlasSans", normal="AtlasSans", bold="AtlasSansBold", italic="AtlasSans", boldItalic="AtlasSansBold")
ink = colors.HexColor("#211d18")
muted = colors.HexColor("#625b52")
accent = colors.HexColor("#91402d")
styles = {
    "title": ParagraphStyle("title", fontName="AtlasSerif", fontSize=27, leading=33, spaceAfter=22, textColor=ink),
    "h2": ParagraphStyle("h2", fontName="AtlasSerif", fontSize=19, leading=24, spaceBefore=17, spaceAfter=10, keepWithNext=True, textColor=ink),
    "body": ParagraphStyle("body", fontName="AtlasSans", fontSize=10, leading=14.5, spaceAfter=10, textColor=ink, alignment=TA_LEFT),
    "small": ParagraphStyle("small", fontName="AtlasSans", fontSize=8.5, leading=12, spaceAfter=7, textColor=muted),
    "work": ParagraphStyle("work", fontName="AtlasSans", fontSize=9.5, leading=13, spaceAfter=5, textColor=ink),
}

def plain(value):
    return str(value).replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")

def markup(text):
    text = plain(text)
    parts, pos = [], 0
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", text):
        parts.append(escape(text[pos:match.start()]))
        parts.append(f'<link href="{escape(match[2], quote=True)}" color="#91402d"><u>{escape(match[1])}</u></link>')
        pos = match.end()
    parts.append(escape(text[pos:]))
    return "".join(parts)

def p(text, kind="body"):
    return Paragraph(markup(text), styles[kind])

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d0c9be"))
    canvas.line(48, 42, A4[0]-48, 42)
    canvas.setFont("AtlasSans", 8)
    canvas.setFillColor(muted)
    canvas.drawString(48, 28, "ARTLINE  /  EUROPEAN COLLECTION RESEARCH  /  9 SEPTEMBER 2026")
    canvas.drawRightString(A4[0]-48, 28, str(doc.page))
    canvas.restoreState()

story = []
source = (SOURCE / "report-source.md").read_text()
for block in re.split(r"\n\s*\n|\n(?=\d+\. )", source.strip()):
    text = re.sub(r"\s*\n\s*", " ", block).strip()
    if text == "## Candidate catalogue":
        break
    if text.startswith("# "):
        story.append(p(text[2:], "title"))
    elif text.startswith("## "):
        story.append(p(text[3:], "h2"))
    else:
        story.append(p(text))

story += [PageBreak(), p("Candidate catalogue", "title"), p("59 works / 26 institutions / 12 countries", "h2")]
story.append(p("All sources accessed 9 September 2026. Unless noted, the source is the named institution’s own artwork record and its update date was not stated. Linked artwork titles are citations. Records support catalogue custody and the stated attribution, not an independent authenticity judgment or a current-display guarantee. Image reuse remains a separate review. No candidate has been imported by this research."))

for institution in sorted(institutions, key=lambda item: (item["country"], item["city"], item["name"])):
    group = [w for w in works if w["institution"] == institution["id"]]
    heading = p(institution["name"], "h2")
    location = p(f'{institution["city"]}, {institution["country"]} - {len(group)} candidate {"record" if len(group) == 1 else "records"}', "small")
    intro = [heading, location]
    route = institution.get("data_route", "No automated access route verified.")
    if institution.get("data_url"):
        route += f' [Official data documentation]({institution["data_url"]}).'
    rights = institution.get("rights", "Image reuse not verified.")
    if institution.get("rights_url"):
        rights += f' [Official rights evidence]({institution["rights_url"]}).'
    intro += [p("Data: " + route, "small"), p("Images: " + rights, "small")]
    for index, work in enumerate(group):
        title = f'{work["painter"]} - [{work["title"]}]({work["url"]})'
        ident = work.get("accession") or ("National catalogue " + work["source_object_id"] if work.get("source_object_id") else "Accession not verified")
        details = f'{work["date_display"]} | {ident}'
        if work.get("attribution"):
            details += " | " + work["attribution"]
        source_note = f'Source: {work.get("source_publisher", institution["name"])}; updated {work.get("source_updated_on") or "not stated"}; {work.get("access", "official object record")}; accessed 2026-09-09.'
        pieces = [p(title, "work"), p(details, "small")]
        if work.get("notes"):
            pieces.append(p(work["notes"], "small"))
        if work.get("aliases"):
            pieces.append(p("Aliases: " + "; ".join(work["aliases"]), "small"))
        if work.get("owner"):
            pieces.append(p("Documented owner: " + work["owner"] + ". Keep distinct from custodian.", "small"))
        if work.get("iiif"):
            pieces.append(p(f'[Object IIIF manifest]({work["iiif"]}) - availability alone does not clear image reuse.', "small"))
        if work.get("source_updated_on") or work.get("access") or work.get("source_publisher"):
            pieces.append(p(source_note, "small"))
        pieces.append(Spacer(1, 7))
        story.append(KeepTogether((intro if index == 0 else []) + pieces))

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=45, bottomMargin=56,
                        title="European painting collections - Artline research", author="Artline research", pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
pdf = PdfReader(OUT)
all_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
links = sum(len(page.get("/Annots", [])) for page in pdf.pages)
assert "Candidate catalogue" in all_text
assert links >= len(works)
assert not any(token in all_text for token in ["turn178", "turn179", "\ufffd"])
print(json.dumps({"path": str(OUT), "pages": len(pdf.pages), "links": links, "works": len(works), "institutions": len(institutions), "painter_counts": dict(Counter(w["painter"] for w in works))}))
