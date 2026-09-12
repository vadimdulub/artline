"""Render and validate the source-linked report; never modifies source evidence.

Run from repository root:
uv run --with reportlab --with pypdf python docs/research/european-deep-expansion/render_report.py
"""
from collections import Counter
from html import escape
from pathlib import Path
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle
from pypdf import PdfReader

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
OUT = ROOT / "output/pdf/european-deep-expansion.pdf"
data = json.loads((SOURCE / "inventory.json").read_text())
receipt = json.loads((ROOT / "output/european-deep-applied.json").read_text())
works, institutions = data["works"], data["institutions"]
assert len(works) == 157 and len(institutions) == 28 and receipt["created_artworks"] == 155
assert receipt["applied"] and len({i["country"] for i in institutions}) == 14
assert len({w["url"] for w in works}) == 157

names = {
    "Q102272": "Jan van Eyck", "Q104884": "Caspar David Friedrich", "Q105320": "Berthe Morisot",
    "Q134741": "Camille Pissarro", "Q159758": "J. M. W. Turner", "Q17169": "Giovanni Bellini",
    "Q184212": "Théodore Géricault", "Q191423": "Domenico Ghirlandaio", "Q191748": "Lucas Cranach the Elder",
    "Q192062": "Bartolomé Esteban Murillo", "Q203371": "Georges de La Tour", "Q209615": "Francisco de Zurbarán",
    "Q23380": "Jean-Auguste-Dominique Ingres", "Q296": "Claude Monet", "Q297": "Diego Velázquez",
    "Q301": "El Greco", "Q33477": "Eugène Delacroix", "Q34661": "Gustav Klimt",
    "Q380706": "Vilhelm Hammershøi", "Q39931": "Pierre-Auguste Renoir", "Q40599": "Édouard Manet",
    "Q41264": "Johannes Vermeer", "Q41406": "Edvard Munch", "Q41554": "Nicolas Poussin",
    "Q42207": "Caravaggio", "Q47551": "Titian", "Q49898": "Hyacinthe Rigaud", "Q5432": "Francisco Goya",
    "Q5580": "Albrecht Dürer", "Q5582": "Vincent van Gogh", "Q5589": "Henri Matisse", "Q5597": "Raphael",
    "Q5598": "Rembrandt van Rijn", "Q5599": "Peter Paul Rubens", "Q5669": "Sandro Botticelli",
    "Q5681": "Andrea Mantegna", "Q762": "Leonardo da Vinci", "Q83155": "Jacques-Louis David",
    "Q8459": "Giorgione", "Q9319": "Tintoretto", "Q9440": "Paolo Veronese",
}
assert set(data["painters"]) == set(names)
font_dir = Path("/System/Library/Fonts/Supplemental")
for name, file in [("AtlasSans", "Arial.ttf"), ("AtlasSansBold", "Arial Bold.ttf"), ("AtlasSerif", "Georgia.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / file)))
pdfmetrics.registerFontFamily("AtlasSans", normal="AtlasSans", bold="AtlasSansBold", italic="AtlasSans", boldItalic="AtlasSansBold")
ink, muted, accent = [colors.HexColor(c) for c in ["#211d18", "#645d53", "#91402d"]]
styles = {
    "title": ParagraphStyle("title", fontName="AtlasSerif", fontSize=29, leading=35, spaceAfter=19, textColor=ink),
    "h2": ParagraphStyle("h2", fontName="AtlasSerif", fontSize=18, leading=23, spaceBefore=16, spaceAfter=9, keepWithNext=True, textColor=ink),
    "body": ParagraphStyle("body", fontName="AtlasSans", fontSize=10, leading=14.5, spaceAfter=10, textColor=ink),
    "small": ParagraphStyle("small", fontName="AtlasSans", fontSize=8.4, leading=11.5, spaceAfter=6, textColor=muted),
    "work": ParagraphStyle("work", fontName="AtlasSans", fontSize=10, leading=13.5, spaceAfter=4, textColor=ink),
    "label": ParagraphStyle("label", fontName="AtlasSansBold", fontSize=9, leading=12, spaceAfter=9, textColor=accent),
}

def plain(s):
    return re.sub("[\u2010-\u2015]", "-", str(s))

def markup(s):
    text = plain(s)
    pieces, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", text):
        pieces.append(escape(text[pos:m.start()]))
        pieces.append(f'<link href="{escape(m[2], quote=True)}" color="#91402d"><u>{escape(m[1])}</u></link>')
        pos = m.end()
    pieces.append(escape(text[pos:]))
    return "".join(pieces)

def p(s, kind="body"):
    return Paragraph(markup(s), styles[kind])

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d0c9be"))
    canvas.line(46, 43, A4[0] - 46, 43)
    canvas.setFont("AtlasSans", 8)
    canvas.setFillColor(muted)
    canvas.drawString(46, 29, "ARTLINE / EUROPEAN COLLECTIONS / 9 SEPTEMBER 2026")
    canvas.drawRightString(A4[0]-46, 29, str(doc.page))
    canvas.restoreState()

story = [p("ARTLINE RESEARCH / SECOND EUROPEAN EXPANSION", "label"), Spacer(1, 20),
         p("European painting\ncollections", "title"), p("Deeper source research and verified local import", "h2"),
         p("157 selected paintings / 41 painters / 28 collections / 14 countries", "body"), Spacer(1, 16)]
metrics = Table([[p("155 new artworks", "work"), p("19 new institutions", "work")],
                 [p("338 new citations", "work"), p("17 museum highlights", "work")]], colWidths=[251, 251], hAlign="LEFT")
metrics.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eee9df")),
                            ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#d0c9be")),
                            ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                            ("LEFTPADDING", (0, 0), (-1, -1), 14)]))
story += [metrics, Spacer(1, 24),
          p("The local catalogue now holds 600 artworks and 55 institutions. Two existing records were enriched without duplication. New records remain in review; no images were downloaded or works published."),
          p("Reading guide", "h2"),
          p("The research brief explains findings, source quality, rights and safeguards. The museum-by-museum appendix links every selected object and records materials, dimensions, dates and the distinctions that need editorial care."),
          p("Scope: selected museum paintings created by 1970, with explicit uncertainty where necessary. This report does not claim exhaustive European holdings, current display, legal title or independent authentication.", "small"),
          PageBreak()]

for block in re.split(r"\n\s*\n", (SOURCE / "report-source.md").read_text().strip()):
    text = re.sub(r"\s*\n\s*", " ", block).strip()
    if text.startswith("# "):
        story.append(p("Research brief", "title"))
    elif text.startswith("## "):
        story.append(p(text[3:], "h2"))
    else:
        story.append(p(text))

story += [PageBreak(), p("Selected object catalogue", "title"),
          p("157 reviewed records; 155 added and 2 enriched", "h2"),
          p("Linked titles are the authoritative source records. All sources accessed 9 September 2026; update dates are shown only when stated. Museum holdings are not current-display promises. Source wording and material/support limitations are preserved. No asset download is licensed by this report."),
          p("The companion JSON contains additional aliases, exact API/IIIF links, source access notes and retained identifiers. The applied JSON receipt maps every source to its local artwork ID.", "small")]

for inst in sorted(institutions, key=lambda i: (i["country"], i["city"], i["name"])):
    group = sorted([w for w in works if w["institution"] == inst["id"]], key=lambda w: (names[w["painter"]], w["title"]))
    intro = [p(inst["name"], "h2"), p(f'{inst["city"]}, {inst["country"]} / {len(group)} selected records', "label")]
    route = "Data: " + inst["data_route"] + "."
    if inst.get("data_url"):
        route += f' [Source/data route]({inst["data_url"]}).'
    rights = "Images: " + inst["rights"]
    if inst.get("rights_url"):
        rights += f' [Rights evidence]({inst["rights_url"]}).'
    intro += [p(route, "small"), p(rights, "small")]
    for index, w in enumerate(group):
        heading = f'{names[w["painter"]]} / [{w["title"]}]({w["url"]})'
        precision = w["creation_date"]["precision"].replace("_", " ")
        ident = w.get("accession") or w.get("source_object_id") or "Accession not established"
        details = f'{w["date_display"]} ({precision}) / {ident}'
        pieces = [p(heading, "work"), p(details, "small"), p(f'{w["medium"]}. {w["dimensions"]}.', "small")]
        if w.get("attribution"):
            pieces.append(p("Attribution: " + w["attribution"], "small"))
        if w.get("owner") or w.get("custody"):
            pieces.append(p("; ".join(x for x in ["Recorded owner: " + w["owner"] if w.get("owner") else "",
                                                     "Custody: " + w["custody"] if w.get("custody") else ""] if x), "small"))
        if w.get("notes"):
            pieces.append(p(w["notes"], "small"))
        if w.get("museum_highlight_url"):
            pieces.append(p(f'[Museum-designated highlight evidence]({w["museum_highlight_url"]})', "small"))
        if w.get("source_updated_on"):
            pieces.append(p("Source updated: " + w["source_updated_on"], "small"))
        pieces.append(Spacer(1, 8))
        story.append(KeepTogether((intro if index == 0 else []) + pieces))

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=46, rightMargin=46, topMargin=43, bottomMargin=58,
                        title="European painting collections - Artline deep expansion", author="Artline research", pageCompression=1)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
pdf = PdfReader(OUT)
text = "\n".join(page.extract_text() or "" for page in pdf.pages)
links = sum(len(page.get("/Annots", [])) for page in pdf.pages)
assert links >= 157
assert not any(x in text for x in ["\ufffd", "turn323", "TODO", "<nil>"])
assert all(plain(w["title"]) in text.replace("\n", " ") for w in works)
print(json.dumps({"path": str(OUT), "pages": len(pdf.pages), "links": links,
                  "artworks": len(works), "collections": len(institutions), "countries": len({i["country"] for i in institutions}),
                  "new_artworks": receipt["created_artworks"], "new_institutions": receipt["created_museums"]}))
