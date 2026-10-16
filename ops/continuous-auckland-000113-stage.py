import importlib.util,json,csv,re,gzip
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000113.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
q=h.load(b.E.parents[1]/'source-queue.json');a=next(x for x in q['sources'] if x['source_id']=='auckland_art_gallery');ids=a['resume_cursor']['pending_artwork_ids'][:25]
b.save('required-input-reconciliation.json',dict(at=h.now(),files=[dict(path=str(p),sha256=h.sha(p.read_bytes())) for p in [Path('AGENTS.md'),Path('docs/ARTLINE_IMAGE_USE.md'),Path('docs/DATA_AND_IMAGE_COLLECTION_PROMPT.md'),Path('docs/LOCAL_DATA_LOCATIONS.md'),Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv')]],registry=list(csv.DictReader(open('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv'))),production_authorized=True,local_catalogue_read_only=True))
b.save('source-queue-before.json',q)
b.save('source-access-holds.json',dict(at=h.now(),route=a,previous_holds=h.load(b.E.parent/'000101/research-holds.json'),no_unchanged_failed_urls_retried=True))
b.save('production-target-reconciliation.json',b.target())
with b.connect() as db:
 prior=h.load(b.E.parent/'000107/independent-production-verification.json');print('107keys',list(prior))
 old=prior['after'];fresh=h.snapshot(db,list(old));assert fresh==old
 b.save('batch107-live-reconciliation.json',dict(at=h.now(),snapshot_equal=True,prior_receipt_sha256=h.sha((b.E.parent/'000107/independent-production-verification.json').read_bytes()),live=fresh,previous_increments_counted=0))
 states=h.snapshot(db,ids)
 cs=[dict(x) for x in db.execute("SELECT entity_id::text,field_name,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 es=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))]
 own=[dict(x) for x in db.execute('SELECT media_id::text FROM media_rights_evidence WHERE adapter_version=%s',(b.i.OP,))];assert not own
 b.save('gap-input.json.gz',dict(at=h.now(),before=states,citations=cs,identifiers=es,ids=ids,own_existing_images=own))
stop=Path('docs/research/illustrated-300k-20261011/workers-stopped.json');b.save('completed-campaign-stop-preservation.json',dict(path=str(stop),sha256=h.sha(stop.read_bytes()),separate_campaign=b.i.OP,restarted=False))
native=b.mod('native113','museum-expansion-auckland-20261006.py');out=[]
for aid in ids:
 st=states[aid]['artwork'];cits=[c for c in cs if c['entity_id']==aid]
 text=json.dumps(cits);urls=list(dict.fromkeys(re.findall(r'https?://www\.aucklandartgallery\.com/[^\s"\\]+',text)))
 urls=[u.replace('http://','https://').replace('/explore-art-and-ideas/','/explore/art-and-artists/') for u in urls if '/artwork/' in u];urls=list(dict.fromkeys(urls))
 row=dict(artwork_id=aid,title=st['title'],source_urls=urls,primary_media_id=st['primary_media_id'])
 if st['primary_media_id']:row['hold']='Already illustrated; exclude from increments'
 elif len({re.search('/artwork/(\d+)',u)[1] for u in urls})!=1:row['hold']='No unique native ID in saved evidence'
 else:
  try:
   raw,rc=b.capture(urls[0]);parsed=native.fields(raw);b.save('native/'+aid+'.json',dict(receipt=rc,parsed=parsed));row.update(fields=parsed['fields'],creators=parsed['creator_names'],native_id=str(parsed['native_route']['attributes']['id']),image_available=bool(parsed['native_route']['attributes']['zoom_image']))
  except Exception as e:row['hold']=str(e)[:300]
 out.append(row);b.save('research/'+aid+'.json',row);print(st['title'],row.get('hold') or (row['fields'].get('Copyright'),row['image_available']),flush=True)
b.save('native-discovery.json',dict(at=h.now(),rows=out))
