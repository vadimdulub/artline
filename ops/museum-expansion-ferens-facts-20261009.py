"""Reproduce selected Ferens metadata; preserve literal qualifications and conflicts."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
p=module('p','museum-expansion-ferens-capture-20261009.py');dates=module('dates','museum-expansion-ferens-selection-v2-20261009.py');m=p.m;RUN=p.RUN;ref=p.ref;IID=p.p.IID
QUALIFIED={
 2:('Follower of Domeniico Beccafumi','by a follower of Domeniico Beccafumi'),
 3:('Attributed to Pieter Stevens II','attributed to Pieter Stevens II'),
 5:('Attributed to Pieter Stevens II','attributed to Pieter Stevens II'),
 6:('Attributed to the Dutch School','attributed to the Dutch School'),
 8:('Dutch School','Nativity, Dutch School'),
 9:('Durtch School','Mountainous Landscape with Figures, Durtch School'),
 17:('Attributed to Helst van der Bartolommeus','attributed to Helst van der Bartolommeus'),
 25:('Cornelius Norbertus Gysbrechts','by Cornelius Norbertus Gysbrechts'),
 29:('English School; possibly a copy of an 18th century original','Possibly a copy of an 18th century original'),
 31:('Attributed to Jonathan Richardson the Elder','attributed to Jonathan Richardson the Elder'),
 38:('Unknown artist; copy after Reynolds','Copy after Reynolds'),
 43:('Benjamin West; copy after Anton Raphael Mengs','copy after Anton Raphael Mengs'),
 45:('Benjamin West; copy after Guido Reni','Copy after Guido Reni'),
 48:('Joseph Wright of Derby','by Joseph Wright of Derby'),
 50:('Follower of Richard Wilson','by a follower of Richard Wilson'),
 57:('Charles James Sartorius','by Charles James Sartorius'),
 61:('Attributed to Romeyn/Romyn, Willem','Attributed to Romeyn/Romyn, Willem'),
 66:('English School; possibly a Norwich School painter','Possibly painted by a Norwich School painter'),
 67:('Hans Meyer; copy or in the manner of a Dutch genre painting','A copy or in the manner of a Dutch genre painting'),
 85:('Charles James Sartorius','by Charles James Sartorius'),
 125:('Attributed to David Roberts','attributed to David Roberts'),
}
DATE_OVERRIDES={
 3:('about 1600','about 1600'),5:('about 1600','about 1600'),
 16:('17th century','seventeenth century'),
 39:('18th century','late eighteenth century'),40:('18th century','late eighteenth century'),
 196:('about 1872','about 1872'),
}
SOURCE_HOLDS={
 4:'Date/Period repeats explicitly stated artist activity1507–1545; independent creation evidence unresolved.',
 43:'Native creator birth1783 conflicts with creation before1762; retain source inconsistency for resolution.',
 47:'Maker field Arthur William Devis conflicts with narrative Arthur Devis1712–1787; creator/version unresolved.',
 48:'Date field1777 conflicts with narrative about1781; Wright versions require reconciliation.',
 57:'Native creation1787 precedes source creator birth1794; same Sartorius conflict held in wave83.',
 67:'Date field1800–1899 repeats artist activity nineteenth century; copy/prototype date requires independent creation evidence.',
 74:'Native title contains apparent character encoding damage and a truncated ending; title/identity needs resolution.',
 208:'Native creator life1883–1901 conflicts with broad creation1875–1899; identity/date requires review.',
}
def checked(r):
 path=m.ROOT/r['path'];assert ref(path)==r;return path
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];assert cap['receipt']['status']==200;return raw
def facts(record):
 parsed=p.w.parsed(body(record['capture']));assert parsed==record['parsed'];n=record['number'];f=parsed['fields']
 def field(k):
  vs=f.get(k,[]);assert len(vs)<=1;return vs[0] if vs else None
 idx=record['index'];assert field('Title:')==idx['title'];assert field('Date/Period:')==idx['date'];assert field('Artist / Maker:')==idx['creator'];assert field('Object Name:')=='painting';assert idx['museum']=='Ferens Art Gallery'
 desc=field('Brief Description:');creator=field('Artist / Maker:');basis='Literal native Artist / Maker field.'
 if n in QUALIFIED:
  creator,quote=QUALIFIED[n];assert quote in desc;basis='Individually reviewed literal description qualification: '+quote
 date=dates.creation(field('Date/Period:'));assert date and date['first']<=date['last']<=1970
 if n in DATE_OVERRIDES:
  literal,quote=DATE_OVERRIDES[n];assert quote in desc;date=dates.creation(literal);date['date_display']=quote;date['date_basis']='Explicit artwork creation statement in native Brief Description: '+quote+'. Structured Date/Period retained separately; lifetime/activity endpoints are not used.'
 # Select only literal material phrases. More complex or absent media remain unknown.
 matches=re.findall(r'\bOil(?: painting)? on (?:canvas on oak panel|paper on oak panel|oak panel|mahogany panel|teak panel|canvas|panel|cardboard|pasteboard|paper|board|copper|ivory|glass)\b',desc,re.I)
 medium=max(matches,key=len) if matches else None
 if n==69:medium='Oil, gilding and incising on panel'
 if n==70:medium='Oil and gold on panel'
 if medium:assert medium.lower() in desc.lower()
 dims=parsed['dimensions'];dimension_text='; '.join(' | '.join(x) for x in dims) or None
 inv=field('Accession No:');assert inv and inv.startswith('KINCM:');other=field('Other Numbers:')
 url=record['url'];irn=idx['source_id'];sourceid='ferens-'+irn
 return dict(source_id=sourceid,native_object_id=irn,source_url=url,native_page_urls=[idx['url']],native_metadata_urls=[],title=field('Title:'),titles=[field('Title:')],creator_label=creator,detail_creator_label=creator,source_fields={'ATTRIBUZIONI':creator},creator_basis=basis,**date,inventory=inv,inventory_aliases=[v.strip() for v in (other or '').split(';') if v.strip()],medium=medium,dimensions_text=dimension_text,work_type='painting',object_form='icon' if n in (69,70) else None,native_fields=f,native_dimensions=dims,description=desc,native_date_display=field('Date/Period:'),source_limitation='Official collection index and accession-level catalogue. Undated Location on Display retained as source evidence only; no current display, physical custody or ownership assertion. No images downloaded. Qualified maker labels remain unlinked. Original field/narrative conflicts retained; dates refer to the selected artwork, not depicted events or prototypes.')
def main():
 dest=RUN/'native-candidates-001.json.gz';assert not dest.exists();cap=RUN/'native-captured-001.json.gz';data=m.load(cap);assert not data['requests_stopped'] and not data['unprocessed_numbers'];selection=RUN/'native-selection-001.json.gz';selected={r['number']:r for r in m.load(selection)['rows'] if r['state']=='selected_detail_review'};out=[]
 for r in data['rows']:
  assert r['state']=='captured_metadata';record=m.load(checked(r['reference']));assert record['index']==selected[r['number']]['index'];v=facts(record);reasons=[SOURCE_HOLDS[r['number']]] if r['number'] in SOURCE_HOLDS else []
  out.append(dict(number=r['number'],institution_id=IID,source_id=v['source_id'],source_reference=r['reference'],index=record['index'],facts=v,state='source_hold' if reasons else 'candidate',reasons=reasons))
 m.save(dest,dict(at=m.now(),rows=out,capture_reference=ref(cap),selection_reference=ref(selection),script_reference=ref(Path(__file__).resolve()),policy='Source candidates only. Manual qualifier/date mappings quote retained native descriptions. Full original metadata remains evidence. Every candidate still needs current cross-catalogue physical identity and grouping review.'));print(json.dumps(dict(rows=len(out),states=dict(collections.Counter(r['state'] for r in out)))),flush=True)
if __name__=='__main__':main()
