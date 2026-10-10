#!/usr/bin/env python3
"""Selected existing local WikiArt gaps under the explicit 6 October approval."""
import argparse
import collections
import html
import importlib.util
import json
import re
import unicodedata
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

s = importlib.util.spec_from_file_location('chicago', Path(__file__).with_name('recover-local-chicago-native-images-20261006.py'))
chicago = importlib.util.module_from_spec(s)
s.loader.exec_module(chicago)
base, core = chicago.base, chicago.core
RUN = core.ROOT / 'docs/research/local-wikiart-approved-images-20261006'
base.RUN = RUN
chicago.RUN = RUN
PROVIDER = 'wikiart-approved-local'
POLICY = 'https://www.wikiart.org/en/terms-of-use'
core.PROVIDERS[PROVIDER] = 'WikiArt'
core.VERSION = 'local-wikiart-user-approved-image-only-v1'
core.HOSTS.add('www.wikiart.org')
EXCLUDE_RUNS = []
# Optional operation-specific, individually frozen native date/version review.
# Without this callback, unknown source dates retain the existing strict hold.
SOURCE_DATE_REVIEW = None


def norm(value):
    value = unicodedata.normalize('NFKD', html.unescape(str(value or '')).casefold())
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in value if not unicodedata.combining(c))))


def approval():
    path = RUN / 'source-authorization.json'
    value = json.loads(path.read_bytes())
    if value['source'] != 'WikiArt' or value['target'] != 'local' or value['record_actual_rights_separately'] is not True:
        raise ValueError('WikiArt source approval scope differs')
    for item in value['documents']:
        data = (RUN / item['capture']).read_bytes()
        if core.sha(data) != item['sha256']:
            raise ValueError('Pinned source approval changed')
    return value


def select(limit):
    if (RUN / 'candidates.json').exists():
        return
    excluded=sorted({c['artwork_id'] for run in EXCLUDE_RUNS for c in json.loads((run/'candidates.json').read_bytes())['candidates']})
    with base.connect() as db:
        rows = db.execute('''WITH eligible AS (
          SELECT a.id, aa.artist_id,
            EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=aa.artist_id AND ac.country_code IN ('RU','GR','CY')) priority,
            row_number() OVER(PARTITION BY aa.artist_id ORDER BY a.creation_year_start,a.id) creator_rank
          FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
          JOIN artwork_artists aa ON aa.artwork_id=a.id
          WHERE e.entity_type='artwork' AND e.scheme='wikiart-artwork'
            AND a.primary_media_id IS NULL AND a.status='review' AND aa.attribution_role='primary'
            AND NOT(a.id=ANY(%s::uuid[]))
            AND NOT EXISTS(SELECT 1 FROM artwork_artists other WHERE other.artwork_id=a.id AND other.artist_id<>aa.artist_id)
            AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
            AND artline_has_selection_evidence(a.id))
          SELECT id::text FROM eligible ORDER BY priority DESC,creator_rank,id LIMIT %s''', (excluded,limit)).fetchall()
        ids = [r['id'] for r in rows]
        rows = db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,
          a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
          to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,
          e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
          ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
          (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
          (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
          COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
          FROM artworks a LEFT JOIN institutions i ON i.id=a.current_institution_id
          JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikiart-artwork'
          WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''', (ids,)).fetchall()
        artists = sorted({c['creator_links'][0]['artist_id'] for c in rows})
        ar = {x['record']['id']: x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])', (artists,))}
        aliases, identifiers = collections.defaultdict(list), collections.defaultdict(list)
        for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY id', (artists,)):
            aliases[x['record']['artist_id']].append(x['record'])
        for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id", (artists,)):
            identifiers[x['record']['entity_id']].append(x['record'])
        baseline = db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    if not rows or len({c['artwork_id'] for c in rows}) != len(rows):
        raise ValueError('Empty or ambiguous bounded selection')
    for c in rows:
        aid = c['creator_links'][0]['artist_id']
        c.update(provider=PROVIDER,artist=ar[aid]['display_name'],target_ids={'local':c['artwork_id']},
            creator_authorities=[dict(artist_record=ar[aid],artist_aliases=aliases[aid],artist_identifiers=identifiers[aid])])
    core.save_new(RUN / 'candidates.json', dict(at=core.now(),baseline=baseline,candidates=rows,excluded_runs=[str(p.relative_to(core.ROOT)) for p in EXCLUDE_RUNS],
        selection='Bounded existing missing-image WikiArt object IDs; PostgreSQL creation eligibility and selection evidence. Creator breadth with RU/GR/CY priority. No catalogue creation or publication.'))
    print('Selected existing WikiArt gaps:',len(rows),'creators:',len(artists),flush=True)


def capture_page(c, fetch):
    path = RUN / 'metadata/pages' / (c['artwork_id'] + '.html')
    if path.exists():
        return path.read_bytes(), json.loads(path.with_suffix('.receipt.json').read_bytes())
    target = c['page']; redirects = []
    for _ in range(4):
        u = urlparse(target)
        if u.scheme != 'https' or u.netloc != 'www.wikiart.org' or not re.fullmatch('/en/[^/]+/[^/]+',u.path) or u.query:
            raise ValueError('Unexpected WikiArt artwork URL')
        core.provider_rate_slot(u.hostname)
        with fetch.session.get(target,timeout=(15,45),allow_redirects=False) as response:
            if response.status_code in (301,302,303,307,308):
                redirects.append(dict(url=target,status=response.status_code,location=response.headers['Location']))
                target=urljoin(target,response.headers['Location']);continue
            response.raise_for_status()
            if response.status_code != 200 or len(response.content)>5_000_000:
                raise ValueError('Unexpected artwork page response')
            data=response.content
            rc=dict(url=target,requested_url=c['page'],redirects=redirects,at=core.now(),bytes=len(data),sha256=core.sha(data),path=str(path.relative_to(core.ROOT)))
            core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),rc)
            return data,rc
    raise ValueError('Too many artwork page redirects')


def visible_creation_date(soup):
    values=[]
    for li in soup.select('.wiki-layout-artwork-info article > ul > li'):
        label=li.find('s')
        if label and norm(label.get_text(' ',strip=True))=='date':
            value=li.get_text(' ',strip=True).removeprefix(label.get_text(' ',strip=True)).strip()
            values.append(value.split(';',1)[0].strip())
    if len(values)!=1:raise ValueError('Unique displayed source date absent')
    return values[0]


def page_facts(c,data,rc):
    soup=BeautifulSoup(data,'html.parser')
    tags=soup.select('.wiki-layout-painting-info-bottom[ng-init]')
    if len(tags)!=1:raise ValueError('Unique WikiArt object metadata absent')
    record=json.loads(tags[0]['ng-init'].split('=',1)[1].strip())
    if record.get('_id')!=c['external_id']:raise ValueError('Exact existing WikiArt object ID differs')
    if norm(record.get('title')) not in {norm(c['title']),norm(c.get('alternate_title'))}-{''}:
        raise ValueError('Current source title needs artwork/version review')
    if len(c['creator_authorities'])!=1 or c['roles']!=['primary']:raise ValueError('Unique local primary creator absent')
    proof=c['creator_authorities'][0]
    if proof['artist_record']['id']!=c['creator_links'][0]['artist_id']:raise ValueError('Creator link differs')
    ids=[x for x in proof['artist_identifiers'] if x['scheme']=='wikiart-artist'];crosswalk=None
    if len(ids)==1:
        artist_url='https://www.wikiart.org/en/'+ids[0]['external_id']
        if ids[0]['canonical_url'] not in (None,artist_url):raise ValueError('Stored WikiArt creator URL conflicts')
    elif not ids:
        qids=[x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']
        if len(qids)!=1 or not re.fullmatch(r'Q[1-9][0-9]*',qids[0]):raise ValueError('Independent creator authority missing or ambiguous')
        url='https://www.wikidata.org/wiki/Special:EntityData/'+qids[0]+'.json';p=RUN/'metadata'/(core.sha(url.encode())+'.json')
        data_authority=p.read_bytes();receipt=json.loads(p.with_suffix('.receipt.json').read_bytes())
        if receipt['url']!=url or core.sha(data_authority)!=receipt['sha256'] or len(data_authority)!=receipt['bytes']:raise ValueError('Pinned creator crosswalk differs')
        entity=json.loads(data_authority)['entities'][qids[0]]
        slugs={claim['mainsnak']['datavalue']['value'] for claim in entity.get('claims',{}).get('P6002',[]) if claim.get('rank')!='deprecated' and claim['mainsnak'].get('snaktype')=='value'}
        if len(slugs)!=1 or not re.fullmatch('[a-z0-9-]+',next(iter(slugs))):raise ValueError('Existing Wikidata creator has no unique WikiArt crosswalk')
        artist_url='https://www.wikiart.org/en/'+next(iter(slugs));crosswalk=dict(entity=entity,receipt=receipt)
    else:raise ValueError('Existing exact WikiArt creator authority ambiguous')
    if urljoin(rc['url'],record.get('artistUrl',''))!=artist_url or rc['url'].rsplit('/',1)[0]!=artist_url:
        raise ValueError('Exact source creator identity differs')
    names={norm(proof['artist_record']['display_name']),*(norm(x['alias']) for x in proof['artist_aliases'])}
    if norm(record.get('artistName')) not in names:raise ValueError('Source creator name/alias differs')
    date=re.fullmatch(r'(?:c\.|ca\.)?\s*(\d{1,4})(?:\s*[-–]\s*(?:c\.|ca\.)?\s*(\d{1,4}))?',str(record.get('year') or ''),re.I)
    date_review=None;date_note=None
    if not date:
        if SOURCE_DATE_REVIEW is None:raise ValueError('Source creation date needs individual review')
        date_review=SOURCE_DATE_REVIEW(c,record,soup,rc,data)
        if not isinstance(date_review,dict) or date_review.get('decision')!='eligible_exact_native_version' or not date_review.get('note'):
            raise ValueError('Individual source date review absent')
        lo=hi=None
        date_note=date_review['note']
    else:
        lo,hi=int(date[1]),int(date[2] or date[1])
        if not 1<=lo<=hi<=1970:raise ValueError('Source creation interval outside scope')
        visible=visible_creation_date(soup)
        displayed=re.fullmatch(r'(?:c\.|ca\.)?\s*(\d{1,4})(?:\s*[-–]\s*(?:c\.|ca\.)?\s*(\d{1,4}))?',visible,re.I)
        if not displayed or (int(displayed[1]),int(displayed[2] or displayed[1]))!=(lo,hi):
            raise ValueError('Displayed source date differs from structured source date')
        if (lo,hi)!=(c['creation_year_start'],c['creation_year_end']):
            date_note=f"WikiArt records {record['year']}; the existing catalogue retains {c['date_display']}. Exact source object and creator IDs match; both recorded intervals are within the pre-1971 scope. No catalogue dates were rewritten."
    images=soup.select('img[itemprop="image"]')
    if len(images)!=1:raise ValueError('Unique source artwork image absent')
    image=images[0].get('src','');u=urlparse(image)
    if u.scheme!='https' or not re.fullmatch(r'uploads\d*\.wikiart\.org',u.hostname or ''):raise ValueError('Image is outside the approved WikiArt image hosts')
    original=urlparse(record.get('image',''))
    if original.scheme!='https' or not re.fullmatch(r'uploads\d*\.wikiart\.org',original.hostname or '') or original.path!=re.sub(r'!Large\.jpg$', '', u.path, flags=re.I):
        raise ValueError('Rendered image and exact source object image differ')
    if urljoin(rc['url'],record.get('paintingUrl',''))!=rc['url']:raise ValueError('Source object canonical page differs')
    labels=soup.select('.copyright-wrapper .copyright')
    texts=[label.get_text(' ',strip=True) for label in labels]
    text='; '.join(texts) if texts else None
    # Copyright-owner and Fair Use badges are separate simultaneous labels.
    # Keep every label; territorial PD labels do not become global PD claims.
    pd=bool(labels) and all(label.select_one('.copyright-icon-public-domain') and norm(value)=='public domain' for label,value in zip(labels,texts))
    status='public_domain' if pd else ('restricted' if labels else 'unknown')
    info=soup.select_one('.wiki-layout-artwork-info')
    result=dict(source_metadata=record,source_image_url=image,source_year_start=lo,source_year_end=hi,
        source_rights_label=text,source_rights_markup='\n'.join(str(label) for label in labels) if labels else None,
        rights_status=status,license_label=('Public domain (WikiArt label)' if pd else (text or 'Rights not specified by WikiArt')),
        artist_url=artist_url,date_note=date_note,
        source_description=info.get_text(' ',strip=True) if info else None,
        source_links=[dict(text=a.get_text(' ',strip=True),url=urljoin(rc['url'],a['href'])) for a in info.select('article a[href]')] if info else [],
        source_image_variants=[dict(n.attrs) for n in soup.select('.image-variants-container a[data-image-url]')])
    if crosswalk:result['creator_crosswalk']=crosswalk
    if date_review:result['individual_source_date_review']=date_review
    return result


def verify_image(im):
    raw=im['raw'];rc=raw['page_capture'];p=RUN/'metadata/pages'/(im['artwork_id']+'.html');data=p.read_bytes()
    if rc!=json.loads(p.with_suffix('.receipt.json').read_bytes()) or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes'] or rc['requested_url']!=im['before_page']:
        raise ValueError('Pinned source page capture differs')
    source=dict(im,page=im['before_page']);facts=page_facts(source,data,rc)
    if facts!=raw['wikiart_facts'] or raw['user_source_approval']!=approval():raise ValueError('Source facts or separate user approval changed')
    for k in ('source_image_url','rights_status','license_label'):
        if im[k]!=facts[k]:raise ValueError('Source image or actual rights label differs')
    if im['page']!=rc['url'] or im['policy_url']!=POLICY or im['creator_credit']!=im['artist']+'; WikiArt':raise ValueError('Source/credit identity differs')
    if facts['date_note'] and facts['date_note'] not in im['attribution_text']:raise ValueError('Source date difference was omitted')
    review_path=RUN/'visible-source-credit-review.json'
    reviews=json.loads(review_path.read_bytes())['images'] if review_path.exists() else []
    matched=[x for x in reviews if x['artwork_id']==im['artwork_id']]
    if matched:
        if len(matched)!=1 or raw.get('visible_source_credit_review')!=matched[0] or matched[0]['note'] not in im['attribution_text']:
            raise ValueError('Visible reproduction credit review differs')
        keys=['source_image_url']+(['source_sha256','sha256'] if im.get('sha256') else [])
        if any(im[k]!=matched[0][k] for k in keys):raise ValueError('Reviewed source-credit photograph differs')
    elif raw.get('visible_source_credit_review'):raise ValueError('Unreviewed photographic credit qualification')


def research(limit):
    approval();select(limit);fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
    for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
        path=RUN/'selected'/PROVIDER/(c['artwork_id']+'.json')
        if path.exists():verify_image(json.loads(path.read_bytes()));continue
        try:
            proof=c['creator_authorities'][0]
            if not any(x['scheme']=='wikiart-artist' for x in proof['artist_identifiers']):
                qids=[x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']
                if len(qids)==1 and re.fullmatch(r'Q[1-9][0-9]*',qids[0]):fetch.metadata('https://www.wikidata.org/wiki/Special:EntityData/'+qids[0]+'.json')
            data,rc=capture_page(c,fetch);facts=page_facts(c,data,rc)
            if facts['source_year_end']==1970 and re.match(r'(?i)\s*(?:c\.|ca\.)',visible_creation_date(BeautifulSoup(data,'html.parser'))):
                raise ValueError('Approximate source date at the cutoff requires individual scope evidence')
            im=dict(c,before_page=c['page'],page=rc['url'],source_image_url=facts['source_image_url'],rights_status=facts['rights_status'],license_label=facts['license_label'],policy_url=POLICY,
                creator_credit=c['artist']+'; WikiArt',checked_at=rc['at'],raw=dict(page_capture=rc,wikiart_facts=facts,user_source_approval=approval()),
                attribution_text=f"{c['artist']}. {c['title']}. Image source: WikiArt. Source rights label: {facts['source_rights_label'] or 'not specified'}. {rc['url']}. Collected under the user's explicit WikiArt source approval of 6 October 2026; this approval is separate from the source's rights assertion. Full-frame proportional resize and JPEG compression."+(' '+facts['date_note'] if facts['date_note'] else ''))
            verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='source_selected'))
            print('Selected:',c['artist'],c['title'],facts['rights_status'],flush=True)
        except Exception as error:
            core.event(RUN,dict(provider=PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)));print('Held:',c['artist'],c['title'],str(error),flush=True)


def prepare():
    fetch=core.Fetcher(RUN/'metadata/downloads');fetch.defer_long_cooldowns=True
    for p in sorted((RUN/'selected'/PROVIDER).glob('*.json')):
        im=json.loads(p.read_bytes());dest=RUN/'images'/p.name
        if dest.exists():verify_image(json.loads(dest.read_bytes()));continue
        verify_image(im);core.validate_source_image_identity(im)
        with base.connect() as db:
            if db.execute('SELECT primary_media_id FROM artworks WHERE id=%s',(im['artwork_id'],)).fetchone()['primary_media_id']:
                core.event(RUN,dict(provider=PROVIDER,artwork_id=im['artwork_id'],outcome='existing_image_preserved'));continue
        try:
            core.HOSTS.add(urlparse(im['source_image_url']).hostname)
            data,headers=fetch.get(im['source_image_url']);sha=core.sha(data)
            archive=base.ARCHIVE/'source-images'/RUN.name/(im['artwork_id']+'-'+sha[:16]+'.image');core.save_new(archive,data)
            result,width,height,quality=core.compress(data)
            if min(width,height)<50 or max(width,height)<200:raise ValueError('Source image too small for review')
            digest=core.sha(result);path='/assets/artworks/imported/'+RUN.name+'/'+im['artwork_id']+'-'+digest[:16]+'.jpg'
            core.save_new(core.ROOT/'apps/web/public'/path.lstrip('/'),result)
            im.update(path=path,sha256=digest,bytes=len(result),width=width,height=height,jpeg_quality=quality,source_sha256=sha,source_bytes=len(data),source_archive=str(archive),downloaded_at=core.now(),response_headers=headers,
                transform='Full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
            core.save_new(dest,im);core.event(RUN,dict(provider=PROVIDER,artwork_id=im['artwork_id'],outcome='prepared'));print('Prepared:',im['artist'],im['title'],flush=True)
        except Exception as error:
            core.event(RUN,dict(provider=PROVIDER,artwork_id=im['artwork_id'],outcome='download_deferred',reason=str(error)));print('Download held:',im['title'],str(error),flush=True)
    # Only render already prepared records; the Commons preparation path never
    # evaluates or overrides this operation's user-approved source policy.
    base.prepare('contact-sheets-only')


def attach(db,im,target):
    if target!='local':raise ValueError('Only local attachment authorized')
    verify_image(im);chicago.verify_view(im)
    facts=im['raw']['wikiart_facts']
    page=(RUN/'metadata/pages'/(im['artwork_id']+'.html')).read_bytes()
    if facts['source_year_end']==1970 and re.match(r'(?i)\s*(?:c\.|ca\.)',visible_creation_date(BeautifulSoup(page,'html.parser'))):
        raise ValueError('Approximate source date at the cutoff requires individual scope evidence')
    chicago.authority_unchanged(db,im,True)
    result=base.m.original_attach(db,im,target)
    if result=='attached':
        db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s,verified_at=%s,verified_by=%s WHERE id=%s',
            (im['creator_credit'],im['attribution_text'],im['checked_at'] if im['rights_status']=='public_domain' else None,core.ACTOR if im['rights_status']=='public_domain' else None,im['media_id']))
        if im.get('alt_text'):
            db.execute('UPDATE media_assets SET alt_text=%s WHERE id=%s',(im['alt_text'],im['media_id']))
        if im.get('view_label'):
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s) ON CONFLICT(artwork_id,media_id) DO NOTHING',(im['artwork_id'],im['media_id'],im['view_label']))
        db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',
            ('Exact existing WikiArt object and creator IDs, current title/date/version and visual review. Actual source rights label retained. User-approved WikiArt source policy of 6 October 2026 separately recorded; no independent copyright-holder permission asserted. Image-only local attachment.',im['media_id']))
    return result


base.m.attach=attach


def verify():
    for im in base.prepared():verify_image(im);chicago.verify_view(im)
    base.verify();receipt=json.loads((RUN/'apply-receipt.json').read_bytes());attached={x['artwork_id'] for x in receipt['receipts'] if x['result']=='attached'}
    checks=[];held=[]
    for item in json.loads((RUN/'held-source-review.json').read_bytes())['findings']:
        im=json.loads((RUN/'images'/(item['artwork_id']+'.json')).read_bytes())
        if (core.ROOT/'apps/web/public'/im['path'].lstrip('/')).exists() or core.sha(Path(item['private_derivative']).read_bytes())!=item['sha256'] or core.sha(Path(item['source_archive']).read_bytes())!=item['source_sha256']:
            raise ValueError('Held image escaped private storage or evidence changed')
    with base.connect() as db:
        for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
            chicago.authority_unchanged(db,c)
            if c['artwork_id'] not in attached:
                if db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(c['artwork_id'],)).fetchone()['record']!=c['before_record']:raise ValueError('Held artwork changed')
                held.append(c['artwork_id']);continue
            im=json.loads((RUN/'images'/(c['artwork_id']+'.json')).read_bytes())
            row=db.execute('SELECT m.creator_credit,m.attribution_text,m.rights_status,m.verified_at,m.verified_by,e.evidence_json,e.source_checksum FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=%s',(im['media_id'],)).fetchone()
            if any(row[k]!=im[k] for k in ('creator_credit','attribution_text','rights_status')) or row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Complete stored source evidence differs')
            if im['rights_status']!='public_domain' and (row['verified_at'] is not None or row['verified_by'] is not None):raise ValueError('User approval was represented as independent rights verification')
            if im.get('view_label'):
                view=db.execute('SELECT m.alt_text,am.view_label FROM media_assets m JOIN artwork_media am ON am.media_id=m.id WHERE m.id=%s AND am.artwork_id=%s',(im['media_id'],im['artwork_id'])).fetchone()
                if view!=dict(alt_text=im['alt_text'],view_label=im['view_label']):raise ValueError('Qualified image view not preserved')
            elif im.get('alt_text'):
                alt=db.execute('SELECT alt_text FROM media_assets WHERE id=%s',(im['media_id'],)).fetchone()
                if not alt or alt['alt_text']!=im['alt_text']:raise ValueError('Individual source image description not preserved')
            checks.append(im)
        baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=len(checks),artwork_ids=[x['artwork_id'] for x in checks],complete_stored_evidence_verified=True,actual_rights_and_user_approval_separate=True,creator_aliases_authorities_and_holding_evidence_unchanged=True,unchanged_held_artworks=held))
    core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=len(checks)+len(held),attached=len(checks),still_unattached=len(held),rights_status_counts=dict(collections.Counter(x['rights_status'] for x in checks)),baseline_after=baseline,all_catalogue_metadata_and_holdings_preserved=True,production_changed=False,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);p.add_argument('--limit',type=int,default=60);p.add_argument('--run-name',default=RUN.name);p.add_argument('--exclude-run',type=Path,action='append',default=[]);a=p.parse_args()
    if not 1<=a.limit<=60:p.error('Use 1–60 existing artworks per review')
    if not re.fullmatch('local-wikiart-[a-z0-9-]+',a.run_name):p.error('Use a local-wikiart operation name')
    RUN=core.ROOT/'docs/research'/a.run_name;base.RUN=RUN;chicago.RUN=RUN;EXCLUDE_RUNS=[x.resolve() for x in a.exclude_run]
    if a.phase=='research':research(a.limit)
    elif a.phase=='prepare':prepare()
    elif a.phase=='apply':base.apply()
    else:verify()
