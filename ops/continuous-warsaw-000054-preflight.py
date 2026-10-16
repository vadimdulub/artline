#!/usr/bin/env python3
"""Independently reconcile saved sources and prior live production deliveries."""
import fcntl, gzip, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000054.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
h=b.h;E=b.E
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
p,pin=h.pinned(b.PHASE);assert len(p['records'])==6 and not p['held']
records=[]
for r in p['records']:
    rc=h.load(E/f"object-{r['source_id']}.receipt.json")
    raw=gzip.decompress(Path(rc['body_path']).read_bytes())
    assert h.sha(raw)==rc['sha256'] and rc['status']==200
    o=json.loads(raw)['data']
    assert o==r['raw'] and o['noEvidence']==r['accession_number'] and o['title']==r['title']
    assert o['owner']=={'id':107515,'name':'Muzeum Narodowe w Warszawie'}
    assert o['copyrights'] and all(c['name']=='DOMENA PUBLICZNA' and not c['restricted'] for c in o['copyrights'])
    assert len(o['createDates'])==1 and o['createDates'][0]['name']==r['date_display'] and o['createDates'][0]['comment'] is None
    bounds={'XVIII w.':(1701,1800),'XIX w.':(1801,1900)}[r['date_display']]
    assert (r['first'],r['last'])==bounds and r['precision']=='range'
    assert r['dimensions']==o['dimensionText'] and r['before'] is None and r['artist_id'] is None and r['creator_link_hold']
    assert all(a['name'] in ['warsztat rosyjski','warsztat staroobrzędowców'] for a in o['authors'])
    assert r['creator_label']==b.attribution(o)
    assert 'deska' in [x['name'] for x in o['materials']] and 'tempera' in [x['name'] for x in o['techniques']]
    assert r['evidence']['sha256']==h.sha((E/f"object-{r['source_id']}.json").read_bytes())
    records.append(dict(source_id=r['source_id'],title=r['title'],inventory=r['accession_number'],source_sha256=rc['sha256'],selected_evidence_sha256=r['evidence']['sha256'],source_date=r['date_display'],creation_bounds=bounds,source_creators=o['authors'],source_owner=o['owner'],source_rights=o['copyrights'],dimensions=o['dimensionText'],historical_numbers=o['extraNumPatterns'],source_description=o['description'],source_history=o['history'],unit='One complete physical painted inventory board; multiple scenes count once',creation_scope='eligible'))
policy=h.load(E/'policy-project.receipt.json');body=gzip.decompress(Path(policy['body_path']).read_bytes())
assert h.sha(body)==policy['sha256'] and policy['status']==200 and b'komercyjnym' in body
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=records,rights_policy_capture=policy,attribution='Workshop names remain original qualified object labels. 498648 explicitly retains questioned Old Believer workshop attribution. No named artist asserted.',current_display_claims=0))
prior=[]
with h.connect() as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    for num in [49,53]:
        folder=E.parent/f'{num:06d}';receipt=h.load(folder/'batch-verification-receipt.json');ids=receipt['production_ids']
        expected={x['id']:x for x in h.load(folder/'independent-production-verification.json')['rows']}
        live=[dict(x) for x in db.execute('SELECT a.id::text,a.primary_media_id::text,m.checksum_sha256::text,m.storage_path,e.adapter_version,e.evidence_json FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=ANY(%s::uuid[])',(ids,))]
        assert len(live)==len(ids)==len(expected)
        for row in live:
            ev=row['evidence_json'];ev=json.loads(ev) if isinstance(ev,str) else ev
            assert ev['selection_sha256']==receipt['selection_sha256'] and ev['batch_visual_review_sha256']==receipt['visual_review_sha256']
            assert f'{num:06d}' in row['adapter_version']
            assert all(row[k]==expected[row['id']][k] for k in ['primary_media_id','checksum_sha256','storage_path'])
        prior.append(dict(batch=num,receipt_sha256=h.sha((folder/'batch-verification-receipt.json').read_bytes()),verified_rows=live,previous_selection_sha256=receipt['selection_sha256'],previous_visual_sha256=receipt['visual_review_sha256']))
    current=h.snapshot(db,[r['artwork_id'] for r in p['records']]);assert not current
    labels=sorted({r['creator_label'] for r in p['records']})
    matches=[dict(x) for x in db.execute("SELECT id::text,display_name FROM artists WHERE normalized_name=ANY(%s)",([h.norm(x) for x in labels],))]
    aliases=[dict(x) for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE alias=ANY(%s)',(labels,))]
b.save('prior-batch-live-reconciliation.json',dict(at=h.now(),previous_batch_verified=True,prior_batches=prior,current_batch_before=current,uncertain_prior_writes=0,previous_additions_excluded=True))
b.save('creator-global-reconciliation.json',dict(at=h.now(),labels=labels,exact_matches=matches,alias_matches=aliases,global_names_and_aliases_checked_by_plan=True,decision='Generic workshop identities are not named individual artists; original wording and authority IDs retained. No painters created or falsely linked.'))
review=h.load(E.parent/'000052/research-review.json')
held=[x for x in review['records'] if int(x['source_id']) not in b.SELECTED]
assert len(held)==18
b.save('research-holds.json',dict(at=h.now(),prior_review=str(E.parent/'000052/research-review.json'),prior_review_sha256=h.sha((E.parent/'000052/research-review.json').read_bytes()),records=held,decision='18 remaining page-three records remain captured but unselected; saved metadata supports targeted future cast, composite, date and qualified creator review. No automatic exclusion or duplicate searches.',pending_ids=[x['source_id'] for x in held]))
b.save('production-target-reconciliation.json',b.target())
print(json.dumps(dict(selected=6,prior_batches_live_reconciled=[49,53],source_checks_passed=True,remaining_saved_reviews=18)))
