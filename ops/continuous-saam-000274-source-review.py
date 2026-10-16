#!/usr/bin/env python3
"""Verify selected source records and independently capture current native pages."""
import importlib.util,gzip,html,json,re
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import requests
s=importlib.util.spec_from_file_location('b','ops/continuous-saam-new-000274.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
p,pin=h.pinned(b.PHASE);rc=h.load(E/'source-captures/saam-45.receipt.json');raw=gzip.decompress((b.ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
objects=[json.loads(x) for x in raw.splitlines()];records=[];artist_review=[]
data=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/000274';data.mkdir(parents=True,exist_ok=True)
def plain(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',t)))
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
  name=labels[0].split(',')[0];matches=[dict(x) for x in db.execute("select distinct a.id::text,a.display_name,a.birth_year,a.death_year,a.status from artists a left join artist_aliases al on al.artist_id=a.id where lower(a.display_name)=lower(%s) or lower(al.alias)=lower(%s)",(name,name))];artist_review.append(dict(native_id=oid,source_label=labels[0],matches=matches,decision='Preserve full object-level creator label; no new painter and no forced link from unresolved global reconciliation.'))
  url={'19435':'https://americanart.si.edu/artwork/merry-xmas-1921-19435','1355':'https://americanart.si.edu/artwork/tiny-white-cap-1355'}[oid];receipt_path=E/'source-captures'/('saam-'+oid+'-current.json');bodypath=data/(oid+'-current.html.gz')
  if receipt_path.exists():current=h.load(receipt_path);body=gzip.decompress(bodypath.read_bytes());assert h.sha(body)==current['sha256']
  else:
   response=requests.get(url,timeout=(15,45));response.raise_for_status();assert response.status_code==200;body=response.content;bodypath.write_bytes(gzip.compress(body,mtime=0));current=dict(url=url,final_url=response.url,status=200,sha256=h.sha(body),body_path=str(bodypath),retrieved_at=h.now());h.save(receipt_path,current)
  text=plain(body.decode())+' '+plain(' '.join(re.findall(r'data-text="([^"]*)"',body.decode())))
  for v in [r['title'],r['accession_number'],r['date_display'],r['medium'],name,r['dimensions']]:assert h.norm(v) in h.norm(text),(oid,v)
  assert ims[0]['idsId'] in body.decode() and 'Free to use' in text
  records.append(dict(artwork_id=r['artwork_id'],native_id=oid,edan_id=d['record_ID'],title=r['title'],accession=r['accession_number'],source_url=d['record_link'],date_bounds=[lo,hi],date_precision=precision,original_roles=f['name'],credit=r['credit'],source_type=vals('objectType'),source_sha256=rc['sha256'],record_sha256=r['evidence']['sha256'],metadata_rights=d['metadata_usage']['access'],object_rights=vals('objectRights'),image_rights=ims[0]['usage']['access'],ids_image_id=ims[0]['idsId'],source_image_url=ims[0]['content'],current_native_page=current,current_source_fields_all_agree=True,current_display_claim=False))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,original_shard_records=len(objects),existing_unique_artist_links=0,new_artists=0,user_approval_separate_from_rights=True))
b.save('artist-identity-holds.json',dict(at=h.now(),records=artist_review))
print(json.dumps(dict(verified_source_records=len(records),artists=artist_review)))
