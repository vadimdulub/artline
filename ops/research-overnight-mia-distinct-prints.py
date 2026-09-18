#!/usr/bin/env python3
"""Review held Mia print titles using independent museum physical-object IDs."""
import argparse,collections,csv,hashlib,importlib.util,json,re,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('mia_import',Path(__file__).with_name('import-overnight-mia-selection.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core;review=m.print_review

def catalogue(path,receipt_path,id_field,wanted):
    receipt=json.loads(receipt_path.read_text())
    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['sha256']
    with path.open(encoding='utf-8-sig') as f:return {o[id_field]:o for o in csv.DictReader(f) if o[id_field] in wanted},receipt

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--source',choices=['mia','cleveland','smk'],default='mia');p.add_argument('--limit',type=int,default=0);a=p.parse_args();r=a.run;r.mkdir(parents=True,exist_ok=True);root=r.parent;leads={};mia_objects={}
 for folder in ('mia-new','mia-followup','mia-popular-followup'):
  source=root/folder
  for c in json.loads((source/'source-leads.json').read_text()):
   if c['work_type']=='print':leads[c['source_object_id']]=c
  for typ in ('paintings','drawings','prints'):
   for row in json.loads((source/(typ+'-metadata.json')).read_text())['records']:mia_objects[str(row['object']['id'])]=row
 for file in ('client-resource-evidence.json','reviewed-public-policy-evidence.json','institution-verified.json'):shutil.copyfile(root/'mia-followup'/file,r/file)
 if a.source=='smk':
  active=m.module('smk_import','import-overnight-smk-selection.py');leads={}
  for folder in ('smk-new','smk-native','smk-linked-followup','smk-new-artist-works','smk-next-artist-works'):
   for c in json.loads((root/folder/'source-leads.json').read_text()):
    if c['work_type']=='print':leads[c['source_object_id']]=c
  records=[active.candidate(c,r) for c in leads.values()];institution=active.INSTITUTION;schemes=[active.smk.SCHEME,'smk-object']
 elif a.source=='cleveland':
  active=m.module('cleveland_import','import-overnight-cleveland-selection.py');leads={}
  for folder in ('cleveland-new','cleveland-followup'):
   for c in json.loads((root/folder/'source-leads.json').read_text()):
    if c['work_type']=='print':leads[c['source_object_id']]=c
  records=[active.candidate(c) for c in leads.values()];institution=active.museum.SLUG;schemes=[active.museum.SCHEME,'cleveland-object']
 else:records=[m.candidate(c,r) for c in leads.values()];institution=m.INSTITUTION;schemes=['mia-object']
 with m.mia.ro('postgres://localhost/artline') as db:
  if a.source=='smk':state=active.snapshot(db,[dict(c,physical_object_review={'pending':True}) for c in records])
  else:
   state=m.guard.snapshot(db,records,institution,schemes)
   state=review.augment(db,[dict(c,physical_object_review={'pending':True}) for c in records],state)
 existing={x['external_id'] for x in state['identifiers'] if x['scheme'] in schemes}
 records=[c for c in records if c['external_id'] not in existing]
 native=state['review_native_keys'];wanted=collections.defaultdict(set)
 for keys in native.values():
  for key in keys:
   provider,oid=key.split(':',1);wanted[provider].add(oid)
 met,met_receipt=catalogue(root/'met-new/MetObjects.csv',root/'met-new/MetObjects.receipt.json','Object ID',wanted['met'])
 nga,nga_receipt=catalogue(root/'nga/metadata/objects.csv',root/'nga/metadata/objects.receipt.json','objectid',wanted['nga'])
 cleveland={};cap=json.loads((root/'cleveland-new/capture.json').read_text())
 for receipt in cap['pages']:
  raw=(root/'cleveland-new/metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['data']:
   oid=str(o['id'])
   if oid in wanted['cleveland'] and oid not in cap['conflicting_object_ids']:cleveland[oid]=(o,receipt)
 smk=m.module('smk_source_review','overnight-smk-selected-images.py');smk_objects={};smk_cap=json.loads((root/'smk-new/capture.json').read_text())
 for receipt in smk_cap['pages']:
  raw=(root/'smk-new/metadata'/(core.sha(receipt['url'].encode())+'.json')).read_bytes();assert core.sha(raw)==receipt['sha256']
  for o in json.loads(raw)['items']:
   if o['object_number'] in wanted['smk'] and o['object_number'] not in smk_cap['duplicate_accession_numbers']:smk_objects[o['object_number']]=(o,receipt)
 proofs={};proof_holds=[]
 for w in state['works']:
  keys=native.get(w['id'],[])
  if len(keys)!=1:continue
  key=keys[0];provider,oid=key.split(':',1)
  try:
   if provider=='met':
    o=met[oid];assert o['Classification']=='Prints' and o['Repository']=='Metropolitan Museum of Art, New York, NY'
    assert not re.search(r'loan|lent by|private collection|deaccession',o['Credit Line'],re.I)
    title=o['Title'];acc=o['Object Number'];url='https://www.metmuseum.org/art/collection/search/'+oid;receipt=met_receipt
   elif provider=='nga':
    o=nga[oid];assert o['classification'].lower()=='print' and o['accessioned']=='1' and o['isvirtual']=='0'
    title=o['title'];acc=o['accessionnum'];url='https://purl.org/nga/collection/artobject/'+oid;receipt=nga_receipt
   elif provider=='mia':
    row=mia_objects[oid];o=row['object'];assert o['classification'].strip()=='Prints'
    assert not re.match(r'^L',o['accession_number'],re.I) and not re.search(r'loan|lent by|private collection|deaccession',o.get('creditline') or '',re.I)
    title=o['title'];acc=o['accession_number'];url='https://collections.artsmia.org/art/'+oid;receipt=row['metadata_capture']
   elif provider=='cleveland':
    o,receipt=cleveland[oid];assert o['type']=='Print' and o['legal_status']=='accessioned' and o['on_loan'] is False and o['record_type']=='object' and not o.get('cover_accession_number')
    title=o['title'];acc=o['accession_number'];url=o['url'];assert url in ('https://www.clevelandart.org/art/'+acc,'https://clevelandart.org/art/'+acc)
   elif provider=='smk':
    o,receipt=smk_objects[oid];assert smk.work_type(o)=='print' and o.get('responsible_department') and o.get('acquisition_date')
    assert not re.search(r'\b(verso|recto)\b',oid,re.I)
    title=next(t['title'] for t in o['titles'] if review.norm(t.get('title'))==review.norm(w['title']));acc=o['object_number'];url=o['frontend_url'];assert url=='https://open.smk.dk/artwork/image/'+acc
   else:continue
   assert acc and review.norm(w['accession_number'])==review.norm(acc) and review.norm(w['title'])==review.norm(title)
   proofs[key]={'key':key,'object_type':'print','title':title,'accession_number':acc,'source_url':url,'source_capture_url':receipt['url'],'source_capture_sha256':receipt['sha256'],'retrieved_at':receipt['retrieved_at'],'holding_evidence':'Separately accessioned physical museum object in the official collection dataset; no display assertion.'}
  except (KeyError,AssertionError,StopIteration,ValueError):proof_holds.append({'key':key,'reason':'Current official catalogue does not fully confirm existing physical-object facts'})
 by_title=collections.defaultdict(list)
 for w in state['works']:
  for aid in w['artist_ids']:by_title[(aid,review.norm(w['title']))].append(w)
 new_by_title=collections.defaultdict(list)
 for c in records:
  new_by_title[(c.get('artist_authority') if a.source=='smk' else c['artist_qid'],review.norm(c['title']))].append(c)
 selected=[];held=[]
 for c in records:
  people=state['artists'].get(c['artist_authority'] if a.source=='smk' else c['artist_qid'],[])
  if len(people)!=1:continue
  collisions=by_title[(people[0]['id'],review.norm(c['title']))];evidence=[];reason=None
  for old in collisions:
   keys=native.get(old['id'],[])
   if len(keys)!=1 or keys[0] not in proofs:reason='A title collision lacks independently verified physical-object identity';break
   evidence.append(proofs[keys[0]])
  if reason:held.append({'source_object_id':c['external_id'],'reason':reason});continue
  for other in new_by_title[(c.get('artist_authority') if a.source=='smk' else c['artist_qid'],review.norm(c['title']))]:
   if other['external_id']==c['external_id']:continue
   receipt=other['raw']['metadata_capture'];evidence.append({'key':review.key(a.source,other['external_id']),'object_type':'print','title':other['title'],'accession_number':other['accession_number'],'source_url':other['page'],'source_capture_url':receipt['url'],'source_capture_sha256':receipt['sha256'],'retrieved_at':receipt['retrieved_at'],'holding_evidence':'Exact museum record, separate accession; loan and ownership restrictions excluded by the source adapter.'})
  decision={'decision':'distinct_accessioned_prints','candidate_key':review.key(a.source,c['external_id']),'candidate_accession':c['accession_number'],'objects':evidence,'note':'These are distinct museum-accessioned physical print objects. Shared titles/designs do not merge impressions. All native-ID, accession, attribution, scope and image-rights guards remain required.'}
  c['physical_object_review']=decision
  if collisions and not review.allow(c,collisions,[],state):held.append({'source_object_id':c['external_id'],'reason':'Physical-object review guard failed'});continue
  lead=dict(leads[c['external_id']],physical_object_review=decision);selected.append(lead)
 selected.sort(key=lambda c:(not c['artist']['popular'],c['artist']['display_name'],c['source_object_id']))
 if a.limit:selected=selected[:a.limit]
 core.save_new(r/'source-leads.json',selected);core.save_new(r/'review-held.json',held);core.save_new(r/'existing-proof-holds.json',proof_holds)
 report={'at':core.now(),'missing_print_leads':len(records),'independent_existing_object_proofs':len(proofs),'selected_for_final_duplicate_guard':len(selected),'popular':sum(c['artist']['popular'] for c in selected),'held':len(held),'policy':'Only separately accessioned physical prints, verified in current official museum datasets. All uncertain/unidentified title collisions remain held. No paintings are added through this exception.'}
 core.save_new(r/'review-report.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
