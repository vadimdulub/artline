"""Independent MNAC field and absent-object verification; no image assertion."""
import importlib.util,json,re,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-mnac-batch-000099.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==11 and not p['new_institutions'] and not p['held'];checks=[]
bounds={'Últim quart del segle XIV':(1376,1400),'Segle XIV':(1301,1400),'Finals del segle XIV':(1301,1400),'Primera meitat del segle XIV':(1301,1350),'Segon quart del segle XIV':(1326,1350),'Tercer quart del segle XIV':(1351,1375),'Segona meitat del segle XIV':(1351,1400),'c. 1350':(1350,1350),'c. 1400':(1400,1400)}
for r in p['records']:
 raw=Path(r['evidence_file']).read_bytes();assert h.sha(raw)==r['evidence']['sha256'] and r['evidence']['status']==200
 sp=BeautifulSoup(raw,'html.parser');ft=[e.get_text(' ',strip=True) for e in sp.select('.ds-feature')];tags=[e.get_text(' ',strip=True) for e in sp.select('.ds-detail-tags')];labels=[e.get_text(' ',strip=True) for e in sp.select('.field-name-field-piece-authors-author .field-item')]
 assert r['title']==sp.title.get_text(' ',strip=True).split(' | ')[0]
 assert ft==r['raw']['features'] and r['accession_number']==ft[-1].split(': ',1)[1] and r['source_id']==r['accession_number']
 assert ft[1]==r['date_display'] and (r['first'],r['last'])==bounds[ft[1]] and ft[2]==r['dimensions'] and ft[3]==r['credit']
 assert r['medium'] in tags and 'Painting' in tags and r['creator_label']=='; '.join(labels)
 assert r['first']<=r['last']<=1400 and not r['before'] and r['add_holding'] and r['holding_confidence']>=.8
 if r['accession_number']=='035677-000':
  assert r['documented_gift_after_former_loan'] and 'given by Julio Muñoz Ramonet, 1950' in r['credit'] and r['artist_id']=='004a0066-111a-57f8-b22c-70c77f89c8d7'
 else:assert 'loan' not in r['credit'].lower() and not r['artist_id']
 checks.append(dict(artwork_id=r['artwork_id'],inventory=r['accession_number'],title=r['title'],date_display=r['date_display'],bounds=bounds[ft[1]],source_checksum=r['evidence']['sha256'],source_url=r['source_url'],creator_label=r['creator_label'],artist_id=r['artist_id'],historical_loan_then_donation=r.get('documented_gift_after_former_loan',False),unit='One native physical inventory unit including whole triptychs/frontals and surviving multi-scene fragments. No separate depicted-scene rows.',medium=r['medium'],dimensions=r['dimensions'],credit=r['credit']))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');b.no_collision(db,p['records']);assert not h.snapshot(db,[r['artwork_id'] for r in p['records']])
 scope=h.load(b.E/'institution-scope-before.json.gz');live={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=ANY(%s::uuid[])',([a['id'] for a in scope],))};assert live=={a['id']:a for a in scope}
 # Reconcile ensemble/component inventory prefixes and translated/native source URL tails.
 component_checks=[]
 for r in p['records']:
  prefix=r['accession_number'].split('-')[0]
  candidates=[a for a in scope if prefix in (a['accession_number'] or '') or prefix in a['title']];assert not candidates
  links=[dict(x) for x in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND (canonical_url ILIKE %s OR external_id ILIKE %s)",([a['id'] for a in scope],'%'+prefix+'%','%'+prefix+'%'))];assert not links
  component_checks.append(dict(inventory=r['accession_number'],existing_same_inventory_prefix=0))
 # Supplement exact-name global reconciliation with token/authority candidates, without invention.
 authority=[dict(x) for x in db.execute("SELECT id::text,display_name FROM artists WHERE display_name ILIKE '%Venezian%' OR display_name ILIKE '%Estamariu%' OR display_name ILIKE '%Cinctorres%'")]
 assert {x['display_name'] for x in authority}=={'Paolo Veneziano','Caterino Veneziano','Domenico Veneziano'},'Additional authority identities require review'
 for candidate in authority:assert 'Antonio' not in candidate['display_name']
 # These are different named artists, not aliases for Antonio Veneziano. No canonical match invented.
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,component_checks=component_checks,scope_records_preserved=len(scope),creator_supplementary_candidates=authority,source_policy=h.load(b.E/'source-policy-verification.json'),image_downloads=0,visual_reviewed_images=0))
assert h.load(b.E/'local-recovery-verification.json')['status']=='VERIFIED' and h.load(b.E/'prior-batch-live-reconciliation.json')['uncertain_prior_writes'] is False
b.save('prewrite-verification.json',dict(at=h.now(),passed=True,plan_sha256=pin,selected=11,images=0,no_existing_production_rows=True,global_identity_evidence='global-identity-reconciliation-final.json',shared_lock='artline-curated-ingestion',local_catalogue_connections=0))
print('Eleven source objects, source dates, existing catalogue preservation and recovery verified')
