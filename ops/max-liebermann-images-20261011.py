#!/usr/bin/env python3
"""Exact-object image research and selected production delivery for 375 works.

The real local database is never connected to. Run each stage explicitly.
"""
import argparse, base64, collections, concurrent.futures, csv, datetime, gzip, hashlib
import importlib.util, io, json, re, subprocess, threading, time, uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote, urlencode
import requests, psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageStat
from google.auth.credentials import Credentials
from google.cloud import storage
from google.api_core.exceptions import PreconditionFailed

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/research/max-liebermann-20261011'
OP = 'max-liebermann-images-20261011'
RUN = ROOT / 'docs/research' / OP
ARCHIVE = Path.home() / 'Library/Application Support/Artline/source-images' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
AID = 'b05c66ac-a834-4677-857a-79ee9c321a08'
ACTOR = 'local-european-research'
PUBLIC = 'https://artlines.org'
LOCKS = collections.defaultdict(threading.Lock)
LAST = {}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + key))
def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n').encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)
def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
def norm(value): return re.sub(r'[^\w]+', '', (value or '').casefold())
def key(url):
    if not url: return ''
    q = re.search(r'wikidata.org/(?:wiki|entity)/(Q\d+)', url)
    if q: return 'wikidata/' + q[1]
    u = urlsplit(url); host = (u.hostname or '').removeprefix('www.'); path = unquote(u.path).rstrip('/')
    for hostpart, pattern, prefix in [
        ('hamburger-kunsthalle', r'/objekt/([^/]+)', 'hamburg/'),
        ('smb.museum', r'/object/(?:obj-)?(\d+)', 'berlin/'),
        ('pinakothek.de', r'/artwork/([^/]+)', 'pinakothek/'),
        ('albertina.at', r'/objects/(\d+)', 'albertina/'),
        ('artic.edu', r'/artworks/(\d+)', 'aic/'),
        ('metmuseum.org', r'/collection/search/(\d+)', 'met/'),
        ('nga.gov', r'(?:art-object-page\.|/artworks/)(\d+)', 'nga/')]:
        m = re.search(pattern, path)
        if hostpart in host and m:
            part = m[1]
            if prefix == 'hamburg/': part = re.sub(r'^HK-', '', part, flags=re.I).lower()
            return prefix + part
    return host + path

def connect(write=False):
    raw = subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'], text=True).strip()
    fields = psycopg.conninfo.conninfo_to_dict(raw)
    fields.update(host='127.0.0.1', port='55448', sslmode='disable')
    return psycopg.connect(**fields, row_factory=dict_row,
        options='-c default_transaction_read_only=' + ('off' if write else 'on') + ' -c statement_timeout=60000')

def snapshots(db, ids):
    return {r['artwork']['id']: r for r in db.execute("""SELECT to_jsonb(a) artwork,
      coalesce((SELECT jsonb_agg(to_jsonb(x) ORDER BY artist_id,attribution_role) FROM artwork_artists x WHERE x.artwork_id=a.id),'[]') creators,
      coalesce((SELECT jsonb_agg(to_jsonb(x) ORDER BY id) FROM artwork_location_assertions x WHERE x.artwork_id=a.id),'[]') holdings,
      coalesce((SELECT jsonb_agg(to_jsonb(x) ORDER BY media_id) FROM artwork_media x WHERE x.artwork_id=a.id),'[]') attachments
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""", (ids,)).fetchall()}

def fetch(url):
    dest = RUN / 'captures' / (sha(url.encode()) + '.json')
    body = dest.with_suffix('.body.gz')
    if dest.exists():
        receipt = load(dest); body=Path(receipt['body_path']) if receipt.get('body_path') else body
        raw = gzip.decompress(body.read_bytes()); assert sha(raw) == receipt['sha256']
    else:
        host = urlsplit(url).netloc; hold = RUN / 'access-holds' / (host + '.json')
        with LOCKS[host]:
            if hold.exists(): raise RuntimeError('Access hold: ' + host)
            time.sleep(max(0, LAST.get(host, 0) + .25 - time.monotonic())); LAST[host] = time.monotonic()
            r = requests.get(url, timeout=(15,45), headers={'User-Agent':'Artline selected Max Liebermann image research'})
            raw = r.content
            receipt = dict(url=url, final_url=r.url, status=r.status_code, retrieved_at=now(), sha256=sha(raw), bytes=len(raw), content_type=r.headers.get('Content-Type'))
            if receipt['content_type'] and receipt['content_type'].startswith('image/'):
                body=ARCHIVE/'captures'/body.name;body.parent.mkdir(parents=True,exist_ok=True);receipt['body_path']=str(body)
            save(dest, receipt); body.write_bytes(gzip.compress(raw, mtime=0))
            if r.status_code in (401,403,429): save(hold, receipt)
    if receipt['status'] != 200: raise RuntimeError('HTTP ' + str(receipt['status']) + ': ' + url)
    return raw, receipt

def baseline():
    assert not (RUN/'baseline.json.gz').exists(), 'Baseline already frozen'
    rows=[]; pages=[]; cursor=None
    for _ in range(40):
        params={'limit':50}
        if cursor: params['cursor']=cursor
        r=requests.get(PUBLIC+'/api/backend/v1/artists/max-liebermann-q158062/works',params=params,timeout=45);r.raise_for_status(); data=r.json()
        rows += data['items']; pages.append(dict(url=r.url,data=data))
        nxt=data.get('next_cursor')
        if not nxt: break
        assert nxt != cursor; cursor=nxt
    else: raise RuntimeError('Pagination bound')
    requested={r['id'] for pg in load(SOURCE/'public-verification-pages.json.gz') for r in pg['data']['items'] if r['work_type'] in ['painting','drawing']}
    selected=[r for r in rows if r['id'] in requested]
    assert collections.Counter(x['work_type'] for x in selected) == {'painting':104,'drawing':271}
    assert len({x['id'] for x in selected}) == 375
    save(RUN/'baseline.json.gz',dict(at=now(),works=selected,all_artist_count=len(rows)))
    save(RUN/'baseline-public-pages.json.gz',pages)
    with connect() as db, db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SELECT display_name FROM artists WHERE id=%s',(AID,)).fetchone()['display_name']=='Max Liebermann'
        states=snapshots(db,[x['id'] for x in selected]); assert len(states)==375
        assert all(any(c['artist_id']==AID for c in s['creators']) for s in states.values())
    save(BACKUP/'baseline.json.gz',states)
    print('Frozen',len(selected),'records; existing images',sum(bool(x['media_url']) for x in selected),flush=True)

def source_soup(r):
    raw=gzip.decompress((ROOT/r['receipt']['body_path']).read_bytes())
    assert sha(raw)==r['receipt']['sha256']
    return BeautifulSoup(raw,'html.parser')

def date_evidence(w, r):
    override_path=RUN/'date-review-overrides.json'
    if override_path.exists():
        override=load(override_path).get(w['id'])
        if override:return override
    if w.get('creation_year_end') is not None and w['creation_year_end']<=1955:
        return dict(eligible=True,basis='Existing object-specific creation date/range ends by 1955; catalogue values preserved.',literal=w['date_display'])
    literal=str(r.get('date') or '')
    years=[int(v) for v in re.findall(r'(?<!\d)(\d{4})(?!\d)',literal)]
    # A lower bound alone ("after 1915") cannot establish an upper bound.
    lower_bound=bool(re.search(r'\b(?:nach|after|ab|since)\b',literal,re.I))
    if years and not lower_bound and all(1500<=y<=1955 for y in years):
        return dict(eligible=True,basis='Literal native artwork date, independently retained as image evidence; unknown catalogue fields preserved.',literal=literal)
    if re.fullmatch(r'19\.\s*Jahrhundert',literal):
        return dict(eligible=True,basis='Native source explicitly dates this object to the nineteenth century; no numeric creation year is invented.',literal=literal)
    # A documented museum acquisition is a terminus ante quem, not an invented creation year.
    acquisition = r.get('fields',{}).get('Acquisition') or r.get('fields',{}).get('Provenance') or r.get('raw',{}).get('acq_note') or ''
    match=re.search(r'(?:Acquired|Erworben)\s+(?:in\s+)?(1[89]\d{2}|19[0-4]\d|195[0-5])\b', acquisition, re.I)
    if not match:
        match=re.search(r'(?:Erworben von Herrn Soyka |vor )(1[89]\d{2}|19[0-4]\d|195[0-5])\b',acquisition,re.I)
    if match:
        return dict(eligible=True,basis='Exact museum acquisition predates 1956 and bounds this physical object; creation date remains unknown.',literal=acquisition,documented_before=int(match[1]))
    return dict(eligible=False,basis='Object creation date unresolved; artist lifespan alone was not used as eligibility.',literal=literal)

def native_candidate(w, r):
    provider=r['source']; images=[]; license_label=None; license_url=None; rights=None; credit=provider; policy=None
    if provider=='Staatliche Museen zu Berlin':
        for im in r['raw'].get('images',[]):
            if im.get('license')=='Public Domain Mark 1.0' and im.get('xl_path'):
                images.append(dict(url='https://search.smb.museum/media'+im['xl_path'],native=im))
        if images:
            license_label='Public Domain Mark 1.0'; license_url='https://creativecommons.org/publicdomain/mark/1.0/';rights='public_domain'
            credit='Staatliche Museen zu Berlin, '+r['raw']['org_unit']+' / '+str(images[0]['native'].get('photographer') or '')
    elif provider=='Städel Museum':
        soup=source_soup(r); tag=soup.select_one('meta[property="og:image"]')
        if tag: images=[dict(url=tag['content'])]
        if r['fields'].get('Picture Copyright')=='Public Domain':
            license_label='Public Domain';license_url='https://creativecommons.org/publicdomain/mark/1.0/';rights='public_domain';policy='https://sammlung.staedelmuseum.de/de/konzept'
        credit=r['fields'].get('Creditline') or provider
    elif provider=='ALBERTINA':
        soup=source_soup(r);tag=soup.select_one('a.media-info[href*="download"]')
        if tag: images=[dict(url=urljoin(r['source_url'],tag['href']))]
        if soup.select_one('img[src="/images/icons/publicdomain.png"]') and not re.search(r'Dauerleihgabe|permanent loan', r['fields'].get('Provenance',''),re.I):
            license_label='Public Domain — ALBERTINA free download up to 1200 pixels';license_url='https://creativecommons.org/publicdomain/mark/1.0/';rights='public_domain';policy='https://www.albertina.at/en/research/image-reproduction-services/'
        credit='ALBERTINA, Wien'
    elif provider=='Bavarian State Painting Collections':
        soup=source_soup(r);tag=soup.select_one('a.artwork__action.action--download');lic=soup.select_one('a.artwork__action.action--creativecommons')
        if tag: images=[dict(url=tag['href'])]
        if lic and '/by-sa/' in lic['href']:
            license_label=lic.get_text(' ',strip=True);license_url=lic['href'];rights='cc_by_sa'
        credit='Bayerische Staatsgemäldesammlungen – Neue Pinakothek München'
    elif provider=='Hamburger Kunsthalle':
        images=[dict(url=url) for url in r.get('image_urls',[]) if not re.search(r'verso',url,re.I)]
        credit='; '.join(x for x in r['fields']['sidebar'] if re.search('Foto:|ARTOTHEK',x)) or provider
        license_label='Museum/ARTOTHEK credit; commercial reuse clearance not established'
    elif provider=='Art Institute of Chicago':
        raw=r['raw']
        if raw.get('image_id'): images=[dict(url='https://www.artic.edu/iiif/2/'+raw['image_id']+'/full/1200,/0/default.jpg')]
        if raw.get('is_public_domain'):
            license_label='CC0 — Art Institute of Chicago Open Access';license_url='https://creativecommons.org/publicdomain/zero/1.0/';rights='cc0'
    elif provider=='Rijksmuseum':
        import xml.etree.ElementTree as ET
        root=ET.fromstring(r['source_xml']);ns={'edm':'http://www.europeana.eu/schemas/edm/'};attr='{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'
        tag=root.find('.//edm:isShownBy',ns);lic=root.find('.//edm:rights',ns)
        if tag is not None:images=[dict(url=tag.attrib[attr])]
        if lic is not None and '/publicdomain/' in lic.attrib[attr]:
            license_url=lic.attrib[attr];license_label='Rijksmuseum '+license_url;rights='public_domain' if '/mark/' in license_url else 'cc0'
    elif provider=='WikiArt':
        if r.get('image_url'): images=[dict(url=r['image_url'])]
        license_label=r.get('rights_label') or 'Unknown';rights=r.get('page',{}).get('rights_status') or 'unknown';policy='https://www.wikiart.org/en/terms-of-use'
    elif provider=='Museo Nacional Thyssen-Bornemisza':
        soup=source_soup(r);tag=soup.select_one('meta[property="og:image"]')
        if tag:images=[dict(url=tag['content'])]
        license_label='Museum image; reuse terms require review'
    if not images:return None
    de=date_evidence(w,r)
    return dict(artwork_id=w['id'],title=w['title'],work_type=w['work_type'],provider=provider,source_url=r['source_url'],source_id=r.get('source_id'),source_receipt=r.get('receipt'),image_url=images[0]['url'],image_alternatives=images,license_label=license_label,license_url=license_url,rights_status=rights,credit=credit,policy_url=policy or license_url,date_evidence=de,eligible=bool(rights) and de['eligible'],identity_confidence=.99,identity_basis='Exact native source object linked by the catalogue citation or reviewed source register; source object identifier and inventory preserved.',hold_reason=None if bool(rights) and de['eligible'] else 'date_review' if not de['eligible'] else 'source_reuse_permission_review',user_source_approval='AGENTS.md / ARTLINE_IMAGE_USE.md: WikiArt approved 6 October 2026' if provider=='WikiArt' else None)

def select():
    works=load(RUN/'baseline.json.gz')['works'];missing=[w for w in works if not w['media_url']]
    records=[]
    for name in ['hamburg-records.json','berlin-records.json','staedel-records.json','albertina-records.json','pinakothek-thyssen-records.json','wikiart-records.json','us-api-records.json','rijks-records.json']:
        records+=load(SOURCE/name)
    bykey=collections.defaultdict(list)
    for r in records:
        if 'error' not in r:bykey[key(r['source_url'])].append(r)
    with (SOURCE/'source-records.csv').open(encoding='utf-8-sig',newline='')as f:register=list(csv.DictReader(f))
    byid=collections.defaultdict(list)
    for r in register:
        for aid in re.findall(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',r['artline_ids']):byid[aid]+=bykey[key(r['source_url'])]
    candidates=[];gaps=[];wd=load(SOURCE/'wikidata-records.json');wdkey=collections.defaultdict(list)
    for r in wd:
        for url in [r['source_url']]+r['described_at']:wdkey[key(url)].append(r)
    commons=[]
    for w in missing:
        matches={key(r['source_url']):r for r in byid[w['id']]}
        for c in w['citations']:
            for r in bykey[key(c['source_url'])]:matches[key(r['source_url'])]=r
            for q in wdkey[key(c['source_url'])]:
                for described in q['described_at']:
                    for r in bykey[key(described)]:matches[key(r['source_url'])]=r
        found=[]
        for r in matches.values():
            candidate=native_candidate(w,r)
            if candidate:found.append(candidate)
        candidates+=found
        links={key(c['source_url']) for c in w['citations']}|set(matches)
        qs={r['source_id']:r for k in links for r in wdkey[k]}
        for r in qs.values():
            for url in r['image_urls']:
                filename=unquote(url.split('Special:FilePath/')[-1])
                commons.append(dict(artwork_id=w['id'],title=w['title'],work_type=w['work_type'],filename=filename,qid=r['source_id'],wikidata=r,date_evidence=date_evidence(w,dict(date='; '.join(r['dates']))),identity_basis='Exact Wikidata item from the catalogue citation or exact native museum described-at URL; P18 file retained for file-level identity and rights review.'))
        gaps.append(dict(artwork_id=w['id'],title=w['title'],work_type=w['work_type'],native_candidates=len(found),native_eligible=sum(c['eligible'] for c in found),wikidata_image_leads=sum(len(r['image_urls']) for r in qs.values())))
    save(RUN/'native-candidates.json.gz',candidates);save(RUN/'commons-leads.json.gz',commons);save(RUN/'discovery-coverage.json',gaps)
    print('Native',len(candidates),'eligible',sum(x['eligible'] for x in candidates),'Commons leads',len(commons),flush=True)
    print(collections.Counter((x['provider'],x['hold_reason']) for x in candidates),flush=True)

def commons():
    leads=load(RUN/'commons-leads.json.gz');out=[]
    for i,lead in enumerate(leads):
        url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',format='json',titles='File:'+lead['filename'],prop='imageinfo',iiprop='url|extmetadata|size|sha1',iiurlwidth=1200))
        try:
            raw,receipt=fetch(url);pages=json.loads(raw)['query']['pages'];page=next(iter(pages.values()));im=page['imageinfo'][0];ext=im.get('extmetadata',{})
            def value(k):return BeautifulSoup(ext.get(k,{}).get('value',''),'html.parser').get_text(' ',strip=True)
            label=value('LicenseShortName');lic=value('LicenseUrl');rights='cc0' if 'CC0' in label else 'cc_by_sa' if label.startswith('CC BY-SA') else 'cc_by' if label.startswith('CC BY') else 'public_domain' if label in ['Public domain','Public Domain','PD'] else None
            c=dict(lead,provider='Wikimedia Commons',source_url=im['descriptionurl'],source_id=str(page['pageid']),source_receipt=receipt,image_url=im.get('thumburl')or im['url'],license_label=label,license_url=lic or ('https://creativecommons.org/publicdomain/mark/1.0/' if rights=='public_domain' else None),rights_status=rights,credit='; '.join(x for x in [value('Artist'),value('Credit'),value('Attribution')] if x),file_metadata=page,identity_confidence=.97,eligible=bool(rights) and lead['date_evidence']['eligible'],hold_reason=None if bool(rights) and lead['date_evidence']['eligible'] else 'date_review' if not lead['date_evidence']['eligible'] else 'source_reuse_permission_review')
            # Italian custodian issues are reviewed independently; do not auto-clear.
            if any('Galleria d’Arte Moderna' in n or "Galleria d'Arte Moderna" in n for n in lead['wikidata']['collections']):c.update(eligible=False,hold_reason='Italian_custodian_clearance_review')
            out.append(c)
        except Exception as e:out.append(dict(lead,eligible=False,error=str(e)))
        if (i+1)%20==0:print('Commons',i+1,'/',len(leads),flush=True)
    save(RUN/'commons-candidates.json.gz',out)
    print('Commons candidates',len(out),'eligible',sum(x['eligible'] for x in out),flush=True)

def commons_retry():
    """Resume after the logged rate-limit backoff using a few batched requests."""
    old=load(RUN/'commons-candidates.json.gz');save(RUN/'commons-candidates-first-pass.json.gz',old)
    leads=load(RUN/'commons-leads.json.gz');works={w['id']:w for w in load(RUN/'baseline.json.gz')['works']}
    w=works['df9fb453-14cc-438f-8267-d65f906a514f'];q=next(r for r in load(SOURCE/'wikidata-records.json')if r['source_id']=='Q19905225')
    assert w['accession_number'] in q['accessions'] and w['title']==q['title']
    for image in q['image_urls']:
        leads.append(dict(artwork_id=w['id'],title=w['title'],work_type=w['work_type'],filename=unquote(image.split('Special:FilePath/')[-1]),qid=q['source_id'],wikidata=q,date_evidence=date_evidence(w,dict(date='; '.join(q['dates']))),identity_basis='Exact Met inventory '+w['accession_number']+', creator, title, 1904 date and holding collection agree with the Wikidata item; P18 file reviewed separately.'))
    resolved={x['filename']:x for x in old if not x.get('error')};pending=list(dict.fromkeys(x['filename']for x in leads if x['filename']not in resolved));byfile={}
    for start in range(0,len(pending),5):
        names=pending[start:start+5]
        url='https://commons.wikimedia.org/w/api.php?'+urlencode(dict(action='query',format='json',titles='|'.join('File:'+n for n in names),prop='imageinfo',iiprop='url|extmetadata|size|sha1',iiurlwidth=1200))
        try:
            raw,receipt=fetch(url);pages=json.loads(raw)['query']['pages']
            for page in pages.values():byfile[page['title'].removeprefix('File:').replace('_',' ')]=(page,receipt)
            print('Commons batch',start+len(names),'/',len(pending),flush=True)
        except Exception as e:print('Commons retry stopped',str(e),flush=True);break
        time.sleep(5)
    file_targets=collections.defaultdict(set)
    for lead in leads:file_targets[lead['filename']].add(lead['artwork_id'])
    out=[]
    for lead in leads:
        if lead['filename'] in resolved:
            c=dict(resolved[lead['filename']],**lead)
        else:
            data=byfile.get(lead['filename'].replace('_',' '))
            if not data:out.append(dict(lead,eligible=False,error='Commons metadata unresolved after bounded rate-limit retry'));continue
            page,receipt=data
            if not page.get('imageinfo'):out.append(dict(lead,eligible=False,error='No Commons file imageinfo'));continue
            im=page['imageinfo'][0];ext=im.get('extmetadata',{})
            def value(k):return BeautifulSoup(ext.get(k,{}).get('value',''),'html.parser').get_text(' ',strip=True)
            label=value('LicenseShortName');lic=value('LicenseUrl');rights='cc0'if 'CC0'in label else 'cc_by_sa'if label.startswith('CC BY-SA')else 'cc_by'if label.startswith('CC BY')else 'public_domain'if label in ['Public domain','Public Domain','PD']else None
            c=dict(lead,provider='Wikimedia Commons',source_url=im['descriptionurl'],source_id=str(page['pageid']),source_receipt=receipt,image_url=im.get('thumburl')or im['url'],license_label=label,license_url=lic or ('https://creativecommons.org/publicdomain/mark/1.0/'if rights=='public_domain'else None),rights_status=rights,credit='; '.join(x for x in [value('Artist'),value('Credit'),value('Attribution')]if x),file_metadata=page,identity_confidence=.97,eligible=bool(rights)and lead['date_evidence']['eligible'],hold_reason=None if bool(rights)and lead['date_evidence']['eligible']else 'source_rights_or_date_review')
        if len(file_targets[lead['filename']])>1:
            c.update(eligible=False,hold_reason='Same Commons file maps to distinct museum objects; version identity needs individual review',identity_confidence=.5)
        out.append(c)
    save(RUN/'commons-candidates.json.gz',out);print('Commons eligible',sum(x['eligible']for x in out),flush=True)

def choose():
    candidates=load(RUN/'native-candidates.json.gz')
    if (RUN/'commons-candidates.json.gz').exists():candidates+=load(RUN/'commons-candidates.json.gz')
    if (RUN/'additional-candidates.json.gz').exists():candidates+=load(RUN/'additional-candidates.json.gz')
    overrides=load(RUN/'date-review-overrides.json')if (RUN/'date-review-overrides.json').exists()else{}
    for c in candidates:
        if c['artwork_id']in overrides:c['date_evidence']=overrides[c['artwork_id']]
    rank={'WikiArt':0,'Wikimedia Commons':3}
    selected={}
    for c in sorted(candidates,key=lambda c:rank.get(c.get('provider'),1)):
        if c['eligible'] and c['artwork_id'] not in selected:selected[c['artwork_id']]=c
    save(RUN/'selection.json.gz',dict(at=now(),records=list(selected.values())))
    print('Selected',len(selected),dict(collections.Counter(c['provider'] for c in selected.values())),flush=True)

def prepare():
    selected=load(RUN/'selection.json.gz')['records']
    def one(c):
        aid=c['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
        if dest.exists():
            previous=load(dest)
            if previous.get('source_image_url')==c['image_url']:return previous
            save(RUN/'superseded-preparation'/(aid+'-'+sha(json.dumps(previous,sort_keys=True).encode())[:12]+'.json'),previous)
        out=dict(artwork_id=aid,title=c['title'],provider=c['provider'],source_image_url=c['image_url'])
        try:
            archive=ARCHIVE/(aid+'.source'); receipt=archive.with_suffix('.json')
            if receipt.exists():
                rc=load(receipt);assert rc['url']==c['image_url'],'Source changed; preserve original and review explicitly'
                raw=archive.read_bytes();assert sha(raw)==rc['sha256']
            else:
                raw,rc=fetch(c['image_url']);assert len(raw)<30000000 and rc['content_type'].startswith('image/')
                archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(raw);save(receipt,rc)
            with Image.open(io.BytesIO(raw))as original:
                assert original.width*original.height<60000000;original.load();im=ImageOps.exif_transpose(original).convert('RGB')
            original_size=im.size;assert min(im.size)>=80 and max(ImageStat.Stat(im).stddev)>3
            if c['provider']=='ALBERTINA':assert max(im.size)<=1200,'Beyond free image size'
            output=None
            for edge in [1500,1300,1100,900,750,600]:
                im.thumbnail((edge,edge),Image.Resampling.LANCZOS)
                for quality in [90,85,80,75,70,65,60]:
                    buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                    if buf.tell()<=100000:output=buf.getvalue();break
                if output:break
            assert output
            digest=sha(output);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:12]+'.jpg';file=ROOT/'apps/web/public'/path.lstrip('/')
            file.parent.mkdir(parents=True,exist_ok=True)
            if file.exists():assert file.read_bytes()==output
            else:file.write_bytes(output)
            out.update(state='prepared',path=str(file),storage_path=path,sha256=digest,bytes=len(output),width=im.width,height=im.height,source_size=original_size,source_sha256=sha(raw),source_archive=str(archive),download=rc,media_id=uid('media/'+aid+'/'+digest))
        except Exception as e:out.update(state='held',reason=str(e))
        save(dest,out);return out
    outcomes=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,row in enumerate(pool.map(one,selected),1):
            outcomes.append(row)
            if i%30==0:print('Prepared',i,'/',len(selected),flush=True)
    save(RUN/'preparation.json.gz',outcomes);print(dict(collections.Counter(x['state'] for x in outcomes)),flush=True)

def sheets():
    rows=[r for r in load(RUN/'preparation.json.gz')if r['state']=='prepared'];byid={r['artwork_id']:r for r in load(RUN/'selection.json.gz')['records']}
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for offset in range(0,len(rows),30):
        group=rows[offset:offset+30];canvas=Image.new('RGB',(1800,1800),'#eeeeee');draw=ImageDraw.Draw(canvas)
        for j,r in enumerate(group):
            x=j%6*300;y=j//6*360
            with Image.open(r['path'])as im:im.thumbnail((290,282));canvas.paste(im,(x+(300-im.width)//2,y+(282-im.height)//2))
            c=byid[r['artwork_id']]
            for line,text in enumerate([str(offset+j+1)+'. '+c['title'][:33],str(c['source_id'])+' '+c['provider'][:18],str(c['date_evidence'].get('literal',''))[:34]]):draw.text((x+3,y+287+line*20),text,font=font,fill='black')
        path=ARCHIVE/('sheet-'+str(offset//30).zfill(2)+'.jpg');canvas.save(path,quality=93)
        save(RUN/'sheets'/(str(offset//30).zfill(2)+'.json'),dict(path=str(path),sha256=sha(path.read_bytes()),items=[dict(artwork_id=r['artwork_id'],title=r['title'],sha256=r['sha256']) for r in group]))
    print('Contact sheets',(len(rows)+29)//30,flush=True)

def preflight():
    review=load(RUN/'visual-review.json');selected={r['artwork_id']:r for r in load(RUN/'selection.json.gz')['records']};rows=[]
    for aid,decision in review['items'].items():
        if decision['decision']!='accept':continue
        c=selected[aid];im=load(RUN/'prepared'/(aid+'.json'))
        assert c['eligible'] and c['date_evidence']['eligible'] and im['state']=='prepared'
        assert im['sha256']==decision['sha256']==sha(Path(im['path']).read_bytes()) and im['bytes']<=100000
        rows.append(dict(candidate=c,image=im,visual_review=decision))
    ids=[r['candidate']['artwork_id'] for r in rows];assert ids and len(set(ids))==len(ids)
    baseline=load(BACKUP/'baseline.json.gz')
    with connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SELECT 1 FROM editor_accounts WHERE user_id=%s',(ACTOR,)).fetchone()
        before=snapshots(db,ids)
        for aid in ids:
            assert before[aid]==baseline[aid], 'Concurrent drift: '+aid
            assert before[aid]['artwork']['primary_media_id'] is None and before[aid]['artwork']['status']!='archived'
    plan=dict(at=now(),rows=rows,before=before,operation=OP,visual_review=review['method'])
    save(BACKUP/'reviewed-plan.json.gz',plan);save(RUN/'plan-pin.json',dict(at=now(),count=len(rows),sha256=sha((BACKUP/'reviewed-plan.json.gz').read_bytes())))
    print('Pinned production image plan',len(rows),flush=True)

def pinned():
    assert sha((BACKUP/'reviewed-plan.json.gz').read_bytes())==load(RUN/'plan-pin.json')['sha256']
    return load(BACKUP/'reviewed-plan.json.gz')

class GcloudCredentials(Credentials):
    def refresh(self,request):
        self.token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip()
        self.expiry=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)+datetime.timedelta(minutes=45)

def upload():
    p=pinned();bucket=storage.Client(project='artline-508319',credentials=GcloudCredentials()).bucket('artline-508319-images')
    def one(row):
        im=row['image'];aid=im['artwork_id'];dest=RUN/'uploads'/(aid+'.json')
        if dest.exists():
            rc=load(dest);assert rc['sha256']==im['sha256'];return rc
        raw=Path(im['path']).read_bytes();assert sha(raw)==im['sha256'] and len(raw)<=100000
        blob=bucket.blob(im['storage_path'].lstrip('/'));blob.cache_control='public,max-age=31536000,immutable';blob.metadata=dict(sha256=sha(raw),operation=OP,artwork_id=aid)
        try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except PreconditionFailed:blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        response=requests.get(PUBLIC+im['storage_path'],timeout=(15,45));response.raise_for_status();assert sha(response.content)==im['sha256']
        rc=dict(at=now(),artwork_id=aid,sha256=im['sha256'],generation=str(blob.generation),public_bytes_verified=True);save(dest,rc);return rc
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for i,_ in enumerate(pool.map(one,p['rows']),1):
            if i%40==0:print('Uploaded and verified',i,'/',len(p['rows']),flush=True)
    print('Public files verified',len(p['rows']),flush=True)

def apply():
    p=pinned();assert not (RUN/'applied.json').exists();ids=[r['candidate']['artwork_id'] for r in p['rows']]
    backups=json.loads(subprocess.check_output(['gcloud','sql','backups','list','--instance=artline-postgres','--project=artline-508319','--filter=description='+OP,'--limit=1','--format=json'],text=True))
    assert backups and backups[0]['status']=='SUCCESSFUL';save(BACKUP/'cloud-sql-backup.json',backups[0])
    for row in p['rows']:
        rc=load(RUN/'uploads'/(row['candidate']['artwork_id']+'.json'));assert rc['public_bytes_verified'] and rc['sha256']==row['image']['sha256']
    with connect(True)as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='30s'")
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall()
        before=snapshots(db,ids);assert before==p['before'],'Concurrent catalogue drift after preflight'
        save(BACKUP/'transaction-before.json.gz',before)
        providers={r['candidate']['provider']:r['candidate']['source_url'] for r in p['rows']}
        for provider,url in providers.items():
            slug=OP+'-'+re.sub('[^a-z0-9]+','-',provider.lower()).strip('-')
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page',%s)",(uid('source/'+provider),slug,provider+' — Liebermann image evidence',url))
        for row in p['rows']:
            c=row['candidate'];im=row['image'];aid=c['artwork_id'];sid=uid('source/'+c['provider'])
            credit=c['credit'];attribution=credit+'. '+str(c['license_label'])+'. Full source frame preserved; proportional resize and JPEG compression.'
            if c['rights_status']=='cc_by_sa':attribution+=' Derivative available under the same '+c['license_label']+' licence.'
            policy=c.get('policy_url')or c.get('license_url')or c['source_url']
            # Rijksmuseum's source XML retains the historic HTTP CC URL. The
            # evidence column requires HTTPS; retain the literal in candidate.
            if policy.startswith('http://creativecommons.org/'):
                policy='https://'+policy.removeprefix('http://')
            assert policy.startswith('https://'), 'Unreviewed policy URL: '+policy
            db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
              VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',
              (im['media_id'],im['storage_path'],c['source_url'],c['provider'],im['width'],im['height'],im['bytes'],im['sha256'],c['title']+' — Max Liebermann',c['rights_status'],c['license_label'],c.get('license_url'),credit,attribution,im['download']['retrieved_at'],ACTOR))
            evidence=dict(candidate=c,prepared_image=im,visual_review=row['visual_review'],plan_sha256=load(RUN/'plan-pin.json')['sha256'],scope='Image only; creator, dates, holdings and publication state preserved. No current-display claim.')
            db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,now(),%s)''',
              (im['media_id'],sid,str(c['source_id']),c.get('source_receipt',{}).get('sha256') or sha(json.dumps(c,sort_keys=True).encode()),c['image_url'],policy,'Exact object and source image label; '+c['identity_basis']+' '+c['date_evidence']['basis'],OP,Jsonb(evidence)))
            order=db.execute('SELECT coalesce(max(sort_order),-1)+1 n FROM artwork_media WHERE artwork_id=%s',(aid,)).fetchone()['n']
            db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,%s,%s)',(aid,im['media_id'],order,row['visual_review'].get('view_label','Full source reproduction')))
            cur=db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],ACTOR,aid));assert cur.rowcount==1
            db.execute("INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,'image_identity',%s,%s,%s,%s,now(),%s)",(uid('citation/'+aid),aid,sid,str(c['source_id']),c['source_url'],json.dumps(dict(operation=OP,identity_confidence=c['identity_confidence'],identity_basis=c['identity_basis'],date_evidence=c['date_evidence'],plan_sha256=load(RUN/'plan-pin.json')['sha256']),ensure_ascii=False),ACTOR))
        after=snapshots(db,ids);allowed={'primary_media_id','revision','updated_at','updated_by'}
        for row in p['rows']:
            aid=row['candidate']['artwork_id'];a=after[aid];b=before[aid]
            assert {k:v for k,v in a['artwork'].items()if k not in allowed}=={k:v for k,v in b['artwork'].items()if k not in allowed}
            assert a['holdings']==b['holdings'] and a['creators']==b['creators'] and len(a['attachments'])==len(b['attachments'])+1
            assert a['artwork']['primary_media_id']==row['image']['media_id']
        save(BACKUP/'transaction-after.json.gz',after)
    save(RUN/'applied.json',dict(at=now(),artwork_ids=ids,new_images=len(ids),backup_id=backups[0]['id'],local_database_connected=False,metadata_holdings_creators_status_preserved=True))
    print('Attached',len(ids),'production images',flush=True)

def verify():
    p=pinned();a=load(RUN/'applied.json');baseline=load(BACKUP/'baseline.json.gz');ids=list(baseline)
    with connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');after=snapshots(db,ids)
        expected=load(BACKUP/'transaction-after.json.gz')
        for aid in ids:assert after[aid]==expected.get(aid,baseline[aid]),'Catalogue drift: '+aid
        media={r['id']:r for r in db.execute('SELECT id::text,checksum_sha256,byte_size,license_label FROM media_assets WHERE id=ANY(%s::uuid[])',([r['image']['media_id']for r in p['rows']],)).fetchall()}
        for row in p['rows']:assert media[row['image']['media_id']]['checksum_sha256']==row['image']['sha256'] and media[row['image']['media_id']]['byte_size']<=100000
    rows=[];pages=[];cursor=None
    for _ in range(40):
        params={'limit':50}
        if cursor:params['cursor']=cursor
        r=requests.get(PUBLIC+'/api/backend/v1/artists/max-liebermann-q158062/works',params=params,timeout=(15,45));r.raise_for_status();d=r.json();rows+=d['items'];pages.append(dict(url=r.url,status=r.status_code,data=d))
        nxt=d.get('next_cursor')
        if not nxt:break
        assert nxt!=cursor;cursor=nxt
    else:raise RuntimeError('Pagination bound')
    byid={x['id']:x for x in rows};assert set(ids)<=set(byid)
    for row in p['rows']:
        item=byid[row['candidate']['artwork_id']];assert item['media_url'].endswith(row['image']['storage_path']) and item['status']==baseline[item['id']]['artwork']['status']
    save(RUN/'verified-public-pages.json.gz',pages)
    proof=dict(at=now(),scope=375,new_images=a['new_images'],total_with_images=sum(bool(byid[aid]['media_url'])for aid in ids),by_type={typ:dict(total=sum(byid[aid]['work_type']==typ for aid in ids),illustrated=sum(byid[aid]['work_type']==typ and bool(byid[aid]['media_url'])for aid in ids))for typ in ['painting','drawing']},api_pages=len(pages),all_original_images_preserved=True,metadata_holdings_creators_status_preserved=True,local_database_connected=False)
    save(RUN/'verification.json',proof);print(json.dumps(proof),flush=True)

def report():
    works=load(RUN/'baseline.json.gz')['works'];candidates=load(RUN/'native-candidates.json.gz')+load(RUN/'commons-candidates.json.gz')
    if (RUN/'additional-candidates.json.gz').exists():candidates+=load(RUN/'additional-candidates.json.gz')
    followup=RUN/'followup'
    if (followup/'commons-candidates.json.gz').exists():candidates+=load(followup/'commons-candidates.json.gz')
    byid=collections.defaultdict(list)
    for c in candidates:byid[c['artwork_id']].append(c)
    applied=load(RUN/'applied.json') if (RUN/'applied.json').exists()else {'artwork_ids':[]};selected={x['artwork_id']:x for x in load(RUN/'selection.json.gz')['records']}
    applied_ids=set(applied['artwork_ids'])
    if (followup/'applied.json').exists():applied_ids.update(load(followup/'applied.json')['artwork_ids'])
    if (followup/'selection.json.gz').exists():selected.update({x['artwork_id']:x for x in load(followup/'selection.json.gz')['records']})
    findings=load(RUN/'unresolved-findings.json')if (RUN/'unresolved-findings.json').exists()else{}
    rows=[]
    for w in works:
        cs=byid[w['id']];c=selected.get(w['id'])or next((x for x in cs if x.get('image_url')),cs[0]if cs else {})
        prepared=RUN/'prepared'/(w['id']+'.json');im=load(prepared)if prepared.exists()else{}
        if (followup/'prepared'/(w['id']+'.json')).exists():im=load(followup/'prepared'/(w['id']+'.json'))
        decision='existing_image_preserved'if w['media_url']else 'image_attached'if w['id']in applied_ids else 'image_download_held'if im.get('state')=='held'else 'source_image_found_pending_review'if c.get('image_url')else 'image_not_located'
        finding=findings.get(w['id'],{})
        rows.append(dict(artwork_id=w['id'],title=w['title'],work_type=w['work_type'],date=w['date_display'],museum=(w.get('holding')or{}).get('name',''),decision=decision,reason=im.get('reason')or c.get('hold_reason')or c.get('error')or finding.get('reason',''),provider=c.get('provider')or w.get('provider_name',''),source_page_url=c.get('source_url')or w.get('source_page_url')or finding.get('source_url',''),source_image_url=c.get('image_url')or w.get('media_url'),rights_label=c.get('license_label')or w.get('license_label'),artline_image_url=PUBLIC+im['storage_path']if w['id']in applied_ids else w['media_url'],artline_url=PUBLIC+'/artists/max-liebermann-q158062/works/'+w['id']))
    path=RUN/'image-results.csv'
    with path.open('w',encoding='utf-8-sig',newline='')as f:writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    save(RUN/'coverage.json',dict(at=now(),total=len(rows),outcomes=dict(collections.Counter(r['decision']for r in rows)),by_type={typ:dict(collections.Counter(r['decision']for r in rows if r['work_type']==typ))for typ in ['painting','drawing']}))
    print(load(RUN/'coverage.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['baseline','select','commons','commons_retry','choose','prepare','sheets','preflight','upload','apply','verify','report'])
    p.add_argument('--followup',action='store_true',help='Use the separately pinned four-candidate inventory-match followup')
    args=p.parse_args()
    if args.followup:
        OP='max-liebermann-images-followup-20261011'
        RUN=RUN/'followup';ARCHIVE=ARCHIVE.parent/OP;BACKUP=BACKUP.parent/OP
    globals()[args.action]()
