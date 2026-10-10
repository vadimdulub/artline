#!/usr/bin/env python3
"""Reconcile explicitly reviewed museum names; retain source identities and URLs."""
import argparse,gzip,importlib.util,json,uuid
from pathlib import Path
s=importlib.util.spec_from_file_location('priority',Path(__file__).with_name('museum-1-10-priority-20261007.py'))
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
c=p.c;RUN=p.ROOT/'institution-identities';OP='museum-1-10-identities-20261007'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
PAIRS=[
 ('a7dbf40f-ec15-5c73-8511-de98ddab08d6','f3a41514-e262-4b0a-9e61-01bba7f4e6e9','https://en.rusmuseum.ru/pages/about/',['The Russian Museum','State Russian Museum','St Petersburg'],'Russian Museum and State Russian Museum identify the same institutional collection in Saint Petersburg; individual palace branches remain distinct.'),
 ('0fcbc49a-a04f-58d0-9306-2777b96a03cd','cc592311-a6e2-41f9-a62e-bd76afedc40e','https://www.pushkinmuseum.art/museum/index.php?lang=en',['Pushkin State Museum of Fine Arts','Moscow'],'Pushkin Museum in Moscow is the shortened name of the existing Pushkin State Museum of Fine Arts institutional collection.'),
 ('f3819670-50b5-5d26-9f06-47a6d5dc684d','30de07a6-aa14-5f2b-a5e1-15b1d901a44a','https://buffaloakg.org/about/our-history',['Buffalo AKG Art Museum','formerly the Albright-Knox Art Gallery'],'The official institutional history explicitly identifies Albright-Knox Art Gallery as the former name of Buffalo AKG Art Museum.'),
 ('88d494df-1f62-5003-88f0-b46821b70a8c','3336bc1c-c1f3-403b-b628-6d898db03956','https://www.mba-lyon.fr/fr',['Musée des Beaux-Arts de Lyon','69001 Lyon'],'The full source label and the existing Joconde institution both identify the Musée des Beaux-Arts in Lyon, not the separate Hospices Civils collection.'),
 ('21eb50f3-b1c1-5ddf-b67d-ed84a51683a4','da77335f-ff65-57a9-9ce9-66b24211c87c','https://www.hlmd.de/en/visit',['Hessisches Landesmuseum Darmstadt','Darmstadt'],'German Hessisches Landesmuseum Darmstadt and English Hessian State Museum Darmstadt identify the same institution; official native name and city confirmed.')]


def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))


def snapshot(db,alias,canonical):
    def rows(table,where,args):return [x['v']for x in db.execute('SELECT to_jsonb(t)v FROM '+table+' t WHERE '+where+' ORDER BY id',args)]
    institutions=rows('institutions','id=ANY(%s::uuid[])',([alias,canonical],));assert len(institutions)==2
    byid={x['id']:x for x in institutions}
    assert all(not x['canonical_institution_id']and x['status']!='archived'for x in institutions)
    assert alias in p.BASE and byid[alias]['name']==p.BASE[alias]['institution']['name']
    assert not db.execute('SELECT 1 FROM institutions WHERE canonical_institution_id=%s',(alias,)).fetchone()
    assert not db.execute('SELECT 1 FROM institution_venues WHERE institution_id=%s',(alias,)).fetchone()
    assert not db.execute('SELECT 1 FROM curated_collections WHERE institution_id=%s',(alias,)).fetchone()
    assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE institution_id=%s AND claim_type='display'",(alias,)).fetchone()
    works=rows('artworks','current_institution_id=%s',(alias,))
    assertions=rows('artwork_location_assertions',"institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(alias,))
    assert {x['id']for x in works}=={x['artwork_id']for x in assertions},'Every transferred work must retain its accepted, sourced holding'
    return dict(institutions=institutions,artworks=works,assertions=assertions)


def plan():
    pairs=[]
    with c.d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for alias,canonical,url,tokens,basis in PAIRS:
            saved=c.load(RUN/'parsed'/(c.d.sha(url.encode())+'.json'));rc=saved['receipt']
            raw=gzip.decompress((c.ROOT/rc['body_path']).read_bytes());assert c.d.sha(raw)==rc['sha256']and rc['status']==200
            assert all(c.norm(token)in c.norm(saved['text'])for token in tokens),(url,'Expected identity statement missing')
            before=snapshot(db,alias,canonical)
            pairs.append(dict(alias=alias,canonical=canonical,source_receipt=rc,basis=basis,editorial_confidence=0.95,confidence_basis='Explicit official museum identity, institutional name/translation and same city; editorial assessment, not calibrated probability.',before=before))
    c.save(RUN/'plan.json.gz',dict(at=c.d.now(),pairs=pairs,scope='Production only; no object merge, publication, image or display changes. Original museum rows remain as resolvable aliases.'))
    c.save(BACKUP/'plan-and-preimages.json.gz',pairs)
    print('Museum identity plan:',len(pairs),'aliases;',sum(len(x['before']['artworks'])for x in pairs),'existing works to consolidate',flush=True)


def apply():
    path=RUN/'plan.json.gz';plan=c.load(path);digest=c.d.sha(path.read_bytes());after=[]
    with c.d.connect(readonly=False)as db,db.transaction():
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(202610053)')
        for row in plan['pairs']:
            rc=row['source_receipt'];raw=gzip.decompress((c.ROOT/rc['body_path']).read_bytes());assert c.d.sha(raw)==rc['sha256']and rc['status']==200
            db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',([row['alias'],row['canonical']],)).fetchall()
            ids=[x['id']for x in row['before']['artworks']]
            db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,)).fetchall()
            assert snapshot(db,row['alias'],row['canonical'])==row['before'],'Museum identity preimages changed'
        c.save(BACKUP/'transaction-preimages.json.gz',dict(at=c.d.now(),plan_sha256=digest,pairs=plan['pairs']))
        c.d.insert(db,'sources',dict(id=uid('source'),slug=OP,name='Reviewed official museum identities for the 1–10 artwork priority pass',source_type='authority_data',base_url=None))
        for row in plan['pairs']:
            alias,canonical=row['alias'],row['canonical'];before=row['before'];ids=[x['id']for x in before['artworks']]
            db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now()WHERE id=%s',(canonical,alias))
            db.execute("UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(canonical,alias))
            db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=ANY(%s::uuid[])AND current_institution_id=%s',(canonical,c.d.ACTOR,ids,alias))
            for iid in [alias,canonical]:
                c.d.insert(db,'citations',dict(id=uid('identity/'+iid),entity_type='institution',entity_id=iid,field_name='institution_identity',source_id=uid('source'),source_url=row['source_receipt']['url'],
                    evidence_note=json.dumps(dict(operation=OP,plan_sha256=digest,basis=row['basis'],editorial_confidence=row['editorial_confidence'],confidence_basis=row['confidence_basis'],source_receipt=row['source_receipt'],original_institutions=before['institutions'],scope=plan['scope']),ensure_ascii=False),retrieved_at=row['source_receipt']['retrieved_at'],created_by=c.d.ACTOR))
            actual=[x['v']for x in db.execute('SELECT to_jsonb(a)v FROM artworks a WHERE id=ANY(%s::uuid[])ORDER BY id',(ids,))]
            for old,new in zip(before['artworks'],actual):
                assert new['current_institution_id']==canonical
                assert all(new[k]==v for k,v in old.items()if k not in {'current_institution_id','updated_at','updated_by','revision'})
            assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s',(alias,)).fetchone()
            after.append(dict(alias=alias,canonical=canonical,artworks=actual))
        c.save(BACKUP/'transaction-after.json.gz',dict(at=c.d.now(),plan_sha256=digest,pairs=after))
    c.save(RUN/'applied.json',dict(at=c.d.now(),target='production',plan_sha256=digest,aliases=len(after),artworks_transferred=sum(len(x['artworks'])for x in after),pairs=after))
    print('Committed',len(after),'museum identity reconciliations',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['plan','apply']);args=ap.parse_args();globals()[args.phase]()
