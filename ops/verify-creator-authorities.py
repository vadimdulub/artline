#!/usr/bin/env python3
"""Read-only full-scope verification for authority creator reconciliation."""
import argparse, importlib.util, json, concurrent.futures
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('apply_authorities',Path(__file__).with_name('reconcile-creator-authorities.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);m=a.m

def verify(target):
    manifest,entries=m.load_plan();snapshot=json.loads((m.BACKUPS/(target+'-preimages.json')).read_text());checked=[]
    with m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];works=m.selected_rows(db,batch);artists=m.artist_rows(db,batch)
            links=db.execute("""SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,c.source_url,c.evidence_note FROM artwork_artists aa
            LEFT JOIN citations c ON c.entity_type='artwork' AND c.entity_id=aa.artwork_id AND c.field_name=%s WHERE aa.artwork_id=ANY(%s::uuid[])""",(m.FIELD,[w['id'] for w in works.values()])).fetchall()
            assert len(links)==len(batch);byid={x['artwork_id']:x for x in links};assert len(byid)==len(batch)
            for e in batch:
                w=works[e['before']['slug']];before=snapshot['works'][w['slug']];artist=artists[e['artist']['slug']];p=artist['row']
                assert w['unlinked_creator_label'] is None and w['status']=='review' and w['published_at'] is None
                ignored={'unlinked_creator_label','revision','updated_at','updated_by'}
                assert {k:v for k,v in w.items() if k not in ignored}=={k:v for k,v in before.items() if k not in ignored},('Preserved metadata differs',w['slug'])
                assert w['revision']==before['revision']+1
                if not e['artist']['new']:assert artist==snapshot['artists'][p['slug']],('Existing painter changed',p['slug'])
                else:
                    assert all(p[k]==e['artist'][k] for k in ('id','slug','display_name','normalized_name','birth_year','death_year','status','entity_type'))
                    assert p['timeline_basis']=='life' and p['timeline_start_year']==p['birth_year'] and p['timeline_end_year']==p['death_year'] and p['published_at'] is None
                    assert artist['authorities']==e['artist']['authorities']
                link=byid[w['id']];assert link['artist_id']==p['id'] and link['attribution_role']=='primary' and link['source_url']==e['evidence']['object_url']
                ev=json.loads(link['evidence_note']);assert ev['plan_sha256']==manifest['sha256'] and ev['original_creator_label']==e['before']['unlinked_creator_label'] and ev['source_painter']==e['painter']
                checked.append({'slug':w['slug'],'artwork_id':w['id'],'title':w['title'],'artist_slug':p['slug'],'artist_id':p['id'],'source':e['source'],'new_painter':e['artist']['new'],'date_precision':w['date_precision'],'work_type':w['work_type'],'status':w['status']})
            restored={e['before']['slug']:{**works[e['before']['slug']],'unlinked_creator_label':e['before']['unlinked_creator_label']} for e in batch};m.guards(db,batch,restored,artists,False)
        totals=db.execute("SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks w WHERE unlinked_creator_label IS NOT NULL AND status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)) unlinked").fetchone()
    assert totals['artworks']==snapshot['counts']['artworks']
    assert totals['artists']==snapshot['counts']['artists']+manifest['new_painters']
    assert totals['unlinked']==snapshot['counts']['unlinked']-len(entries)
    m.save(target+'-verification.json',{'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'links_verified':len(checked),'new_painters_verified':manifest['new_painters'],'existing_painters_unchanged':True,'artwork_metadata_and_images_unchanged':True,'counts':totals,'rows':checked})
    print(target,'verified',len(checked),'links;',totals['unlinked'],'remain',flush=True)

def live():
    local=m.read('local-verification.json');prod=m.read('production-verification.json')
    key=lambda row:{k:v for k,v in row.items() if k not in ('artwork_id','artist_id')}
    assert [key(x) for x in local['rows']]==[key(x) for x in prod['rows']]
    samples={}
    for row in prod['rows']:samples.setdefault(row['artist_slug'],row)
    site='https://artline-web-lpuqqlugnq-ew.a.run.app'
    def check(row):
        url=site+'/api/backend/v1/artists/'+row['artist_slug']+'/works/'+row['artwork_id']
        response=requests.get(url,timeout=90);response.raise_for_status();d=response.json()
        assert d['id']==row['artwork_id'] and d['title']==row['title'] and d['status']=='review' and d['unlinked_creator_label'] is None
        return {'url':url,'status':response.status_code,'artist_slug':row['artist_slug'],'title':d['title']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(check,samples.values()))
    newslug=next(row['artist_slug'] for row in prod['rows'] if row['new_painter'])
    filters=[]
    for path in ['/api/backend/v1/painters/options?selected='+newslug+'&popular=false','/api/backend/v1/timeline?start=1100&end=2000&popular=false&painter='+newslug]:
        response=requests.get(site+path,timeout=90);response.raise_for_status();assert newslug in response.text
        filters.append({'url':site+path,'status':response.status_code})
    m.save('live-verification.json',{'at':m.r.core.now(),'checks':result,'filter_checks':filters,'local_production_mappings_equal':True})
    print('Live public preview passed for',len(result),'painters',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('target',choices=['local','production','live']);arg=p.parse_args();live() if arg.target=='live' else verify(arg.target)
