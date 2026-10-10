#!/usr/bin/env python3
"""Validate guide membership, local links, preserved evidence, and sample HTTP headers."""
import ast
import collections
import concurrent.futures
import gzip
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote,urlsplit
import requests

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);ROOT=r.ROOT/'docs/research/museum-guides-20261005'


def main():
    guide=r.load(ROOT/'guide-manifest.json');expected={};media={};sample_by_museum={};files_checked=0;local_links=0
    for entry in r.load(ROOT/'snapshots/final/manifest.json')['museums']:
        path=ROOT/entry['path'];assert r.sha(path.read_bytes())==entry['sha256']
        data=r.load(path)
        for w in data['artworks']:
            assert w['id']not in expected;expected[w['id']]=data['institution']['slug']
            if w.get('media'):
                m=w['media'];media[m['id']]=m
                if m.get('storage_kind')=='local'and(m.get('storage_path')or'').startswith('/assets/'):
                    sample_by_museum.setdefault(data['institution']['slug'],{'museum':data['institution']['name'],'media_id':m['id'],'url':'https://artlines.org'+m['storage_path'],'expected_mime':m.get('mime_type'),'expected_bytes':m.get('byte_size')})
    observed={};table_rows=0
    unavailable_urls={'https://artlines.org'+v['path']for v in r.load(ROOT/'missing-local-assets-live-check.json')['assets']if v.get('status')==404}
    for entry in guide['markdown_files']:
        path=ROOT/entry['path'];raw=path.read_bytes();assert r.sha(raw)==entry['sha256'];assert len(raw)==entry['bytes']
        text=raw.decode();ids=re.findall(r'<a id="artwork-([a-f0-9-]{36})"></a>',text)
        assert len(ids)<=500,(path,len(ids))
        for aid in ids:
            assert aid not in observed,(aid,path);assert aid in expected,aid
            assert path.relative_to(ROOT).parts[1]in [expected[aid],expected[aid]+'.md'],(aid,path)
            observed[aid]=entry['path']
        for line in text.splitlines():
            if '<a id="artwork-'in line:
                assert len(re.findall(r'(?<!\\)\|',line))==7,(path,line[:160]);table_rows+=1
        for target in re.findall(r'\]\(([^)\n]+)\)',text):
            if target.startswith(('https://','http://')):
                assert urlsplit(target).hostname,target
                assert unquote(target)not in unavailable_urls,('Known broken image still linked',path,target)
            else:
                target=unquote(target.split('#',1)[0]);assert (path.parent/target).resolve().exists(),(str(path),target);local_links+=1
        files_checked+=1
    assert set(observed)==set(expected)and table_rows==guide['artworks']
    missing_assets=[];size_mismatches=[];local_assets=0
    for m in media.values():
        if m.get('storage_kind')!='local':continue
        path=r.ROOT/'apps/web/public'/m['storage_path'].lstrip('/')
        if not path.is_file():missing_assets.append({'media_id':m['id'],'path':m['storage_path']});continue
        local_assets+=1
        if m.get('byte_size')is not None and path.stat().st_size!=m['byte_size']:size_mismatches.append({'media_id':m['id'],'path':m['storage_path'],'actual':path.stat().st_size,'recorded':m['byte_size']})
    associations=r.load(ROOT/'artwork-image-source-associations.json.gz')['associations'];receipts={}
    for association in associations:
        assert association['artwork_id']in expected
        image=association['image_evidence'];rc=image['source_receipt'];key=(rc['body_path'],rc['sha256']);receipts[key]=rc
        if image.get('wikidata_receipt'):
            rc=image['wikidata_receipt'];receipts[(rc['body_path'],rc['sha256'])]=rc
    source_bytes=0
    for rc in receipts.values():
        path=r.ROOT/rc['body_path'];raw=path.read_bytes()
        if path.suffix=='.gz':raw=gzip.decompress(raw)
        assert r.sha(raw)==rc['sha256'],str(path);source_bytes+=len(raw)
    wanted=['musee-du-louvre','museo-del-prado','tate','rijksmuseum','the-met','national-gallery-of-art','state-russian-museum']
    samples=[sample_by_museum[x]for x in wanted if x in sample_by_museum]
    # HEAD inspects existing asset headers only; no image bodies are downloaded.
    def probe(item):
        try:
            response=requests.head(item['url'],allow_redirects=True,timeout=(10,20))
            return {**item,'status':response.status_code,'final_url':response.url,'content_type':response.headers.get('content-type'),'content_length':response.headers.get('content-length')}
        except Exception as exc:return {**item,'error':type(exc).__name__+': '+str(exc)[:160]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:probes=list(pool.map(probe,samples))
    scripts=sorted({*r.ROOT.joinpath('ops').glob('*museum*20261005e.py'),*r.ROOT.joinpath('ops').glob('*museum*20261006.py'),
        r.ROOT/'ops/export-museum-guides-20261005.py',r.ROOT/'ops/write-museum-guides-20261005.py',
        r.ROOT/'ops/research-artwork-location-tate-current-20261005e.py',r.ROOT/'ops/refine-artwork-location-deposit-recipients-20261005e.py',
        r.ROOT/'ops/refine-artwork-location-colombia-review-20261005e.py'})
    script_manifest=[]
    for path in scripts:
        ast.parse(path.read_text());script_manifest.append({'path':str(path.relative_to(r.ROOT)),'sha256':r.sha(path.read_bytes())})
    result={'at':r.now(),'markdown_files_verified':files_checked,'artwork_rows_verified':table_rows,'local_document_links_verified':local_links,
        'unique_existing_media':len(media),'local_asset_files_present':local_assets,'missing_local_assets':missing_assets,'local_asset_size_mismatches':size_mismatches,
        'image_source_associations':len(associations),'source_response_hashes_verified':len(receipts),'source_bytes_verified':source_bytes,
        'sample_existing_asset_head_checks':probes,'all_external_urls_live_tested':False,'no_image_bodies_downloaded':True,
        'script_manifest':script_manifest,'database_mutations':'None: this verification is read-only.'}
    r.save(ROOT/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items()if k not in ['script_manifest','missing_local_assets','local_asset_size_mismatches','sample_existing_asset_head_checks']},ensure_ascii=False),flush=True)
    print('Missing local assets',len(missing_assets),'size mismatches',len(size_mismatches),'HEAD',[(v['museum'],v.get('status'),v.get('error'))for v in probes],flush=True)


if __name__=='__main__':main()
