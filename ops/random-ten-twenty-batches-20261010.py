#!/usr/bin/env python3
"""Frozen artist research; production read-only until separate pinned delivery."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('artist_selection', ROOT/'ops/select-random-200-painters-round6-20261007.py')
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
m=s.m; r=m.r; q=m.q
OP='random-ten-twenty-batches-20261010'
RUN=ROOT/'docs/research'/OP
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/OP
m.OP=OP; m.RUN=s.RUN=r.RUN=q.RUN=RUN; m.BACKUP=s.BACKUP=BACKUP; m.ORIGINALS=ORIGINALS
r.PORT=55519

def cohort():
    pairs=r.load(RUN/'cohort.json')['painters']
    assert len(pairs)==200 and len({p['artist']['id'] for p in pairs})==200
    return pairs
m.cohort=cohort

def bootstrap():
    if (RUN/'cohort.json').exists():
        print([(x['artist']['display_name'],x['source']['count']) for x in cohort()]); return
    directory_path=ROOT/'docs/research/production-wikiart-images-20261006/wikiart-directory.json.gz'
    directory=r.load(directory_path); byname=collections.defaultdict(dict); byurl={x['url']:x for x in directory}
    for x in directory: byname[q.norm(x['name'])][x['url']]=x
    with r.connect('production') as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists=[x['a'] for x in db.execute("SELECT to_jsonb(a) a FROM artists a WHERE entity_type='person' AND status<>'archived' ORDER BY id")]
        aliases=collections.defaultdict(list); identifiers=collections.defaultdict(list)
        for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases'): aliases[x['artist_id']].append(x['alias'])
        for x in db.execute("SELECT to_jsonb(e) e FROM external_identifiers e WHERE entity_type='artist'"):
            identifiers[x['e']['entity_id']].append(x['e'])
    frame=[]
    for a in artists:
        sources={}; aid=a['id']
        for name in [a['display_name']]+aliases[aid]: sources.update(byname[q.norm(name)])
        for e in identifiers[aid]:
            u=(e.get('canonical_url') or '').rstrip('/')
            if u in byurl: sources[u]=byurl[u]
        sources={u:x for u,x in sources.items() if all(a.get(k) is None or x.get(k) is None or a[k]==x[k] for k in ['birth_year','death_year'])}
        if len(sources)==1:
            frame.append(dict(artist=a, aliases=aliases[aid], identifiers=identifiers[aid], source=next(iter(sources.values()))))
    counts=collections.Counter(x['source']['url'] for x in frame)
    ambiguous=[x for x in frame if counts[x['source']['url']]>1]
    frame=[x for x in frame if counts[x['source']['url']]==1]
    prior=r.load(ROOT/'docs/research/vyzantios-random-ten-20261010/cohort.json')['painters']
    excluded_ids={x['artist']['id'] for x in prior};excluded_urls={x['source']['url'] for x in prior}
    nonpersons=r.load(ROOT/'docs/research/random-200-painters-round6-20261007/sampling-nonperson-review.json')['excluded_source_urls']
    excluded_urls.update(nonpersons)
    frame=[x for x in frame if x['artist']['id'] not in excluded_ids and x['source']['url'] not in excluded_urls]
    assert len(frame)>=200
    seed=secrets.token_hex(16)
    chosen=sorted(frame,key=lambda x:hashlib.sha256((seed+'/'+x['artist']['id']).encode()).digest())[:200]
    for i,pair in enumerate(chosen):pair['batch']=i//10+1;pair['batch_rank']=i%10+1
    r.save_gz(RUN/'sampling-frame.json.gz',dict(frame=frame, ambiguous=ambiguous, excluded_artist_ids=sorted(excluded_ids), excluded_source_urls=sorted(excluded_urls), directory_sha256=r.sha(directory_path.read_bytes())))
    r.save(RUN/'cohort.json',dict(at=r.now(),seed=seed,method='Uniform SHA256 random ordering without replacement, 200 active production person identities uniquely matched to WikiArt, partitioned into 20 ordered batches of 10. Previous Vyzantios cohort and reviewed nonindividual categories excluded. No country, popularity or artwork-count weighting.',painters=chosen))
    r.save(RUN/'authorization.json',dict(at=r.now(),user_instruction='pick 10 random artist and do the sames, repeat 20 times',target='production',local_database_read_only=True,cohort_sha256=r.sha((RUN/'cohort.json').read_bytes()),interpretation='Audit complete accessible artist indexes and existing catalogue records; source-backed pre-1971 additions and missing pictures under the established artist workflow. Preserve uncertain dates in review; source image URLs retained for date holds. No claim of complete lifetime oeuvre.',rules=['Exact creator and object/version checks','Actual source rights separate from user approval','No existing metadata or primary image replacement','New works remain review personal selections','No local database writes']))
    with (RUN/'selected-artists.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['rank','artist','artist_id','source_url','index_estimate']); w.writeheader()
        for i,x in enumerate(chosen,1): w.writerow(dict(rank=i,artist=x['artist']['display_name'],artist_id=x['artist']['id'],source_url=x['source']['url'],index_estimate=x['source']['count']))
    for batch in range(1,21):
        values=[x for x in chosen if x['batch']==batch];assert len(values)==10
        r.save(RUN/'batches'/f'{batch:02d}'/'cohort.json',dict(batch=batch,painters=values))
        print('Batch',batch,':',', '.join(x['artist']['display_name'] for x in values),flush=True)
    print('Frozen 200 distinct artists; source index estimate',sum(x['source']['count'] for x in chosen),flush=True)

def leads():
    names=collections.defaultdict(set)
    for pair in cohort():
        for name in [pair['artist']['display_name'],pair['source']['name']]+pair['aliases']:
            k=s.normalized(name); names[k].add(pair['artist']['id']); words=k.split(); names[' '.join(words[-1:]+words[:-1])].add(pair['artist']['id'])
    with r.connect('production') as db:
        labels=[x['unlinked_creator_label'] for x in db.execute("SELECT DISTINCT unlinked_creator_label FROM artworks WHERE unlinked_creator_label IS NOT NULL AND status<>'archived'")]
        selected={x:names[s.normalized(x)] for x in labels if s.normalized(x) in names}
        rows=db.execute("SELECT to_jsonb(a) artwork FROM artworks a WHERE unlinked_creator_label=ANY(%s) AND status<>'archived'",(list(selected),)).fetchall() if selected else []
    r.save(RUN/'expanded-creator-leads.json',[dict(artist_id=aid,artwork=x['artwork']) for x in rows for aid in selected[x['artwork']['unlinked_creator_label']]])

def research():
    bootstrap(); m.snapshot();
    if not (RUN/'expanded-creator-leads.json').exists():leads()
    m.indexes(); m.translations(); m.pages()

def backup():
    desc='Before twenty batches of ten random artists '+OP
    dest=BACKUP/'cloud-backup-request.json'
    if not dest.exists():
        r.save(dest,json.loads(subprocess.check_output(['gcloud','sql','backups','create','--instance=artline-postgres','--project=artline-508319','--description='+desc,'--async','--format=json'],text=True)))
    entries=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--limit=30','--format=json'],text=True))
    matches=[x for x in entries if x.get('description')==desc]
    for x in matches:
        if x['status']=='SUCCESSFUL' and not (BACKUP/'cloud-backup.json').exists():r.save(BACKUP/'cloud-backup.json',x)
    print([(x.get('id'),x.get('status')) for x in matches])

if __name__=='__main__':
    phase=sys.argv[1]
    if phase=='select':s.select()
    elif phase=='pages':m.pages()
    else:globals()[phase]()
