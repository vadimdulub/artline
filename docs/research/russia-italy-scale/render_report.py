"""Render the canonical progress report; source facts remain in report-source.md."""
from pathlib import Path
from html import escape
import hashlib
import json
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/'output/pdf/russia-italy-catalogue-expansion.pdf'
checks=json.loads((ROOT/'output/russia-italy-verification.json').read_text())
api=json.loads((ROOT/'output/russia-italy-api-optimized.json').read_text())
assert checks['counts']['artworks']==34264
assert checks['new_artworks']==32041 and checks['new_images']==19
assert checks['replays_unchanged'] and checks['unsafe_new_rows']==0
assert all(r['status']==200 for r in api['results'][:-2])
fonts=Path('/System/Library/Fonts/Supplemental')
for name,file in [('AtlasSans','Arial.ttf'),('AtlasBold','Arial Bold.ttf'),('AtlasSerif','Georgia.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
ink=colors.HexColor('#211d18');muted=colors.HexColor('#645d53');accent=colors.HexColor('#91402d')
styles={
 'title':ParagraphStyle('title',fontName='AtlasSerif',fontSize=26,leading=31,spaceAfter=12,textColor=ink),
 'h2':ParagraphStyle('h2',fontName='AtlasSerif',fontSize=21,leading=27,spaceAfter=14,keepWithNext=True,textColor=ink),
 'body':ParagraphStyle('body',fontName='AtlasSans',fontSize=9.5,leading=13.7,spaceAfter=11,textColor=ink),
 'small':ParagraphStyle('small',fontName='AtlasSans',fontSize=8,leading=11,spaceAfter=12,textColor=muted),
 'cell':ParagraphStyle('cell',fontName='AtlasSans',fontSize=8.3,leading=11.8,textColor=ink),
 'label':ParagraphStyle('label',fontName='AtlasBold',fontSize=9,leading=12,spaceAfter=12,textColor=accent),
}
def markup(s):
    s=re.sub('[\u2010-\u2015]','-',str(s));parts=[];pos=0
    for m in re.finditer(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',s):
        parts.append(escape(s[pos:m.start()]));parts.append(f'<link href="{escape(m[2],quote=True)}" color="#91402d"><u>{escape(m[1])}</u></link>');pos=m.end()
    return ''.join(parts)+escape(s[pos:])
def p(s,kind='body'):return Paragraph(markup(s),styles[kind])
def table(lines):
    rows=[[p(c.strip(),'cell') for c in row.strip('|').split('|')] for row in lines if not re.match(r'^\|[-: |]+\|$',row)]
    t=Table(rows,colWidths=[164,73,266],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7dfd2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.8,accent),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d0c9be'))]))
    return t
def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#d0c9be'));c.line(46,43,A4[0]-46,43);c.setFont('AtlasSans',8);c.setFillColor(muted);c.drawString(46,29,'ARTLINE / CATALOGUE EXPANSION / 9 SEPTEMBER 2026');c.drawRightString(A4[0]-46,29,str(doc.page));c.restoreState()
source=(HERE/'report-source.md').read_text()
story=[p('RESEARCH + IMPLEMENTATION / VERIFIED PROGRESS','label')]
section=0
for block in re.split(r'\n\s*\n',source.strip()):
    text=re.sub(r'\s*\n\s*',' ',block).strip()
    if text.startswith('# '):story.append(p(text[2:],'title'))
    elif text.startswith('Audience:'):story.append(p(text,'small'))
    elif text.startswith('## '):
        if section:story.append(PageBreak())
        story.append(p(text[3:],'h2'));section+=1
    elif text.startswith('|'):
        story.extend([table(block.splitlines()),Spacer(1,13)])
    else:story.append(p(text))
if OUT.exists():raise FileExistsError(OUT)
OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=44,bottomMargin=60,title='Artline - Russian and Italian museum catalogue expansion',author='Artline research')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
pdf=PdfReader(OUT)
text='\n'.join(page.extract_text() or '' for page in pdf.pages)
links=[a.get_object().get('/A',{}).get('/URI') for page in pdf.pages for a in page.get('/Annots',[])]
expected=re.findall(r'\[[^\]]+\]\((https?://[^\s)]+)\)',source)
assert set(expected)<=set(links)
for phrase in ['34,264','32,041','15,736','3,851','1,729','4,628','2018','2,716','450']:
    assert phrase in text,phrase
assert not re.search(r'turn\d+(view|search)|tool_call|\u25a0',text)
assert len(pdf.pages)<=6
print(json.dumps({'path':str(OUT),'pages':len(pdf.pages),'links':len(links),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}))
