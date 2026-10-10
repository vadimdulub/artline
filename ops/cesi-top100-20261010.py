#!/usr/bin/env python3
"""Source-pinned Cesi review and bounded Top 100 catalogue continuation.

Production writes are separate from research. The local catalogue is read-only.
No publication, invented creation dates, or current-display assertions.
"""
import argparse, ast, collections, concurrent.futures, datetime, difflib, gzip, hashlib, html, importlib.util, io, json, os, re, subprocess, time, unicodedata, uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import psycopg, requests
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont

ROOT = Path(__file__).resolve().parents[1]
OP = 'cesi-top100-20261010'
RUN = ROOT / 'docs/research' / OP
BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images' / OP
ACTOR = 'local-european-research'
UA = 'Artline catalogue research (selected museum and artist records)'
_dsn = None

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def uid(key): return str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + key))
def norm(s): return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')).casefold() if not unicodedata.combining(c))))
def serial(x): return json.loads(json.dumps(x, default=str))
def load(p): return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())
def save(p, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    if p.suffix == '.gz': raw = gzip.compress(raw, mtime=0)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists(): assert p.read_bytes() == raw, 'Immutable evidence differs: ' + str(p)
    else: p.write_bytes(raw)
def chunks(xs, size=400):
    for i in range(0, len(xs), size): yield xs[i:i+size]
def connect(write=False, local=False):
    global _dsn
    assert not (write and local), 'Local catalogue is read-only'
    if not local and _dsn is None:
        secret = subprocess.check_output(['gcloud','secrets','versions','access','latest','--secret=artline-database-url','--project=artline-508319'], text=True).strip()
        kw = psycopg.conninfo.conninfo_to_dict(secret)
        kw.update(host='127.0.0.1', port='55519', sslmode='disable', connect_timeout=20)
        _dsn = psycopg.conninfo.make_conninfo(**kw)
    return psycopg.connect('postgresql://localhost/artline' if local else _dsn, row_factory=dict_row,
        options='-c timezone=UTC -c statement_timeout=180000 -c lock_timeout=10000' + ('' if write else ' -c default_transaction_read_only=on'))
def capture(url, params=None):
    request_url = requests.Request('GET', url, params=params).prepare().url
    key = sha(request_url.encode()); path = RUN/'captures'/(key+'.json.gz')
    if path.exists():
        d=load(path); raw=(RUN/'captures'/(key+'.body.gz')).read_bytes(); raw=gzip.decompress(raw)
        assert sha(raw)==d['sha256']; return raw,d
    hold = RUN/'access-holds'/(urlsplit(request_url).hostname+'.json')
    if hold.exists():
        denied=load(hold)
        # The separate WikiArt shop is not the catalogue. Never retry its denied surface.
        different_surface=(urlsplit(denied['url']).path.startswith('/store/') and not urlsplit(request_url).path.startswith('/store/'))
        assert different_surface, 'Source access held: ' + request_url
    r=requests.get(request_url,headers={'User-Agent':UA},timeout=(15,60))
    d=dict(url=request_url,final_url=r.url,status=r.status_code,retrieved_at=now(),sha256=sha(r.content),bytes=len(r.content),content_type=r.headers.get('Content-Type'))
    save(path,d); p=RUN/'captures'/(key+'.body.gz'); p.write_bytes(gzip.compress(r.content,mtime=0))
    if r.status_code in (401,403,429):
        if hold.exists(): save(RUN/'access-holds'/(key+'.json'),d)
        else: save(hold,d)
    return r.content,d
def baseline():
    with connect() as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        artists=db.execute("""SELECT to_jsonb(a) record,to_jsonb(d) discovery,
          coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
          coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases
          FROM artists a LEFT JOIN artist_discovery_selection d ON d.artist_id=a.id
          WHERE a.status<>'archived' AND (d.is_popular OR a.normalized_name='bartolomeo cesi')
          ORDER BY d.popularity_rank NULLS LAST,a.display_name""").fetchall()
        assert sum(bool(a['discovery'] and a['discovery']['is_popular']) for a in artists)==100
        ids=[a['record']['id'] for a in artists]
        works=db.execute('SELECT DISTINCT a.* FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])',(ids,)).fetchall()
        wids=[str(w['id']) for w in works]
        creators=[]; ext=[]; media=[]; citations=[]
        for batch in chunks(wids):
            creators+=db.execute('SELECT * FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(batch,)).fetchall()
            ext+=db.execute("SELECT * FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(batch,)).fetchall()
            media+=db.execute('SELECT am.artwork_id,am.view_label,ma.* FROM artwork_media am JOIN media_assets ma ON ma.id=am.media_id WHERE am.artwork_id=ANY(%s::uuid[])',(batch,)).fetchall()
            citations+=db.execute("SELECT id,entity_id,source_url,source_record_id,field_name FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(batch,)).fetchall()
        institutions=db.execute("SELECT to_jsonb(i) record,p.country_code,p.name city FROM institutions i LEFT JOIN places p ON p.id=i.place_id WHERE i.status<>'archived'").fetchall()
        qp=db.execute('EXPLAIN (FORMAT JSON) SELECT a.* FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s',(ids[0],)).fetchone()
    value=serial(dict(at=now(),target='production',artists=artists,artworks=works,creators=creators,identifiers=ext,media=media,citations=citations,institutions=institutions,query_plan=qp))
    save(RUN/'baseline.json.gz',value); BACKUP.mkdir(parents=True,exist_ok=True); BACKUP.chmod(0o700); save(BACKUP/'baseline.json.gz',value)
    with connect(local=True) as db:
        local=db.execute("SELECT count(*) artworks,count(*) FILTER(WHERE primary_media_id IS NOT NULL) illustrated FROM artworks").fetchone()
    save(RUN/'local-readonly-baseline.json',dict(at=now(),counts=local))
    by=collections.defaultdict(list)
    for aa in value['creators']: by[aa['artist_id']].append(aa['artwork_id'])
    wm={w['id']:w for w in value['artworks']}
    report=[]
    for a in value['artists']:
        ws=[wm[i] for i in by[a['record']['id']] if wm[i]['status']!='archived']
        report.append(dict(name=a['record']['display_name'],id=a['record']['id'],rank=(a['discovery'] or {}).get('popularity_rank'),works=len(ws),images=sum(bool(w['primary_media_id']) for w in ws),museum_links=sum(bool(w['current_institution_id']) for w in ws),wikiart=[e['canonical_url'] for e in a['identifiers'] if e['scheme']=='wikiart-artist']))
    save(RUN/'cohort-review.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

def dateparse(value):
    text=str(value or '').strip().replace('–','-').replace('—','-')
    match=re.fullmatch(r'(?:(c\.?|ca\.?|circa)\s*)?(\d{3,4})(?:\s*-\s*(\d{3,4}))?',text,re.I)
    if not match: return None
    first=int(match[2]);last=int(match[3] or match[2])
    if not 500<=first<=last<=1970: return None
    return dict(first=first,last=last,precision=('circa' if first==last else 'circa_range') if match[1] else ('exact' if first==last else 'range'),display=str(value))

def indexes():
    b=load(RUN/'baseline.json.gz')
    artistworks=collections.defaultdict(set)
    for aa in b['creators']:artistworks[aa['artist_id']].add(aa['artwork_id'])
    def one(a):
        ar=a['record'];dest=RUN/'indexes'/(ar['id']+'.json.gz')
        if dest.exists(): return load(dest)
        profiles=sorted({e['canonical_url'].rstrip('/') for e in a['identifiers'] if e['scheme']=='wikiart-artist' and e['canonical_url']})
        if not profiles:
            profiles=sorted({urlsplit(e['canonical_url']).scheme+'://'+urlsplit(e['canonical_url']).netloc+urlsplit(e['canonical_url']).path.rsplit('/',1)[0] for e in b['identifiers'] if e['scheme']=='wikiart-artwork' and e.get('canonical_url') and e['entity_id'] in artistworks[ar['id']]})
        out=dict(artist_id=ar['id'],name=ar['display_name'],profiles=profiles,works=[],state='unresolved_profile')
        if len(profiles)==1:
            try:
                profile=profiles[0];raw,rc=capture(profile+'/all-works/text-list');out['receipt']=rc
                assert rc['status']==200, 'Index HTTP '+str(rc['status'])
                sp=BeautifulSoup(raw,'html.parser');works={}
                for li in sp.select('li'):
                    for a in li.select('a[href]'):
                        url=urljoin(profile,a['href']);prefix=profile+'/'
                        if not url.startswith(prefix) or 'all-works' in url:continue
                        title=a.get_text(' ',strip=True);literal=li.get_text(' ',strip=True).removeprefix(title).strip(' ,')
                        works[url]=dict(url=url,title=title,source_date=literal,date=dateparse(literal))
                assert works, 'No catalogue entries parsed'
                out.update(state='captured',works=list(works.values()))
            except Exception as e:out.update(state='held',reason=type(e).__name__+': '+str(e))
        save(dest,out); print(ar['display_name'],out['state'],len(out['works']),flush=True);return out
    # At most two concurrent metadata streams, no image downloads at discovery.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(one,b['artists']))
    save(RUN/'index-summary.json',dict(at=now(),artists=len(rows),states=dict(collections.Counter(r['state'] for r in rows)),source_entries=sum(len(r['works']) for r in rows),policy='Metadata discovery only. Object pages and selected images require separate identity, date, and collection/highlight review.'))

def wiki_fields(url):
    raw,rc=capture(url); assert rc['status']==200, 'Object HTTP '+str(rc['status'])
    sp=BeautifulSoup(raw,'html.parser');tag=sp.select_one('.wiki-layout-painting-info-bottom[ng-init]');assert tag,'Native object metadata absent'
    md=json.loads(tag['ng-init'].split('=',1)[1].strip());fields={}
    for label in ['Location','Media','Dimensions','Genre','Style']:
        node=sp.find(string=re.compile(r'^\s*'+label+r':\s*$'))
        if node:fields[label]=node.parent.parent.get_text(' ',strip=True).removeprefix(label+':').strip()
    im=sp.select_one('img[itemprop=image]');rights=sp.select_one('.copyright-wrapper .copyright')
    return dict(provider='wikiart',source_url=url,source_id=md['_id'],scheme='wikiart-artwork',title=html.unescape(md['title']),date=dateparse(md.get('year')),creator=md['artistName'],artist_url=urljoin(url,md['artistUrl']),metadata=md,fields=fields,receipt=rc,
      image_url=im['src'] if im else None,rights_label=rights.get_text(' ',strip=True) if rights else 'Rights not specified',rights_status='public_domain' if rights and rights.select_one('.copyright-icon-public-domain') else ('restricted' if rights else 'unknown'),license_url='https://www.wikiart.org/en/terms-of-use',rights_basis='WikiArt source approved by the user on 6 October 2026. Actual source label preserved separately; no independent licence asserted.')

def museum_map(b):
    museums={i['record']['id']:i['record'] for i in b['institutions']};aliases=collections.defaultdict(set)
    for i in museums.values():
        for name in [i['name'],i['name'].split(' — ')[0]]:aliases[norm(name).removeprefix('the ')].add(i['id'])
    tree=ast.parse((ROOT/'ops/reconcile-random-5000-wikiart-round4-20261007.py').read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALIASES' for t in node.targets):
            for label,mid in ast.literal_eval(node.value).items():
                if mid in museums:aliases[norm(label).removeprefix('the ')].add(mid)
    def resolve(label):
        value=norm(label).removeprefix('the ')
        if not value or re.search(r'private|unknown|destroyed|lost|stolen',value):return None
        matches=aliases.get(value,set())
        if not matches:
            # Longest reviewed institutional name; never a city-only match.
            hits=[(len(k),ids) for k,ids in aliases.items() if len(k)>=12 and value.startswith(k+' ')]
            if hits:
                longest=max(h[0] for h in hits);matches=set().union(*(ids for length,ids in hits if length==longest))
        canonical=set()
        for mid in matches:
            seen=set()
            while museums[mid].get('canonical_institution_id'):
                assert mid not in seen;seen.add(mid);mid=museums[mid]['canonical_institution_id']
            canonical.add(mid)
        return next(iter(canonical)) if len(canonical)==1 else None
    return resolve

def discover(artist_ids=None,output_folder='discovery-v2',index_folder='indexes',summary_name='discovery-summary.json'):
    b=load(RUN/'baseline.json.gz');wm={w['id']:w for w in b['artworks']};byartist=collections.defaultdict(set);creators=collections.defaultdict(list)
    for aa in b['creators']:byartist[aa['artist_id']].add(aa['artwork_id']);creators[aa['artwork_id']].append(aa)
    byurl=collections.defaultdict(set);bysource=collections.defaultdict(set)
    for e in b['identifiers']:
        if e['canonical_url']:byurl[e['canonical_url'].rstrip('/')].add(e['entity_id'])
        if e['scheme']=='wikiart-artwork':bysource[e['external_id']].add(e['entity_id'])
    for e in b['citations']:
        if e['source_url']:byurl[e['source_url'].rstrip('/')].add(e['entity_id'])
    for e in b['media']:
        if e['source_page_url']:byurl[e['source_page_url'].rstrip('/')].add(e['artwork_id'])
    resolve=museum_map(b)
    def one(a):
        artist=a['record'];aid=artist['id'];dest=RUN/output_folder/(aid+'.json.gz')
        if dest.exists():return load(dest)
        ix=load(RUN/index_folder/(aid+'.json.gz'));out=dict(artist_id=aid,name=artist['display_name'],rows=[],held=[],skipped=collections.Counter(),source_entries=len(ix['works']))
        if ix['state']!='captured':out['state']=ix['state'];save(dest,out);return out
        works=[wm[i] for i in byartist[aid]];titles=collections.defaultdict(set)
        for w in works:
            for t in [w['title'],w['alternate_title']]:
                if t:titles[norm(t)].add(w['id'])
        featured=set()
        try:
            raw,rc=capture(ix['profiles'][0]);sp=BeautifulSoup(raw,'html.parser')
            for tag in sp.select('[ng-init]'):
                init=tag['ng-init']
                if not re.search(r"['\"]masonryId['\"]\s*:\s*['\"]famous-works['\"]",init):continue
                match=re.search(r"['\"]customSource['\"]\s*:\s*",init)
                if match:
                    data,_=json.JSONDecoder().raw_decode(init[match.end():]);featured.update(urljoin(ix['profiles'][0],w['paintingUrl']) for w in data.get('_v',[]))
            out['profile_receipt']=rc
        except Exception as e:out['profile_error']=str(e)
        gap=[];connections=[];fresh=[]
        for item in ix['works']:
            date=item['date'];url=item['url'];key=norm(item['title'])
            if not date or date['last']>1955:out['skipped']['unknown_or_post_1955']+=1;continue
            if re.search(r'\b(detail|fragment|reconstruction|copy after|after the)\b',key):out['skipped']['version_requires_review']+=1;continue
            exact=byurl[url.rstrip('/')];hits=exact or titles.get(key,set())
            if hits:
                if len(hits)!=1:out['held'].append(dict(url=url,reason='Multiple existing object identities',ids=sorted(hits)));continue
                w=wm[next(iter(hits))]
                if w['status']=='archived' or len(creators[w['id']])!=1 or creators[w['id']][0]['attribution_role']!='primary' or w['id'] not in byartist[aid]:out['skipped']['archived_or_qualified_creator']+=1;continue
                if w['work_type'] in ['print','sculpture']:out['skipped']['physical_edition_needs_review']+=1;continue
                if not w['creation_year_end'] or w['creation_year_end']>1955:out['skipped']['existing_date_review']+=1;continue
                if not exact and (w['creation_year_start'],w['creation_year_end'])!=(date['first'],date['last']):out['held'].append(dict(url=url,reason='Title candidate date differs',ids=[w['id']]));continue
                if not exact and (len(key)<14 or re.fullmatch(r'(?:the )?(?:self portrait|portrait|landscape|still life|untitled|nude|composition)(?: \d+)?',key)):out['held'].append(dict(url=url,reason='Generic title lacks unique object identifier'));continue
                candidate=dict(item,existing_id=w['id'],exact_identifier=bool(exact))
                if not w['primary_media_id']:gap.append(candidate)
                elif not w['current_institution_id']:connections.append(candidate)
                else:out['skipped']['already_illustrated_and_linked']+=1
            else:
                close=difflib.get_close_matches(key,list(titles),n=3,cutoff=.87)
                if close:out['held'].append(dict(url=url,reason='Potential existing title or translated version',titles=close));continue
                fresh.append(dict(item,featured=url in featured))
        period=collections.Counter(w['creation_year_start']//10 for w in works if w['primary_media_id'] and w['creation_year_start'])
        fresh.sort(key=lambda x:(not x['featured'],period[x['date']['first']//10],x['date']['first'],x['title']))
        gap.sort(key=lambda x:(not x['exact_identifier'],not bool(wm[x['existing_id']]['current_institution_id']),x['title']))
        pending=gap[:25]+connections[:15]+fresh[:45]+gap[25:40]
        out['candidate_counts']=dict(gaps=len(gap),connections=len(connections),new=len(fresh),selected_object_pages=len(pending));seen=set();new_count=0
        for item in pending:
            if not item.get('existing_id') and new_count>=30:continue
            try:
                f=wiki_fields(item['url']);date=f['date'];assert date and date['last']<=1955,'Detail date unknown or after 1955'
                assert f['artist_url'].rstrip('/')==ix['profiles'][0].rstrip('/'),'Creator profile differs'
                assert norm(f['title'])==norm(item['title']),'Index/detail title differs'
                assert (date['first'],date['last'])==(item['date']['first'],item['date']['last']),'Index/detail date differs'
                existing=item.get('existing_id');sourcehits=bysource[f['source_id']]
                assert not sourcehits or sourcehits==({existing} if existing else set()),'Source ID already catalogued under another identity'
                assert f['source_id'] not in seen,'Duplicate source identity in selection';seen.add(f['source_id'])
                genre=f['fields'].get('Genre','');medium=f['fields'].get('Media','');location=f['fields'].get('Location','');mid=resolve(location)
                assert not re.search(r'\b(lithograph|etching|engraving|woodcut|linocut|screenprint|sculpture|bronze|marble)\b',medium+' '+genre,re.I),'Print edition or sculpture needs individual physical-object review'
                if existing:
                    w=wm[existing]
                    if w['current_institution_id'] and location:
                        assert mid==w['current_institution_id'],'Source holding differs or cannot be reconciled with existing institution'
                    if not item.get('exact_identifier'):
                        # A native holding match corroborates weak/generic title cases; longer distinctive titles already screened.
                        assert (w['creation_year_start'],w['creation_year_end'])==(date['first'],date['last']),'Image-only date conflict requires separate review'
                    assert not (w['primary_media_id'] and not mid),'No new supported image or holding'
                    wid=existing;image_needed=not bool(w['primary_media_id']);add_holding=bool(mid and not w['current_institution_id'])
                else:
                    wid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikiart.org/artwork/'+f['source_id']));image_needed=True;add_holding=bool(mid);new_count+=1
                assert f['image_url'] or not image_needed,'No source reproduction'
                kind='drawing' if re.search(r'\b(chalk|pencil|charcoal|graphite|pastel|ink)\b',medium,re.I) else 'watercolor' if 'watercolor' in medium.lower() else 'fresco' if 'fresco' in medium.lower() else 'painting' if re.search(r'\b(oil|tempera|gouache)\b',medium,re.I) or 'painting' in genre else 'unknown'
                f.update(artwork_id=wid,artist_id=aid,artist_name=artist['display_name'],state='existing' if existing else 'new',image_needed=image_needed,add_holding=add_holding,institution_id=mid,work_type=kind,attribution_role='primary',featured=item.get('featured',False),
                  selection_basis='Existing catalogue image/collection gap' if existing else ('WikiArt famous-works selection' if item.get('featured') else 'Personal owner highlight selected to broaden an under-illustrated creation period in the requested Top 100 continuation; not a museum masterpiece designation'),
                  identity_confidence=.99 if item.get('exact_identifier') or not existing else .94,
                  identity_basis='Exact native source object and verified artist profile; source ID and URL checked against existing records.' if item.get('exact_identifier') or not existing else 'Unique distinctive exact artist/title and creation bounds, with compatible documented holding where supplied; generic names and physical editions withheld.')
                out['rows'].append(f)
            except Exception as e:out['held'].append(dict(url=item['url'],reason=type(e).__name__+': '+str(e)))
        out['state']='reviewed';out['skipped']=dict(out['skipped']);save(dest,out)
        print(artist['display_name'],'selected',len(out['rows']),'new',new_count,'holds',len(out['held']),flush=True);return out
    cohort=[a for a in b['artists'] if artist_ids is None or a['record']['id'] in artist_ids]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,cohort))
    rows=[x for r in results for x in r['rows']]
    save(RUN/summary_name,dict(at=now(),artists=len(results),rows=len(rows),new=sum(r['state']=='new' for r in rows),images=sum(r['image_needed'] for r in rows),holdings=sum(r['add_holding'] for r in rows),locations=dict(collections.Counter(r['fields'].get('Location') for r in rows)),limits='Per artist: up to 40 existing image gaps, 15 existing connection gaps, 45 fresh object-page candidates and 30 accepted new highlights. Metadata indexes reviewed in full.'))

def all_rows():
    rows=[r for p in sorted((RUN/'discovery-v2').glob('*.json.gz')) for r in load(p)['rows']]
    rows += [r for p in sorted((RUN/'discovery-supplements').glob('*.json.gz')) for r in load(p)['rows']]
    if (RUN/'cesi-candidates.json').exists():rows+=load(RUN/'cesi-candidates.json')['rows']
    return rows

def safe_rows():
    rows=all_rows();counts=collections.Counter(r['artwork_id'] for r in rows);titles={}
    for p in (RUN/'indexes').glob('*.json.gz'):
        ix=load(p);titles[ix['artist_id']]=collections.Counter(norm(w['title']) for w in ix['works'])
    for p in (RUN/'indexes-corrections').glob('*.json.gz'):
        ix=load(p);titles[ix['artist_id']]=collections.Counter(norm(w['title']) for w in ix['works'])
    return [r for r in rows if counts[r['artwork_id']]==1 and not (r['provider']=='wikiart' and r['state']=='existing' and r['identity_confidence']<.99 and titles[r['artist_id']][norm(r['title'])]>1)]

def imagehash(im):
    small=im.convert('L').resize((9,8),Image.Resampling.LANCZOS);pixels=list(small.getdata());value=0
    for y in range(8):
        for x in range(8):value=(value<<1)|int(pixels[y*9+x]>pixels[y*9+x+1])
    return format(value,'016x')

def prepare():
    rows=[r for r in safe_rows() if r['image_needed']];ORIGINALS.mkdir(parents=True,exist_ok=True)
    def one(r):
        aid=r['artwork_id'];dest=RUN/'prepared'/(aid+'.json')
        if dest.exists():return load(dest)['state']
        out=dict(artwork_id=aid,title=r['title'],artist=r['artist_name'],artist_id=r['artist_id'],source_url=r['source_url'],source_image_url=r['image_url'])
        try:
            u=r['image_url'];host=urlsplit(u).hostname
            assert urlsplit(u).scheme=='https' and (re.fullmatch(r'uploads\d+\.wikiart\.org',host) or host in {'media.getty.edu','iiif.micr.io','images.navigart.fr'}),'Image host not approved for this selection'
            hold=RUN/'image-access-holds'/(host+'.json');assert not hold.exists(),'Image host access held'
            original=ORIGINALS/(aid+'.source');receipt=ORIGINALS/(aid+'.receipt.json')
            if receipt.exists():rc=load(receipt);raw=original.read_bytes();assert sha(raw)==rc['sha256']
            else:
                response=requests.get(u,headers={'User-Agent':UA},timeout=(15,60));rc=dict(url=u,final_url=response.url,status=response.status_code,retrieved_at=now(),sha256=sha(response.content),bytes=len(response.content),content_type=response.headers.get('Content-Type'))
                if response.status_code in (401,403,429):save(hold,rc)
                response.raise_for_status();raw=response.content;assert rc['content_type'].startswith('image/') and len(raw)<30_000_000
                original.write_bytes(raw);save(receipt,rc)
            with Image.open(io.BytesIO(raw)) as opened:
                assert opened.width*opened.height<=100_000_000
                if opened.width*opened.height>40_000_000:opened.draft('RGB',(2400,2400))
                opened.load();im=ImageOps.exif_transpose(opened).convert('RGB');dh=imagehash(im);im.thumbnail((1200,1200),Image.Resampling.LANCZOS)
                output=None
                for edge in [1200,1000,843,700,600,500,400]:
                    im.thumbnail((edge,edge),Image.Resampling.LANCZOS)
                    for quality in [90,85,80,75,70,65,60,55]:
                        buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True,progressive=True)
                        if buf.tell()<=100000:output=buf.getvalue();break
                    if output:break
                assert output and max(im.size)>=300 and min(im.size)>=40
                digest=sha(output);path='/assets/artworks/imported/'+OP+'/'+aid+'-'+digest[:16]+'.jpg';local=ROOT/'apps/web/public'/path.lstrip('/');local.parent.mkdir(parents=True,exist_ok=True)
                if local.exists():assert local.read_bytes()==output
                else:local.write_bytes(output)
                out.update(state='prepared',path=str(local),storage_path=path,sha256=digest,bytes=len(output),width=im.width,height=im.height,quality=quality,dhash=dh,media_id=uid('media/'+aid+'/'+digest),download=rc,original_path=str(original))
        except Exception as e:out.update(state='held',reason=type(e).__name__+': '+str(e)[:350])
        save(dest,out);return out['state']
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,state in enumerate(pool.map(one,rows),1):
            counts[state]+=1
            if i%100==0:print('Prepared',i,'/',len(rows),dict(counts),flush=True)
    print('Image preparation',len(rows),dict(counts),flush=True)

def sheets():
    seen={item['artwork_id'] for p in (RUN/'sheets').glob('*.json') for item in load(p)['items']}
    ims=[load(p) for p in sorted((RUN/'prepared').glob('*.json')) if load(p)['state']=='prepared' and load(p)['artwork_id'] not in seen]
    output=ORIGINALS/'sheets';output.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
    index=len(list((RUN/'sheets').glob('*.json')))
    for offset in range(0,len(ims),40):
        index+=1;subset=ims[offset:offset+40];canvas=Image.new('RGB',(2560,1950),'#eeeeee');draw=ImageDraw.Draw(canvas);items=[]
        for j,im in enumerate(subset):
            x=(j%8)*320;y=(j//8)*390
            with Image.open(im['path']) as opened:
                thumb=opened.convert('RGB');thumb.thumbnail((310,325),Image.Resampling.LANCZOS);canvas.paste(thumb,(x+(320-thumb.width)//2,y+(325-thumb.height)//2))
            draw.text((x+5,y+330),str(j+1)+'. '+im['artist'][:35],font=font,fill='black');draw.text((x+5,y+352),im['title'][:39],font=font,fill='black')
            items.append(dict(number=j+1,artwork_id=im['artwork_id'],sha256=im['sha256'],title=im['title']))
        path=output/f'{index:03}.jpg';canvas.save(path,quality=93);save(RUN/'sheets'/f'{index:03}.json',dict(path=str(path),sha256=sha(path.read_bytes()),items=items))
    print('Contact sheets',index,'new images',len(ims),flush=True)

def existing_hashes():
    b=load(RUN/'baseline.json.gz');works={w['id']:w for w in b['artworks']};artists=collections.defaultdict(list)
    for r in b['creators']:artists[r['artwork_id']].append(r['artist_id'])
    # Legacy primary images may have no artwork_media row; include those too.
    mids=sorted({w['primary_media_id'] for w in b['artworks'] if w['primary_media_id']});media={}
    with connect() as db:
        for batch in chunks(mids,1000):
            for r in db.execute('SELECT id::text,storage_path FROM media_assets WHERE id=ANY(%s::uuid[])',(batch,)):media[r['id']]=r
    rows=[dict(media[w['primary_media_id']],artwork_id=w['id']) for w in b['artworks'] if w['primary_media_id'] in media]
    def one(r):
        p=ROOT/'apps/web/public'/str(r.get('storage_path') or '').lstrip('/');out=dict(artwork_id=r['artwork_id'],artist_ids=artists[r['artwork_id']],media_id=r['id'],storage_path=r.get('storage_path'),title=works[r['artwork_id']]['title'])
        try:
            assert r.get('storage_path') and p.is_file()
            with Image.open(p) as im:out.update(state='hashed',dhash=imagehash(im),aspect=im.width/im.height,sha256=sha(p.read_bytes()))
        except Exception as e:out.update(state='unavailable',reason=type(e).__name__)
        return out
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result=list(pool.map(one,rows))
    save(RUN/'existing-primary-image-hashes.json.gz',dict(at=now(),rows=result,counts=dict(collections.Counter(r['state'] for r in result))))
    print('Existing image comparison coverage',collections.Counter(r['state'] for r in result),flush=True)

def duplicates():
    existing=load(RUN/'existing-primary-image-hashes.json.gz');groups=collections.defaultdict(list)
    for r in existing['rows']:
        if r['state']=='hashed':
            for aid in r['artist_ids']:groups[aid].append(r)
    rows=safe_rows();result={}
    for r in rows:
        path=RUN/'prepared'/(r['artwork_id']+'.json')
        if r['state']!='new' or not path.exists():continue
        im=load(path)
        if im['state']!='prepared':continue
        dh=int(im['dhash'],16);aspect=im['width']/im['height'];matches=[]
        for other in groups[r['artist_id']]:
            distance=(dh^int(other['dhash'],16)).bit_count();ratio=abs(aspect/other['aspect']-1)
            if distance<=3 or (distance<=6 and ratio<.08):matches.append(dict(artwork_id=other['artwork_id'],title=other['title'],distance=distance,aspect_difference=ratio))
        result[r['artwork_id']]=dict(decision='hold' if matches or dh.bit_count() in (0,64) else 'clear',matches=matches,method='Perceptual similarity is a conservative duplicate/version warning, not proof of physical identity. Comparison to readable current primary images and preceding selected works by the same artist.')
        groups[r['artist_id']].append(dict(artwork_id=r['artwork_id'],title=r['title'],dhash=im['dhash'],aspect=aspect))
    save(RUN/'duplicate-image-review.json',result);print('Image duplicate screen',collections.Counter(v['decision'] for v in result.values()),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command');args=p.parse_args();globals()[args.command]()
