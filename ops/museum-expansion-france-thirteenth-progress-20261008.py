"""Freeze a partial editorial review and verify the untouched local baseline."""
import gzip,hashlib,importlib.util,json
from pathlib import Path

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

i=module('identity',Path(__file__).with_name('museum-expansion-france-thirteenth-identity-20261008.py'))
m=i.m;RUN=i.RUN

def main():
    dest=RUN/'review-progress-001.json';assert not dest.exists()
    cp=RUN/'native-candidates-001.json.gz';ip=RUN/'native-identity-001.json.gz'
    citp=RUN/'identity-citations-001.json.gz';initialp=RUN/'initial-scope-001.json.gz'
    rows=m.load(cp)['rows'];ix=m.load(ip);initial=m.load(initialp)
    assert len(rows)==620 and ix['candidate_reference']==i.ref(cp)
    for dep in m.load(cp)['dependencies']+[m.load(cp)['parser_reference'],ix['query_reference'],ix['base_query_reference']]:i.checked(dep)
    working=Path(__file__).with_name('museum-expansion-france-thirteenth-notes-20261008.py')
    snapshot=RUN/'review-progress-notes-001.py';assert not snapshot.exists()
    snapshot.write_bytes(working.read_bytes());notes=module('notes_snapshot',snapshot)
    reviewed=set(notes.NOTES)|set(notes.HOLDS)
    assert set(notes.NOTES).isdisjoint(notes.HOLDS) and reviewed==set(range(1,421))
    assert set(notes.QUALIFIED)<=set(notes.NOTES) and set(notes.DATE_OVERRIDES)<=set(notes.NOTES)
    for n,(label,key) in notes.QUALIFIED.items():assert label and rows[n-1]['facts']['source_fields'].get(key)
    for n,value in notes.DATE_OVERRIDES.items():
        assert value['first']<=value['last']<=1970 and str(value['first']) in rows[n-1]['facts']['source_fields'][value['source_field']]
    dependencies={cp,ip,citp,initialp,snapshot,Path(__file__).resolve()}
    primary=[];citations=m.load(citp)['citations']
    for aid in sorted(notes.EXTRA_COMPARATOR_IDS):
        matches=[c for c in citations if c['entity_id']==aid and '/notice/joconde/' in c['source_url']]
        assert matches,aid
        for citation in matches:
            note=json.loads(citation['evidence_note']);sid=citation['source_url'].rstrip('/').split('/')[-1]
            if note.get('native_capture_reference'):
                path=i.checked(note['native_capture_reference']);bundle=m.load(path);i.f.body(bundle)
                dependencies.update([path,m.ROOT/bundle['body_path']])
                for key in ['review_reference','identity_reference']:
                    if note.get(key):dependencies.add(i.checked(note[key]))
                sources=bundle['data']
            else:
                path=m.ROOT/(note.get('body_path') or note['evidence_path'])
                expected=note.get('source_receipt',{}).get('sha256') or note['source_response_sha256']
                raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==expected
                sources=json.loads(raw)['data'];dependencies.add(path)
            source=[r for r in sources if r['Reference']==sid];assert len(source)==1
            if note.get('facts',{}).get('source_fields'):assert source[0]==note['facts']['source_fields']
            primary.append(dict(existing_artwork_id=aid,source_record_id=sid,literal_primary_record=source[0],citation=citation,evidence_reference=i.ref(path)))
    primary_path=RUN/'manual-comparison-supplement-001.json.gz';assert not primary_path.exists()
    m.save(primary_path,dict(at=m.now(),rows=primary,dependencies=[i.ref(p) for p in sorted(dependencies) if p!=snapshot],policy='Read-only primary evidence for manual comparison leads. Existing records and museum links unchanged.'))
    observations=RUN/'web-observations-002.json';assert not observations.exists()
    m.save(observations,dict(at=m.now(),research_leads_only=True,observations=[dict(source_url='https://www.musee-orsay.fr/fr/ressources/repertoire-artistes-personnalites/bisceglia-3882',title='Bisceglia — Musée d’Orsay artist/foundry authority',method='Public web-search result; no direct page capture attempted',observed_fact='The authority lists activity in 1904–1962, with Bisceglia frères identified as the 1907–1912 phase and Bisceglia as 1912–1962.',application='Candidate 314 bears the frères Paris mark but a 1904 model/inscription date. Hold actual casting chronology; this general authority does not establish an exact casting year for the object.',access_policy='The earlier Coubertin-page HTTP 403 hold remains in place. No retry or alternate retrieval of that denied page was attempted.')]))
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        actual=json.loads(json.dumps(i.snapshot(db,initial['scoped_ids']),default=str))
        counts=i.counts(db)
        assert actual==initial['snapshot']
        assert json.loads(json.dumps(counts,default=str))==initial['counts']
    states=[dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],state=('provisional_accept_pending_final_identity' if r['number'] in notes.NOTES else 'editorial_hold'),basis=(notes.NOTES|notes.HOLDS)[r['number']]) for r in rows if r['number'] in reviewed]
    targets=m.load(i.f.n.DISCOVERY)['targets']
    by_museum={t['id']:dict(name=t['name'],slug=t['slug'],reviewed=sum(r['institution_id']==t['id'] for r in states),provisional=sum(r['institution_id']==t['id'] and r['state']=='provisional_accept_pending_final_identity' for r in states),held=sum(r['institution_id']==t['id'] and r['state']=='editorial_hold' for r in states),unreviewed=sum(r['institution_id']==t['id'] and r['number'] not in reviewed for r in rows)) for t in targets}
    dependencies.update([primary_path,observations])
    m.save(dest,dict(at=m.now(),read_only=True,database_writes=0,reviewed=len(reviewed),provisional=len(notes.NOTES),held=len(notes.HOLDS),remaining=len(rows)-len(reviewed),unreviewed_numbers=sorted(set(range(1,621))-reviewed),decisions=states,by_museum=by_museum,protected_initial_records=len(initial['scoped_ids']),baseline_unchanged=True,counts=counts,notes_snapshot=i.ref(snapshot),mutable_notes_digest_at_capture=i.ref(working)['sha256'],dependencies=[i.ref(p) for p in sorted(dependencies)],pending_work=['Review 421–500 Jean de La Fontaine and 501–620 Tomi Ungerer.','Complete batch identity and alias/maker expansion; recompute final read-only identity scope.','Integrate and test explicit new-record cast-date derivation for candidate 266, retaining original fields.','Resolve or retain physical-unit, version, date and sparse-existing-record holds.','Only then freeze final review, prepare and verify transactional local additions, readback/replay and wave-68 delivery.'],policy='Partial research checkpoint, not an approved production plan. Mutable working notes remain editable; the immutable copy is the historical evidence. No museum target is declared achieved from provisional records.'))
    print(json.dumps(dict(reviewed=len(reviewed),provisional=len(notes.NOTES),held=len(notes.HOLDS),remaining=len(rows)-len(reviewed),protected_unchanged=len(initial['scoped_ids']),database_writes=0,manual_primary_records=len(primary),by_museum=by_museum,checkpoint=i.ref(dest)),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
