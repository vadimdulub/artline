"""Generate the source-linked research report from verified local receipts."""
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
OUT=ROOT/'output/pdf/us-europe-museum-research.pdf'
checks=json.loads((ROOT/'output/us-europe-verification.json').read_text())
coverage=json.loads((HERE/'assembled/coverage.json').read_text())
nga=json.loads((ROOT/'docs/research/nga-catalogue-expansion/reviewed/summary.json').read_text())
applied=json.loads((ROOT/'output/nga-catalogue-applied.json').read_text())
directory=json.loads((HERE/'assembled/museum-directory.json').read_text())
assert checks['replays_unchanged'] and checks['dry_run_unchanged'] and checks['unsafe_new_rows']==0
assert checks['after']['artworks']==checks['before']['artworks']+applied['created_artworks']==2223
assert len(directory)==coverage['stage_rows']==5869
assert len({r['record_id'] for r in directory if r['source']=='wikidata'})==4542
fonts=Path('/System/Library/Fonts/Supplemental')
for name,file in [('AtlasSans','Arial.ttf'),('AtlasBold','Arial Bold.ttf'),('AtlasSerif','Georgia.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
ink=colors.HexColor('#211d18');muted=colors.HexColor('#645d53');accent=colors.HexColor('#91402d')
styles={
 'title':ParagraphStyle('title',fontName='AtlasSerif',fontSize=29,leading=35,spaceAfter=18,textColor=ink),
 'h2':ParagraphStyle('h2',fontName='AtlasSerif',fontSize=17,leading=22,spaceBefore=13,spaceAfter=8,keepWithNext=True,textColor=ink),
 'body':ParagraphStyle('body',fontName='AtlasSans',fontSize=9.5,leading=13.4,spaceAfter=9,textColor=ink),
 'small':ParagraphStyle('small',fontName='AtlasSans',fontSize=8,leading=11,spaceAfter=7,textColor=muted),
 'cell':ParagraphStyle('cell',fontName='AtlasSans',fontSize=8,leading=10,textColor=ink),
 'label':ParagraphStyle('label',fontName='AtlasBold',fontSize=9,leading=12,spaceAfter=12,textColor=accent),
}
def markup(s):
    s=re.sub('[\u2010-\u2015]','-',str(s));parts=[];pos=0
    for m in re.finditer(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',s):
        parts.append(escape(s[pos:m.start()]));parts.append(f'<link href="{escape(m[2],quote=True)}" color="#91402d"><u>{escape(m[1])}</u></link>');pos=m.end()
    return ''.join(parts)+escape(s[pos:])
def p(s,kind='body'):return Paragraph(markup(s),styles[kind])
def table(rows,widths):
    t=Table([[p(c,'cell') for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7dfd2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.8,accent),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d0c9be'))]))
    return t
def footer(c,doc):
    c.saveState();c.setStrokeColor(colors.HexColor('#d0c9be'));c.line(46,43,A4[0]-46,43);c.setFont('AtlasSans',8);c.setFillColor(muted);c.drawString(46,29,'ARTLINE / MUSEUM COVERAGE / 9 SEPTEMBER 2026');c.drawRightString(A4[0]-46,29,str(doc.page));c.restoreState()

story=[p('ARTLINE RESEARCH / US + EUROPE','label'),Spacer(1,13),p('A museum inventory.\nA larger art catalogue.','title'),p('2,223 artworks / 4,542 museum candidates','h2'),p('A verified first systematic pass, with explicit source and coverage limits. Prepared for the Artline owner on 9 September 2026.'),Spacer(1,10)]
rows=[['Measure','Before','After'],['Catalogue artworks','715','2,223'],['Catalogue institutions','56','56'],['Museum discovery candidates','Not staged','4,542'],['Official Muséofile directory rows','Not staged','1,216'],['Research source records','0','10,324'],['Downloaded media assets','211','211'],['Published artworks / display claims','0 / 0','0 / 0']]
story += [table(rows,[303,95,105]),Spacer(1,14),p('Source counts overlap. Discovery candidates include buildings, branches and unresolved institutions; they are not a complete census of active art museums. NGA staging includes accepted and deferred/out-of-scope records, not 4,455 extra published artworks.','small'),PageBreak()]
source=(HERE/'report-source.md').read_text()
for block in re.split(r'\n\s*\n',source.strip()):
    text=re.sub(r'\s*\n\s*',' ',block).strip()
    if text.startswith('# '):continue
    if text.startswith('Audience:'):story.append(p(text,'small'))
    elif text.startswith('## '):story.append(p(text[3:],'h2'))
    else:story.append(p(text))

story += [PageBreak(),p('NGA review outcomes','title'),p('4,455 source painting records. One primary decision per row; a row can have additional issues in its raw evidence. The selected 1,510 include two existing artworks. These categories are not independent estimates of every possible source defect.','small')]
labels={'eligible':'Eligible and linked to existing authorities','creator_authority_requires_review':'Local creator authority unresolved','qualified_creator_requires_review':'Qualified/current creator needs review','multiple_or_missing_creators':'Multiple or missing creators','date_literal_requires_review':'Literal date needs review','date_literal_numeric_conflict':'Literal/numeric date conflict','date_crosses_1970':'Creation interval crosses 1970','after_1970':'After 1970','inseparable_child_record':'Inseparable intellectual child','accession_or_virtual_requires_review':'Accession or virtual-object review'}
story.append(table([['Primary decision','Records']]+[[labels.get(k,k),str(v)] for k,v in sorted(nga['decisions'].items(),key=lambda kv:-kv[1])]+[['Total',str(nga['painting_catalogue_records'])]],[423,80]))
story += [Spacer(1,15),p('Data available now','h2'),p('Catalogue fields include title, creation date, medium, labelled dimensions, accession, painter, holding and source citations. Full source provenance, inscriptions, credits, relationships, terms and catalogue texts remain in the separate backend evidence store. There is no new public bulk-data endpoint or provenance reader UI.'),p('Next local opportunity','h2'),p('1,636 of the 1,699 artist-authority backlog records carry source QIDs, spanning 647 distinct IDs not in the currently matched cohort. Reconcile these with existing names and authority conflicts before creating sourced review artists. The remaining 63 need an alternative authority route.')]

names=dict(item.split(':',1) for item in 'US:United States|AL:Albania|AD:Andorra|AT:Austria|BY:Belarus|BE:Belgium|BA:Bosnia and Herzegovina|BG:Bulgaria|HR:Croatia|CZ:Czechia|DK:Denmark|EE:Estonia|FI:Finland|FR:France|DE:Germany|GR:Greece|VA:Holy See|HU:Hungary|IS:Iceland|IE:Ireland|IT:Italy|LV:Latvia|LI:Liechtenstein|LT:Lithuania|LU:Luxembourg|MT:Malta|MD:Moldova|MC:Monaco|ME:Montenegro|NL:Netherlands|MK:North Macedonia|NO:Norway|PL:Poland|PT:Portugal|RO:Romania|RU:Russia*|SM:San Marino|RS:Serbia|SK:Slovakia|SI:Slovenia|ES:Spain|SE:Sweden|CH:Switzerland|UA:Ukraine|GB:United Kingdom|AX:Åland|FO:Faroe Islands|GG:Guernsey|IM:Isle of Man|JE:Jersey|SJ:Svalbard and Jan Mayen|GI:Gibraltar|CY:Cyprus*|TR:Turkey*|AM:Armenia*|AZ:Azerbaijan*|GE:Georgia*|XK:Kosovo*'.split('|'))
story += [PageBreak(),p('Country / territory coverage','title'),p('Wikidata candidate identities per partition, not unique active museums. Country overlaps can make row totals exceed 4,542. Basic queries did not request closure, parent or place fields. * Boundary/geographic review scope. Italy is missing, not zero. A zero count means the query found no matching entries, not that the country has no museums.','small')]
rows=[['Country / territory','Candidates','Query coverage']]
for c in sorted(coverage['country_coverage'],key=lambda c:names[c['country']]):
    state='Unavailable' if c['status']=='unavailable' else ('Basic retry' if c.get('query_method','').startswith('basic') else 'Detailed')
    rows.append([f"{names[c['country']]} ({c['country']})",'Unknown' if c['unique_candidates'] is None else str(c['unique_candidates']),state])
story += [table(rows,[263,90,150])]
if OUT.exists():raise FileExistsError(OUT)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=45,bottomMargin=59,title='Artline - US and European museum research',author='Artline research')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
pdf=PdfReader(OUT);text='\n'.join(page.extract_text() or '' for page in pdf.pages)
links=[a.get_object().get('/A',{}).get('/URI') for page in pdf.pages for a in page.get('/Annots',[])]
expected=re.findall(r'\[[^\]]+\]\((https?://[^\s)]+)\)',source)
assert set(expected)<=set(links)
for phrase in ['2,223','4,542','1,508','1,216','10,324','Italy (IT)','Unknown','1,699']:
    assert phrase in text,phrase
assert len(pdf.pages)<16
print(json.dumps({'path':str(OUT),'pages':len(pdf.pages),'links':len(links),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}))
