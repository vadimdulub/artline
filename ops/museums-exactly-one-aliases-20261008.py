#!/usr/bin/env python3
"""Reconcile specifically reviewed duplicate museum identities in production."""
import argparse,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('round3',Path(__file__).with_name('museums-exactly-one-round3-20261008.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);d=m.d
RUN=m.RUN/'aliases';OP=m.OP+'-aliases';BACKUP=Path.home()/'Library/Application Support/Artline/backups'/m.OP/'aliases'
# Specific city and institution identities, never a fuzzy-name merge.
PAIRS=[
 ('0d867be6-bb10-5f84-8693-4399f4ca4d11','02c1abce-47a7-4bf7-aed4-a01095aa6462','https://mba.caen.fr/le-musee-des-beaux-arts-de-caen',['Caen','Beaux-Arts'],'Caen museum authority Q569079 and Museofile M0657 identify the same fine-arts museum in the château, not the separate Musée de Normandie.'),
 ('45a357d5-cee2-5215-8ff4-9b4598ab1566','ab9b25e7-6b81-457c-98c0-0ff535df594c','https://www.carcassonne.org/article-page/presentation-et-horaires',['Carcassonne','beaux-arts'],'Carcassonne museum authority Q3330195 and Museofile M0440 identify the same fine-arts museum in the former Présidial.'),
 ('4e43d7bd-80b9-5b72-8398-c978e2780714','e69f8210-9774-44aa-8f42-75196ce42aa9','https://www.doledujura.fr/musee-des-beaux-arts',['Dole','beaux-arts'],'The fine-arts and archaeology museum in Dole is the museum abbreviated Musée des Beaux-Arts de Dole; retain Museofile M0347 as canonical.'),
 ('9d543f55-86c1-5a81-b8a3-446f2ea5eb17','b356393c-480a-43f7-8414-21d8d17a3ad4','https://musee-des-beaux-arts.nancy.fr/accueil',['Nancy','Beaux-arts'],'Both names identify Musée des Beaux-Arts de Nancy, Museofile M0512; not the separate Musée lorrain.'),
 ('465640a2-8090-5011-b2b5-3117559b571f','d9c38ba1-7856-5562-9917-75638b5b3992','https://www.roubaix-lapiscine.com/',['Roubaix','Piscine'],'La Piscine in Roubaix is the Musée d’art et d’industrie André Diligent, Museofile M0634; the short and full names identify one collection.'),
 ('ba659c8c-83a4-51c6-9855-b1e15d9963c9','bcc39b03-70ed-461a-968a-2c806ebf47e6','https://www.museegoya.fr/',['Castres','Goya'],'Goya Museum Q246821 and Musée Goya — Castres (M0594) identify the same Castres collection, not a Spanish Goya museum.'),
 ('78ec4c88-dc54-5128-a782-eb0991d8d74a','bc7ec6b3-6e17-53dd-9b4c-af86ec4443c9','https://discovernewfields.org/',['Indianapolis Museum of Art'],'The English IMA name and French Musée d’Art d’Indianapolis Q1117704 identify the art museum at Newfields; this does not merge other Newfields sites.'),
 ('00628c62-9053-5526-9271-6990774a32ea','62b67d4e-3089-5d3f-9541-a2bdccf38ad0','https://www.gamtorino.it/it',['Torino','Moderna'],'GAM Turin and Turin Civic Gallery of Modern and Contemporary Art Q3757708 identify the same Galleria Civica d’Arte Moderna e Contemporanea, not the separate civic ancient-art museum.'),
 ('cbe5c847-b35a-5e24-bf5f-e5300bf9fbce','fff62843-358e-5d70-8489-43494304d030','https://museum-nesterov.ru/',['Нестеров','Уф'],'The Bashkirian/Bashkir State Art Museum named for M. V. Nesterov in Ufa is one institution, authority Q4080170.'),
 ('84c43240-95c1-5ece-82d3-73103ec3ce3f','a1f5706d-e5d8-5f11-97db-88952a4ba523','https://vmhkolkata.com/',['Victoria Memorial','Kolkata'],'Victoria Memorial Hall and Victoria Memorial Q1356352 identify the same Kolkata museum, not other monuments with this name.'),
]

def capture(url):
    path=RUN/'captures'/(d.sha(url.encode())+'.json')
    if path.exists():
        rc=d.load(path);raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes());assert d.sha(raw)==rc['sha256'];return raw,rc
    response=d.requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (institution identity verification)'},timeout=(12,30));raw=response.content;assert len(raw)<5_000_000
    body=path.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0))
    rc=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=d.now(),sha256=d.sha(raw),body_path=str(body.relative_to(m.ROOT)),bytes=len(raw));d.save(path,rc)
    return raw,rc

def sources():
    ready=[];held=[]
    for aid,cid,url,tokens,basis in PAIRS:
        try:
            raw,rc=capture(url);assert rc['status']==200,'HTTP '+str(rc['status'])
            soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
            assert all(t.casefold() in text.casefold() for t in tokens),'identity text absent'
            ready.append(dict(alias=aid,canonical=cid,source=rc,basis=basis,required_identity_tokens=tokens,confidence=.95))
            print('Supported museum identity',url,flush=True)
        except Exception as e:
            held.append(dict(alias=aid,canonical=cid,url=url,reason=str(e)));print('Held identity',url,str(e),flush=True)
    d.save(RUN/'source-reviewed.json',dict(ready=ready,held=held))

def snapshot(db,aid,cid):
    institutions={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(i) v FROM institutions i WHERE id=ANY(%s::uuid[]) ORDER BY id',([aid,cid],))}
    assert len(institutions)==2
    def rows(table,where,args):return [x['v'] for x in db.execute('SELECT to_jsonb(t) v FROM '+table+' t WHERE '+where+' ORDER BY id',args)]
    arts=rows('artworks','current_institution_id=%s',(aid,))
    holds=rows('artwork_location_assertions',"institution_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(aid,))
    assert {x['id'] for x in arts}=={x['artwork_id'] for x in holds}
    assert len(arts)==1 and arts[0]['status']!='archived'
    assert not db.execute("SELECT 1 FROM artwork_location_assertions WHERE institution_id=%s AND claim_type='display' LIMIT 1",(aid,)).fetchone()
    assert not db.execute('SELECT 1 FROM institution_venues WHERE institution_id=%s LIMIT 1',(aid,)).fetchone()
    assert not db.execute('SELECT 1 FROM curated_collections WHERE institution_id=%s LIMIT 1',(aid,)).fetchone()
    aidrows=[x['id'] for x in arts]
    sources=rows('citations',"entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aidrows,))
    identifiers=rows('external_identifiers',"entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(aidrows,))
    creators=[x['v'] for x in db.execute('SELECT to_jsonb(t) v FROM artwork_artists t WHERE artwork_id=ANY(%s::uuid[]) ORDER BY artist_id',(aidrows,))]
    media=[x['v'] for x in db.execute('SELECT to_jsonb(t) v FROM artwork_media t WHERE artwork_id=ANY(%s::uuid[]) ORDER BY media_id',(aidrows,))]
    counts=db.execute("SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(cid,)).fetchone()['n']
    return dict(institutions=institutions,artworks=arts,assertions=holds,citations=sources,identifiers=identifiers,creators=creators,media=media,canonical_count=counts)

def plan():
    source=d.load(RUN/'source-reviewed.json');ready=[];held=list(source['held'])
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        for row in source['ready']:
            try:
                before=snapshot(db,row['alias'],row['canonical'])
                assert all(not i['canonical_institution_id'] and i['status']!='archived' for i in before['institutions'].values())
                ready.append(dict(row,before=before))
                print('Plan',before['institutions'][row['alias']]['name'],'1 +',before['canonical_count'],flush=True)
            except AssertionError as e:held.append(dict(row,reason='Relationship review required: '+str(e)))
    value=dict(at=d.now(),operation=OP,records=ready,held=held)
    d.save(RUN/'plan.json.gz',value);d.save(BACKUP/'plan-and-preimages.json.gz',value)

def apply():
    path=RUN/'final-plan.json.gz';plan=d.load(path);digest=d.sha(path.read_bytes());assert plan['records']
    assert d.load(m.RUN/'backups.json')['production']['status']=='SUCCESSFUL'
    applied=[]
    with d.connect(False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='180s'")
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT pg_advisory_xact_lock(202610053)')
        allids=sorted({x[k] for x in plan['records'] for k in ['alias','canonical']})
        db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(allids,)).fetchall()
        for row in plan['records']:
            aid,cid=row['alias'],row['canonical'];before=row['before'];current=snapshot(db,aid,cid)
            assert current==before,'Production changed since reviewed plan'
            raw,rc=capture(row['source']['url']);assert rc==row['source'] and rc['status']==200
            assert all(t.casefold() in BeautifulSoup(raw,'html.parser').get_text(' ',strip=True).casefold() for t in row['required_identity_tokens'])
        d.save(BACKUP/'locked-preimages.json.gz',dict(plan_sha256=digest,records=plan['records']))
        sid=d.uid(OP+'/source')
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'authority_data',NULL)",(sid,OP,'Individually reviewed official museum identity reconciliation'))
        for row in plan['records']:
            aid,cid=row['alias'],row['canonical'];before=row['before'];artid=before['artworks'][0]['id']
            db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(artid,)).fetchone()
            db.execute('UPDATE institutions SET canonical_institution_id=%s,updated_at=now() WHERE id=%s',(cid,aid))
            db.execute("UPDATE artwork_location_assertions SET institution_id=%s WHERE institution_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(cid,aid))
            db.execute('UPDATE artworks SET current_institution_id=%s,revision=revision+1,updated_by=%s,updated_at=now() WHERE id=%s',(cid,d.ACTOR,artid))
            note=dict(plan_sha256=digest,basis=row['basis'],editorial_confidence=row['confidence'],confidence_is_probability=False,source_receipt=row['source'],original_alias_id=aid,canonical_id=cid,policy='Preserve original museum record and source identities as a canonical alias. Preserve artwork metadata, creators, source citations, media and publication. No new artwork or display claim.')
            for iid in [aid,cid]:db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'institution',%s,'institution_identity',%s,%s,%s,%s,%s)",(d.uid(OP+'/'+iid),iid,sid,row['source']['url'],json.dumps(note,ensure_ascii=False),row['source']['retrieved_at'],d.ACTOR))
            after=db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE id=%s',(artid,)).fetchone()['v']
            allowed={'current_institution_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in after.items() if k not in allowed}=={k:v for k,v in before['artworks'][0].items() if k not in allowed}
            assert after['current_institution_id']==cid and after['revision']==before['artworks'][0]['revision']+1
            applied.append(dict(alias=aid,canonical=cid,artwork_id=artid,canonical_before=before['canonical_count']))
    d.save(RUN/'applied.json',dict(at=d.now(),plan_sha256=digest,records=applied))
    print('COMMITTED',len(applied),'reviewed museum aliases and preserved artwork links',flush=True)

def final_plan():
    initial=d.load(RUN/'plan.json.gz');aid,cid,oldurl,tokens,basis=PAIRS[-1]
    url='https://www.victoriamemorial-cal.org/home/'
    raw,rc=capture(url);assert rc['status']==200
    text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert all(t.casefold() in text.casefold() for t in tokens)
    with d.connect() as db:before=snapshot(db,aid,cid)
    row=dict(alias=aid,canonical=cid,source=rc,basis=basis,required_identity_tokens=tokens,confidence=.95,before=before)
    plan=dict(initial,records=initial['records']+[row],held=[x for x in initial['held'] if x['alias']!=aid],prior_plan_sha256=d.sha((RUN/'plan.json.gz').read_bytes()),alternate_official_website=dict(original=oldurl,verified=url,basis='Official national Museums of India directory links victoriamemorial-cal.org for Victoria Memorial Hall, Kolkata.'))
    assert len(plan['records'])==10
    d.save(RUN/'final-plan.json.gz',plan);d.save(BACKUP/'final-plan-and-preimages.json.gz',plan)
    print('Final reviewed alias plan',len(plan['records']),flush=True)

def verify():
    plan=d.load(RUN/'final-plan.json.gz');receipt=d.load(RUN/'applied.json')
    assert receipt['plan_sha256']==d.sha((RUN/'final-plan.json.gz').read_bytes())
    loc=m.module('alias_verify','apply-artwork-locations-20261004.py');rows=[]
    with d.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        after=loc.snapshots(db,[r['before']['artworks'][0]['id'] for r in plan['records']])
        for row in plan['records']:
            before=row['before'];old=before['artworks'][0];new=after[old['id']];aid,cid=row['alias'],row['canonical']
            allowed={'current_institution_id','revision','updated_at','updated_by'}
            assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new['artwork'].items() if k not in allowed}
            assert new['artwork']['current_institution_id']==cid
            for key in ['identifiers','creators','media']:assert new[key]==before[key]
            current_assertions={x['id']:x for x in new['assertions']}
            for oldhold in before['assertions']:
                h=current_assertions[oldhold['id']]
                assert h['institution_id']==cid and {k:v for k,v in h.items() if k not in ['institution_id','updated_at']}=={k:v for k,v in oldhold.items() if k not in ['institution_id','updated_at']}
            cites=[x['v'] for x in db.execute("SELECT to_jsonb(c) v FROM citations c WHERE entity_type='artwork' AND entity_id=%s ORDER BY id",(old['id'],))]
            assert cites==before['citations']
            i=db.execute('SELECT canonical_institution_id::text FROM institutions WHERE id=%s',(aid,)).fetchone()
            assert i['canonical_institution_id']==cid
            assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s LIMIT 1',(aid,)).fetchone()
            n=db.execute("SELECT count(*) n FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(cid,)).fetchone()['n'];assert n>=before['canonical_count']+1
            rows.append(dict(alias_id=aid,alias_name=before['institutions'][aid]['name'],alias_slug=before['institutions'][aid]['slug'],canonical_id=cid,canonical_name=before['institutions'][cid]['name'],canonical_slug=before['institutions'][cid]['slug'],artwork_id=old['id'],artwork_title=old['title'],before_alias=1,before_canonical=before['canonical_count'],after=n,source_url=row['source']['url']))
    d.save(RUN/'verification.json',dict(at=d.now(),verified_aliases=len(rows),preserved_existing_artwork_records=len(rows),all_metadata_dates_creators_media_sources_publication_preserved=True,new_artworks=0,rows=rows))
    print('Verified',len(rows),'museum aliases and all preserved artwork relationships',flush=True)

def api_verify():
    proof=d.load(RUN/'verification.json');checks=[]
    for row in proof['rows']:
        paths=['https://artlines.org/api/backend/v1/museums/'+row[k]+'/works/'+row['artwork_id'] for k in ['alias_slug','canonical_slug']]
        results=[d.requests.get(url,timeout=(15,45)) for url in paths]
        ok=all(x.status_code==200 for x in results) and results[0].json()==results[1].json() and results[0].json().get('title')==row['artwork_title']
        checks.append(dict(alias=row['alias_name'],urls=paths,statuses=[x.status_code for x in results],verified=ok))
        print('Alias API',row['alias_name'],ok,flush=True)
    d.save(RUN/'api-verification.json',dict(at=d.now(),checks=checks,passed=sum(x['verified'] for x in checks),failed=sum(not x['verified'] for x in checks)))
    assert all(x['verified'] for x in checks)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['sources','plan','final_plan','apply','verify','api_verify']);args=p.parse_args();globals()[args.phase]()
