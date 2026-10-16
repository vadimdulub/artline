#!/usr/bin/env python3
"""500 existing Artline painters: scoped production research and evidence reuse."""
import collections
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('selection',ROOT/'ops/select-wikiart-500-painters-20261011.py')
s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
m=s.m;r=m.r;q=m.q
OP='wikiart-500-painters-20261011'
RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
m.OP=OP;m.RUN=s.RUN=r.RUN=q.RUN=RUN;m.BACKUP=s.BACKUP=BACKUP;m.ORIGINALS=ORIGINALS
r.PORT=55448

def production_only(target='production',readonly=True):
    assert target=='production','The real local catalogue must remain untouched'
    return m.cached_connection(target,readonly=readonly)
r.connect=production_only

def cohort():
    pairs=r.load(RUN/'cohort.json')['painters']
    assert len(pairs)==500 and len({x['artist']['id']for x in pairs})==500
    return pairs
m.cohort=cohort

def bootstrap():
    if (RUN/'cohort.json').exists():return
    origin=ROOT/'docs/research/random-ten-twenty-batches-round2-20261011/sampling-frame.json.gz'
    prior_paths=sorted(p for p in (ROOT/'docs/research').glob('*/cohort.json')if p.parent!=RUN and any(v in p.parent.name for v in ['random-200-painters','random-ten-twenty-batches','vyzantios-random-ten','low-count-200-painters']))
    previous=[pair for p in prior_paths for pair in r.load(p).get('painters',r.load(p).get('artists',[]))]
    excluded_ids={x['artist']['id']for x in previous};excluded_urls={x['source']['url']for x in previous}
    excluded_urls.update(r.load(ROOT/'docs/research/random-200-painters-round6-20261007/sampling-nonperson-review.json')['excluded_source_urls'])
    excluded_urls.add('https://www.wikiart.org/en/otto-dix')
    available=[x for x in r.load(origin)['frame']if x['artist']['id']not in excluded_ids and x['source']['url']not in excluded_urls]
    ids=[x['artist']['id']for x in available]
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists={x['a']['id']:x['a']for x in db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))}
        aliases=collections.defaultdict(list)
        for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])',(ids,)):aliases[x['artist_id']].append(x['alias'])
        query='''SELECT aa.artist_id::text,count(*) works,count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) images
          FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
          WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY aa.artist_id'''
        r.save(RUN/'selection-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) '+query,(ids,)).fetchone())
        counts={x['artist_id']:x for x in db.execute(query,(ids,))}
    frame=[];held=[]
    for old in available:
        a=artists.get(old['artist']['id']);src=old['source']
        if not a or a['status']=='archived' or a['entity_type']!='person':held.append(dict(artist=old['artist'],reason='Inactive or non-person catalogue identity'));continue
        if any(a.get(k)is not None and src.get(k)is not None and a[k]!=src[k]for k in ['birth_year','death_year']):held.append(dict(artist=a,reason='Source lifespan conflict'));continue
        if q.norm(src['name'])not in {q.norm(n)for n in [a['display_name']]+aliases[a['id']]}:
            assert any((e.get('canonical_url')or'').rstrip('/')==src['url']for e in old['identifiers']),'Unresolved artist identity'
        if a.get('birth_year')and a['birth_year']>1955:held.append(dict(artist=a,reason='Prioritize creators with potential works in the existing image date scope'));continue
        c=counts.get(a['id'],dict(works=0,images=0));pair=dict(old,artist=a,aliases=aliases[a['id']],baseline_counts=c)
        pair['estimated_addition_gap']=max(0,src['count']-c['works']);pair['missing_catalogue_images']=c['works']-c['images'];frame.append(pair)
    assert len(frame)>=500
    ordered=sorted(frame,key=lambda x:(-x['estimated_addition_gap'],-x['missing_catalogue_images'],-x['source']['count'],x['artist']['id']))
    chosen=ordered[:500];assert len({x['source']['url']for x in chosen})==500
    for i,pair in enumerate(chosen):pair.update(batch=i//10+1,batch_rank=i%10+1)
    r.save_gz(RUN/'sampling-frame.json.gz',dict(frame=frame,origin=str(origin.relative_to(ROOT)),origin_sha256=r.sha(origin.read_bytes()),excluded_artist_ids=sorted(excluded_ids),excluded_source_urls=sorted(excluded_urls),prior_cohorts=[dict(path=str(p.relative_to(ROOT)),sha256=r.sha(p.read_bytes()))for p in prior_paths],identity_or_scope_holds=held))
    r.save(RUN/'cohort.json',dict(at=r.now(),method='500 distinct active production creators uniquely matched to WikiArt, excluding recorded previous painter cohorts and prioritizing estimated source artwork gaps, then missing catalogue images. Counts are selection estimates, not claims of new or unique objects. Deterministic artist-ID tie break.',painters=chosen))
    r.save(RUN/'authorization.json',dict(at=r.now(),user_instruction="ok, we have wikiart let's review 500 painters in artlie and add additional materials for them, pictures and more artworks! go ahead",target='production',painters=500,local_database_read_only=True,cohort_sha256=r.sha((RUN/'cohort.json').read_bytes()),rules=['Fresh source-index audit for every selected painter','Exact creator and artwork/version checks; no duplicate objects','New supported personal-selection records remain review; known post-1970 creation excluded','Selected images require explicit creation bound by 1955; unknown dates retained without invented eligibility','WikiArt approved; actual rights labels and credits distinct from user approval','Existing images, metadata, creator links, holdings and publication states preserved','No local database connection or writes; no commit or application deployment']))
    r.save(RUN/'fresh-production-cohort-validation.json',dict(at=r.now(),artists=500,records={x['artist']['id']:x['artist']for x in chosen},errors=[],local_database_connected=False))
    with (RUN/'selected-artists.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=['rank','batch','artist','artist_id','source_url','source_index_estimate','existing_works','existing_images','estimated_addition_gap']);writer.writeheader()
        for i,x in enumerate(chosen,1):writer.writerow(dict(rank=i,batch=x['batch'],artist=x['artist']['display_name'],artist_id=x['artist']['id'],source_url=x['source']['url'],source_index_estimate=x['source']['count'],existing_works=x['baseline_counts']['works'],existing_images=x['baseline_counts']['images'],estimated_addition_gap=x['estimated_addition_gap']))
    print('Frozen 500 painters from',len(frame),'eligible identities; source estimate',sum(x['source']['count']for x in chosen),'existing works',sum(x['baseline_counts']['works']for x in chosen),flush=True)

def leads():
    names=collections.defaultdict(set)
    for pair in cohort():
        for name in [pair['artist']['display_name'],pair['source']['name']]+pair['aliases']:
            key=s.normalized(name);names[key].add(pair['artist']['id']);words=key.split();names[' '.join(words[-1:]+words[:-1])].add(pair['artist']['id'])
    with r.connect('production')as db:
        labels=[x['unlinked_creator_label']for x in db.execute("SELECT DISTINCT unlinked_creator_label FROM artworks WHERE unlinked_creator_label IS NOT NULL AND status<>'archived'")]
        selected={x:names[s.normalized(x)]for x in labels if s.normalized(x)in names}
        rows=db.execute("SELECT to_jsonb(a) artwork FROM artworks a WHERE unlinked_creator_label=ANY(%s) AND status<>'archived'",(list(selected),)).fetchall()if selected else[]
    r.save(RUN/'expanded-creator-leads.json',[dict(artist_id=aid,artwork=x['artwork'])for x in rows for aid in selected[x['artwork']['unlinked_creator_label']]])

def reuse_pages():
    cache=m.cache_catalogue();reused=[]
    for pair in cohort():
        aid=pair['artist']['id'];index=r.load(RUN/'indexes'/(aid+'.json.gz'))
        for item in index['items']:
            if item['date']and item['date']['creation_year_start']>1970:continue
            key=r.sha(item['url'].encode());dest=RUN/'pages'/aid/(key+'.json.gz');old=cache.get(item['url'])
            if dest.exists()or not old:continue
            parent=(ROOT/old['receipt_path']).parent.parent
            for path in [parent/folder/aid/(key+'.json.gz')for folder in ['page-retries','pages']]:
                if not path.exists():continue
                data=r.load(path);page=data.get('page',{})
                if data.get('outcome')!='captured'or page.get('receipt',{}).get('sha256')!=old['sha256']or page.get('url')!=item['url']:continue
                if page['metadata']['artistUrl']!=m.urlsplit(pair['source']['url']).path or not {'title','fields','rights_label','rights_status','image_url'}<=set(page):continue
                body=ROOT/old['body_path'];raw=body.read_bytes();raw=gzip.decompress(raw)if body.suffix=='.gz'else raw;assert r.sha(raw)==old['sha256']
                r.save_gz(dest,dict(artist_id=aid,index=item,outcome='captured',page=page,parsed_evidence_reuse=dict(path=str(path.relative_to(ROOT)),sha256=r.sha(path.read_bytes()),raw_source_sha256=old['sha256'],basis='Checksum-identical parsed evidence; exact source creator and original retrieval time retained.')))
                reused.append(dict(artist_id=aid,url=item['url'],source_file=str(path.relative_to(ROOT)),source_sha256=r.sha(path.read_bytes()),raw_sha256=old['sha256']));break
    r.save_gz(RUN/'parsed-page-reuse.json.gz',dict(at=r.now(),reused=reused));print('Reused',len(reused),'checksum-identical parsed pages',flush=True)

def research():
    bootstrap();m.snapshot()
    if not(RUN/'expanded-creator-leads.json').exists():leads()
    m.indexes();m.translations();reuse_pages();m.pages()

def backup():
    description='Before '+OP;dest=BACKUP/'cloud-backup-request.json'
    if not dest.exists():r.save(dest,json.loads(subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+description,'--async','--format=json'],text=True)))
    entries=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--filter=description="'+description+'"','--limit=5','--format=json'],text=True))
    for item in entries:
        if item['status']=='SUCCESSFUL'and not(BACKUP/'cloud-backup.json').exists():r.save(BACKUP/'cloud-backup.json',item)
    print([(x.get('id'),x.get('status'))for x in entries],flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='select':s.select()
    elif action in ['snapshot','indexes','translations','pages']:getattr(m,action)()
    else:globals()[action]()
