#!/usr/bin/env python3
"""Read-only source selection for the next five underfilled French collections."""
import collections,csv,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('museum-expansion-france-fifth-apply-20261008.py'));prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior);m=prior.m
RUN=m.RUN/'native/france-sixth-minimum-20261008';DISCOVERY=RUN/'five-museum-discovery-001.json.gz'
CODES=['M0812','M0810','M0467','M0615','M0072']
def main():
    assert not DISCOVERY.exists();cp=prior.RUN/'delivery-checkpoint-001.json';assert prior.reference(cp)['sha256']=='432ad5f978e1dd6d8f802f158dfbb901cb9fa9626ae1c81cc39e5c35fa67e947'
    frozen=m.load(cp)
    for dep in frozen['artifacts']:
        prior.prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==prior.prior.b.prior.old.h.OLD else prior.checked(dep)
    for dep in frozen['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
    p,d=prior.validate_plan()
    with m.connect() as db:proof=prior.verify(db,p,d)
    m.save(RUN/'continuation-001.json',dict(at=m.now(),previous_goal_turn='progress',verified_additions=147,previous_checkpoint=prior.reference(cp),database_verification=proof,goal_remains_active=True))
    with (m.RUN/'museum-coverage-after-wave-60.csv').open(newline='') as fp:targets=[r for r in csv.DictReader(fp) if r['slug'] in ['joconde-'+c.lower() for c in CODES]]
    assert len(targets)==5;by={r['slug'].removeprefix('joconde-').upper():r for r in targets}
    with m.SNAPSHOT.open('rb') as fp:assert hashlib.file_digest(fp,'sha256').hexdigest()==m.SNAPSHOT_SHA
    csv.field_size_limit(8_000_000);rows=[]
    with m.SNAPSHOT.open(encoding='utf-8-sig',newline='') as fp:
        for raw in csv.DictReader(fp,delimiter='|'):
            if raw['Code_Museofile'] in by:rows.append(dict(museum=by[raw['Code_Museofile']],raw_source_record=raw))
    ids=sorted({r['raw_source_record']['Reference'] for r in rows});urls=sorted({protocol+'://'+host+'/notice/joconde/'+rid+slash for protocol in ['http','https'] for host in ['pop.culture.gouv.fr','www.pop.culture.gouv.fr'] for rid in ids for slash in ['','/']})
    with m.connect() as db:
        knownids=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%joconde%%' ORDER BY entity_id,scheme,external_id",(ids,)).fetchall()
        cites=db.execute("SELECT entity_id::text,source_record_id,source_url,field_name FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_record_id,source_url,field_name",(urls,)).fetchall()
        iids=sorted(r['id'] for r in targets);existing=db.execute('SELECT '+prior.r.identity.i.ARTCOLS+' FROM artworks a WHERE current_institution_id=ANY(%s::uuid[]) OR a.id IN (SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[])) ORDER BY a.id',(iids,iids)).fetchall()
    known={v['external_id'] for v in knownids}|{v['source_url'].rstrip('/').rsplit('/',1)[-1] for v in cites}
    for row in rows:row['already_known']=row['raw_source_record']['Reference'] in known
    m.save(DISCOVERY,dict(at=m.now(),snapshot_path=str(m.SNAPSHOT.relative_to(m.ROOT)),snapshot_sha256=m.SNAPSHOT_SHA,targets=targets,rows=rows,known_identifiers=knownids,known_citations=cites,existing=existing,discovery_code=prior.reference(Path(__file__).resolve()),read_only=True))
    print(json.dumps(dict(rows=len(rows),new_source_ids=len(ids)-len(known),by_museum={code:dict(rows=sum(r['raw_source_record']['Code_Museofile']==code for r in rows),new=sum(r['raw_source_record']['Code_Museofile']==code and not r['already_known'] for r in rows)) for code in CODES})),flush=True)
if __name__=='__main__':main()
