"""Reconcile a member-access policy edit without weakening any artwork preflight."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-kazantzakis-more-resume-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
a,m,RUN=r.a,r.m,r.RUN
ORIGINAL=a.PLAN
a.PLAN=a.RUN/(a.KEY+'-plan-002.json.gz')
ORIGINAL_SHA='6e43e487b4c4fa63455b230f53a64bb83d123c7c30ff8854c9ffac2a330386fd'
OLD_POLICY='63970685af72ae983e79b0f21205d3144db690eb6e97db8f1beeccf5518c04d6'
NEW_POLICY='ad0d8067ebf9a99e3198d1d6d0c9853e6acdd8932c5a5a0a9e5bb006416d0241'

def prepare():
    assert not a.PLAN.exists()and a.reference(ORIGINAL)['sha256']==ORIGINAL_SHA
    old=m.load(ORIGINAL);agents=m.ROOT/'AGENTS.md';raw=agents.read_text();assert hashlib.sha256(agents.read_bytes()).hexdigest()==NEW_POLICY
    start=raw.index('- Member access and bookmarks (10 October 2026):');end=raw.index('- Unified catalogue (8 October 2026):')
    removed=raw[start:end];reconstructed=raw[:start]+raw[end:]
    assert hashlib.sha256(reconstructed.encode()).hexdigest()==OLD_POLICY
    for pin in old['evidence']:
        if pin['path']=='AGENTS.md':assert pin['sha256']==OLD_POLICY
        else:a.checked(pin)
    for pin in old['external_evidence']:assert hashlib.sha256(Path(pin['path']).read_bytes()).hexdigest()==pin['sha256']
    assert hashlib.sha256(Path(old['backup_path']).read_bytes()).hexdigest()==old['backup_sha256']
    assert not(a.RUN/(a.KEY+'-applied.json')).exists()
    with a.i.prod.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');a.preflight(db,old)
    policy=RUN/'policy-reconciliation-001.json'
    m.save(policy,dict(at=m.now(),original_plan=a.reference(ORIGINAL),old_policy_sha256=OLD_POLICY,new_policy_reference=a.reference(agents),added_instruction=removed,
        exact_change_proof='Removing this one added member-access/bookmarks paragraph reproduces the exact previous AGENTS.md SHA-256.',
        assessment='The added instruction makes artist/artwork pages public, requires login for museum browsing/private bookmarks, and forbids local-debug database fixtures. It does not change source-backed selected production additions, creator/date evidence, review state, holdings/display separation, or local read-only safeguards. This batch changes none of those access controls.',
        initial_apply_attempt='Rejected by original immutable plan hash validation before any database connection or production write.',
        live_preflight_repeated=True,records_unchanged=105,protected_existing_unchanged=128,protected_prior_unchanged=921,
        backup_reuse='Successful CloudSQL backup1791630924075 still precedes all batch writes. Scoped before-state and prior-state were freshly rechecked unchanged; no backup restart is required.',
        script_reference=a.reference(Path(__file__).resolve())))
    new=copy.deepcopy(old);new['at']=m.now();new['supersedes_plan']=a.reference(ORIGINAL);new['policy_reconciliation_reference']=a.reference(policy)
    new['evidence']=[a.reference(agents)if pin['path']=='AGENTS.md'else pin for pin in old['evidence']]
    new['evidence'] += [a.reference(p)for p in [ORIGINAL,policy,Path(__file__).resolve(),a.RUN/'cloud-backup-001.json',RUN/'cloud-backup-completed-001.json']]
    assert len({x['path']for x in new['evidence']})==len(new['evidence'])
    assert new['records']==old['records']and new['before']==old['before']and new['prior_state']==old['prior_state']and new['scoped_ids']==old['scoped_ids']
    m.save(a.PLAN,new);p,digest=a.validate_plan();assert p==new
    print(json.dumps(dict(plan=a.reference(a.PLAN),records=105,live_preflight_rechecked=True)),flush=True)

if __name__=='__main__':prepare()
