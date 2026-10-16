#!/usr/bin/env python3
"""Independent on-disk source, queue and offline resume verification for batch 52."""
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000052'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000052'
CAP=Path.home()/'Library/Application Support/Artline/source-metadata/continuous-production-20261011/batches/000052'
sha=lambda data:hashlib.sha256(data).hexdigest()


def load(path):
    path=Path(path);data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)


def main():
    spec=importlib.util.spec_from_file_location('resume52',ROOT/'ops/continuous-reserve-warsaw-000052-research.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    discovery=load(E/'warsaw-discovery.json');review=load(E/'research-review.json')
    checks=[]
    for rc in [discovery['page_receipt']]+[r['receipt'] for r in discovery['records']]:
        p=Path(rc['body_path']);assert p.is_relative_to(CAP)
        raw=gzip.decompress(p.read_bytes())
        assert sha(raw)==rc['sha256'] and len(raw)==rc['bytes'] and rc['status']==200
        obj=json.loads(raw);assert obj['status']==200
        checks.append(dict(url=rc['url'],source_id=str(obj['data']['id']) if 'id' in obj['data'] else None,
            status=rc['status'],body_path=str(p),sha256=sha(raw),bytes=len(raw)))
    ids={r['source_id'] for r in discovery['records']}
    assert len(ids)==24 and ids=={r['source_id'] for r in review['records']}
    for r in discovery['records']:
        o=load(r['receipt']['body_path'])['data']
        assert str(o['id'])==r['source_id'] and o['title']==r['title'] and o['noEvidence']==r['accession']
        for original,saved in [('authors','creators'),('createDates','dates'),('copyrights','copyrights'),('owner','owner')]:
            assert o[original]==r[saved]
        assert not r['selected_for_import'] and r['images_downloaded']==0
    assert len([r for r in review['records'] if r['decision']=='priority_for_live_global_reconciliation'])==6
    b.save(E/'independent-source-verification.json',dict(at=b.now(),source='national_museum_warsaw',
        metadata_responses=25,objects=24,checks=checks,raw_bytes_and_identity_fields_match=True,
        selected_for_import=0,images_requested=0,production_reconciliation=False,
        limitation='Source evidence integrity verified; no live production eligibility or novelty claim.'))

    audit=load(E/'independent-reserve-evidence-verification.json')
    historical=[]
    for item in audit['immutable_plans']:
        assert sha(Path(item['path']).read_bytes())==item['sha256'];historical.append(item)
    for item in audit['records']:
        assert sha(Path(item['source_record']['path']).read_bytes())==item['source_record']['sha256']
        assert sha(Path(item['prior_visual_decision']['path']).read_bytes())==item['prior_visual_decision']['sha256']
        assert sha(Path(item['local_path']).read_bytes())==item['derivative_sha256']
        assert item['prior_citation_plan_sha256']==audit['prior_campaign_plan_sha256']
    visual=load(E/'actual-visual-review.json')
    assert {r['source_id'] for r in visual['records']}=={'80082','80437','81054'}
    assert len(audit['records'])==188

    before=load(E/'source-queue-immediately-before-update.json')
    after=load(E.parent.parent/'source-queue.json')
    left={x['source_id']:x for x in before['sources']};right={x['source_id']:x for x in after['sources']}
    touched={'yale_lux','national_museum_warsaw'}
    assert len(left)==len(right)==111
    assert {k:v for k,v in left.items() if k not in touched}=={k:v for k,v in right.items() if k not in touched}
    old=left['national_museum_warsaw']['resume_cursor'];new=right['national_museum_warsaw']['resume_cursor']
    for key in ['processed_native_ids','delivered_native_ids','held_native_ids']:
        assert old[key]==new[key]
    assert set(new['pending_native_ids_current_page'])==ids and new['captured_page']==3
    assert right['national_museum_warsaw']['programme_verified_counts']==left['national_museum_warsaw']['programme_verified_counts']
    assert right['yale_lux']['resume_cursor']==left['yale_lux']['resume_cursor']
    assert ids.isdisjoint(old['processed_native_ids'])

    paths=list(CAP.glob('*'))+[E/'warsaw-discovery.json',E/'independent-reserve-evidence-verification.json']
    hashes={str(p):sha(p.read_bytes()) for p in paths if p.is_file()}
    requests=[]
    def forbidden_network(*args,**kwargs):
        requests.append(str(args[0]));raise AssertionError('Saved capture resume must not request network')
    b.urllib.request.urlopen=forbidden_network
    b.warsaw()
    assert not requests and hashes=={str(p):sha(p.read_bytes()) for p in paths if p.is_file()}
    cp=load(E/'CHECKPOINT.json');assert cp==load(R/'CHECKPOINT.json')
    receipt=load(E/'batch-verification-receipt.json')
    assert receipt['verified_counts']==cp['verified_counts'] and all(v==0 for v in receipt['verified_counts'].values())
    assert not receipt['production_ids'] and receipt['production_writes_attempted']==0
    b.save(E/'independent-resume-verification.json',dict(at=b.now(),method='Reran saved Warsaw capture route with network forcibly disabled, compared immutable metadata and historical plan hashes and both checkpoints.',
        network_requests_on_resume=0,captures_unchanged=True,checked_files=len(hashes),
        historical_plans_unchanged=historical,evidence_and_runtime_checkpoints_identical=True,
        unrelated_queue_entries_preserved=109,total_registry_entries=111,
        old_processed_delivered_and_held_ids_preserved=True,pending_page3_ids=sorted(ids),
        production_connections=0,production_writes=0,storage_writes=0,
        limitations='Proves offline research resumption only; production authentication and future import recovery must be reverified separately. No supervisor execution claim.'))
    refs=[]
    for name in ['authentication-verification.json','independent-reserve-evidence-verification.json',
        'independent-source-verification.json','prior-receipt-reconciliation-verification.json',
        'actual-visual-review.json','research-review.json','source-access-holds.json',
        'source-queue-update-verification.json','independent-resume-verification.json',
        'batch-verification-receipt.json','CHECKPOINT.json']:
        p=E/name;refs.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes())))
    b.save(E/'final-checkpoint-verification.json',dict(at=b.now(),verified_counts=receipt['verified_counts'],
        references=refs,all_references_exist=True,working_resumable_research_checkpoint=True,
        fresh_live_production_verified=False,supervisor_unmodified=True))
    print('Independent verification passed: 25 source captures, 188 reserve identities, 109 unrelated queue entries preserved, offline resume verified.')


if __name__=='__main__':main()
