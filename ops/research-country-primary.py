#!/usr/bin/env python3
"""Cross-check selected Rijksmuseum objects against the official Linked Art API."""
import argparse,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlencode,urlparse
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def values(value,key):
 if isinstance(value,dict):
  for k,v in value.items():
   if k==key:yield v
   yield from values(v,key)
 elif isinstance(value,list):
  for v in value:yield from values(v,key)

def capture(code,number):
 run=m.x.BASE/code/f'round-{number:02d}'/'delivery';path=run/'official-object-review.json'
 if path.exists():return
 records=[json.loads(p.read_text())['record'] for p in sorted((run/'ready').glob('Q*.json'))];results=[]
 for rec in records:
  if rec['collection']['qid']!='Q190804' or not rec['accession']:continue
  q=rec['qid'];acc=rec['accession'];item={'qid':q,'accession':acc,'review':'needs_review'}
  try:
   data,receipt=m.x.r.fetch('https://data.rijksmuseum.nl/search/collection?'+urlencode({'objectNumber':acc}))
   ids=data.get('orderedItems',[])
   if len(ids)!=1 or data.get('partOf',{}).get('totalItems')!=1:raise ValueError('Official accession search not unique')
   uri=ids[0]['id'];assert urlparse(uri).hostname=='id.rijksmuseum.nl'
   obj,oreceipt=m.x.r.fetch(uri+'?_profile=la-framed');assert obj['id']==uri and obj['type']=='HumanMadeObject'
   accessions=[n['content'] for n in obj.get('identified_by',[]) if n.get('type')=='Identifier' and n.get('content')]
   if m.m.accession_key(acc) not in {m.m.accession_key(a) for a in accessions}:raise ValueError('Official object accession differs')
   production=obj.get('produced_by',{});people=[];qualifier_notes=[]
   if any(re.search(r'rejected attribution|verworpen toeschrijving',str(n),re.I) for n in values(production,'content')):raise ValueError('Museum explicitly rejects the source creator attribution')
   for part in production.get('part',[]):
    for person in part.get('carried_out_by',[]):
     if person.get('type')=='Person':people.append(person)
    for assignment in part.get('assigned_by',[]):
     if assignment.get('assigned_property')!='carried_out_by':continue
     notes=[n.get('content','') for n in part.get('referred_to_by',[])]
     if not any('(mentioned on object)' in n or '(signed by artist)' in n for n in notes) or any(re.search(r'attributed to|copy after|workshop|school of|possibly|probably',n,re.I) for n in notes):raise ValueError('Qualified museum attribution needs editorial review')
     qualifier_notes.extend(notes)
     for person in assignment.get('assigned',[]):
      if person.get('type')=='Person' and urlparse(person.get('id','')).hostname=='id.rijksmuseum.nl':
       full,preceipt=m.x.r.fetch(person['id']+'?_profile=la-framed');people.append(full)
   ids={url.rsplit('/',1)[-1] for person in people for url in values(person,'id') if isinstance(url,str) and 'wikidata.org/' in url}
   if ids!={rec['creator_qid']}:raise ValueError('Official creator authority requires reconciliation')
   time_span=production.get('timespan',{});first=time_span.get('begin_of_the_begin');last=time_span.get('end_of_the_end')
   years=[int(v[:4]) if v and re.match(r'^\d{4}-',v) else None for v in [first,last]]
   d=rec['date']
   if all(y is not None for y in years) and d['first'] is not None and (years[1]<d['first'] or years[0]>d['last']):raise ValueError('Official creation range conflicts with candidate date')
   # Direct museum person IDs are a corroborating authority, never a name-only link.
   people_evidence=[]
   for person in people:
    person_uri=person.get('id','')
    if urlparse(person_uri).hostname=='id.rijksmuseum.nl':
     pe,preceipt=m.x.r.fetch(person_uri+'?_profile=la-framed');people_evidence.append({'id':person_uri,'entity':pe,'receipt':preceipt})
   item.update(review='official_object_creator_and_accession_corroborated',object_url=uri,object_receipt=oreceipt,search_receipt=receipt,creator_qids=sorted(ids),official_creation_bounds=years,official_date_display=[n.get('content') for n in time_span.get('identified_by',[])],people=people_evidence,metadata_licence='https://creativecommons.org/publicdomain/zero/1.0/',creator_qualification_notes=qualifier_notes,date_policy='Museum source bounds retained; no automatic replacement of existing uncertain dating. Current display not inferred or imported.')
  except Exception as e:item['reason']=type(e).__name__+': '+str(e)[:300]
  results.append(item);print(code,number,'official museum',q,item['review'],flush=True)
 m.m.core.save_new(path,{'at':m.m.core.now(),'records':results,'verified':sum(r['review']=='official_object_creator_and_accession_corroborated' for r in results)})

def cite(code,number,target):
 batch=m.configure(code,number);run=m.m.r.RUN;path=run/('official-citations-'+target+'.json')
 if path.exists():return
 review_path=run/'official-object-review.json'
 if not review_path.exists():
  # Some country scopes have no Rijksmuseum objects and therefore no capture.
  # Missing evidence for a real Rijksmuseum candidate must still stop delivery.
  assert not any(json.loads(p.read_text())['record']['collection']['qid']=='Q190804' for p in (run/'ready').glob('Q*.json')),'Rijksmuseum candidate lacks primary object review'
  m.m.core.save_new(path,{'at':m.m.core.now(),'citations':[],'reason':'No Rijksmuseum candidates in this scope.'})
  return
 review=json.loads(review_path.read_text());out=[]
 with m.m.r.base.connect(target=='production') as db:
  for e in review['records']:
   receipt=run/'applied'/target/(e['qid']+'.json')
   if e['review']!='official_object_creator_and_accession_corroborated' or not receipt.exists():continue
   aid=json.loads(receipt.read_text())['artwork_id']
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)')
    slug='overnight-rijksmuseum-primary-20260913' if m.x.SESSION_NAME=='overnight-countries-20260913' else m.x.SESSION_NAME+'-rijksmuseum-primary'
    sid=m.m.source(db,slug,'Rijksmuseum official object and creator authority cross-checks','museum_api','https://data.rijksmuseum.nl/')
    exists=db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='official_object_identity'",(aid,sid)).fetchone()
    if not exists:m.m.r.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='official_object_identity',source_record_id=e['object_url'].rsplit('/',1)[-1],source_url=e['object_url'],retrieved_at=e['object_receipt']['retrieved_at'],created_by=m.m.ACTOR,evidence_note=json.dumps({k:v for k,v in e.items() if k!='people'},ensure_ascii=False)))
   out.append({'artwork_id':aid,'qid':e['qid'],'object_url':e['object_url']})
 m.m.core.save_new(path,{'at':m.m.core.now(),'citations':out});print(target,'official citations',len(out),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['capture','cite']);p.add_argument('--country',choices=m.x.COUNTRIES,required=True);p.add_argument('--round',type=int,required=True);p.add_argument('--target',choices=['local','production']);a=p.parse_args();capture(a.country,a.round) if a.command=='capture' else cite(a.country,a.round,a.target)
