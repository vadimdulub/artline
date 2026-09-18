#!/usr/bin/env python3
"""Read-only integrity and public-preview checks of creator reconciliation."""
import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import requests

spec=importlib.util.spec_from_file_location('reconcile',Path(__file__).with_name('reconcile-creators-followup.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def verify(target):
    manifest,entries=m.load_plan()
    snapshot=json.loads((m.BACKUPS/(target+'-preimages.json')).read_text())
    checked=[];images_changed=[]
    with m.r.base.connect(target=='production') as db,db.transaction():
        db.execute('SET TRANSACTION READ ONLY');db.execute("SET LOCAL statement_timeout='120s'")
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];works=m.selected_rows(db,batch);artists=m.artist_rows(db,batch)
            relations=db.execute('''SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,
              c.evidence_note,c.source_url,c.field_name FROM artwork_artists aa
              LEFT JOIN citations c ON c.entity_type='artwork' AND c.entity_id=aa.artwork_id AND c.field_name=%s
              WHERE aa.artwork_id=ANY(%s::uuid[])''',(m.FIELD,[w['id'] for w in works.values()])).fetchall()
            assert len(relations)==len(batch),'Missing or duplicate links/citations'
            links={row['artwork_id']:row for row in relations};assert len(links)==len(batch)
            for entry in batch:
                work=works[entry['before']['slug']];old=snapshot['works'][work['slug']];artist=artists[entry['artist']['slug']]
                assert work['unlinked_creator_label'] is None and work['status']=='review' and work['published_at'] is None
                ignored={'unlinked_creator_label','revision','updated_at','updated_by','primary_media_id'}
                assert {k:v for k,v in work.items() if k not in ignored}=={k:v for k,v in old.items() if k not in ignored},('Artwork metadata changed',work['slug'])
                assert work['revision']>=old['revision']+1
                if work['primary_media_id']!=old['primary_media_id']:images_changed.append(work['slug'])
                assert artist==snapshot['artists'][artist['row']['slug']],('Painter metadata changed',artist['row']['slug'])
                link=links[work['id']];assert link['artist_id']==artist['row']['id'] and link['attribution_role']=='primary'
                evidence=json.loads(link['evidence_note']);assert evidence['plan_sha256']==manifest['sha256'] and evidence['original_creator_label']==entry['before']['unlinked_creator_label'] and evidence['source_painter']==entry['painter']
                assert link['source_url']==entry['evidence']['object_url']
                checked.append({'artwork_id':work['id'],'slug':work['slug'],'title':work['title'],'artist_id':artist['row']['id'],'artist_slug':artist['row']['slug'],'source':entry['source'],'date_precision':work['date_precision'],'work_type':work['work_type'],'status':work['status'],'research_candidate':work['research_candidate'],'media_id':work['primary_media_id']})
            # Re-check immutable museum facts and supplied CSV identities without
            # expecting the intentionally cleared creator labels to be present.
            originals={e['before']['slug']:e['before']['unlinked_creator_label'] for e in batch}
            restored={slug:{**row,'unlinked_creator_label':originals[slug]} for slug,row in works.items()}
            m.guards(db,batch,restored,artists,check_links=False)
        totals=db.execute("SELECT (SELECT count(*) FROM artworks) artworks,(SELECT count(*) FROM artists) artists,(SELECT count(*) FROM artworks w WHERE w.unlinked_creator_label IS NOT NULL AND w.status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id)) unlinked").fetchone()
    assert totals['artworks']==snapshot['counts']['artworks'] and totals['artists']==snapshot['counts']['artists'],'Concurrent catalogue row-count change requires review'
    assert totals['unlinked']==snapshot['counts']['unlinked']-len(entries),'Unexpected unresolved-count change'
    result={'at':m.r.core.now(),'plan_sha256':manifest['sha256'],'links_verified':len(checked),'painters_verified':manifest['existing_painters'],'counts':totals,'unknown_dates_preserved':sum(x['date_precision']=='unknown' for x in checked),'unknown_types_preserved':sum(x['work_type']=='unknown' for x in checked),'independent_media_pointer_changes':images_changed,'rows':checked,'existing_painter_metadata_unchanged':True,'original_csv_and_museum_evidence_unchanged':True}
    m.save(target+'-verification.json',result)
    print(target,'verified',len(checked),'links;',totals['unlinked'],'unresolved remain; metadata preserved',flush=True)


def live():
    local=m.read('local-verification.json');prod=m.read('production-verification.json')
    key=lambda row:{k:v for k,v in row.items() if k not in ('artwork_id','artist_id','media_id')}
    assert [key(x) for x in local['rows']]==[key(x) for x in prod['rows']]
    groups={}
    for row in prod['rows']:groups.setdefault(row['source'],row)
    wiki=[x for x in prod['rows'] if x['source']=='wikidata']
    legacy={row['artist_slug']:row for row in prod['rows'] if '_' in row['artist_slug']}
    spread=prod['rows'][::max(1,len(prod['rows'])//25)][:25]
    samples=list({row['artwork_id']:row for row in [*groups.values(),*wiki[:3],*legacy.values(),*spread]}.values())
    site='https://artline-web-lpuqqlugnq-ew.a.run.app'
    def check(row):
        url=site+'/api/backend/v1/artists/'+row['artist_slug']+'/works/'+row['artwork_id']
        response=requests.get(url,timeout=90);response.raise_for_status();data=response.json()
        assert data['id']==row['artwork_id'] and data['title']==row['title'] and data['status']=='review'
        assert data['unlinked_creator_label'] is None
        return {'url':url,'status':response.status_code,'title':data['title'],'artist_slug':row['artist_slug'],'source':row['source']}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,samples))
    slug=next(iter(legacy),prod['rows'][0]['artist_slug'])
    filters=[]
    for path in ['/api/backend/v1/painters/options?selected='+slug+'&popular=false', '/api/backend/v1/timeline?start=1100&end=2000&popular=false&painter='+slug]:
        response=requests.get(site+path,timeout=60);response.raise_for_status()
        assert slug in response.text
        filters.append({'url':site+path,'status':response.status_code})
    response=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/coverage/summary',timeout=60);assert response.status_code==401
    m.save('live-verification.json',{'at':m.r.core.now(),'checks':results,'filter_checks':filters,'legacy_painters_verified':len(legacy),'protected_editor_status':response.status_code,'local_production_mapping_equal':True})
    print('All public creator/work details passed; local and production mappings match',len(results),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('target',choices=['local','production','live']);args=parser.parse_args()
    live() if args.target=='live' else verify(args.target)
