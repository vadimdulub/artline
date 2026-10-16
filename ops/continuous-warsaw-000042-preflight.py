#!/usr/bin/env python3
"""Independent persisted-source and previous-transaction reconciliation."""
import fcntl,gzip,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000042.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==7 and not p['held']
records=[]
for r in p['records']:
 rc=h.load(E/('object-'+r['source_id']+'.receipt.json'));raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 o=json.loads(raw)['data'];assert o==r['raw'] and o['noEvidence']==r['accession_number'] and o['title']==r['title']
 assert o['owner']=={'id':107515,'name':'Muzeum Narodowe w Warszawie'} and o['copyrights'] and all(x['name']=='DOMENA PUBLICZNA' and not x['restricted'] for x in o['copyrights'])
 assert len(o['createDates'])==1 and o['createDates'][0]['name']==r['date_display']
 # Independent conservative creation bounds; restoration date is a different event.
 bounds={'3. ćw. XIX w.':(1851,1875),'2. poł. XIX w.':(1851,1900),'XIX w.':(1801,1900)}[r['date_display']]
 assert (r['first'],r['last'])==bounds and r['last']<=1970 and r['precision']=='range'
 assert r['dimensions']==o['dimensionText'] and r['before'] is None and not r['artist_id'] and r['creator_link_hold']
 assert r['evidence']['sha256']==h.sha((E/('object-'+r['source_id']+'.json')).read_bytes())
 assert any(x['name']=='deska' for x in o['materials']) and any(x['name']=='tempera' for x in o['techniques'])
 records.append(dict(source_id=r['source_id'],title=r['title'],inventory=r['accession_number'],source_sha256=rc['sha256'],selected_evidence_sha256=r['evidence']['sha256'],date_display=r['date_display'],bounds=bounds,date_comment=o['createDates'][0]['comment'],source_creators=o['authors'],source_owner=o['owner'],source_rights=o['copyrights'],dimensions=o['dimensionText'],historical_numbers=o['extraNumPatterns'],unit='One physical painted board; its narrative scenes are not counted separately',creation_scope='eligible',description_reviewed=True))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,qualified_attribution='498706 retains both Radowij Walew? [Malarz ikon (?)] and warsztat prowincjonalny. No unqualified painter link.',restoration_date='498337: explicit XIX w. creation; comment about XX w. restoration retained as evidence, not creation date.',shared_historical_number='498553 historical 13552/06 occurs on previous museum objects; source current inventory IK 316, subject Elijah and dimensions 43.9 x 34.5 cm establish a distinct board.',rights_policy_capture=h.load(E/'policy-project.receipt.json')))
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 prev=E.parent/'000041';receipt=h.load(prev/'batch-verification-receipt.json');ids=receipt['production_ids'];assert len(ids)==27
 old=h.load(prev/'independent-production-verification.json')
 expected={x['id']:x for x in old['media']} if 'media' in old else None
 live=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,e.adapter_version,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
 assert len(live)==27
 for row in live:
  ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
  assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256'] and '000041' in row['adapter_version']
  if expected:assert row['primary_media_id']==expected[row['id']]['primary_media_id'] and row['checksum_sha256']==expected[row['id']]['checksum_sha256']
 b.save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch=41,previous_batch_verified=True,primary_rows=live,previous_selection_sha256=receipt['selection_sha256'],previous_visual_sha256=receipt['visual_review_sha256'],no_previous_increments_counted=True,current_batch_before=h.snapshot(db,[r['artwork_id'] for r in p['records']]),uncertain_prior_writes=0))
 candidates=[dict(x) for x in db.execute("SELECT id::text,display_name FROM artists WHERE display_name ILIKE '%%Radow%%' OR display_name ILIKE '%%Walew%%' OR display_name ILIKE '%%Валев%%' OR display_name ILIKE '%%Радов%%'")]
 aliases=[dict(x) for x in db.execute("SELECT artist_id::text,alias FROM artist_aliases WHERE alias ILIKE '%%Radow%%' OR alias ILIKE '%%Walew%%' OR alias ILIKE '%%Валев%%' OR alias ILIKE '%%Радов%%'")]
 b.save('creator-global-reconciliation.json',dict(at=h.now(),candidates=candidates,aliases=aliases,decision='No creator record created. Doubly questioned source attribution preserved verbatim at object level; no basis to identify a unique painter. Other six records have workshop labels. Global exact-name and alias reconciliation also executed by pinned plan helper.'))
holds={498347:'Four-wing cast-metal devotional object: separate catalogue-unit and complete-open-image review required; not a painted board.',498661:'XIX/XX w. crossing centuries: exact established boundary treatment requires review; source narrative includes a tentative restoration/damage history. No invented year.',498335:'Two-component icon and later metal cover, IK 115/a-b; source dates icon XVIII w. and cover second half XIX w.; component identities must be modeled and visual representation checked.',498657:'Left physical panel of Deesis with IK 41 and IK 45: reconcile parent/group and separately inventoried boards before insertion.',498667:'Generic Resurrection title matches earlier museum works: exact board/version reconciliation required using distinct IK 53 and 26.3 x 22 cm.',498656:'Right physical panel of Deesis, related to IK 41 and IK 46: reconcile parent/group and separately inventoried boards before insertion.',499488:'Modern assembled triptych from former SZM 724 and SZM 1719 objects: reconcile ensemble/component and former inventory identities.',498653:'Generic Resurrection title matches earlier works: exact board/version review required with IK 42 and 29.5 x 25 cm; retain koniec XIX w. wording.',498429:'Cast devotional cross: separate metalwork classification and exact cast/full-image review; not an icon painting.',498663:'Same museum title as delivered 498674 but different inventory IK 50 and dimensions 53.7 x 43 cm: further composition/version review required before new insertion.'}
b.save('research-holds.json',dict(at=h.now(),captured=17,selected=7,records=[dict(source_id=str(k),reason=v,evidence='object-'+str(k)+'.receipt.json',retry='Do not repeat source searches; use these saved exact captures for the specified editorial review') for k,v in holds.items()],prior_unchanged_holds=['498325','498334','498652']))
b.save('production-target-reconciliation.json',b.target())
print(json.dumps(dict(selected=7,source_checks_passed=True,prior_images_reconciled=27,unselected=10)))
