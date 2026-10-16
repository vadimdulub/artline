#!/usr/bin/env python3
"""One bounded batch, reusing established Te Papa attachment and recovery workflow."""
import csv, fcntl, gzip, importlib.util, inspect, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('tepapa37',ROOT/'ops/continuous-tepapa-images-000037.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
i=b.i;h=b.h;load=b.load;connect=b.connect;save=b.save;target=b.target
E=ROOT/'docs/research/continuous-production-20261011/batches/000062'
RUNTIME=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000062'
B='tepapa-direct-062'
POLICY=b.POLICY
b.E=E;b.RUNTIME=RUNTIME;b.B=B
i.OP='continuous-primary-images-20261011-b000062';i.RUN=E
i.ORIG=Path.home()/'Library/Application Support/Artline/source-images'/i.OP
i.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/i.OP
for p in [E,RUNTIME,i.ORIG,i.BACKUP]:p.mkdir(parents=True,exist_ok=True)
# Preserve the original policy receipt, and persist the corrected official rights-guide reference.
copycode=inspect.getsource(b.copy_rows).replace("E/'source-policy-verification.json'", "E/'source-policy-verification-v2.json'").replace("photo['title']", "photo.get('title','')")
exec(compile(copycode,__file__,'exec'),b.__dict__);i.n.copy_rows=b.copy_rows
native_copy_rows=b.copy_rows
def copy_rows(db,table,rows):
 if table=='media_rights_evidence':
  for row in rows:
   ev=json.loads(row['evidence_json']);ev['additional_identity_review']=load(E/'additional-identity-review.json');row['evidence_json']=json.dumps(ev,ensure_ascii=False)
 return native_copy_rows(db,table,rows)
i.n.copy_rows=copy_rows

def checked_target(write=False):
 assert __import__('os').environ.get('ARTLINE_SWISS_INDIA_PROXY_PORT','55519')=='55519'
 return target(write)
b.target=checked_target
original_deliver=b.deliver
def checked_deliver():
 assert load(E/'independent-prewrite-verification.json')['selection_sha256']==h.sha((i.folder(B)/'selection.json.gz').read_bytes())
 return original_deliver()
b.deliver=checked_deliver

def creator_alias(r,o):
 a=r['artwork'];native=o['production'][0]['contributor'];historical=json.loads(r['citation']['evidence_note'])['raw_source_record']['creators']
 matches=[(qid,v) for qid,v in historical.items() if v['entity']['labels'].get('en',{}).get('value')==a['unlinked_creator_label'] and native['title'] in [v['value'] for v in v['entity'].get('aliases',{}).get('en',[])]]
 assert len(matches)==1
 qid,source=matches[0];rc=source['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and json.loads(raw)['entities'][qid]==source['entity']
 dates={}
 for prop,key in [('P569','birthDate'),('P570','deathDate')]:
  vals=[v['mainsnak']['datavalue']['value'] for v in source['entity']['claims'][prop]]
  assert any(v['precision']==11 and v['time'][1:11]==native[key] for v in vals)
  dates[key]=dict(native=native[key],historical_claims=vals)
 return dict(catalogue_label=a['unlinked_creator_label'],native_label=native['title'],wikidata_id=qid,same_explicit_alias=True,matching_exact_life_date_claims=True,conflicting_historical_life_dates_preserved=True,dates=dates,source=source)

def title_matches(r,o):
 if o['title'].replace('’',"'")==r['artwork']['title'].replace('’',"'"):return True
 assert r['native_id']=='1130277' and r['inventory']==o['identifier']=='2010-0029-1'
 assert o['title'].replace('[Poeatua]','[Poetua]')==r['artwork']['title']
 assert r['artwork']['title'] in o['hasRepresentation'][0]['title']
 txt=load(E/'object-research/1130277.json')['text']
 assert 'the present picture, the only one of the three dated (1785)' in txt
 save(E/'webber-version-review.json',dict(at=h.now(),native_id='1130277',inventory=o['identifier'],source_title=o['title'],catalogue_title=r['artwork']['title'],source_sha256=load(E/'object-research/1130277.json')['receipt']['sha256'],decision='Bracketed personal-name variant only. Native media caption retains catalogue spelling; exact inventory, John Webber, 1785 and 925 x 1445 mm identify the dated Te Papa version. Museum explicitly distinguishes Greenwich and National Library of Australia versions and documents Pomare provenance. No title, creator, date, provenance or holding update.'))
 return True
b.creator_alias=creator_alias;b.title_matches=title_matches

def preflight():
 save(E/'tepapa-production-target-reconciliation.json',target())
 q=load(E.parents[1]/'source-queue.json')
 with connect() as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  if not (E/'tepapa-bounded-gap-input.json.gz').exists():
   cursor=next(r for r in q['sources'] if r['source_id']=='te_papa')['resume_cursor']['after_artwork_id']
   rows=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,creation_year_start,creation_year_end,date_precision,date_display,work_type,unlinked_creator_label FROM artworks WHERE current_institution_id=%s AND id>%s::uuid AND status<>'archived' AND primary_media_id IS NULL AND creation_year_end<=1955 ORDER BY id LIMIT 25",(b.MID,cursor))]
   ids=[r['id'] for r in rows];assert ids
   citations=[dict(r) for r in db.execute("SELECT id::text,entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
   identifiers=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
   save(E/'tepapa-bounded-gap-input.json.gz',dict(at=h.now(),after_artwork_id=cursor,rows=rows,states=h.snapshot(db,ids),identifiers=identifiers,citations=citations))
 print('Next Te Papa primary gaps:',len(load(E/'tepapa-bounded-gap-input.json.gz')['rows']),flush=True)

def prepare():
 if (i.folder(B)/'selection.json.gz').exists():return b.finish()
 extra=[]
 for r in load(E/'identity-crosswalk-input.json.gz'):
  oid=r['native_id'];rc=load(E/'object-research'/(oid+'.json'))['receipt'];o=b.object_from_page(gzip.decompress((ROOT/rc['body_path']).read_bytes()));ims=o.get('hasRepresentation',[])
  if not ims or ims[0]['rights']['title']!='No Known Copyright Restrictions':continue
  reasons=[];prod=o.get('production',[]);a=r['artwork']
  if re.search(r'\bcropped\b',ims[0].get('title',''),re.I):reasons.append('Native primary photograph explicitly labelled cropped; full-composition comparison with alternate views required before attachment')
  if len(prod)!=1 or not re.fullmatch(r'\d{4}',prod[0].get('verbatimCreatedDate','')):reasons.append('Literal source date needs separate reconciliation; catalogue date preserved')
  if len(prod)==1 and h.norm(prod[0]['contributor']['title'])!=h.norm(a['unlinked_creator_label']):
   if oid=='37514':save(E/'sperrey-alias-review.json',creator_alias(r,o))
   else:reasons.append('Native creator name differs; authority-alias reconciliation required')
  if any(d.get('extentType','').lower() in ['image','support','sheet'] and not d.get('sizeUnitText') for d in o.get('observedDimension',[])):reasons.append('Source physical dimensions omit measurement units; no inferred conversion')
  if reasons:extra.append(dict(artwork_id=a['id'],native_id=oid,reason='; '.join(reasons),images_requested=0,source_sha256=rc['sha256']))
 save(E/'supplemental-editorial-holds-v3.json',dict(at=h.now(),records=extra,scope='New batch 62 current-page cases; prior holds preserved without retries.'))
 b.extra_holds={r['native_id']:r for r in extra}
 code=inspect.getsource(b.prepare)
 # Native historical quantities explicitly use either centimetres or millimetres.
 olddim="val=values[0];assert val['unit'].endswith('/Q174728');d=dims[0];native=float(d[key])/(10 if d.get('sizeUnitText')=='mm' else 1);assert abs(native-float(val['amount']))<.11,(oid,key,native,val);dimensions.append(dict(field=key,source=d,wikidata_cm=val['amount']))"
 newdim="val=values[0];assert val['unit'].rsplit('/',1)[-1] in ['Q174728','Q174789'];d=dims[0];assert d.get('sizeUnitText') in ['mm','cm'];native=float(d[key])/(10 if d['sizeUnitText']=='mm' else 1);cm=float(val['amount'])/(10 if val['unit'].endswith('/Q174789') else 1);assert abs(native-cm)<.11,(oid,key,native,val);dimensions.append(dict(field=key,source=d,wikidata_cm=cm,historical_quantity=val,difference_cm=round(native-cm,4)))"
 assert olddim in code;code=code.replace(olddim,newdim)
 old="photo=ims[0]"
 new="if oid in extra_holds:holds.append(extra_holds[oid]);continue\n   photo=ims[0]"
 assert old in code
 code=code.replace(old,new).replace("o['title']==a['title']","title_matches(r,o)")
 start=code.index("    assert oid=='1118264'");end=code.index("\n\n   note=",start)
 code=code[:start]+"    creator_variant=creator_alias(r,o)"+code[end:]
 exec(compile(code,__file__,'exec'),b.__dict__)
 sourcebatch='tepapa-source-062';b.B=sourcebatch;finish=b.finish;b.finish=lambda:None
 b.prepare();b.finish=finish;b.B=B
 parent=i.folder(sourcebatch)/'selection.json.gz';p=load(parent);rows=[]
 for row in p['rows']:
  oid=row['current_source_id'];url=row['image']['image_url'];dest=E/'media-response-diagnostics'/(oid+'.json')
  if dest.exists():diag=load(dest)
  else:
   i.provider_slot('collections.tepapa.govt.nz')
   with i.session().get(url,timeout=(15,45),allow_redirects=False,stream=True) as res:
    diag=dict(at=h.now(),url=url,status=res.status_code,location=res.headers.get('Location'),retry_after=res.headers.get('Retry-After'))
   save(dest,diag)
   if diag['status'] in [401,403,429]:save(E/'access-holds/collections.tepapa.govt.nz.json',diag);raise AssertionError('Provider access hold')
  photo=row['image']['source']['hasRepresentation'][0]
  assert diag['status']==303 and diag['location']=='https://co3-api-mediastorage.s3.ap-southeast-2.amazonaws.com/'+str(photo['id'])+'/preview'
  rows.append(dict(row,image=dict(row['image'],image_url=diag['location'],native_media_url=diag['url'],redirect_receipt=diag)))
 save(i.folder(B)/'selection.json.gz',dict(p,at=h.now(),batch=B,rows=rows,parent_selection_sha256=h.sha(parent.read_bytes()),selection_basis=p['selection_basis']+' Exact official HTTP 303 redirect preserved; no access bypass.'))
 save(i.folder(B)/'pin.json',dict(sha256=h.sha((i.folder(B)/'selection.json.gz').read_bytes())))
 b.finish()

if __name__=='__main__':
 with (RUNTIME/'worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  name=sys.argv[1]
  if name in ['preflight','prepare']:globals()[name]()
  else:getattr(b,name)()
