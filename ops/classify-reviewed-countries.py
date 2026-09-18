#!/usr/bin/env python3
"""Set the reviewed country classification flag; never publish a painter."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('countries',Path(__file__).with_name('review-painter-countries.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
RUN=c.RUN/'classification';FIELD='geography'
def save(name,value):c.m.r.core.save_new(RUN/name,value)
def read(name):return json.loads((RUN/name).read_text())

def prepare():
    manifest,entries=c.load_plan();candidates=[]
    for target in ('local','production'):
        assert c.read(target+'-verification.json')['plan_sha256']==manifest['sha256']
        snapshots={}
        with c.m.r.base.connect(target=='production') as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            for start in range(0,len(entries),100):
                batch=entries[start:start+100];rows=c.selected(db,batch)
                for e in batch:
                    row=rows[e['artist']['slug']]
                    if row['row']['geography_review_state']!='not_reviewed':continue
                    assert row['row']['status']=='review' and row['row']['published_at'] is None
                    assert any(x['country_code']==e['country_code'] and x['relationship_type']=='cultural_affiliation' for x in row['countries'])
                    snapshots[row['row']['slug']]=row
                    if target=='local':candidates.append({'slug':row['row']['slug'],'country_code':e['country_code'],'evidence':e['evidence']})
        if target=='production':assert set(snapshots)=={x['slug'] for x in candidates},'Classification candidates differ between DBs'
        path=c.BACKUPS/('country-classification-'+target+'-preimages.json');c.m.r.core.save_new(path,{'at':c.m.r.core.now(),'rows':snapshots,'source_plan_sha256':manifest['sha256']})
        save(target+'-preflight.json',{'rows':len(snapshots),'preimage_sha256':c.m.r.core.sha(path.read_bytes())})
    save('plan.json',candidates);save('manifest.json',{'at':c.m.r.core.now(),'rows':len(candidates),'sha256':c.m.r.core.sha((RUN/'plan.json').read_bytes()),'source_plan_sha256':manifest['sha256']});print('Country classification plan',len(candidates),flush=True)

def apply(target):
    manifest=read('manifest.json');assert c.m.r.core.sha((RUN/'plan.json').read_bytes())==manifest['sha256'];entries=read('plan.json')
    before=json.loads((c.BACKUPS/('country-classification-'+target+'-preimages.json')).read_text())
    for name in ('local','production'):assert read(name+'-preflight.json')['rows']==manifest['rows']
    with c.m.r.base.connect(target=='production') as db:
        for start in range(0,len(entries),100):
            path=RUN/'applied'/target/f'{start//100+1:03d}.json'
            if path.exists():continue
            batch=entries[start:start+100];outcomes=[]
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE');db.execute("SET LOCAL statement_timeout='90s'");db.execute('SELECT pg_advisory_xact_lock(2026090959)');db.execute('SELECT pg_advisory_xact_lock(559220260914)')
                sid=db.execute("SELECT id FROM sources WHERE slug='overnight-country-review-20260913'").fetchone()['id']
                rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in batch],True)
                with db.pipeline():
                    for e in batch:
                        now=rows[e['slug']];old=before['rows'][e['slug']];assert now==old,('Painter changed after country review',e['slug'])
                        proof=db.execute("SELECT evidence_note::jsonb proof FROM citations WHERE entity_type='artist' AND entity_id=%s AND field_name=%s",(now['row']['id'],c.FIELD)).fetchone();assert proof and proof['proof']['plan_sha256']==manifest['source_plan_sha256'] and proof['proof']['country_code']==e['country_code']
                        db.execute("UPDATE artists SET geography_review_state='classified',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND geography_review_state='not_reviewed'",(c.ACTOR,now['row']['id']))
                        ev=e['evidence'][0]
                        c.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=now['row']['id'],field_name=FIELD,source_id=sid,source_record_id=ev['source_scheme']+':'+ev['person_id'],source_url=ev['source_receipt']['url'],retrieved_at=ev['source_receipt']['retrieved_at'],created_by=c.ACTOR,evidence_note=json.dumps({'classification_plan_sha256':manifest['sha256'],'country_code':e['country_code'],'country_evidence':e['evidence'],'scope':'Source-supported cultural affiliation reviewed. Does not assert exclusive citizenship or approve publication.'},ensure_ascii=False)))
                        outcomes.append({'slug':e['slug'],'artist_id':now['row']['id'],'country_code':e['country_code']})
            c.m.r.core.save_new(path,{'at':c.m.r.core.now(),'plan_sha256':manifest['sha256'],'outcomes':outcomes});print(target,'country classification',start//100+1,len(batch),flush=True)
    checked=[]
    with c.m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY')
        for start in range(0,len(entries),100):
            batch=entries[start:start+100];rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in batch])
            for e in batch:
                now=rows[e['slug']];old=before['rows'][e['slug']];ignored={'revision','updated_at','updated_by','geography_review_state'}
                assert {k:v for k,v in now['row'].items() if k not in ignored}=={k:v for k,v in old['row'].items() if k not in ignored}
                assert now['row']['geography_review_state']=='classified' and now['row']['revision']==old['row']['revision']+1 and now['countries']==old['countries'] and now['authorities']==old['authorities']
                checked.append(e['slug'])
        citation_count=db.execute("SELECT count(*) n FROM citations WHERE field_name='geography' AND evidence_note::jsonb->>'classification_plan_sha256'=%s AND source_id=(SELECT id FROM sources WHERE slug='overnight-country-review-20260913')",(manifest['sha256'],)).fetchone()['n'];assert citation_count==len(entries)
    save(target+'-verification.json',{'at':c.m.r.core.now(),'plan_sha256':manifest['sha256'],'classified':len(checked),'all_other_metadata_and_review_status_preserved':True,'slugs':checked});print(target,'country classification verified',len(checked),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply']);p.add_argument('--target',choices=['local','production']);a=p.parse_args();prepare() if a.command=='prepare' else apply(a.target)
