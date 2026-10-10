#!/usr/bin/env python3
"""Validate retained National Gallery of Australia partner metadata; no database mutations."""
import collections,importlib.util,re
from functools import lru_cache
from urllib.parse import unquote,urlsplit,parse_qs
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-ngaustralia-gac-capture-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
m=c.m;RUN=c.RUN;d=c.d;ref=c.ref
@lru_cache(maxsize=24)
def index_rows(path,digest):
 fp=m.ROOT/path;assert ref(fp)['sha256']==digest
 return c.cards(c.body(m.load(fp)['capture']))
def creation(v):
 # Normalize only the explicit circa marker, retaining the original date.
 text=re.sub(r'^(?:ca\.?|circa)\s+','c. ',v or '',flags=re.I)
 text=re.sub(r'^between (\d{3,4}) and (\d{3,4})$',r'\1-\2',text,flags=re.I)
 text=re.sub(r'^c(?=\d)', 'c.',text,flags=re.I)
 return dates.creation(text)
def checked_record(path):
 x=m.load(path);p=c.parsed_object(c.body(x['capture']));assert p==x['parsed']
 rc=x['capture']['receipt'];assert rc['url']==x['index']['url'] and unquote(rc['url'])==unquote(rc['final_url'])
 for reference in x['index']['index_refs']:
  fp=m.ROOT/reference['path'];assert ref(fp)==reference
  rows=index_rows(reference['path'],reference['sha256']);assert {k:x['index'][k] for k in ['source_id','title','creator','url']} in rows
 return x,p
def facts(x,p):
 fields={r['label']:r['value'] for r in p['fields']};assert len(fields)==len(p['fields'])
 assert fields['Title']==x['index']['title'] and p['headings']==[fields['Title']]
 sid=x['index']['source_id'];title=fields['Title'];creator=fields.get('Creator');source_type=fields.get('Type')
 types={'paintings':'painting','painting':'painting','drawings':'drawing','drawing':'drawing','sculptures':'sculpture','sculpture':'sculpture','wooden sculpture':'sculpture','prints':'print','print':'print','photograph':'photograph','photography':'photograph'}
 typeparts=(source_type or '').split(',',1);kind=typeparts[0].strip().lower();medium=fields.get('Medium') or (typeparts[1].strip() if len(typeparts)>1 else None)
 native=[a['url'] for r in p['fields'] if r['label']=='External Link' for a in r['links']];irns=[]
 for url in native:
  u=urlsplit(url);match=re.fullmatch(r'/object/(\d+)',u.path)
  if u.hostname=='searchthecollection.nga.gov.au' and match:irns.append(match[1])
  elif u.hostname=='artsearch.nga.gov.au' and u.path=='/Detail.cfm':irns+=parse_qs(u.query).get('IRN',[])
 assert len(set(irns))<=1
 dims=fields.get('Physical Dimensions');dimension_issue=None
 if dims and re.match(r'^w[\d.,]+\s*x\s*h[\d.,]+',dims):dimension_issue='Legacy partner dimension format has unresolved unit/scale reliability; retain literal source evidence and leave catalogue dimensions unknown.'
 titles=[title];t=re.sub(r'\s*-\s*Ned Kelly Series$', '',title,flags=re.I)
 if t!=title:titles.append(t)
 bilingual=re.fullmatch(r'(.+?)\s*\[([^\]]+)\]',title)
 if bilingual:titles.extend([bilingual[1].strip(),bilingual[2].strip()])
 return dict(source_id=sid,source_url=x['index']['url'],title=title,titles=list(dict.fromkeys(titles)),creator_label=creator,detail_creator_label=creator,date_display=fields.get('Date Created'),**creation(fields.get('Date Created')),inventory=fields.get('Inventory Number'),native_object_id=irns[0] if irns else None,medium=medium,dimensions_text=None if dimension_issue else dims,source_dimensions_text=dims,dimension_issue=dimension_issue,work_type=types.get(kind,'unknown'),object_form=None,publisher=fields.get('Publisher'),rights=fields.get('Rights'),copyright=fields.get('Copyright'),acquisition_text=fields.get('Rights') or fields.get('Copyright'),provenance=fields.get('Provenance'),native_external_links=native,native_fields=p['fields'],publisher_heading=p['publisher_heading'],source_type=source_type,source_note='Museum-published Google Arts & Culture object metadata. Native IRN is an object identifier, never an accession number. Unknown inventory and uncertain catalogue dimensions remain empty; exact source dimensions, creation wording, qualified creators, rights, acquisition credit and native links remain evidence. Documented collection connection only; no current-display, physical-custody or legal-title inference. Current native catalogue access failed and the older site returned navigation only.')
def candidates():
 capture=m.load(RUN/'gac-selected-capture-001.json.gz');out=[]
 for reference in capture['records']:
  path=m.ROOT/reference['path'];assert ref(path)==reference;x,p=checked_record(path);f=facts(x,p);holds=[]
  if f['date_issue']:holds.append(f['date_issue'])
  if not f['creator_label']:holds.append('No creator label supplied')
  if re.sub(r'\s+',' ',f['creator_label'] or '').strip()!=re.sub(r'\s+',' ',x['index']['creator'] or '').strip():holds.append('Index/object creator labels differ')
  if not f['native_object_id']:holds.append('No unique native museum object identity')
  if f['publisher_heading']!='National Gallery of Australia Canberra, Australia':holds.append('Publisher/collection identity requires review')
  if '/partner/national-gallery-of-australia-canberra' not in p['partner_links']:holds.append('Museum partner link absent')
  # An acquisition credit is not mandatory for a documented museum connection.
  # Missing credits remain unknown and require explicit editorial review.
  out.append(dict(source_id=f['source_id'],facts=f,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/'gac-candidates-002.json.gz',dict(at=m.now(),rows=out,counts=dict(collections.Counter(x['state'] for x in out)),policy='Metadata candidates only. Individual narrative, identity, casting/version and collection review required before additions.'))
 print(collections.Counter(x['state'] for x in out),flush=True)
if __name__=='__main__':candidates()
