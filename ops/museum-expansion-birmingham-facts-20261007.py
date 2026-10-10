#!/usr/bin/env python3
"""Validate selected Birmingham native metadata; no database changes."""
import importlib.util,re,collections
from pathlib import Path
from functools import lru_cache
from urllib.parse import unquote
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-birmingham-native-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
m=c.m;d=c.d;RUN=c.RUN;ref=c.ref
@lru_cache(maxsize=20)
def checked_index(path,digest):
 fp=m.ROOT/path;assert ref(fp)['sha256']==digest;x=m.load(fp);parsed=c.index(c.body(x['capture']));assert parsed==x['parsed'];return parsed['rows']
def checked_record(path):
 x=m.load(path);p=c.parsed(c.body(x['capture']));assert p==x['parsed'];rc=x['capture']['receipt'];assert rc['url']==rc['final_url']==x['index']['url']
 for reference in x['index']['index_refs']:
  rows=checked_index(reference['path'],reference['sha256']);assert {k:x['index'][k] for k in ['source_id','url','title','creator_label','medium']} in rows
 return x,p

def creation(raw):
 t=re.sub(r'^(?:about|around|circa|ca\.?)\s+','c. ',raw or '',flags=re.I)
 t=re.sub(r'^c\.(?=\d)', 'c. ',t,flags=re.I)
 period=re.fullmatch(r'.+? (?:dynasty|period) \((\d{3,4})\s*-\s*(\d{3,4})\), (.+)',t,re.I)
 if period:
  value=creation(period[3])
  if value['date_issue'] is None and value['first'] is not None and int(period[1])<=value['first']<=value['last']<=int(period[2]):return value
  return dict(first=None,last=None,date_precision='unknown',date_issue='Creation suffix does not agree with explicit cultural-period bounds')
 # Slash-separated full years are retained as a bounded source envelope;
 # this does not assert uninterrupted production between the two endpoints.
 slash=re.fullmatch(r'(c\.\s*)?(\d{3,4})\s*/\s*(\d{1,4})',t,re.I)
 if slash:
  first=int(slash[2]);last=int(slash[3]) if len(slash[3])==len(slash[2]) else (first//(10**len(slash[3])))*(10**len(slash[3]))+int(slash[3])
  if 100<=first<=last<=1970 and not (slash[1] and last==1970):return dict(first=first,last=last,date_precision='circa_range' if slash[1] else 'range',date_issue=None)
 qualifier=r'(?:(?:early|mid|late)[ -]|(?:first|second) half(?: of(?: the)?)? )?'
 cent=re.fullmatch(qualifier+r'(\d{1,2})(?:st|nd|rd|th)(?:[–/-]'+qualifier+r'(\d{1,2})(?:st|nd|rd|th))? century',t,re.I)
 if cent:
  first=(int(cent[1])-1)*100+1;last=int(cent[2] or cent[1])*100
  if 100<=first<=last<=1970:return dict(first=first,last=last,date_precision='circa_range' if cent[2] else 'century',date_issue=None)
 return dates.creation(t)

def facts(x,p):
 fields={r['label']:r['value'] for r in p['fields']};assert len(fields)==len(p['fields'])
 assert p['title']==x['index']['title'];assert unquote(p['canonical'])==unquote(x['index']['url'])
 credit=fields.get('Credit Line');inv=re.search(r'(?:^|,\s*)((?:AFI\.?\s*)?\d{1,4}\.[A-Za-z0-9.\-]+(?:\s*[–-]\s*[A-Za-z0-9.]+)?)$',(credit or '').split(', image ',1)[0])
 work=fields.get('Work Type');kind={'painting':'painting','drawing':'drawing','print':'print','sculpture':'sculpture'}.get(work,'unknown');title=p['title'];titles=[title];alternate=fields.get('Titles')
 # Parenthetical wording supplies discovery labels only, never invented catalogue
 # alternate titles or asserted translations. Empty punctuation and front/back
 # component labels do not become global title lookups.
 bilingual=re.fullmatch(r'(.+?) \(([^()]+)\)',title)
 if bilingual and len(m.norm(bilingual[2]))>=3 and m.norm(bilingual[2]) not in ['front','back','recto','verso']:titles.extend([bilingual[1],bilingual[2]])
 return dict(source_id=x['index']['source_id'],source_url=x['index']['url'],native_object_id=p['native_object_id'],title=title,titles=list(dict.fromkeys(titles)),creator_label=p['creator_label'],detail_creator_label=p['creator_label'],native_artist_field=fields.get('Artist'),date_display=p['date_display'],date_basis='Literal source creation wording preserved. Slash-separated full years use both endpoints as a search envelope, without asserting continuous production; qualified centuries retain whole named centuries. No artist-life or acquisition-year inference.',**creation(p['date_display']),inventory=inv[1] if inv else None,medium=fields.get('Medium'),dimensions_text=fields.get('Dimensions'),work_type=kind,object_form=None,source_work_type=work,source_classification=fields.get('Classification'),credit_line=credit,provenance=fields.get('Provenance'),native_fields=p['fields'],narrative=p['narrative'],alternate_titles_field=alternate,source_note='Official Birmingham Museum of Art Alabama collection page with original HTTP bytes and source timestamps. Creation field is distinct from artist life, acquisition, inscription and exhibition dates. Native WordPress object ID is distinct from credit-line accession. Full creator qualifications, narrative, provenance, grouping, source rights and unknown fields are preserved. Collection connection only, not current display, custody or legal title.')

def candidates():
 refs=m.load(RUN/'selected-capture-001.json.gz')['records'];out=[]
 for reference in refs:
  path=m.ROOT/reference['path'];assert ref(path)==reference;x,p=checked_record(path);f=facts(x,p);holds=[]
  if f['date_issue']:holds.append(f['date_issue'])
  if not f['inventory']:holds.append('No unambiguous accession extracted from credit line')
  if not f['creator_label']:holds.append('No creator/cultural label supplied')
  if f['creator_label']!=x['index']['creator_label']:holds.append('Index/object attribution differs')
  if f['medium']!=x['index']['medium']:holds.append('Index/object medium differs')
  if f['source_classification']!='Paintings':holds.append('Source classification differs from selected filter')
  if 'Birmingham Museum of Art' not in (p['footer'] or ''):holds.append('Museum identity footer absent')
  out.append(dict(source_id=f['source_id'],facts=f,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/'native-candidates-002.json.gz',dict(at=m.now(),rows=out,counts=dict(collections.Counter(x['state'] for x in out)),policy='Source eligibility candidates only. Object/version/attribution/provenance/collection and database identity review required before additions. No new artwork, museum link, image or display claim.'))
 print(collections.Counter(x['state'] for x in out),flush=True)
if __name__=='__main__':candidates()
