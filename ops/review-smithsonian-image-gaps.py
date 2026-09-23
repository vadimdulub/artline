#!/usr/bin/env python3
"""Refresh only Smithsonian metadata shards containing existing eligible gaps."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('saam', ROOT/'ops/overnight-saam-images.py')
saam = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saam)
core = saam.core
HOST = 'smithsonian-open-access.s3-us-west-2.amazonaws.com'
core.HOSTS.add(HOST)


def oid(record):
    url=record.get('content',{}).get('descriptiveNonRepeating',{}).get('record_link','')
    return parse_qs(urlparse(url).query).get('id',[None])[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    a=p.parse_args()
    a.run.mkdir(parents=True,exist_ok=True)
    with saam.ro('postgres://localhost/artline') as db:
        rows=db.execute(saam.QUERY+' AND a.primary_media_id IS NULL ORDER BY a.id').fetchall()
        artists=db.execute('''SELECT p.slug,to_jsonb(p) record FROM artists p
            WHERE p.slug=ANY(%s)''',([s for r in rows for s in r['artist_slugs']],)).fetchall()
    core.save_new(a.run/'catalogue-gaps.json',{'at':core.now(),'records':rows,'artists':artists})
    wanted={r['external_id']:r for r in rows}
    cached=ROOT/'docs/research/overnight-images-20260915/saam/metadata'
    shard_names=set()
    for path in cached.glob('*.txt'):
        for line in path.read_text().splitlines():
            if oid(json.loads(line)) in wanted:
                shard_names.add(path.name)
    fetch=core.Fetcher(a.run/'metadata')
    objects={}
    for name in sorted(shard_names):
        url='https://'+HOST+'/metadata/edan/saam/'+name
        path=a.run/'metadata'/name
        receipt_path=path.with_suffix('.receipt.json')
        if path.exists():
            raw=path.read_bytes()
            receipt=json.loads(receipt_path.read_text())
            if core.sha(raw)!=receipt['sha256'] or receipt['url']!=url:
                raise ValueError('Metadata capture checksum differs')
        else:
            raw,headers=fetch.get(url,20_000_000)
            receipt={'url':url,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'headers':headers}
            core.save_new(path,raw)
            core.save_new(receipt_path,receipt)
        for line in raw.splitlines():
            record=json.loads(line)
            key=oid(record)
            if key in wanted:
                objects[key]={'object':record,'metadata_capture':receipt}
    outcomes=[]
    for c in rows:
        record=objects.get(c['external_id'])
        if not record:
            outcomes.append({'artwork_id':c['artwork_id'],'reason':'Object not found in refreshed shards; broader source lookup required'})
            continue
        o=record['object']
        dn=o['content']['descriptiveNonRepeating']
        ft=o['content']['freetext']
        try:
            saam.source_match(c,o)
            reason='eligible'
        except ValueError as error:
            reason=str(error)
        result={'artwork_id':c['artwork_id'],'external_id':c['external_id'],
                'title':c['title'],'artist':c['artist'],'aliases':c['aliases'],
                'source_artist':saam.fields(ft,'name','Artist'),
                'source_rights':saam.fields(ft,'objectRights','Restrictions & Rights'),
                'media':[{'id':v.get('idsId'),'rights':v.get('usage'),'content':v.get('content')}
                         for v in dn.get('online_media',{}).get('media',[])], 'reason':reason}
        core.save_new(a.run/'objects'/(c['external_id']+'.json'),record)
        outcomes.append(result)
    summary={'checked_at':core.now(),'gaps':len(rows),'refreshed_shards':len(shard_names),
             'outcomes':dict(collections.Counter(r['reason'] for r in outcomes)), 'records':outcomes}
    core.save_new(a.run/'review.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
