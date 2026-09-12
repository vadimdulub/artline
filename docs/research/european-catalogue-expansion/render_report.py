"""Build a concise source-linked catalogue supplement from verified local receipts.
Run with: uv run --with reportlab --with pypdf python <this file>
"""
from collections import Counter
from html import escape
from pathlib import Path
import hashlib
import json
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from pypdf import PdfReader

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
OUT = ROOT / "output/pdf/european-catalogue-expansion.pdf"
raw = (SOURCE / "inventory.json").read_bytes()
data = json.loads(raw)
receipt = json.loads((ROOT / "output/european-catalogue-applied.json").read_text())
checks = json.loads((ROOT / "output/european-catalogue-verification.json").read_text())
assert receipt["applied"] and receipt["snapshot_sha256"] == hashlib.sha256(raw).hexdigest()
assert checks["dry_run_unchanged"] and checks["replays_unchanged"]
assert checks["after"]["artworks"] == checks["before"]["artworks"] + receipt["created_artworks"]
works = data["works"]
assert len(receipt["works"]) == len(works)
names = {
    "Q296":"Claude Monet", "Q134741":"Camille Pissarro", "Q47551":"Titian", "Q5597":"Raphael",
    "Q42207":"Caravaggio", "Q297":"Diego Velázquez", "Q5598":"Rembrandt", "Q5599":"Peter Paul Rubens",
    "Q5582":"Vincent van Gogh", "Q35548":"Paul Cézanne", "Q46373":"Edgar Degas", "Q39931":"Pierre-Auguste Renoir",
    "Q5669":"Sandro Botticelli", "Q41554":"Nicolas Poussin", "Q159758":"J. M. W. Turner", "Q148458":"Jean-François Millet",
    "Q40599":"Édouard Manet", "Q37693":"Paul Gauguin", "Q34013":"Georges Seurat", "Q175130":"Alfred Sisley",
    "Q148475":"Camille Corot", "Q151573":"Paul Signac", "Q34618":"Gustave Courbet", "Q82445":"Henri de Toulouse-Lautrec",
}
assert set(data["painters"]) <= set(names)
fonts = Path("/System/Library/Fonts/Supplemental")
for name, file in [("AtlasSans","Arial.ttf"),("AtlasSansBold","Arial Bold.ttf"),("AtlasSerif","Georgia.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
ink, muted, accent = [colors.HexColor(c) for c in ("#211d18","#645d53","#91402d")]
styles = {
    "title":ParagraphStyle("title",fontName="AtlasSerif",fontSize=29,leading=35,spaceAfter=18,textColor=ink),
    "h2":ParagraphStyle("h2",fontName="AtlasSerif",fontSize=18,leading=23,spaceBefore=14,spaceAfter=8,keepWithNext=True,textColor=ink),
    "body":ParagraphStyle("body",fontName="AtlasSans",fontSize=10,leading=14.5,spaceAfter=10,textColor=ink),
    "small":ParagraphStyle("small",fontName="AtlasSans",fontSize=8.5,leading=11.5,spaceAfter=6,textColor=muted),
    "work":ParagraphStyle("work",fontName="AtlasSans",fontSize=9.2,leading=12.2,spaceAfter=3,textColor=ink),
    "label":ParagraphStyle("label",fontName="AtlasSansBold",fontSize=9,leading=12,spaceAfter=10,textColor=accent),
}
def plain(s): return re.sub("[\u2010-\u2015]", "-", str(s))
def markup(s):
    s = plain(s)
    chunks, pos = [], 0
    for m in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)",s):
        chunks.append(escape(s[pos:m.start()]))
        chunks.append(f'<link href="{escape(m[2],quote=True)}" color="#91402d"><u>{escape(m[1])}</u></link>')
        pos=m.end()
    return "".join(chunks)+escape(s[pos:])
def p(s,kind="body"): return Paragraph(markup(s),styles[kind])
def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor("#d0c9be"));c.line(46,43,A4[0]-46,43)
    c.setFont("AtlasSans",8);c.setFillColor(muted)
    c.drawString(46,29,"ARTLINE / CATALOGUE SUPPLEMENT / 9 SEPTEMBER 2026")
    c.drawRightString(A4[0]-46,29,str(doc.page));c.restoreState()

story=[p("ARTLINE RESEARCH / THIRD EUROPEAN EXPANSION","label"),Spacer(1,18),
       p("More paintings,\nbetter catalogue evidence","title"),
       p(f'{receipt["created_artworks"]} new artworks / {len(data["painters"])} painters / {len(data["institutions"])} museum collections',"h2"),
       p(f'The local catalogue now contains {checks["after"]["artworks"]} artworks. This supplement expands existing museum coverage; it does not claim a complete census.'),
       p("All additions remain in review. No images downloaded, works published, display assertions added, or commits made."),Spacer(1,16)]
for block in re.split(r"\n\s*\n",(SOURCE/"report-source.md").read_text().strip()):
    text=re.sub(r"\s*\n\s*"," ",block).strip()
    if text.startswith("# "): continue
    if text.startswith("## "): story.append(p(text[3:],"h2"))
    else: story.append(p(text))
story += [PageBreak(),p("Selected object catalogue","title"),
          p("Every linked title opens the museum’s official object record. Dates are creation dates; dimensions are of the object, not its frame. Source access: 9 September 2026. Source update dates appear where supplied; otherwise unknown. Approximate/range wording is retained. These are holdings, not promises of current display.","small")]
for inst in data["institutions"]:
    group=sorted([w for w in works if w["institution"]==inst["id"]],key=lambda w:(names[w["painter"]],w["title"]))
    noun = "addition" if len(group) == 1 else "additions"
    story += [p(inst["name"],"h2"),p(f'{inst["city"]}, {inst["country"]} / {len(group)} {noun}',"label")]
    for w in group:
        facts=f'{names[w["painter"]]} / {w["date_display"]} / {w["accession"]}'
        dimensions=f'{w["medium"]}; {w["dimensions"]}'
        if w.get("source_updated_on"):
            dimensions += f' / Source updated {w["source_updated_on"]}'
        story.append(KeepTogether([p(f'[{w["title"]}]({w["url"]})',"work"),p(facts,"small"),p(dimensions,"small"),Spacer(1,3)]))
story += [p("Coverage boundary","h2"),p("The research inventory retains source response hashes, catalogue references, aliases, provenance and unresolved alternatives. Reproductions require a separate rights check. Complete European coverage, current room locations and public publication approval remain outside this batch.","small")]
if OUT.exists(): raise FileExistsError(OUT)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=45,bottomMargin=59,
    title="Artline - European catalogue expansion",author="Artline research")
doc.build(story,onFirstPage=footer,onLaterPages=footer)
pdf=PdfReader(OUT)
text="\n".join(page.extract_text() or "" for page in pdf.pages)
for w in works:
    assert plain(w["accession"]) in text, w["accession"]
links=[a.get_object().get("/A",{}).get("/URI") for page in pdf.pages for a in page.get("/Annots",[])]
assert all(w["url"] in links for w in works)
assert len(pdf.pages)<18
print(json.dumps({"path":str(OUT),"pages":len(pdf.pages),"source_links":len(links),"bytes":OUT.stat().st_size,"sha256":hashlib.sha256(OUT.read_bytes()).hexdigest()}))
