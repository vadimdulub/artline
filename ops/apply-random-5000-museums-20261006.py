#!/usr/bin/env python3
"""Production-only delivery of reviewed museum evidence for the frozen sample."""
import argparse,collections,gzip,importlib.util,json,re,uuid
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('task',ROOT/'ops/random-5000-museum-research-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);d=m.d;r=m.r;RUN=m.RUN
r.RUN=RUN;r.BACKUP=m.BACKUP;r.PORT=55482;d.ACTOR='random-5000-museums-20261006'
original_connect=r.connect
def production_connect(target='production',readonly=True):
    assert target=='production','This task never writes to or samples the local catalogue'
    return original_connect('production',readonly=readonly)
r.connect=production_connect
PROVIDERS=['wikiart-reviewed','indexed-primary-reviewed','primary-reconciled','joconde-final','lombardia','fng','manual-primary']

def indexed_receipt(c):
    path=ROOT/c['evidence_path'];assert r.sha(path.read_bytes())==c['evidence_sha256']
    return {'url':c['source_url'],'body_path':c['evidence_path'],'sha256':c['evidence_sha256'],'retrieved_at':c['captured_at'],'transport':'web_search_index_of_primary_object_page','http_status_not_observed':True}

def verified_receipt(c):
    rc=dict(c['source_receipt']);capture=c.get('object_evidence',{}).get('page',{}).get('capture',{})
    if not rc.get('body_path'):
        assert capture.get('body_path')and capture.get('sha256')==rc.get('sha256'),'Legacy receipt needs its exact preserved capture mapping'
        rc['body_path']=capture['body_path'];rc['legacy_receipt_path']=capture.get('receipt_path')
    rc.setdefault('retrieved_at',capture.get('retrieved_at')or c['checked_at'])
    if 'status'not in rc and 'status_code'not in rc:rc['http_status_not_observed']=True
    raw=(ROOT/rc['body_path']).read_bytes();raw=gzip.decompress(raw)if rc['body_path'].endswith('.gz')else raw
    assert r.sha(raw)==rc['sha256'],('Source evidence hash mismatch',c['artwork_id'])
    assert rc['url'].startswith('https://')and rc['retrieved_at']
    return rc

def repair_receipts():
    names=r.load(RUN/'final-providers.json');new=[];total=0;legacy=0
    for name in names:
        data=r.load(RUN/'primary-plans'/(name+'.json.gz'))
        for c in data['claims']:
            legacy+=not bool(c['source_receipt'].get('body_path'));c['source_receipt']=verified_receipt(c);total+=1
        new.append(name+'-evidence-verified');data['evidence_verified_at']=r.now();r.save_gz(RUN/'primary-plans'/(new[-1]+'.json.gz'),data)
    r.save(RUN/'validated-providers.json',new);r.save(RUN/'evidence-file-verification.json',{'at':r.now(),'claims_checked':total,'legacy_capture_path_mappings':legacy,'all_source_body_hashes_verified':True,'observed_http_statuses_preserved_without_invention':True})
    print('Verified evidence bodies',total,'legacy path mappings',legacy,flush=True)

def prepare():
    sample=r.load(RUN/'sample.json');baseline=r.load(RUN/'baseline.json.gz');assert len(baseline)==5000 and r.sha((RUN/'baseline.json.gz').read_bytes())==sample['baseline_sha256']
    r.save_gz(RUN/'missing-locations.json.gz',r.load(RUN/'primary-input-rows.json.gz'))
    wiki=r.load(RUN/'wikiart-holding-plan-v5.json.gz')
    for c in wiki['claims']:
        c['identity_basis']='Exact existing WikiArt native ID, canonical object URL and title; reviewed named-creator variant or preserved anonymous tradition label; explicit museum Location reconciled to institution authority.'
        c['object_evidence']['creator_check_scope']='Named creator variants reconciled; Fayum portrait and Orthodox Icons are source tradition categories, not invented named creators. Existing unknown creator labels are unchanged.'
    r.save_gz(RUN/'primary-plans/wikiart-reviewed.json.gz',{'at':r.now(),'claims':wiki['claims'],'holds':[o for o in wiki['outcomes']if o['outcome']!='supported_wikiart_museum_holding'],'source_plan':'wikiart-holding-plan-v5.json.gz'})
    pin=r.load(RUN/'latest-web-review.json');web=r.load(RUN/pin['path']);validation=r.load(RUN/'primary-page-validation.json.gz');direct={v['url']:v for v in validation['results']}
    excluded={'cd28d96a-35fc-4bde-a551-061f8877829c':'Official acquisition credit identifies the Gere private collection on long-term loan; not assigned as a museum collection holding.','4f620afe-6ac5-4041-85f3-0189c3b1deb2':'Composite altarpiece group with missing original elements; individual surviving panels need separate version reconciliation.'}
    claims=[];holds=[]
    for aid,group in web['supported_candidates'].items():
        if aid in excluded:holds.append({'artwork_id':aid,'reason':excluded[aid],'source_urls':[c['source_url']for c in group]});continue
        if len(group)!=1:holds.append({'artwork_id':aid,'reason':'multiple_source_objects_need_individual_review'});continue
        c=group[0];assert c['outcome']=='supported'and c['institution']and not c['qualified_holding_text']and not c['print_impression_unresolved']
        evidence={'reviewed_indexed_object':c,'primary_page_validation':direct.get(c['source_url']),'review_scope':'Exact native URL/inventory, or matching supplied museum plus distinctive title, creator and date; full indexed record and acquisition fields reviewed. Related-work links, exhibition histories, loans and generic-title collisions excluded.'}
        # Retain the actual successful response where available, while keeping
        # the source-index proof used for identity matching in the pinned plan.
        rc=indexed_receipt(c);v=direct.get(c['source_url'],{});http=v.get('receipt',{})
        if http.get('status')==200:
            raw=gzip.decompress((ROOT/http['body_path']).read_bytes());assert r.sha(raw)==http['sha256'];rc=http
        claims.append({'artwork_id':aid,'title':c['title'],'scheme':'museum-catalogue-url','external_id':c['source_url'],'institution':c['institution'],'source_url':c['source_url'],'checked_at':rc['retrieved_at'],'location_text':c['institution']['name'],'identity_basis':'Reviewed primary object record: '+('existing exact source URL'if c['exact_source_url']else 'matching accession/inventory'if c['inventory_correspondence']else 'distinctive title, named creator, supplied museum and creation-date correspondence')+'; explicit collection/acquisition evidence retained.','source_class':'museum_contributed_artuk_catalogue_indexed'if urlsplit(c['source_url']).hostname=='artuk.org'else 'primary_museum_catalogue'if http.get('status')==200 else 'indexed_primary_museum_catalogue','source_receipt':rc,'object_evidence':evidence,'claim_type':'holding','review_state':'accepted','limitation':'Museum collection connection only. Source creator qualifications, original dates and review status are preserved. No current-display, legal-ownership or physical-whereabouts claim. Index transport and any direct-access failure are recorded honestly.'})
    r.save_gz(RUN/'primary-plans/indexed-primary-reviewed.json.gz',{'at':r.now(),'claims':claims,'holds':holds,'review_pin':pin,'validation_path':'primary-page-validation.json.gz'})
    aid='018ac858-7686-44f4-b625-4d72e03a5d8b';a=baseline[aid]['artwork'];assert a['title']=='Paesaggio rurale, La strada'and a['unlinked_creator_label']=='Lanaro Dino'and a['creation_year_start']==a['creation_year_end']==1950
    path=RUN/'lanaro-official-object-review.json';proof=r.load(path);assert all(t in proof['result']for t in ['0300668802','Museo MAGA','Lanaro, Dino','1950 - 1950','Gallarate','006'])
    inst={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/random-5000-museums-20261006/institution/museo-maga-gallarate')),'slug':'museum-research-maga-gallarate','name':'Museo MAGA — Gallarate','normalized_name':'museo maga gallarate','website_url':None,'wikidata_id':None,'kind':'museum','status':'review','description':'Museum and Gallarate location explicitly identified by the Italian national catalogue object record 0300668802; authority remains in review.'}
    url='https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0300668802';rc={'url':url,'body_path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes()),'retrieved_at':proof['at'],'transport':'web_tool_primary_page_view','http_status_not_observed':True}
    c={'artwork_id':aid,'title':a['title'],'scheme':'arco-object','external_id':'0300668802','institution':inst,'source_url':url,'checked_at':proof['at'],'location_text':inst['name'],'identity_basis':'Exact supplied distinctive title components, named creator, 1950 creation date and Museo MAGA; official Italian catalogue national ID 0300668802, inventory 006, signed D. Lanaro 50.','source_class':'primary_national_collection_catalogue','source_receipt':rc,'object_evidence':{'national_id':'0300668802','inventory':'006','title':'La strada. Paesaggio rurale','creator':'Lanaro, Dino','creation_date':'1950 - 1950','museum':'Museo MAGA','city':'Gallarate','source_capture':str(path.relative_to(ROOT))},'claim_type':'holding','review_state':'accepted','limitation':'Museum collection connection only; original unverified date text, unknown artwork type and unlinked creator label preserved; no current-display or ownership claim.'}
    r.save_gz(RUN/'primary-plans/manual-primary.json.gz',{'at':r.now(),'claims':[c],'holds':[]})
    allclaims=[c for name in PROVIDERS for c in r.load(RUN/'primary-plans'/(name+'.json.gz'))['claims']]
    assert {c['artwork_id']for c in allclaims}<=set(sample['artwork_ids'])
    print('Reviewed source claims',len(allclaims),'distinct artworks',len({c['artwork_id']for c in allclaims}),'by provider',dict(collections.Counter(name for name in PROVIDERS for c in r.load(RUN/'primary-plans'/(name+'.json.gz'))['claims'])),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['prepare','repair-receipts','plan','apply','verify']);ap.add_argument('--wave',default='museum-holdings-01');args=ap.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='repair-receipts':repair_receipts()
    elif args.command=='plan':d.plan(args.wave,r.load(RUN/'validated-providers.json')if(RUN/'validated-providers.json').exists()else r.load(RUN/'final-providers.json')if(RUN/'final-providers.json').exists()else PROVIDERS,targets=['production'])
    elif args.command=='apply':d.apply(args.wave,'production')
    else:d.verify(args.wave,targets=['production'])
