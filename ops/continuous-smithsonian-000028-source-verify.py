#!/usr/bin/env python3
"""Independent verification against exact original Smithsonian shard bytes."""
import importlib.util,gzip,json,re
from pathlib import Path
from urllib.parse import parse_qs,urlparse
s=importlib.util.spec_from_file_location('b','ops/continuous-smithsonian-batch-000028.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
p,pin=h.pinned(b.PHASE);rc=h.load(E/'source-captures/saam-00.receipt.json');raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
objects=[json.loads(x) for x in raw.splitlines()];records=[]
with h.connect() as db:
 for r in p['records']:
  o=r['raw']['object'];assert o in objects;d=o['content']['descriptiveNonRepeating'];f=o['content']['freetext'];oid=parse_qs(urlparse(d['record_link']).query)['id'][0]
  def vals(k,label=None):return [v['content'] for v in f.get(k,[]) if label is None or v['label']==label]
  assert oid==r['source_id'] and vals('identifier','Object number')==[r['accession_number']] and d['title']['content']==r['title']
  assert vals('date','Date')==[r['date_display']];date=re.fullmatch(r'(ca\. )?(\d{4})(?:-(\d{4}))?',r['date_display']);lo=int(date[2]);hi=int(date[3] or date[2]);precision=('circa' if lo==hi else 'circa_range') if date[1] else ('exact' if lo==hi else 'range');assert (lo,hi,precision)==(r['first'],r['last'],r['precision']) and hi<=1970
  assert db.execute('SELECT artline_creation_scope(%s,%s,%s) v',(lo,hi,precision)).fetchone()['v']=='eligible'
  assert d['data_source']==b.MUSEUM and o['unitCode']==d['unit_code']=='SAAM' and 'Smithsonian American Art Museum Collection' in vals('setName','See more items in')
  assert vals('creditLine')==[r['credit']] and vals('physicalDescription','Medium')==[r['medium']] and vals('physicalDescription','Dimensions')==[r['dimensions']]
  labels=vals('name','Artist');assert '; '.join(labels)==r['creator_label'] and r['raw']['source_roles']==f['name']
  assert d['metadata_usage']['access']=='CC0' and vals('objectRights','Restrictions & Rights')==['CC0'];ims=d['online_media']['media'];assert len(ims)==1 and ims[0]['usage']['access']=='CC0' and ims[0]['type']=='Images'
  assert parse_qs(urlparse(ims[0]['content']).query)['id']==[ims[0]['idsId']] and urlparse(ims[0]['content']).hostname=='ids.si.edu'
  ep=b.ROOT/r['evidence_file'];assert h.sha(ep.read_bytes())==r['evidence']['sha256'] and h.load(ep)['object']==o
  if r['artist_id']:
   artist=db.execute('SELECT id::text,display_name,birth_year,death_year FROM artists WHERE id=%s',(r['artist_id'],)).fetchone();assert artist['display_name']=='Joseph de Longueil' and (artist['birth_year'],artist['death_year'])==(1730,1792)
  else:assert len(labels)>1 or labels[0].startswith('Unidentified')
  records.append(dict(artwork_id=r['artwork_id'],native_id=oid,edan_id=d['record_ID'],title=r['title'],accession=r['accession_number'],source_url=d['record_link'],date_bounds=[lo,hi],date_precision=precision,original_roles=f['name'],credit=r['credit'],source_type=vals('objectType'),source_sha256=rc['sha256'],record_sha256=r['evidence']['sha256'],metadata_rights=d['metadata_usage']['access'],object_rights=vals('objectRights'),image_rights=ims[0]['usage']['access'],ids_image_id=ims[0]['idsId'],source_image_url=ims[0]['content'],current_display_claim=False))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,original_shard_records=len(objects),anonymous_and_joint_creator_labels_preserved=True,existing_unique_artist_links=1,new_artists=0))
print('Verified four original source records, literal dates, exact image IDs, credits and creator roles.')
