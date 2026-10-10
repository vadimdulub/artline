#!/usr/bin/env python3
"""Validate retained Budapest partner metadata; no database mutations."""
import collections,importlib.util,re
from functools import lru_cache
from urllib.parse import unquote
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-budapest-gac-capture-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
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
 types={'paintings':'painting','painting':'painting','drawings':'drawing','drawing':'drawing','sculptures':'sculpture','sculpture':'sculpture','wooden sculpture':'sculpture','prints':'print','print':'print'}
 return dict(source_id=sid,source_url=x['index']['url'],title=title,titles=[title],creator_label=creator,detail_creator_label=creator,date_display=fields.get('Date Created'),**creation(fields.get('Date Created')),inventory=fields.get('Inventory Number'),medium=fields.get('Medium'),dimensions_text=fields.get('Physical Dimensions'),work_type=types.get((source_type or '').lower(),'unknown'),object_form=None,publisher=fields.get('Publisher'),rights=fields.get('Rights'),native_external_links=[a['url'] for r in p['fields'] if r['label']=='External Link' for a in r['links']],native_fields=p['fields'],publisher_heading=p['publisher_heading'],source_type=source_type,source_note='Museum-published Google Arts & Culture object metadata. Exact creation wording, inventory, publisher, rights and external native links retained. Documented collection connection only; no current-display, physical-custody or legal-title inference. The native museum site was unavailable during this pass.')
def candidates():
 capture=m.load(RUN/'gac-selected-capture-001.json.gz');out=[]
 for reference in capture['records']:
  path=m.ROOT/reference['path'];assert ref(path)==reference;x,p=checked_record(path);f=facts(x,p);holds=[]
  if f['date_issue']:holds.append(f['date_issue'])
  if not f['creator_label']:holds.append('No creator label supplied')
  if re.sub(r'\s+',' ',f['creator_label'] or '').strip()!=re.sub(r'\s+',' ',x['index']['creator'] or '').strip():holds.append('Index/object creator labels differ')
  if not f['inventory']:holds.append('No inventory number supplied')
  if f['publisher']!='Museum of Fine Arts Budapest' or f['publisher_heading']!='Museum of Fine Arts, Budapest Budapest, Hungary':holds.append('Publisher/collection identity requires review')
  if '/partner/museum-of-fine-arts-budapest' not in p['partner_links']:holds.append('Museum partner link absent')
  out.append(dict(source_id=f['source_id'],facts=f,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/'gac-candidates-001.json.gz',dict(at=m.now(),rows=out,counts=dict(collections.Counter(x['state'] for x in out)),policy='Metadata candidates only. Individual narrative, identity, casting/version and collection review required before additions.'))
 print(collections.Counter(x['state'] for x in out),flush=True)
if __name__=='__main__':candidates()
