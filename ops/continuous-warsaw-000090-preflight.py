#!/usr/bin/env python3
"""Read-only source and global creator checks for one pinned batch."""
import fcntl,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-warsaw-batch-000090.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);assert 1<=len(p['records'])<=50 and not p['held']
bounds={x[0]:x[1:] for x in b.DATES.values()}
checks=[]
for r in p['records']:
 rc=h.load(E/f"object-{r['source_id']}.receipt.json");raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
 o=json.loads(raw)['data'];assert o==r['raw'] and o['title']==r['title'] and o['noEvidence']==r['accession_number']
 assert o['owner']=={'id':107515,'name':'Muzeum Narodowe w Warszawie'}
 assert o['copyrights'] and all(c['name']=='DOMENA PUBLICZNA' and not c['restricted'] for c in o['copyrights'])
 assert len(o['createDates'])==1 and o['createDates'][0]['name']+(' ['+o['createDates'][0]['comment']+']' if o['createDates'][0]['comment'] else '')==r['date_display']
 assert (r['first'],r['last'])==bounds[r['date_display']] and r['precision']=='range' and r['last']<=1970
 assert r['dimensions']==o['dimensionText'] and r['before'] is None and r['artist_id'] is None and r['creator_link_hold']
 assert all(re.search('warsztat|szkoła',a['name'],re.I) for a in o['authors']) and r['creator_label']==b.attribution(o)
 techniques=[x['name'] for x in o['techniques']];assert r['source_type']==('metalwork' if 'odlew' in techniques else 'painting')
 assert r['evidence']['sha256']==h.sha((E/f"object-{r['source_id']}.json").read_bytes())
 checks.append(dict(source_id=r['source_id'],inventory=r['accession_number'],source_sha256=rc['sha256'],selected_evidence_sha256=r['evidence']['sha256'],source_date=r['date_display'],creation_bounds=bounds[r['date_display']],source_creators=o['authors'],source_owner=o['owner'],source_rights=o['copyrights'],dimensions=o['dimensionText'],historical_numbers=o['extraNumPatterns'],source_description=o['description'],source_history=o['history'],unit='One complete surviving inventory object; joined triptych and multi-scene panel each count once.',date_review='455236 structured date first half XV; narrative XIV-XV and nineteenth-century alteration/conservation preserved in citation. No modern conservation date used as creation.' if r['source_id']=='455236' else 'Source creation wording retained; acquisition years excluded.'))
policy=h.load(E/'policy-project.receipt.json');body=gzip.decompress(Path(policy['body_path']).read_bytes());assert h.sha(body)==policy['sha256'] and policy['status']==200 and b'komercyjnym' in body
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,rights_policy_capture=policy,current_display_claims=0))
labels=sorted({r['creator_label'] for r in p['records']});hist=sorted({str(x['number']) for r in p['records'] for x in r['raw']['extraNumPatterns']})
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');before=h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert not before
 matches=[dict(x) for x in db.execute('SELECT id::text,display_name FROM artists WHERE normalized_name=ANY(%s)',([h.norm(x) for x in labels],))]
 aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE alias=ANY(%s)',(labels,))]
 historical=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)',(hist,))];assert not historical
b.save('creator-global-reconciliation.json',dict(at=h.now(),labels=labels,exact_matches=matches,alias_matches=aliases,global_names_and_aliases_checked_by_plan=True,decision='Workshop/school identities, remain source-qualified object labels. Do not fabricate an individual painter or flatten a collective attribution. Native authorities retained.'))
b.save('independent-historical-inventory-verification.json',dict(at=h.now(),historical_numbers=hist,matches=historical,all_selected_new_ids_absent=True,interpretation='Current unique IK inventory and physical composition govern. Shared acquisition references are not unique physical-object identifiers.'))
print('Verified selected source records and pre-insert absence; creator and historical-number checks passed')
