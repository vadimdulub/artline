#!/usr/bin/env python3
"""Second, bounded production WikiArt pass: resolve versions and object identities.

Prior evidence is immutable. Delivery reuses the audited missing-image-only
transaction, with a separate plan, originals, recovery backup and source IDs.
"""
import argparse
import collections
import concurrent.futures
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urljoin, urlsplit

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-production-wikiart-images-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
q=d.q;r=d.r
OLD=q.RUN
RUN=ROOT/'docs/research/production-wikiart-round2-20261006'
q.RUN=r.RUN=d.RUN=RUN
r.PORT=55446
d.OP=RUN.name
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/d.OP


def pointer(folder,name):
    p=r.load(folder/('latest-'+name+'-pass.json'));path=ROOT/p['path']
    assert r.sha(path.read_bytes())==p['sha256']
    return r.load(path)


def pin(name,data):
    path=RUN/(name+'-passes')/(r.now().replace('-','').replace(':','')+'.json.gz')
    r.save_gz(path,data)
    (RUN/('latest-'+name+'-pass.json')).write_text(json.dumps({'path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes())}))


def discover():
    prior=pointer(OLD,'candidate');review=pointer(OLD,'review')
    wanted={x['work']['id'] for x in review['held'] if x['review_outcome']!='rights_restricted_unknown_or_territorial'}
    wanted.update(x['artwork_id'] for x in prior['outcomes'] if not x['has_image'] and x['outcome']=='multiple_source_versions')
    old_visual={x['artwork_id'] for x in r.load(OLD/'visual-review.json')['held']}
    wanted-=old_visual
    works={}
    for part in r.load(OLD/'snapshot.json')['parts']:
        path=ROOT/part['path'];assert r.sha(path.read_bytes())==part['sha256']
        for w in r.load(path):
            if w['id'] in wanted:works[w['id']]=w
    assert len(works)==len(wanted)
    # Scoped fresh read: drop newly illustrated works; preserve the full current
    # object snapshot for later drift checks. No local catalogue connection.
    with r.connect('production') as db:
        current=d.snapshots(db,list(works))
    changed=[]
    for aid,w in list(works.items()):
        x=current.get(aid);a=x['artwork'] if x else {}
        keys=['title','alternate_title','creation_year_start','creation_year_end','date_precision','status','accession_number','unlinked_creator_label','primary_media_id']
        if not x or any(a[k]!=w[k] for k in keys) or a['current_institution_id']!=w['institution_id'] or sorted((c['artist_id'],c['attribution_role']) for c in x['creators'])!=sorted((c['artist_id'],c['role']) for c in w['creators']):
            changed.append(aid);del works[aid]
    r.save_gz(RUN/'fresh-production-scope.json.gz',{'at':r.now(),'read_only':True,'records':current,'changed_since_round1':changed})
    cached=r.load(OLD/'cached-images.json.gz');image_pages={q.image_key(x['image_url']):x for x in cached}
    title_index=collections.defaultdict(dict)
    for x in cached:
        title_index[(x['artist_url'],q.norm(x['title']))][q.image_key(x['image_url'])]={**x,'date':(x['year_start'],x['year_end']) if x.get('year_start') and x.get('year_end') else None}
    english={}
    for path in list((OLD/'artist-indexes').glob('*.json.gz'))+list((OLD/'translated-indexes').glob('*.json.gz')):
        record=r.load(path)
        if record['outcome']!='indexed':continue
        for x in record['items']:
            key=q.image_key(x.get('image'))
            if not key or not q.norm(x.get('title')):continue
            old=image_pages.get(key,{})
            if not record.get('language'):english[(record['source']['url'],x['contentId'])]=x
            original=english.get((record['source']['url'],x['contentId']),{})
            page=old.get('url') or record['source']['url']+'/'+key.rsplit('/',1)[-1].rsplit('.',1)[0]
            c={'title':q.html.unescape(x.get('title') or ''),'artist':x.get('artistName'),'artist_url':record['source']['url'],
               'date':q.parse_date(x.get('yearAsString')),'image_url':x['image'],'url':page,'page_url_verified':bool(old),
               'content_id':x['contentId'],'api_receipt':record['receipt'],'source_id':old.get('source_id'),
               'language':record.get('language','en'),'english_title':q.html.unescape(original.get('title') or x.get('title') or '')}
            title_index[(c['artist_url'],q.norm(c['title']))][key]=c
    sources=r.load(OLD/'artist-sources.json.gz')
    artist_sources={x['artist']['id']:x['source']['url'] for x in sources['matches']}
    label_sources={q.norm(x['unlinked_creator_label']):x['source']['url'] for x in sources['object_labels']}
    out=[];outcomes=[]
    prior_by={x['work']['id']:x for x in prior['candidates']}
    for w in works.values():
        possible={}
        artist_urls={artist_sources[c['artist_id']] for c in w['creators'] if c['artist_id'] in artist_sources}
        if q.norm(w.get('unlinked_creator_label')) in label_sources:artist_urls.add(label_sources[q.norm(w['unlinked_creator_label'])])
        for artist_url in artist_urls:
            for title in q.title_keys(w):possible.update(title_index[(artist_url,title)])
        if w['id'] in prior_by:
            old=prior_by[w['id']];possible[q.image_key(old['candidate']['image_url'])]=old['candidate']
        compatible=[c for c in possible.values() if q.date_compatible(w,c.get('date'))]
        for c in compatible:out.append({'work':w,'candidate':c,'candidate_count':len(possible),'missing_target_count':1,'creator_basis':'inherited_verified_round1_authority'})
        outcomes.append({'artwork_id':w['id'],'institution_id':w['institution_id'],'title':w['title'],'has_image':False,'outcome':'version_or_object_reconciliation','possible_candidates':len(possible),'date_compatible_candidates':len(compatible)})
    inst=r.load(OLD/'institutions.json.gz');r.save_gz(RUN/'institutions.json.gz',inst)
    counts=collections.Counter(w['institution_id'] for w in works.values())
    path=RUN/'snapshot/0000.json.gz';r.save_gz(path,list(works.values()))
    r.save(RUN/'snapshot.json',{'at':r.now(),'target':'production','read_only':True,'artworks':len(works),
        'scope':'Second round: unresolved dated candidates and multiple source versions from the complete first-round audit, excluding existing images and prior explicit rights/visual holds.',
        'parent_snapshot':str((OLD/'snapshot.json').relative_to(ROOT)),'changed_since_round1':changed,
        'museum_counts':[{'institution_id':iid,'works':n,'images':0} for iid,n in counts.items()],
        'excluded_institutions':r.load(OLD/'snapshot.json')['excluded_institutions'],
        'parts':[{'path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes()),'rows':len(works)}]})
    for name in ['indexes-summary.json','translations-summary.json']:
        r.save(RUN/name,{'inherited_evidence':str((OLD/name).relative_to(ROOT)),'sha256':r.sha((OLD/name).read_bytes()),'summary':r.load(OLD/name)})
    pin('candidate',{'at':r.now(),'snapshot_complete':True,'indexes_complete':True,'candidates':out,'outcomes':outcomes,'counts':dict(collections.Counter(x['outcome'] for x in outcomes))})
    print(json.dumps({'works':len(works),'candidates':len(out),'unique_source_images':len({q.image_key(x['candidate']['image_url']) for x in out}),'changed_since_round1':len(changed)}),flush=True)


def pages():
    # Reuse checksum-pinned page evidence. Failed earlier hints are retried by
    # the official artist text list; ambiguous links stay unresolved.
    data=q.candidate_pass();reused=0
    for x in data['candidates']:
        key=r.sha(x['candidate']['url'].encode())+'.json.gz'
        for folder in ['resolved-pages','pages']:
            p=OLD/folder/key
            if p.exists() and r.load(p).get('outcome')=='captured':
                result=r.load(p);rc=result['page']['receipt'];raw=gzip.decompress((ROOT/rc['body_path']).read_bytes())
                assert r.sha(raw)==rc['sha256']
                r.save_gz(RUN/'pages'/key,result);reused+=1;break
    print('Reused verified page captures',reused,flush=True)
    q.pages()
    for p in (OLD/'artist-links').glob('*.json.gz'):
        r.save_gz(RUN/'artist-links'/p.name,r.load(p))
    q.resolve_pages()


def get_page(c):
    key=r.sha(c['url'].encode())+'.json.gz'
    for folder in ['resolved-pages','pages']:
        path=RUN/folder/key
        if path.exists():
            x=r.load(path)
            if x.get('outcome')=='captured':return x['page']


def canonical(url):
    p=urlsplit(url);return p.netloc.removeprefix('www.').casefold()+p.path.casefold().rstrip('/').removesuffix('/text-summary').removesuffix('/text-catalogue-entry')


def linked_primary(item,page):
    """Exact external object URL or museum accession embedded in source link."""
    raw=gzip.decompress((ROOT/page['receipt']['body_path']).read_bytes());assert r.sha(raw)==page['receipt']['sha256']
    info=q.BeautifulSoup(raw,'html.parser').select_one('.wiki-layout-artwork-info')
    if not info:return None
    urls=[a['href'] for a in info.select('a[href]') if a['href'].startswith(('https://','http://'))]
    expected={canonical(x['url']) for x in item['work']['identifiers'] if x.get('url')}
    links=[u for u in urls if canonical(u) in expected]
    if links:return {'basis':'WikiArt links the exact museum catalogue object URL already assigned to this artwork','urls':links}
    # Tate identity is pinned by an exact accession in its catalogue URL.
    acno=item['work'].get('accession_number')
    if item['institution']['slug']=='tate' and acno:
        links=[u for u in urls if urlsplit(u).hostname in ['tate.org.uk','www.tate.org.uk'] and re.search('-'+re.escape(acno.casefold())+r'(?:/|$)',urlsplit(u).path.casefold())]
        if links:return {'basis':'WikiArt links the Tate catalogue with the exact production accession','accession':acno,'urls':links}
    return None


def primary():
    review=pointer(OLD,'review')
    selected=[x for x in review['held'] if x['review_outcome'] in ['insufficient_object_corroboration','museum_location_needs_reconciliation','broad_date_needs_review'] and x['institution']['slug']=='tate' and x['work'].get('accession_number')]
    fields='title,acno,url,allArtists,contributors,dateText,dimensions,start_year,end_year,master_images,masterImageStatus,masterImageCC,collection'
    def one(x):
        acno=x['work']['accession_number'];dest=RUN/'primary-tate'/(acno+'.json.gz')
        if dest.exists():return r.load(dest)
        raw,rc=r.capture('https://www.tate.org.uk/api/v2/artworks/',{'acno':acno,'fields':fields},tag='primary-tate-captures',timeout=45)
        result={'artwork_id':x['work']['id'],'accession':acno,'receipt':rc,'data':json.loads(raw) if rc['status']==200 and 'json' in rc.get('content_type','') else None}
        r.save_gz(dest,result)
        if rc['status'] in [403,429]:raise RuntimeError('Tate access restriction; stop')
        q.time.sleep(.7)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows=list(pool.map(one,selected))
    print('Selected Tate primary metadata',len(rows),collections.Counter(x['receipt']['status'] for x in rows),flush=True)
    raw,rc=r.capture('https://www.clevelandart.org/art/1980.8',tag='primary-cleveland-captures',timeout=45)
    text=q.BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert rc['status']==200 and 'known to be under copyright' in text
    old=next(x for x in review['held'] if x['work']['id']=='0fce3c4a-c9e8-4ca5-b0fd-5bb714ee6415')
    r.save(RUN/'corroboration.json',{old['work']['id']:{'source_id':old['page']['metadata']['_id'],'source_url':old['page']['url'],
        'hold':'primary_museum_rights_conflict','note':'Exact accession 1980.8 has an explicit Cleveland artwork copyright statement conflicting with the WikiArt PD label.','receipt':rc}})


def primary_dimensions(item,page):
    w=item['work'];acno=w.get('accession_number')
    if item['institution']['slug']!='tate' or not acno:return None
    path=RUN/'primary-tate'/(acno+'.json.gz')
    if not path.exists():return None
    evidence=r.load(path);objects=(evidence.get('data') or {}).get('items',[])
    if evidence['receipt']['status']!=200 or len(objects)!=1:return None
    o=objects[0]
    if o.get('acno')!=acno or o.get('collection')!='Tate' or q.norm(o.get('title')) not in q.title_keys(w):return None
    maker=set(q.norm(page['metadata'].get('artistName')).split())
    if len(maker)<2 or not maker.issubset(set(q.norm(o.get('allArtists')).split())):return None
    makers=o.get('contributors',[])
    if len(makers)!=1 or makers[0].get('role_display')!='artist' or makers[0].get('prepend_role_to_name') or makers[0].get('append_role_to_name'):return None
    if any(im.get('copyright') for im in o.get('master_images',[])):return None
    primary=re.search(r'support:\s*([\d.]+)\s*x\s*([\d.]+)\s*mm',o.get('dimensions',''))
    source=re.fullmatch(r'([\d.]+)\s*x\s*([\d.]+)\s*cm',page['fields'].get('Dimensions',''))
    if not primary or not source:return None
    pd=sorted(float(primary[i])/10 for i in [1,2]);sd=sorted(float(source[i]) for i in [1,2])
    if not all(abs(a-b)<=.15 for a,b in zip(pd,sd)):return None
    if not (o.get('start_year') is not None and q.date_compatible(w,(o['start_year'],o.get('end_year') or o['start_year']))):return None
    return {'basis':'Exact current Tate accession, title, sole named creator and compatible date; independently matching physical support dimensions to within 1.5 mm.',
        'museum_object':o,'primary_dimensions_cm':pd,'wikiart_dimensions_cm':sd,'receipt':evidence['receipt']}


def assess():
    data=q.candidate_pass();institutions={x['id']:x for x in r.load(RUN/'institutions.json.gz')}
    # Leading article is part of the local Cleveland label but omitted by
    # WikiArt. This exact institutional alias retains its city/name specificity.
    q.MUSEUM_ALIASES['cleveland-museum-of-art']=['Cleveland Museum of Art (CMA), Cleveland']
    edges=[]
    manual=r.load(RUN/'corroboration.json') if (RUN/'corroboration.json').exists() else {}
    for item in data['candidates']:
        x=copy.deepcopy(item);x['institution']=institutions[x['work']['institution_id']]
        page=get_page(x['candidate'])
        outcome=q.assess_one(x,page,x['institution']) if page else 'page_verification_pending_or_failed'
        if page:
            x['page']=page
            if outcome in ['insufficient_object_corroboration','broad_date_needs_review']:
                link=linked_primary(x,page)
                if link:x['primary_corroboration']=link;outcome='high_exact_primary_object_link'
            if outcome in ['insufficient_object_corroboration','broad_date_needs_review'] or (outcome=='museum_location_needs_reconciliation' and page['fields'].get('Location')=='Private Collection'):
                dims=primary_dimensions(x,page)
                if dims:x['primary_corroboration']=dims;outcome='high_exact_primary_accession_and_physical_dimensions'
            extra=manual.get(x['work']['id'])
            if extra and extra.get('source_id')==page['metadata']['_id']:
                assert extra['source_url']==page['url']
                if extra.get('hold'):outcome=extra['hold'];x['primary_corroboration']=extra
                elif outcome in ['insufficient_object_corroboration','broad_date_needs_review','museum_location_needs_reconciliation','partial_or_study_needs_visual_reconciliation','object_creator_needs_review']:
                    outcome='high_primary_object_corroborated';x['primary_corroboration']=extra
        x['review_outcome']=outcome;edges.append(x)
    bywork=collections.defaultdict(list)
    for x in edges:bywork[x['work']['id']].append(x)
    ready=[];held=[]
    for aid,choices in bywork.items():
        high=[x for x in choices if x['review_outcome'].startswith('high_')]
        # Different CDN image variants that resolve to the same source object
        # are one identity. Keep a page only after exact image checks above.
        objects={x['page']['metadata']['_id']:x for x in high}
        if len(objects)==1:
            chosen=next(iter(objects.values()));chosen['alternative_reviews']=[{'url':x.get('page',{}).get('url',x['candidate']['url']),'outcome':x['review_outcome']} for x in choices if x is not chosen]
            ready.append(chosen)
        elif len(objects)>1:held.append({**choices[0],'review_outcome':'multiple_verified_source_versions','alternatives':[{'url':x['page']['url'],'outcome':x['review_outcome']} for x in high]})
        else:held.append(choices[0])
    counts=collections.Counter(x['page']['metadata']['_id'] for x in ready)
    for x in ready[:]:
        if counts[x['page']['metadata']['_id']]>1:
            ready.remove(x);held.append({**x,'review_outcome':'multiple_catalogue_targets_after_museum_reconciliation'})
    pin('review',{'at':r.now(),'candidate_pass':r.load(RUN/'latest-candidate-pass.json'),'ready':ready,'held':held,
        'confidence_policy':'At least 90% requested confidence implemented as high-corroboration gates, not a calibrated probability. Exact source artist/title/date/image and unrestricted public-domain label are mandatory; competing objects need unique museum/object corroboration.'})
    r.save_gz(RUN/'edge-reviews'/((r.now().replace(':',''))+'.json.gz'),edges)
    print(json.dumps({'ready':len(ready),'held':len(held),'ready_reasons':dict(collections.Counter(x['review_outcome'] for x in ready)),'held_reasons':dict(collections.Counter(x['review_outcome'] for x in held))}),flush=True)


def backup():
    description='Before verified WikiArt production museum image round2 20261006'
    def gcloud(*args):return subprocess.check_output(['gcloud',*args,'--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True)
    rows=json.loads(gcloud('sql','backups','list','--instance=artline-postgres','--limit=40'))
    matching=[x for x in rows if x.get('description')==description]
    if not matching:
        result=json.loads(gcloud('sql','backups','create','--instance=artline-postgres','--description='+description,'--async'))
        r.save(d.BACKUP/'cloud-sql-backup-operation.json',result);print('Requested separate round 2 Cloud SQL backup',flush=True);return
    current=max(matching,key=lambda x:int(x['id']))
    if current['status']!='SUCCESSFUL':print('Cloud SQL backup status',current['status'],flush=True);return
    r.save(d.BACKUP/'cloud-sql-backup.json',current)
    r.save(RUN/'cloud-sql-backup.json',{'id':current['id'],'status':current['status'],'at':r.now()})
    print('Cloud SQL recovery backup verified',current['id'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['discover','pages','primary','assess','prepare','contact_sheets','record_visual_review','resolve_mariana','resolve_date_versions','source_date_candidates','correct_dock_version','correct_print_impressions','version_evidence','plan','backup','upload','apply','verify','verify_combined','report','expand_scope','expand_sources','expand_translations','expand_titles','expand_candidates'])
    parser.add_argument('--expanded',action='store_true')
    parser.add_argument('--date-review',action='store_true')
    args=parser.parse_args();name=args.command
    helper=None
    if args.expanded or args.date_review:
        spec=importlib.util.spec_from_file_location('expanded',ROOT/'ops/wikiart-authoritative-expansion-20261006.py')
        helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.configure(sys.modules[__name__],date_review=args.date_review)
    (getattr(helper,name,None) or globals().get(name) or getattr(d,name))()
