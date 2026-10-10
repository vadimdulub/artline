#!/usr/bin/env python3
"""Evidence and orchestration for the explicitly authorized fourth random cohort.

The first campaign is immutable. Production is read only until delivery.apply;
source approval never changes source rights assertions or editorial status.
"""
import argparse
import collections
import concurrent.futures
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import secrets
import time

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('round_four_delivery',ROOT/'ops/deliver-random-200-painters-round4-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
s=d.s;m=d.m;r=d.r;q=d.q;RUN=d.RUN;BACKUP=d.BACKUP
PREVIOUS=ROOT/'docs/research/random-200-painters-20261006'
PRIOR_RUNS=[PREVIOUS,ROOT/'docs/research/random-200-painters-round2-20261006',ROOT/'docs/research/random-200-painters-round3-20261006']


def csv_file(name,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    path=RUN/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def bootstrap():
    if (RUN/'authorization.json').exists():
        assert r.load(RUN/'authorization.json')['cohort_sha256']==r.sha((RUN/'cohort.json').read_bytes())
        print('Existing frozen round-four cohort preserved',flush=True);return
    previous=[pair for folder in PRIOR_RUNS for pair in r.load(folder/'cohort.json')['painters']]
    excluded_ids={x['artist']['id'] for x in previous}
    excluded_urls={x['source']['url'] for x in previous}|{'https://www.wikiart.org/en/otto-dix'}
    prior_pins=[{'operation':folder.name,'cohort_sha256':r.sha((folder/'cohort.json').read_bytes())} for folder in PRIOR_RUNS]
    assert len(excluded_ids)==600 and len(excluded_urls)==601
    old_frame=r.load(PREVIOUS/'sampling-frame.json');directory_path=ROOT/old_frame['directory_path']
    assert r.sha(directory_path.read_bytes())==old_frame['directory_sha256']
    directory=r.load(directory_path);by_name=collections.defaultdict(dict);by_url={x['url']:x for x in directory}
    for source in directory:by_name[q.norm(source['name'])][source['url']]=source
    with r.connect('production') as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists=[x['artist'] for x in db.execute("SELECT to_jsonb(a) artist FROM artists a WHERE entity_type='person' AND status<>'archived' ORDER BY id").fetchall()]
        aliases=collections.defaultdict(list);identifiers=collections.defaultdict(list)
        for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases ORDER BY artist_id,alias').fetchall():aliases[x['artist_id']].append(x['alias'])
        for x in db.execute("SELECT to_jsonb(e) identifier FROM external_identifiers e WHERE entity_type='artist' ORDER BY entity_id,id").fetchall():
            e=x['identifier'];identifiers[e['entity_id']].append(e)
    frame=[]
    for artist in artists:
        aid=artist['id'];sources={}
        if aid in excluded_ids or q.norm(artist['display_name'])=='otto dix':continue
        for name in [artist['display_name']]+aliases[aid]:sources.update(by_name[q.norm(name)])
        for ident in identifiers[aid]:
            url=(ident.get('canonical_url') or '').rstrip('/')
            if url in by_url:sources[url]=by_url[url]
        sources={url:source for url,source in sources.items() if all(artist.get(k) is None or source.get(k) is None or artist[k]==source[k] for k in ['birth_year','death_year'])}
        if len(sources)==1:
            source=next(iter(sources.values()))
            if source['url'] in excluded_urls:continue
            frame.append({'artist':artist,'aliases':aliases[aid],'identifiers':identifiers[aid],'source':source,
                          'basis':'Unique exact creator name/alias or explicit source identifier, without lifespan conflict.'})
    # Two catalogue authorities for one WikiArt identity are ambiguous, not two chances to sample the same painter.
    multiplicity=collections.Counter(x['source']['url'] for x in frame)
    ambiguous=[x for x in frame if multiplicity[x['source']['url']]>1]
    frame=[x for x in frame if multiplicity[x['source']['url']]==1]
    assert len(frame)>=200
    seed=secrets.token_hex(16)
    chosen=sorted(frame,key=lambda x:hashlib.sha256((seed+'/'+x['artist']['id']).encode()).digest())[:200]
    assert len({x['source']['url'] for x in chosen})==200 and not ({x['artist']['id'] for x in chosen}&excluded_ids)
    r.save(RUN/'sampling-frame.json',{'at':r.now(),'catalogue_persons':len(artists),'directory_path':old_frame['directory_path'],
        'directory_sha256':old_frame['directory_sha256'],'prior_cohorts':prior_pins,
        'excluded_artist_ids':sorted(excluded_ids),'excluded_source_urls':sorted(excluded_urls),'ambiguous_duplicate_authorities':ambiguous,
        'securely_matched_painters':len(frame),'frame':frame})
    r.save(RUN/'cohort.json',{'at':r.now(),'seed':seed,'method':'Uniform random ordering without replacement using SHA256(seed + / + production artist UUID); seed frozen before artwork research.',
        'frame':'Active production person artists uniquely matched to distinct WikiArt profiles; all three previous 200-painter cohorts and Otto Dix excluded. No popularity, country, date or artwork-count weighting.','painters':chosen})
    r.save(RUN/'authorization.json',{'at':r.now(),'target':'production','painters':200,
        'user_instruction':'see new md file - wiki art is fully approved; nice, pick other 200 randomly selected painters',
        'continues':'Previous explicitly authorized production artwork research, review-record import, selected WikiArt image upload and related-artwork research.',
        'cohort_sha256':r.sha((RUN/'cohort.json').read_bytes()),'prior_cohorts':prior_pins,
        'source_approval':'WikiArt approved across project source, image-use, rights-review and public/commercial-display policies; restricted or absent rights labels alone do not block selected images.',
        'policy_path':'docs/ARTLINE_IMAGE_USE.md#user-approved-wikiart-source-policy--6-october-2026',
        'policy_sha256':r.sha((ROOT/'docs/ARTLINE_IMAGE_USE.md').read_bytes()),'agents_sha256':r.sha((ROOT/'AGENTS.md').read_bytes()),
        'rules':['Freeze disjoint random sample with no replacements.','Preserve actual rights labels and record user approval separately.',
                 'Identity/version/date scope checks remain in force; unknown dates and fields preserved in review.',
                 'Existing images, catalogue metadata, holdings and publication preserved.','No local database writes.']})
    csv_file('selected-200-painters.csv',[{'rank':i,'artist':x['artist']['display_name'],'artist_id':x['artist']['id'],'wikiart_url':x['source']['url'],'source_index_estimate':x['source']['count']} for i,x in enumerate(chosen,1)])
    print('Frozen new random sample:',len(chosen),'from',len(frame),'eligible distinct identities; overlap with all three earlier batches: 0',flush=True)
    print('First ten:',', '.join(x['artist']['display_name'] for x in chosen[:10]),flush=True)


def creator_leads():
    """Inspect only existing object labels; never infer a creator link from a name."""
    path=RUN/'expanded-creator-leads.json'
    if path.exists():print('Preserving expanded creator leads',flush=True);return
    names=collections.defaultdict(set)
    for pair in m.cohort():
        aid=pair['artist']['id']
        for name in [pair['artist']['display_name'],pair['source']['name']]+pair['aliases']:
            normalized=s.normalized(name)
            if len(normalized)>=6 and len(normalized.split())>=2:
                names[normalized].add(aid)
                words=normalized.split();names[' '.join(words[-1:]+words[:-1])].add(aid)
    with r.connect('production') as db:
        query="SELECT DISTINCT unlinked_creator_label FROM artworks WHERE unlinked_creator_label IS NOT NULL AND status<>'archived'"
        r.save(RUN/'creator-label-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) '+query).fetchone())
        labels=[x['unlinked_creator_label'] for x in db.execute(query).fetchall()]
        selected={label:names[s.normalized(re.sub(r'\([^)]*\)','',label))] for label in labels if s.normalized(re.sub(r'\([^)]*\)','',label)) in names}
        rows=db.execute("SELECT to_jsonb(a) artwork FROM artworks a WHERE unlinked_creator_label=ANY(%s) AND status<>'archived' ORDER BY id",(list(selected),)).fetchall() if selected else []
    leads=[{'artist_id':aid,'artwork':row['artwork']} for row in rows for aid in sorted(selected[row['artwork']['unlinked_creator_label']])]
    r.save(path,leads);r.save(RUN/'creator-label-search.json',{'at':r.now(),'labels_examined':len(labels),'matching_labels':selected,
        'lead_rows':len(leads),'basis':'Full normalized canonical/source/alias name and surname-first form; parenthesized qualifiers retained in original evidence. Candidates only, no creator reassignment.'})
    print('Expanded existing creator-label leads:',len(leads),'across',len({x['artist_id'] for x in leads}),'painters',flush=True)


def index_gaps():
    """Keep visible source rows that have no artwork link, including source omissions."""
    path=RUN/'unlinked-index-entries.json.gz'
    if path.exists():return
    rows=[]
    for pair in m.cohort():
        url=pair['source']['url']+'/all-works/text-list';key=r.sha(url.encode())
        raw=gzip.decompress((RUN/'index-captures'/(key+'.body.gz')).read_bytes())
        receipt=r.load(RUN/'index-captures'/(key+'.receipt.json'))
        soup=m.BeautifulSoup(raw,'html.parser')
        for position,li in enumerate(soup.select('li.painting-list-text-row'),1):
            links=li.find_all('a',href=True)
            if any(m.urlsplit(m.urljoin(url,a['href'])).hostname=='www.wikiart.org' and m.urlsplit(m.urljoin(url,a['href'])).path.startswith(m.urlsplit(pair['source']['url']).path+'/') for a in links):continue
            spans=li.find_all('span',recursive=False)
            if links:
                title=links[0].get_text(' ',strip=True);date=li.get_text(' ',strip=True).removeprefix(title).strip(' ,')
            elif len(spans)>=2:
                title=spans[0].get_text(' ',strip=True);date=spans[1].get_text(' ',strip=True).strip(' ,')
            else:continue
            rows.append({'artist_id':pair['artist']['id'],'artist':pair['artist']['display_name'],'title':title,
                         'source_date':date,'date':m.dates.creation_date(date),'url':url,'source_row':position,'receipt':receipt,
                         'external_reference_links':[m.urljoin(url,a['href']) for a in links],
                         'reason':'WikiArt index supplies a title but no WikiArt artwork-page link. Page identity, exact version and image evidence remain unresolved.'})
    r.save_gz(path,rows);print('Preserved unlinked source index rows:',len(rows),'across',len({x['artist_id'] for x in rows}),'artists',flush=True)


def retry_pages():
    """One fresh bounded attempt after the primary run; retain all initial failures."""
    m.CACHE=m.cache_catalogue();jobs=[]
    for pair in m.cohort():
        aid=pair['artist']['id']
        for path in (RUN/'pages'/aid).glob('*.json.gz'):
            old=r.load(path)
            if old['outcome']!='captured' and not (RUN/'page-retries'/aid/path.name).exists():jobs.append((pair,path,old))
    def one(job):
        pair,path,old=job;result={'artist_id':pair['artist']['id'],'index':old['index'],'initial_failure':str(path.relative_to(ROOT))}
        try:
            raw,rc=m.capture(old['index']['url'],'retry-captures',fresh=True)
            assert rc['status']==200,'HTTP '+str(rc['status'])
            p=q.page_metadata(raw,rc);assert p['metadata']['artistUrl']==m.urlsplit(pair['source']['url']).path,'Source creator differs'
            soup=m.BeautifulSoup(raw,'html.parser');label=soup.select_one('.copyright-wrapper')
            p['rights_label']=label.get_text(' ',strip=True) if label else 'Rights label not supplied'
            p['rights_status']='public_domain' if p['rights_label']=='Public domain' else ('restricted' if label else 'unknown')
            p['date']=s.source_date(p);p['title']=m.html.unescape(p['metadata']['title'])
            p['reference_links']=[{'title':a.get_text(' ',strip=True),'url':m.urljoin(p['url'],a['href'])} for a in soup.select('.wiki-layout-artwork-info a[href]') if m.urlsplit(m.urljoin(p['url'],a['href'])).hostname not in ['www.wikiart.org','www.1st-art-gallery.com']]
            result.update(outcome='captured',page=p)
        except Exception as exc:result.update(outcome='source_unavailable',error=str(exc)[:400])
        r.save_gz(RUN/'page-retries'/pair['artist']['id']/path.name,result);return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(one,jobs))
    print('Fresh metadata retries:',dict(collections.Counter(x['outcome'] for x in results)),flush=True)


def cross_creator_audit():
    """Compare selected reproductions across this and the prior delivered cohort."""
    path=RUN/'cross-creator-image-audit.json'
    if path.exists():return
    images=[r.load(p) for p in (RUN/'prepared-images').glob('*.json')]
    ready=[im for im in images if im['outcome']=='prepared'];bysha=collections.defaultdict(list)
    prior=[]
    for folder in PRIOR_RUNS:
        for planpath in (folder/'delivery-plans').glob('*.json.gz'):
            prior.extend(r.load(planpath)['images'])
        if (folder/'supplemental-plan.json.gz').exists():prior.extend(r.load(folder/'supplemental-plan.json.gz')['images'])
    for im in ready+prior:
        for digest in {im['sha256'],im['download']['sha256']}:bysha[digest].append(im)
    groups={};holds={};current_ids={im['artwork_id'] for im in ready}
    for digest,items in bysha.items():
        unique={im['artwork_id']:im for im in items}
        if len({im['artist_id'] for im in unique.values()})>1 and set(unique)&current_ids:
            key=','.join(sorted(unique));groups[key]=[{'artwork_id':im['artwork_id'],'artist_id':im['artist_id'],'artist':im['artist'],'title':im['title'],'source_url':im['source_page_url']} for im in unique.values()]
            for aid in set(unique)&current_ids:holds[aid]='Exact image also assigned to another creator in this or the previous cohort; source attribution/version requires individual resolution.'
    r.save(path,{'at':r.now(),'selected_images':len(ready),'prior_delivered_images_compared':len(prior),'cross_creator_groups':list(groups.values()),'held_artwork_ids':holds})
    print('Cross-creator exact-image audit:',len(ready),'current images;',len(holds),'held;',len(prior),'prior images compared',flush=True)


def pipeline():
    """Prepare completed artist research while the remaining metadata is collected."""
    while True:
        research_done=(RUN/'pages-summary.json').exists()
        if research_done:retry_pages()
        s.select();d.prepare();d.audits();d.sheets()
        selected=len(list((RUN/'selections').glob('*.json.gz')))
        m.status('pipeline',selected_painters=selected,research_done=research_done)
        if research_done and selected==200:
            cross_creator_audit();print('All metadata selections and image preparation complete; visual reviews required before delivery.',flush=True);return
        time.sleep(15)


def cached_relationships():
    """Search already captured artwork titles for full-name subject references.

    This is a bounded evidence inventory, not a worldwide relationship claim.
    Creator fields are never reassigned to the person depicted in a title.
    """
    dest=RUN/'cached-related-work-leads-v2.json.gz'
    if dest.exists():return
    pairs=m.cohort();names=collections.defaultdict(set)
    for pair in pairs:
        for name in [pair['artist']['display_name'],pair['source']['name']]:
            key=s.normalized(name)
            if len(key.split())>=2 and len(key)>=7:names[key].add(pair['artist']['id'])
    pattern=re.compile(r'(?<!\w)('+ '|'.join(re.escape(x) for x in sorted(names,key=len,reverse=True))+r')(?!\w)')
    cache=m.cache_catalogue();found={};examined=0
    for url,entry in cache.items():
        if not re.fullmatch(r'/en/[^/]+/[^/]+',m.urlsplit(url).path):continue
        path=ROOT/entry['body_path'];raw=path.read_bytes()
        if path.suffix=='.gz':raw=gzip.decompress(raw)
        text=raw.decode('utf-8',errors='replace')
        match=re.search(r'ng-init="paintingJson\s*=\s*(\{[^"]+)"',text)
        if not match:continue
        try:metadata=json.loads(m.html.unescape(match[1]))
        except ValueError:continue
        examined+=1;title=s.normalized(metadata.get('title'))
        for match in pattern.finditer(title):
            for aid in names[match[1]]:
                pair=next(x for x in pairs if x['artist']['id']==aid)
                if metadata.get('artistUrl')==m.urlsplit(pair['source']['url']).path:continue
                key=(aid,metadata['_id'])
                found[key]={'artist_id':aid,'artist':pair['artist']['display_name'],'relation':'title_name_lead',
                    'creator':metadata.get('artistName'),'title':metadata.get('title'),'source_id':metadata['_id'],
                    'source_url':url,'source_date':metadata.get('year'),'image_url':metadata.get('image'),
                    'matched_full_name':match[1],'capture':entry,
                    'basis':'Full source/canonical artist name occurs in another creator’s captured artwork title. Subject, dedication or influence remains an evidenced lead; no creator reassignment.'}
    assert examined>10000,'Expected artwork JSON was not found in the saved capture inventory'
    r.save_gz(dest,{'at':r.now(),'captured_pages_examined':examined,'rows':list(found.values()),'scope':'Previously captured English WikiArt artwork pages; no worldwide-completeness claim.'})
    print('Related title leads:',len(found),'from',examined,'previously captured artwork pages',flush=True)


def preflight():
    """Check the complete frozen delivery without mutating production."""
    dest=RUN/'production-preflight.json'
    if dest.exists():print('Preserving production preflight',flush=True);return
    expected_count=len(m.cohort())
    deliveries=list(d.pinned_deliveries());assert len(deliveries)==expected_count
    pairs=m.cohort();previous=[pair for folder in PRIOR_RUNS for pair in r.load(folder/'cohort.json')['painters']]
    assert len({v['artist']['id'] for v in pairs})==expected_count
    assert not {v['artist']['id'] for v in pairs}&{v['artist']['id'] for v in previous}
    assert not {v['source']['url'] for v in pairs}&({v['source']['url'] for v in previous}|{'https://www.wikiart.org/en/otto-dix'})
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    approved,visual_holds=d.visual_decisions()
    quality=r.load(RUN/'quality-final-candidates.json')
    quality_review=r.load(RUN/'quality-final-review.json')
    assert quality['painters']==quality_review['painters']==expected_count
    assert quality_review['candidate_sha256']==r.sha((RUN/'quality-final-candidates.json').read_bytes())
    assert quality_review['all_title_and_architectural_candidates_reviewed']
    rows=[row for data,pin in deliveries for row in data['rows']]
    images=[im for data,pin in deliveries for im in data['images']]
    assert len(rows)==len({row['artwork_id'] for row in rows})==len({row['source_id'] for row in rows})
    assert len(images)==len({im['artwork_id'] for im in images})==len({im['sha256'] for im in images})
    row_by_id={row['artwork_id']:row for row in rows}
    for issue in quality['lifespan_or_qualified_creator']:
        row=row_by_id.get(issue['artwork_id'])
        assert row is None or row.get('reviewed_source_discrepancy'),'Unreviewed creator/date anomaly'
    for data,pin in deliveries:
        assert set(data['image_audit']['visual_sample_ids'])<=set(approved)|set(visual_holds)
        for row in data['rows']:
            assert row['confidence']>=.90
            assert row['page']['metadata']['artistUrl']==m.urlsplit(next(v['source']['url'] for v in pairs if v['artist']['id']==row['artist_id'])).path
            if row['action']=='existing':assert row['artwork_id'] in data['preimages']
        for im in data['images']:
            row=row_by_id[im['artwork_id']];date=s.source_date(row['page'])
            assert date and date['creation_year_end']<=1970 and not row.get('has_image') and not row.get('image_hold')
            assert im['artwork_id'] not in data['held'] and im['artwork_id'] not in visual_holds
            assert im['rights_status']==row['rights_status'] and im['source_rights_label']==row['source_rights_label']
            assert im['rights_status']==('public_domain' if im['source_rights_label']=='Public domain' else ('unknown' if im['source_rights_label']=='Rights label not supplied' else 'restricted'))
            if im.get('source_display_placeholder'):assert approved.get(im['artwork_id'])==im['sha256']
            raw=Path(im['visual_path']).read_bytes();assert len(raw)==im['bytes']<=100000 and r.sha(raw)==im['sha256']
            if row['action']=='existing':assert data['preimages'][im['artwork_id']]['artwork']['primary_media_id'] is None
    new=sum(row['action']=='create' for row in rows)
    with r.connect('production') as db:
        position=db.execute('SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(m.COLLECTION,)).fetchone()['n']
        assert position+new<=100000
    result={'at':r.now(),'painters':expected_count,'overlap_with_previous_cohorts_or_otto_dix':0,'records':len(rows),'new_review_records':new,
        'existing_records':len(rows)-new,'images':len(images),'actual_rights_labels':dict(collections.Counter(im['rights_status'] for im in images)),
        'visual_samples_approved':len(approved),'visual_samples_held':len(visual_holds),'display_placeholder_images_individually_reviewed':sum(bool(im.get('source_display_placeholder')) for im in images),
        'maximum_derivative_bytes':max(im['bytes'] for im in images),'collection_position_before':position,'remaining_collection_capacity':100000-position-new,
        'successful_cloud_backup':r.load(BACKUP/'cloud-backup.json')['id'],'checks':['Immutable selection and delivery pins','Artist and artwork source identity','Creation-date image scope','Source rights distinct from approval','No existing-image replacement','Full QA sample accounting','Unique delivery artwork IDs, source IDs and image checksums','Derivative byte bounds and checksums','Owner collection capacity'],'errors':[]}
    r.save(dest,result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['bootstrap','creator_leads','index_gaps','retry_pages','cross_creator_audit','pipeline','cached_relationships','preflight'])
    args=parser.parse_args();globals()[args.phase]()
