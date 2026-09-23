#!/usr/bin/env python3
"""Armenian painter roster and selected historical artwork collection expansion."""
import argparse
import collections
import concurrent.futures
import importlib.util
import json
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('coverage', ROOT / 'ops/wikiart-artist-coverage.py')
c = importlib.util.module_from_spec(s)
s.loader.exec_module(c)
m = c.m
PRIOR = c.RUN
OLD = ROOT / 'docs/research/armenian-georgian-women-20260913'
RUN = ROOT / 'docs/research/armenian-painters-20260920'
c.RUN = m.RUN = RUN
m.BACKUP = Path.home() / 'Library/Application Support/Artline/backups/armenian-painters-20260920'
m.ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images/armenian-painters-20260920'
SOURCE = 'armenian-painters-20260920'
ACTOR = m.ACTOR
s = importlib.util.spec_from_file_location('wikimedia', ROOT / 'ops/research-wikimedia-catalogues.py')
w = importlib.util.module_from_spec(s)
s.loader.exec_module(w)
w.RUN = RUN
w.BACKUPS = m.BACKUP


def save(path, value):
    m.save_atomic(path, value)


def captured(url):
    return w.fetch(url)


def claims(entity, prop):
    rows = [v for v in entity.get('claims', {}).get(prop, []) if v.get('rank') != 'deprecated' and v.get('mainsnak', {}).get('snaktype') == 'value']
    return [v for v in rows if v.get('rank') == 'preferred'] or rows


def values(entity, prop):
    return [v['mainsnak']['datavalue']['value'] for v in claims(entity, prop)]


def label(entity):
    return next((entity['labels'][lang]['value'] for lang in ('en', 'mul', 'hy', 'ru', 'fr') if lang in entity.get('labels', {})), entity['id'])


def names(entity):
    return list(dict.fromkeys([v['value'] for v in entity.get('labels', {}).values()] + [v['value'] for group in entity.get('aliases', {}).values() for v in group]))


def year(entity, prop):
    return w.year(entity, prop)


def entities(ids):
    missing = [q for q in ids if not (RUN / 'entities' / (q + '.json')).exists()]
    for start in range(0, len(missing), 30):
        part = missing[start:start + 30]
        # This bounded metadata phase is answering the waiting user's request.
        # MediaWiki explicitly permits interactive queries without maxlag:
        # https://www.mediawiki.org/wiki/Manual:Maxlag_parameter
        # Keep the shared pacing, HTTP retry/backoff and rate-limit handling.
        data, receipt = captured('https://www.wikidata.org/w/api.php?' + urlencode({'action': 'wbgetentities', 'ids': '|'.join(part), 'props': 'labels|descriptions|aliases|claims|sitelinks', 'languages': 'en|hy|ru|fr|mul', 'format': 'json'}))
        for q in part:
            save(RUN / 'entities' / (q + '.json'), {'entity': data['entities'][q], 'receipt': receipt})
        print('Captured authorities', start + len(part), 'of', len(missing), flush=True)
    return {q: json.loads((RUN / 'entities' / (q + '.json')).read_bytes()) for q in ids}


def source_probe():
    selected=json.loads((RUN/'work-candidate-selection.json').read_bytes())['selected']
    missing=sorted({v['qid'] for v in selected if not (RUN/'entities'/(v['qid']+'.json')).exists()})
    response=w.SESSION.get('https://www.wikidata.org/w/api.php',params={'action':'wbgetentities','ids':'|'.join(missing[:30]),'props':'labels|descriptions|aliases|claims|sitelinks','languages':'en|hy|ru|fr|mul','format':'json','maxlag':5},timeout=(15,40))
    print(json.dumps({'http_status':response.status_code,'retry_after':response.headers.get('Retry-After'),'body_preview':response.text[:600],'bytes':len(response.content)}),flush=True)


def image_duplicate_audit():
    from PIL import Image,ImageOps,ImageDraw
    images=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')]
    aids={im['artwork_id'] for im in images}
    artists=list({im['work']['artist']['id'] for im in images})
    with m.read_only() as db:
        rows=db.execute("""SELECT aa.artist_id::text,a.id::text,a.title,a.creation_year_start,a.creation_year_end,ma.storage_path,ma.checksum_sha256
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id JOIN media_assets ma ON ma.id=a.primary_media_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' AND NOT(a.id=ANY(%s::uuid[]))""",(artists,list(aids))).fetchall()
    def fingerprint(path):
        image=Image.open(ROOT/'apps/web/public'/path.lstrip('/')).convert('L').resize((17,16))
        pixels=list(image.getdata());number=0
        for y in range(16):
            for x in range(16):
                number=(number<<1)|int(pixels[y*17+x]>pixels[y*17+x+1])
        return number
    hashes={}
    for row in rows:
        try:hashes[row['id']]=fingerprint(row['storage_path'])
        except (FileNotFoundError,OSError):continue
    matches=[]
    for im in images:
        h=fingerprint(im['path'])
        for row in rows:
            if row['artist_id']!=im['work']['artist']['id'] or row['id'] not in hashes:continue
            distance=(h^hashes[row['id']]).bit_count()
            if distance<=12 or im['sha256']==row['checksum_sha256']:
                matches.append({'selected':{k:im[k] for k in ('artwork_id','artist','title','source_year','path','sha256')},'existing':row,'distance':distance})
    save(RUN/'image-duplicate-audit.json',{'compared_images':len(images),'existing_images':len(rows),'near_matches':matches,'note':'256-bit horizontal difference hash; candidate generation only, not identity proof.'})
    canvas=Image.new('RGB',(800,max(1,len(matches))*275),'white');draw=ImageDraw.Draw(canvas)
    for n,match in enumerate(matches):
        for col,(path,title) in enumerate([(match['selected']['path'],match['selected']['title']),(match['existing']['storage_path'],match['existing']['title'])]):
            image=Image.open(ROOT/'apps/web/public'/path.lstrip('/')).convert('RGB');thumb=ImageOps.contain(image,(390,230))
            canvas.paste(thumb,(col*400+(400-thumb.width)//2,n*275))
            draw.text((col*400+5,n*275+235),str(n+1)+' '+title[:45],fill='black')
    canvas.save('/tmp/artline-armenian-image-matches.jpg',quality=90)
    print('Image near matches',len(matches),flush=True)


def deduplicate_source():
    import base64,hashlib
    audit=json.loads((RUN/'image-duplicate-audit.json').read_bytes())
    assert len(audit['near_matches'])==1
    match=audit['near_matches'][0];aid=match['selected']['artwork_id'];existing=match['existing']
    assert aid=='538dcf8f-9896-546f-9920-7df4f68718f6' and existing['id']=='8b99ffdc-875d-5f3c-ba3c-165e49eb50eb'
    path=RUN/'images'/(aid+'.json');archive=RUN/'duplicate-sources'/(aid+'.json')
    im=json.loads((path if path.exists() else archive).read_bytes())
    assert im['source_year']==existing['creation_year_start']==existing['creation_year_end']==1884
    # Both frames were visually compared: identical house, cart, sky and shadows.
    save(archive,im)
    raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
    assert len(raw)<=100000 and m.core.sha(raw)==im['sha256']
    bucket=m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    blob=bucket.blob(im['path'].lstrip('/'));blob.cache_control='public,max-age=31536000,immutable'
    try:blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
    except m.PreconditionFailed:blob.reload(timeout=30)
    assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        receipt=RUN/'duplicate-source-receipts'/(target+'.json')
        if receipt.exists():continue
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            with db.transaction():
                sid=source(db)
                row=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(existing['id'],)).fetchone()['record']
                media=db.execute('SELECT checksum_sha256 FROM media_assets WHERE id=%s',(row['primary_media_id'],)).fetchone()
                assert media['checksum_sha256']==existing['checksum_sha256']
                backup=m.BACKUP/'duplicate-source'/(target+'.json');save(backup,{'artwork':row,'selected':im})
                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikiart-artwork',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(existing['id'],im['source_id'],im['page'],sid,im['checked_at']))
                w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=existing['id'],source_id=sid,field_name='additional_image_source',source_record_id=im['source_id'],source_url=im['page'],evidence_note=json.dumps({'basis':'Visual identity confirmed: same house, cart, sky and shadows; same artist and 1884 creation year. Existing primary image retained; no duplicate artwork created.','public_alternate_image':im['path'],'sha256':im['sha256']}),retrieved_at=im['checked_at'],created_by=ACTOR))
                assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(existing['id'],)).fetchone()['record']==row
            save(receipt,{'artwork_id':existing['id'],'duplicate_source_artwork_id':aid,'public_path':im['path'],'sha256':im['sha256'],'backup':str(backup),'at':m.core.now()})
    save(RUN/'prepare-held'/(aid+'.json'),{'artwork_id':aid,'url':im['page'],'error':'Visually confirmed existing artwork with primary image; source identifier and alternate public file retained without a duplicate record.'})
    if path.exists():path.unlink()
    print('Duplicate source reconciled; existing image retained and alternate file public',flush=True)


def discover():
    query = '''SELECT DISTINCT ?artist ?country WHERE {
      VALUES ?country { wd:Q399 wd:Q79797 }
      ?artist (wdt:P27|wdt:P172) ?country; wdt:P106/wdt:P279* wd:Q1028181 .
    } ORDER BY ?artist ?country'''
    data, receipt = captured('https://query.wikidata.org/sparql?' + urlencode({'query': query, 'format': 'json'}))
    save(RUN / 'roster-discovery.json', {'query': query, 'rows': data['results']['bindings'], 'receipt': receipt, 'limit': None})
    qids = sorted({x['artist']['value'].rsplit('/', 1)[-1] for x in data['results']['bindings']})
    entities(qids)
    raw, receipt = m.Fetcher().get('https://www.wikiart.org/en/artists-by-nation/armenian')
    soup = c.BeautifulSoup(raw, 'html.parser')
    artists = []
    for li in soup.select('li'):
        a = li.find('a', recursive=False)
        if a and re.fullmatch(r'/en/[^/]+', a.get('href', '')) and re.search(r'\d+ artworks', li.get_text()):
            artists.append({'name': a.get_text(' ', strip=True), 'url': urljoin(receipt['final_url'], a['href']), 'text': li.get_text(' ', strip=True)})
    assert artists
    save(RUN / 'wikiart-armenian-directory.json', {'artists': artists, 'receipt': receipt})
    with m.read_only() as db:
        rows = db.execute("""SELECT to_jsonb(a) record,
          coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers,
          coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
          coalesce((SELECT jsonb_agg(to_jsonb(ac)) FROM artist_countries ac WHERE ac.artist_id=a.id),'[]') countries
          FROM artists a WHERE a.status<>'archived' ORDER BY a.id""").fetchall()
    save(RUN / 'artist-baseline.json', {'at': m.core.now(), 'artists': rows})
    print('Discovered', len(qids), 'Wikidata painter authorities and', len(artists), 'WikiArt Armenian artist profiles', flush=True)


def authority_plan(plan_filename='authority-plan.json', qids_override=None, affiliation_sources=None):
    roster = json.loads((RUN / 'roster-discovery.json').read_bytes())
    qids = qids_override or sorted({x['artist']['value'].rsplit('/', 1)[-1] for x in roster['rows']})
    baseline = json.loads((RUN / 'artist-baseline.json').read_bytes())['artists']
    byqid = collections.defaultdict(list)
    byname = collections.defaultdict(dict)
    for row in baseline:
        for e in row['identifiers']:
            if e['scheme'] == 'wikidata':
                byqid[e['external_id']].append(row)
        for name in [row['record']['display_name']] + row['aliases']:
            byname[m.norm(name)][row['record']['id']] = row
    selected, held = [], []
    for q in qids:
        capture = json.loads((RUN / 'entities' / (q + '.json')).read_bytes())
        e = capture['entity']
        row = {'qid': q, 'name': label(e), 'capture': str(RUN / 'entities' / (q + '.json'))}
        if e.get('id') != q or 'Q5' not in {v.get('id') for v in values(e, 'P31') if isinstance(v, dict)}:
            held.append(dict(row, reason='Source entity is not an unreconciled human painter identity')); continue
        birth, death = year(e, 'P569'), year(e, 'P570')
        countries = []
        if 'Q399' in {v.get('id') for v in values(e, 'P27') if isinstance(v, dict)}:
            countries.append('citizenship')
        if 'Q79797' in {v.get('id') for v in values(e, 'P172') if isinstance(v, dict)}:
            countries.append('cultural_affiliation')
        if (affiliation_sources or {}).get(q):
            row['affiliation_source'] = affiliation_sources[q]
            if 'cultural_affiliation' not in countries:
                countries.append('cultural_affiliation')
        if not countries:
            held.append(dict(row, reason='Current entity lacks matching Armenian affiliation statement')); continue
        candidates = byqid[q]
        if not candidates:
            named = {p['record']['id']: p for name in names(e) for p in byname[m.norm(name)].values()}
            candidates = [p for p in named.values() if all(v is None or p['record'][k] is None or v == p['record'][k] for k,v in [('birth_year', birth), ('death_year', death)])]
            if named and len(candidates) != 1:
                held.append(dict(row, reason='Existing name/date identity needs reconciliation', candidate_ids=list(named))); continue
        if len(candidates) > 1:
            held.append(dict(row, reason='Multiple existing artist authorities', candidate_ids=[p['record']['id'] for p in candidates])); continue
        if candidates:
            existing = candidates[0]
            other_qids = {x['external_id'] for x in existing['identifiers'] if x['scheme'] == 'wikidata'} - {q}
            if other_qids:
                held.append(dict(row, reason='Name match has another authority identifier', other_qids=sorted(other_qids))); continue
            artist = existing['record']
            action = 'existing'
        else:
            if birth is None and death is None:
                held.append(dict(row, reason='No unambiguous life year for required artist timeline')); continue
            if birth is not None and death is not None and birth > death:
                held.append(dict(row, reason='Conflicting life dates')); continue
            first = birth if birth is not None else death
            last = death if death is not None else birth
            display = str(birth) + '–' + str(death) if birth is not None and death is not None else ('Born ' + str(birth) + '; later activity undated' if birth is not None else 'Died ' + str(death) + '; earlier activity undated')
            artist = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/wikimedia-catalogue/artist/' + q)),
                'slug': 'wikimedia-painter-' + q.lower(), 'display_name': label(e), 'sort_name': label(e), 'normalized_name': m.norm(label(e)),
                'entity_type': 'person', 'birth_year': birth, 'death_year': death, 'birth_display': str(birth) if birth is not None else None,
                'death_display': str(death) if death is not None else None, 'birth_precision': 'exact' if birth is not None else None,
                'death_precision': 'exact' if death is not None else None, 'timeline_start_year': first, 'timeline_end_year': last,
                'timeline_display': display, 'timeline_basis': 'life', 'status': 'review', 'created_by': ACTOR, 'updated_by': ACTOR}
            action = 'new'
        selected.append(dict(row, artist=artist, action=action, country_relationships=countries))
    duplicates = collections.Counter(v['artist']['id'] for v in selected)
    assert all(n == 1 for n in duplicates.values()), 'Two source identities resolve to one artist'
    save(RUN / plan_filename, {'selected': selected, 'held': held, 'roster_count': len(qids)})
    print('Authority plan', dict(collections.Counter(v['action'] for v in selected)), 'held', len(held), flush=True)


def source(db):
    db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,'Armenian painters — source authority and artwork research','collection_page','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING", (SOURCE,))
    return db.execute('SELECT id FROM sources WHERE slug=%s AND is_active', (SOURCE,)).fetchone()['id']


def authority_apply(plan_filename='authority-plan.json', marker='authorities'):
    plan = json.loads((RUN / plan_filename).read_bytes())
    def apply_target(target, dsn):
        counts = collections.Counter()
        with m.psycopg.connect(dsn, autocommit=True, row_factory=m.dict_row) as db:
            sid = source(db)
            for item in plan['selected']:
                q, artist = item['qid'], item['artist']
                receipt_path = RUN / 'authorities-applied' / target / (q + '.json')
                if receipt_path.exists():
                    counts['already_applied'] += 1; continue
                capture = json.loads(Path(item['capture']).read_bytes())
                e = capture['entity']
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='3s'")
                    candidates = db.execute("""SELECT DISTINCT a.id::text,to_jsonb(a) record FROM artists a
                        LEFT JOIN external_identifiers x ON x.entity_type='artist' AND x.entity_id=a.id AND x.scheme='wikidata'
                        WHERE a.id=%s OR a.slug=%s OR x.external_id=%s""", (artist['id'], artist['slug'], q)).fetchall()
                    assert len(candidates) <= 1, ('Target authority collision', target, q)
                    existing = candidates[0]['record'] if candidates else None
                    aid = existing['id'] if existing else artist['id']
                    if existing:
                        assert existing['status'] != 'archived'
                        assert m.norm(existing['display_name']) in {m.norm(n) for n in names(e)} | {m.norm(artist['display_name'])}
                        other = db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id<>%s", (aid,q)).fetchall()
                        assert not other, ('Different target authority', target, q)
                    elif item['action'] != 'new':
                        raise ValueError('Existing local artist absent in production: ' + q)
                    countries = db.execute('SELECT to_jsonb(x) record FROM artist_countries x WHERE artist_id=%s', (aid,)).fetchall()
                    identifiers = db.execute("SELECT to_jsonb(x) record FROM external_identifiers x WHERE entity_type='artist' AND entity_id=%s", (aid,)).fetchall()
                    aliases = db.execute('SELECT to_jsonb(x) record FROM artist_aliases x WHERE artist_id=%s', (aid,)).fetchall()
                    backup = m.BACKUP / 'authorities' / target / (q + '.json')
                    save(backup, {'artist': existing, 'countries': countries, 'identifiers': identifiers, 'aliases': aliases, 'planned': item})
                    if not existing:
                        fields = list(artist)
                        db.execute('INSERT INTO artists(' + ','.join(fields) + ') VALUES(' + ','.join(['%s'] * len(fields)) + ')', tuple(artist[k] for k in fields))
                    db.execute("""INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                        VALUES('artist',%s,'wikidata',%s,%s,%s,%s) ON CONFLICT DO NOTHING""", (aid,q,'https://www.wikidata.org/wiki/'+q,sid,capture['receipt']['retrieved_at']))
                    for lang,v in e.get('labels', {}).items():
                        db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) VALUES(%s,%s,%s,%s,'alternate') ON CONFLICT DO NOTHING", (aid,v['value'],m.norm(v['value']),lang))
                    added = 0
                    for relationship in item['country_relationships']:
                        note = ('WikiArt explicitly includes this artist in its Armenian nationality directory; profile and linked authority identity retained. Cultural affiliation, not exclusive citizenship.' if item.get('affiliation_source') and relationship=='cultural_affiliation' else 'Explicit Wikidata '+('P27 Armenia citizenship' if relationship=='citizenship' else 'P172 Armenian affiliation')+' statement; source retained in Armenian painter research. Other country relationships preserved.')
                        cur = db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'AM',%s,false,%s) ON CONFLICT DO NOTHING", (aid,relationship,note))
                        added += cur.rowcount
                    citation_id = str(uuid.uuid5(uuid.NAMESPACE_URL, SOURCE + '/artist/' + target + '/' + q))
                    db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                        VALUES(%s,'artist',%s,%s,'armenian_identity_and_affiliation',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""", (citation_id,aid,sid,q,'https://www.wikidata.org/wiki/'+q,json.dumps({'entity_sha256':capture['receipt']['sha256'],'country_relationships':item['country_relationships'],'affiliation_source':item.get('affiliation_source'),'life_dates':'Only unambiguous source years copied for new profiles. A single known life year is a timeline anchor, not a fabricated lifespan. Existing artist metadata preserved.'}),capture['receipt']['retrieved_at'],ACTOR))
                    after = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s', (aid,)).fetchone()['record']
                    assert not existing or after == existing
                save(receipt_path, {'at': m.core.now(), 'qid': q, 'artist_id': aid, 'created': not bool(existing), 'country_links_added': added, 'after': after, 'backup': str(backup), 'backup_sha256': m.core.sha(backup.read_bytes())})
                counts['created' if not existing else 'existing'] += 1
                counts['country_links_added'] += added
                if (counts['created'] + counts['existing']) % 50 == 0:
                    print('Artist delivery', target, dict(counts), flush=True)
        finished=RUN / (marker + '-' + target + '-finished.json')
        if not finished.exists():save(finished, {'counts': dict(counts), 'at': m.core.now()})
        return target, dict(counts)
    dsns = {'local': 'postgres://localhost/artline', 'cloud': m.core.cloud_dsn()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(apply_target, target, dsn) for target,dsn in dsns.items()]
        for future in futures:
            print('Artist delivery finished', future.result(), flush=True)


def authority_supplement():
    original = json.loads((RUN/'authority-plan.json').read_bytes())
    existing = {v['qid'] for v in original['selected']}
    extras = json.loads((RUN/'wikiart-extra-authorities.json').read_bytes())['artists']
    directory = json.loads((RUN/'wikiart-armenian-directory.json').read_bytes())
    proof = {v['qid']:{'profile':v['source'],'directory':directory['receipt']} for v in extras if v.get('source')}
    qids = sorted(({v['qid'] for v in original['held']} | set(proof)) - existing)
    path = RUN/'authority-supplement-plan.json'
    if not path.exists():
        authority_plan(path.name,qids,proof)
    authority_apply(path.name,'authority-supplement')


def authority_final_reconcile():
    baseline=json.loads((RUN/'artist-baseline.json').read_bytes())['artists']
    selected=[]
    # MoMA native identifier establishes identity despite the 1924/1925 source
    # birth discrepancy; retain the catalogue's existing date and document both.
    q='Q4282221';capture=json.loads((RUN/'entities'/(q+'.json')).read_bytes())
    assert values(capture['entity'],'P2174')==['2341']
    artist=next(v['record'] for v in baseline if v['record']['id']=='6ca05442-fa4b-402d-8746-5d81871b3b81')
    selected.append({'qid':q,'name':label(capture['entity']),'capture':str(RUN/'entities'/(q+'.json')),'artist':artist,'action':'existing','country_relationships':['cultural_affiliation']})
    # These are two different generations of the Hovnatanyan family. The old
    # authority's generic Russian alias is not evidence for merging them.
    q='Q4330727';capture=json.loads((RUN/'entities'/(q+'.json')).read_bytes());e=capture['entity']
    assert year(e,'P569')==1806 and year(e,'P570')==1881
    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artist/'+q))
    artist={'id':aid,'slug':'wikimedia-painter-'+q.lower(),'display_name':label(e),'sort_name':label(e),'normalized_name':m.norm(label(e)),
        'entity_type':'person','birth_year':1806,'death_year':1881,'birth_display':'1806','death_display':'1881','birth_precision':'exact','death_precision':'exact',
        'timeline_start_year':1806,'timeline_end_year':1881,'timeline_display':'1806–1881','timeline_basis':'life','status':'review','created_by':ACTOR,'updated_by':ACTOR}
    selected.append({'qid':q,'name':label(e),'capture':str(RUN/'entities'/(q+'.json')),'artist':artist,'action':'new','country_relationships':['cultural_affiliation']})
    save(RUN/'authority-final-plan.json',{'selected':selected,'held':[],'basis':{'Q4282221':'Same MoMA artist ID 2341; Wikidata 1925 birth vs MoMA/catalogue 1924 retained as a discrepancy. https://www.moma.org/artists/2341-marcos-grigorian',
        'Q4330727':'Hakob Mkrtum Hovnatanyan (1806–1881), distinct from Hakob Nagashi Hovnatanyan (1692–1757). National Gallery identifies the later portrait painter: https://oldgallery.deespaces.app/en/Armenian/OilPainting/'}})
    authority_apply('authority-final-plan.json','authority-final')
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            note_id=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE+'/marcos-date-conflict/'+target))
            db.execute("""INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_url,evidence_note,retrieved_at,created_by)
                VALUES(%s,'artist',%s,%s,'birth_date_source_conflict','https://www.moma.org/artists/2341-marcos-grigorian',%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
                (note_id,'6ca05442-fa4b-402d-8746-5d81871b3b81',sid,'MoMA native ID 2341 confirms the existing identity. MoMA and the existing catalogue give birth year 1924; Wikidata Q4282221 gives 1925. Preserve the existing year and both source claims for review.',m.core.now(),ACTOR))


def identity_review():
    # Explicit source identifier, not a fuzzy name or coincident lifespan.
    q = 'Q2379692'
    entity = json.loads((RUN/'entities'/(q+'.json')).read_bytes())['entity']
    assert values(entity,'P6002') == ['mher-abeghian']
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        receipt_path = RUN/'identity-resolutions'/('mher-'+target+'.json')
        if receipt_path.exists():
            continue
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            with db.transaction():
                sid = source(db)
                canonical = db.execute("SELECT to_jsonb(a) record FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikiart-artist' AND e.external_id='mher-abeghian'").fetchone()['record']
                created = db.execute("SELECT to_jsonb(a) record FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s",(q,)).fetchone()['record']
                assert canonical['id']!=created['id'] and created['status']=='review'
                assert not db.execute('SELECT 1 FROM artwork_artists WHERE artist_id=%s LIMIT 1',(created['id'],)).fetchone()
                tables = {}
                for table,col in [('artist_aliases','artist_id'),('artist_countries','artist_id'),('external_identifiers','entity_id'),('citations','entity_id')]:
                    tables[table] = db.execute('SELECT to_jsonb(x) record FROM '+table+' x WHERE '+col+'=ANY(%s::uuid[])',([canonical['id'],created['id']],)).fetchall()
                backup = m.BACKUP/'identity-resolutions'/('mher-'+target+'.json')
                save(backup,{'canonical':canonical,'created':created,'references':tables,'basis':'Wikidata P6002 explicitly identifies the existing WikiArt artist mher-abeghian.'})
                db.execute("INSERT INTO artist_aliases(artist_id,alias,normalized_alias,language_code,alias_type) SELECT %s,alias,normalized_alias,language_code,alias_type FROM artist_aliases WHERE artist_id=%s ON CONFLICT DO NOTHING",(canonical['id'],created['id']))
                db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) SELECT %s,country_code,relationship_type,false,note FROM artist_countries WHERE artist_id=%s ON CONFLICT DO NOTHING",(canonical['id'],created['id']))
                for table in ('external_identifiers','citations'):
                    db.execute('UPDATE '+table+" SET entity_id=%s WHERE entity_type='artist' AND entity_id=%s",(canonical['id'],created['id']))
                db.execute("UPDATE artists SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(ACTOR,created['id']))
                w.base.insert(db,'citations',dict(entity_type='artist',entity_id=created['id'],source_id=sid,field_name='reconciled_duplicate_authority',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note='Newly created duplicate authority archived after explicit WikiArt identifier reconciliation. Existing canonical artist: '+canonical['id']+'. All supplied source identity references retained on that artist.',retrieved_at=m.core.now(),created_by=ACTOR))
                after = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(created['id'],)).fetchone()['record']
                assert db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(canonical['id'],)).fetchone()['record']==canonical
            save(receipt_path,{'canonical_id':canonical['id'],'archived_id':created['id'],'archived_after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
        print('Reconciled Mher Abeghyan',target,flush=True)
    from PIL import Image,ImageOps,ImageDraw
    ims=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')]
    titles={'Canon Table Page','PAINTING IN SPACE'}
    chosen=sorted([im for im in ims if im['title'] in titles],key=lambda v:(v['artist'],v['source_year'],v['artwork_id']))
    width=1200;cellw=300;cellh=285
    canvas=Image.new('RGB',(width,cellh*((len(chosen)+3)//4)),'white');draw=ImageDraw.Draw(canvas)
    index=[]
    for n,im in enumerate(chosen):
        src=Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')).convert('RGB')
        thumb=ImageOps.contain(src,(280,230));x=(n%4)*cellw;y=(n//4)*cellh
        canvas.paste(thumb,(x+(cellw-thumb.width)//2,y))
        draw.text((x+7,y+232),str(n+1)+' '+im['artist']+' '+str(im['source_year']),fill='black')
        draw.text((x+7,y+251),im['artwork_id'][:18],fill='black')
        index.append({'number':n+1,'artwork_id':im['artwork_id'],'source_year':im['source_year'],'path':im['path'],'page':im['page'],'sha256':im['sha256']})
    canvas.save('/tmp/artline-armenian-title-review.jpg',quality=90)
    save(RUN/'title-review-index.json',index)
    print('Title review sheet',len(chosen),'images',flush=True)


def resolve_titles():
    index = json.loads((RUN/'title-review-index.json').read_bytes())
    chosen = [x for x in index if x['number'] in (2,3,4,8,9)]
    leon=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')]
    leon=[im for im in leon if im['artist'].startswith('Léon') and im['title']=='Composition']
    for im in leon:
        receipt=json.loads((RUN/'delivery'/(im['artwork_id']+'.json')).read_bytes())
        if any(v['outcome']=='held' for v in receipt['targets'].values()):
            chosen.append({'artwork_id':im['artwork_id'],'number':10,'leon':True})
    # Three distinct illuminated pages; separately dated and visibly different
    # 1930/1931 spatial compositions. The two further 1929 views stay unresolved.
    for row in chosen:
        im = json.loads((RUN/'images'/(row['artwork_id']+'.json')).read_bytes())
        peers = [x['artwork_id'] for x in index if x['number']!=row['number'] and ((x['number']<=4)==(row['number']<=4))]
        basis='Visual comparison of selected source frames: different illuminated page architecture and ornament, or separately dated 1930/1931 spatial compositions. Source IDs and dates remain in review.'
        if row.get('leon'):
            peers=[x['artwork_id'] for x in leon if x['artwork_id']!=im['artwork_id']]
            basis='Visually different compositions: a 1928 pale organic form on a dark background and a 1927 arrangement of angular stippled triangles on tan paper. Distinct source IDs and creation years retained.'
        save(RUN/'title-identity-resolutions'/(im['artwork_id']+'.json'),{'image_sha256':im['sha256'],'distinct_from':peers,'basis':basis})
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            for row in chosen:
                aid = row['artwork_id'];filename = aid+'.json'
                output = RUN/'title-resolved'/target/filename
                im = json.loads((RUN/'images'/filename).read_bytes())
                if output.exists():
                    result = json.loads(output.read_bytes())
                else:
                    state = c.target_before(db,im)
                    assert state['outcome']=='create',(aid,state)
                    backup = m.BACKUP/'resolved-titles'/target/filename
                    save(backup,state)
                    result = c.apply_image(db,im,state)
                    assert result['outcome']=='attached'
                    result['backup'] = str(backup)
                    save(output,result)
                for folder in ('applied/'+target,'delivery'):
                    path = RUN/folder/filename
                    previous = json.loads(path.read_bytes())
                    replacement = result if folder.startswith('applied/') else dict(previous,targets={**previous['targets'],target:result})
                    if previous==replacement:
                        continue
                    save(RUN/'title-resolution-history'/target/folder/filename,previous)
                    temp = path.with_suffix('.replacement')
                    temp.write_bytes(m.core.encode(replacement));temp.replace(path)
                print('Resolved title',target,im['artist'],im['title'],flush=True)
    marker = RUN/'personal-selection-finished.json'
    if marker.exists():
        save(RUN/'title-resolution-history'/('selection-finished-'+m.core.sha(marker.read_bytes())[:16]+'.json'),marker.read_bytes());marker.unlink()
    c.sync_selection()


def artwork_discover():
    roster = json.loads((RUN / 'roster-discovery.json').read_bytes())
    qids = sorted({x['artist']['value'].rsplit('/', 1)[-1] for x in roster['rows']})
    rows = []
    for start in range(0,len(qids),40):
        part = qids[start:start+40]
        path = RUN / 'work-discovery' / (str(start).zfill(4) + '.json')
        if path.exists():
            data = json.loads(path.read_bytes())
        else:
            query = '''SELECT DISTINCT ?work ?artist ?collection ?date ?image WHERE {
              VALUES ?artist { ''' + ' '.join('wd:'+q for q in part) + ''' }
              ?work wdt:P170 ?artist; wdt:P195 ?collection .
              OPTIONAL { ?work wdt:P571 ?date } OPTIONAL { ?work wdt:P18 ?image }
            } ORDER BY ?artist ?work'''
            response, receipt = captured('https://query.wikidata.org/sparql?' + urlencode({'query':query,'format':'json'}))
            data = {'artist_qids':part,'query':query,'receipt':receipt,'rows':response['results']['bindings']}
            save(path,data)
        rows.extend(data['rows'])
        print('Artwork discovery',start+len(part),'of',len(qids),'rows',len(rows),flush=True)
    save(RUN / 'work-discovery.json',{'rows':rows,'artists_surveyed':len(qids),'limit':None})
    with m.read_only() as db:
        existing = db.execute("SELECT e.external_id,a.id::text,a.primary_media_id::text FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s)", (list({v['work']['value'].rsplit('/',1)[-1] for v in rows}),)).fetchall()
    existing = {v['external_id']:v for v in existing}
    groups = collections.defaultdict(dict)
    for row in rows:
        q = row['work']['value'].rsplit('/',1)[-1]
        aq = row['artist']['value'].rsplit('/',1)[-1]
        yr = int(row['date']['value'][:4]) if re.match(r'\d{4}-',row.get('date',{}).get('value','')) else None
        if yr is not None and yr > 1955:
            continue
        if q in existing and existing[q]['primary_media_id']:
            continue
        groups[aq][q] = {'qid':q,'year':yr,'image':row.get('image'), 'existing':existing.get(q)}
    selected = []
    for aq,items in groups.items():
        ranked = sorted(items.values(),key=lambda v:(v['year'] is None,not bool(v['image']),bool(v['existing']),v['qid']))[:8]
        selected.extend(dict(v,artist_qid=aq) for v in ranked)
    save(RUN / 'work-candidate-selection.json', {'selected':selected,'source_rows':len(rows),'artist_groups':len(groups),'policy':'Up to eight further museum-connected records per painter, dated by 1955 first. Unknown source dates remain review metadata without image or automatic date eligibility.'})
    entities(sorted({v['qid'] for v in selected}))
    print('Selected artwork entities',len(selected),'for',len(groups),'artists',flush=True)


def wikiart_select():
    inventory = json.loads((PRIOR / 'artist-matches.json').read_bytes())
    sources = {p['url']: p for p in inventory['unmatched_source_artists']}
    pairs = inventory['matches'] + inventory['ambiguous']
    sources.update({p['wikiart']['url']:p['wikiart'] for p in pairs})
    known = {p['wikiart']['url']:p['artist']['id'] for p in inventory['matches']}
    for filename in ('extra-artist-matches.json','supplemental-artist-matches.json'):
        for p in json.loads((PRIOR / filename).read_bytes())['matches']:
            known[p['wikiart']['url']] = p['artist']['id']
    national = json.loads((RUN / 'wikiart-armenian-directory.json').read_bytes())
    national_urls = {v['url'] for v in national['artists']}
    with m.read_only() as db:
        artists = db.execute("""SELECT to_jsonb(a) record,
          coalesce((SELECT jsonb_agg(alias) FROM artist_aliases WHERE artist_id=a.id),'[]') aliases,
          coalesce((SELECT jsonb_agg(external_id) FROM external_identifiers WHERE entity_type='artist' AND entity_id=a.id AND scheme='wikidata'),'[]') qids,
          EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND country_code='AM') armenian
          FROM artists a WHERE a.status<>'archived'""").fetchall()
        byid = {v['record']['id']:v for v in artists}
        byname = collections.defaultdict(dict)
        byqid = {}
        for v in artists:
            for q in v['qids']:
                byqid[q] = v
            for name in [v['record']['display_name']] + v['aliases']:
                byname[m.norm(name)][v['record']['id']] = v
        chosen, held = [], []
        for url, source_record in sources.items():
            matched = byid.get(known.get(url))
            if url not in national_urls and not (matched and matched['armenian']):
                continue
            slug = urlparse(url).path.rsplit('/',1)[-1]
            profile_path = PRIOR / 'profiles' / (slug+'.json')
            if profile_path.exists():
                profile = json.loads(profile_path.read_bytes())
                save(RUN / 'profiles' / profile_path.name, profile)
            else:
                profile = c.profile_one(source_record)
            if not matched:
                qs = [byqid[q] for q in profile.get('wikidata_ids',[]) if q in byqid]
                matches = qs or list(byname[m.norm(source_record['name'])].values())
                if len(matches) == 1:
                    matched = matches[0]
            if not matched:
                held.append({'source':source_record,'reason':'Artist identity requires reconciliation'}); continue
            chosen.append({'artist':dict(matched['record'],selection_limit=12),'wikiart':source_record,'country_evidence':national['receipt'] if url in national_urls else None})
        excluded = set()
        for previous in (c.PREVIOUS,PRIOR,ROOT/'docs/research/wikiart-artist-followup-20260920'):
            for path in (previous / 'images').glob('*.json'):
                excluded.add(json.loads(path.read_bytes())['source_id'])
        for pair in chosen:
            c.select_one(pair,db,excluded)
    matches = m.discovered_matches()
    save(RUN/'wikiart-artist-selection.json',{'pairs':chosen,'held':held,'national_directory_profiles':len(national_urls)})
    save(RUN/'discovered-v2.json',{'matches':matches,'artist_count':len(chosen),'at':m.core.now()})
    print('WikiArt selection',len(matches),'works from',len(chosen),'artist profiles; unmatched',len(held),flush=True)


def wikiart_prepare():
    c.configure_preparation()
    m.prepare()


def wikiart_expand():
    extra = json.loads((RUN/'wikiart-extra-authorities.json').read_bytes())['artists']
    excluded = set()
    for previous in (c.PREVIOUS,PRIOR,ROOT/'docs/research/wikiart-artist-followup-20260920',RUN):
        for path in (previous/'images').glob('*.json'):
            excluded.add(json.loads(path.read_bytes())['source_id'])
    outcomes = []
    with m.read_only() as db:
        for row in extra:
            if not row.get('source'):
                continue
            artist = db.execute("SELECT to_jsonb(a) record FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(row['qid'],)).fetchone()
            if not artist:
                continue
            artist = dict(artist['record'],selection_limit=12)
            c.select_one({'artist':artist,'wikiart':row['source']},db,excluded)
            outcomes.append({'source_url':row['source']['url'],'qid':row['qid'],'artist_id':artist['id']})
    for filename in ('discovered-v2.json','preparation-finished.json','delivery-finished.json','personal-selection-finished.json'):
        path = RUN/filename
        if path.exists():
            save(RUN/'expanded-source-history'/filename,path.read_bytes());path.unlink()
    save(RUN/'wikiart-extra-matches.json',{'matches':outcomes})
    matches = m.discovered_matches()
    save(RUN/'discovered-v2.json',{'matches':matches,'at':m.core.now(),'artist_count':len(list((RUN/'discovery-v2').glob('*.json')))})
    print('Expanded WikiArt candidates',len(matches),flush=True)


def wikiart_deliver():
    c.deliver_ready()


def wikiart_selection():
    c.sync_selection()


def wikiart_verify():
    c.verify()


def artwork_select(allow_unknown_types=False, only_qids=None, output_name='catalogue.json'):
    candidates = json.loads((RUN / 'work-candidate-selection.json').read_bytes())['selected']
    if only_qids is not None:
        candidates=[v for v in candidates if v['qid'] in only_qids]
    selected, held = [], []
    with m.read_only() as db:
        artist_rows = db.execute("SELECT e.external_id,to_jsonb(a) record FROM external_identifiers e JOIN artists a ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'", (list({v['artist_qid'] for v in candidates}),)).fetchall()
        artist_byqid = {v['external_id']:v['record'] for v in artist_rows}
        cached_works = {}
        for item in candidates:
            q,aq = item['qid'],item['artist_qid']
            capture = json.loads((RUN/'entities'/(q+'.json')).read_bytes())
            e = capture['entity']
            creator_capture = json.loads((RUN/'entities'/(aq+'.json')).read_bytes())
            creator = creator_capture['entity']
            cs = claims(e,'P170')
            types = {v.get('id') for v in values(e,'P31') if isinstance(v,dict)}
            date = w.date(e)
            date['eligible'] = bool(date['first'] is not None and date['last'] <= 1955)
            reason = None
            if e.get('id') != q or label(e) == q:
                reason = 'Missing independent artwork identity or title'
            elif len(cs) != 1 or cs[0].get('qualifiers') or cs[0]['mainsnak']['datavalue']['value'].get('id') != aq:
                reason = 'Qualified or multiple creators remain unresolved'
            elif not allow_unknown_types and not types.intersection({'Q3305213','Q93184','Q1278452','Q22669139','Q132137','Q429785'}):
                reason = 'Artwork type needs separate mapping'
            elif date['first'] is not None and not date['eligible']:
                reason = 'Source creation date exceeds 1955'
            elif not claims(e,'P195'):
                reason = 'No retained collection source statement'
            artist = artist_byqid.get(aq)
            if reason:
                held.append(dict(item,reason=reason,title=label(e)));continue
            existing = db.execute("SELECT to_jsonb(a) record FROM external_identifiers e JOIN artworks a ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s", (q,)).fetchall()
            if len(existing)>1:
                held.append(dict(item,reason='Multiple existing authority matches'));continue
            if not existing and artist:
                if aq not in cached_works:
                    cached_works[aq] = c.artist_works(db,artist['id'])
                titles = {m.norm(n) for n in names(e)}
                possible = [v for v in cached_works[aq] if {m.norm(v['title']),m.norm(v.get('alternate_title'))} & titles]
                source_accessions={v for v in values(e,'P217') if isinstance(v,str)}
                compatible = [v for v in possible if date['eligible'] and v['creation_year_start'] is not None and v['creation_year_end'] is not None and date['first']<=v['creation_year_end'] and date['last']>=v['creation_year_start'] and len(v['creators'])==1 and v['creators'][0]['role']=='primary'
                    and (not source_accessions or not v['accession_number'] or v['accession_number'] in source_accessions)]
                if possible and len(compatible)!=1:
                    held.append(dict(item,reason='Existing title requires object identity review',artwork_ids=[v['artwork_id'] for v in possible]));continue
                if compatible:
                    existing = [{'record':compatible[0]['before_record']}]
            existing = existing[0]['record'] if existing else None
            if existing and (existing['status']=='archived' or existing['primary_media_id']):
                held.append(dict(item,reason='Existing record or primary image preserved',artwork_id=existing['id']));continue
            images = [v for v in values(e,'P18') if isinstance(v,str)]
            accession = [v for v in values(e,'P217') if isinstance(v,str)]
            collection_ids = sorted({v.get('id') for v in values(e,'P195') if isinstance(v,dict) and v.get('id')})
            record = {'qid':q,'title':label(e),'titles':names(e),'date':date,'entity':e,'entity_receipt':capture['receipt'],
                'creator_qid':aq,'creator_label':label(creator),'creator_entity':creator,'creator_receipt':creator_capture['receipt'],
                'artist':artist,'collection':{'qid':','.join(collection_ids),'institution':{'slug':'source-collection-unvalidated'}},
                'collection_qids':collection_ids,'accession':accession[0] if len(accession)==1 else None,'images':images,
                'existing_local':existing,'selection_note':'Owner-selected Armenian painter research. Collection statements retained as supplied source metadata; no accepted holding or current display asserted.',
                'work_type':'painting' if 'Q3305213' in types else ('fresco' if 'Q22669139' in types else 'unknown')}
            selected.append(record)
    assert len({v['qid'] for v in selected})==len(selected)
    save(RUN/'selected-museum'/output_name,{'selected':selected,'held':held})
    print('Museum artwork selection',len(selected),'records, existing',sum(bool(v['existing_local']) for v in selected),'eligible dated',sum(v['date']['eligible'] for v in selected),'with images',sum(bool(v['images']) and v['date']['eligible'] for v in selected),'held',len(held),flush=True)


def artwork_expand():
    path=RUN/'selected-museum'/'catalogue.json'
    original=json.loads(path.read_bytes())
    qids={v['qid'] for v in original['held'] if v['reason']=='Artwork type needs separate mapping'}
    artwork_select(True,qids,'additional.json')
    extra=json.loads((RUN/'selected-museum'/'additional.json').read_bytes())
    merged={'selected':original['selected']+extra['selected'],'held':[v for v in original['held'] if v['qid'] not in qids]+extra['held'],
        'unknown_types':'Source object forms and types remain in entity evidence. Broad artwork, graphic-work, portrait, sculpture and manuscript classifications are retained as unknown catalogue type rather than invented as paintings.'}
    assert len({v['qid'] for v in merged['selected']})==len(merged['selected'])
    save(RUN/'selected-museum-history'/'catalogue.json',original)
    temp=path.with_suffix('.replacement');temp.write_bytes(m.core.encode(merged));temp.replace(path)
    print('Expanded museum records',len(merged['selected']),flush=True)


def artwork_prepare():
    s = importlib.util.spec_from_file_location('imageprep',ROOT/'ops/prepare-wikimedia-catalogue-images.py')
    p = importlib.util.module_from_spec(s);s.loader.exec_module(p)
    # The existing Commons adapter checks file identity, actual source rights,
    # credit and original hashes before compression. Keep these checks intact.
    p.r = w
    work_run = RUN/'museum-images'
    work_run.mkdir(parents=True,exist_ok=True)
    records = json.loads((RUN/'selected-museum'/'catalogue.json').read_bytes())['selected']
    selection={'selected':records}
    selection_name='selection-'+m.core.sha(m.core.encode(selection))[:16]+'.json'
    save(work_run/'selected'/selection_name,selection)
    for record in records:
        if not record['date']['eligible'] or not record['images']:
            save(work_run/'ready'/(record['qid']+'.json'),{'record':record,'image':None,'image_outcome':'metadata_retained','image_reason':'Unknown creation date or no source-linked image'})
    original_date = w.date
    def date(e):
        value = original_date(e)
        value['eligible'] = value['first'] is not None and value['last']<=1955
        return value
    w.date = date
    w.RUN = work_run
    w.BACKUPS = m.BACKUP/'museum-images'
    p.main()


def artwork_apply():
    import base64
    import hashlib
    inputs = [json.loads(p.read_bytes()) for p in sorted((RUN/'museum-images'/'ready').glob('*.json'))]
    selected = json.loads((RUN/'selected-museum'/'catalogue.json').read_bytes())['selected']
    assert len(inputs)==len(selected), 'Finish all selected image decisions before delivery'
    bucket = m.storage.Client(project='artline-508319',credentials=m.core.GcloudCredentials()).bucket(m.core.BUCKET)
    for item in inputs:
        im = item['image']
        if not im:
            continue
        receipt = RUN/'museum-uploads'/(item['record']['qid']+'.json')
        if receipt.exists():
            continue
        raw = (ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert len(raw)==im['bytes'] and len(raw)<=100000 and m.core.sha(raw)==im['sha256']
        blob = bucket.blob(im['path'].lstrip('/'))
        blob.cache_control = 'public,max-age=31536000,immutable'
        blob.metadata = {'sha256':im['sha256'],'wikidata':item['record']['qid']}
        try:
            blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        except m.PreconditionFailed:
            blob.reload(timeout=30)
        assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        save(receipt,{'qid':item['record']['qid'],'path':im['path'],'generation':blob.generation,'sha256':im['sha256'],'bytes':len(raw)})
    collection_id = str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    def apply_target(target,dsn):
        counts = collections.Counter()
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid = source(db)
            for item in inputs:
                rec,im = item['record'],item['image']
                q,aq = rec['qid'],rec['creator_qid']
                receipt_path = RUN/'museum-applied'/target/(q+'.json')
                if receipt_path.exists():
                    continue
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    db.execute("SET LOCAL statement_timeout='45s'")
                    collection_before=db.execute('SELECT to_jsonb(cc) record FROM curated_collections cc WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    artist = db.execute("SELECT a.id::text,a.slug,a.display_name FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(aq,)).fetchone()
                    existing = db.execute("SELECT to_jsonb(a) record FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s",(q,)).fetchall()
                    assert len(existing)<=1
                    existing = existing[0]['record'] if existing else None
                    if not existing and rec.get('existing_local'):
                        old = rec['existing_local']
                        found = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s OR slug=%s',(old['id'],old['slug'])).fetchall()
                        assert len(found)<=1
                        existing = found[0]['record'] if found else None
                        if existing:
                            assert m.same_artwork(existing,old), ('Matched existing work metadata differs',target,q)
                    if not existing and artist:
                        titles = {m.norm(t) for t in rec['titles']}
                        peer_rows = db.execute('SELECT to_jsonb(a) record FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s',(artist['id'],)).fetchall()
                        peers = [x['record'] for x in peer_rows if {m.norm(x['record']['title']),m.norm(x['record'].get('alternate_title'))}&titles]
                        if peers:
                            good = [p for p in peers if rec['date']['eligible'] and p['creation_year_start'] is not None and p['creation_year_end'] is not None and rec['date']['first']<=p['creation_year_end'] and rec['date']['last']>=p['creation_year_start']
                                and (not rec['accession'] or not p['accession_number'] or rec['accession']==p['accession_number'])]
                            if len(good)!=1:
                                save(RUN/'museum-held'/target/(q+'.json'),{'reason':'Existing title needs reconciliation','ids':[p['id'] for p in peers]})
                                counts['held']+=1;continue
                            existing = good[0]
                    if existing:
                        assert existing['status']!='archived'
                        creators = db.execute('SELECT artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=%s',(existing['id'],)).fetchall()
                        if creators and (not artist or creators!=[{'artist_id':artist['id'],'attribution_role':'primary'}]):
                            save(RUN/'museum-held'/target/(q+'.json'),{'reason':'Existing creator identity differs','artwork_id':existing['id']})
                            counts['held']+=1;continue
                    aid = existing['id'] if existing else str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artwork/'+q))
                    backup = m.BACKUP/'museum-artworks'/target/(q+'.json')
                    links = db.execute('SELECT to_jsonb(i) record FROM curated_collection_items i WHERE artwork_id=%s',(aid,)).fetchall()
                    identifiers = db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=%s",(aid,)).fetchall()
                    save(backup,{'artwork':existing,'collection':collection_before,'collection_items':links,'identifiers':identifiers,'record':rec})
                    image_allowed = im and rec['date']['eligible'] and (not existing or (existing['primary_media_id'] is None and existing['creation_year_start'] is not None and existing['creation_year_end']<=1955))
                    mid = str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/image/'+q+'/'+im['sha256'])) if image_allowed else None
                    if mid:
                        media = dict(id=mid,storage_kind='local',storage_path=im['path'],source_page_url=im['source_page_url'],provider_name='Wikimedia Commons',mime_type='image/jpeg',width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=rec['title']+' — '+rec['creator_label'],rights_status=im['rights_status'],license_label=im['license_label'],license_url=im['license_url'],creator_credit=im['creator_credit'],attribution_text=im['attribution_text'],retrieved_at=im['download']['retrieved_at'],verified_at=im['checked_at'],verified_by=ACTOR)
                        w.base.insert(db,'media_assets',media)
                        w.base.insert(db,'media_rights_evidence',dict(media_id=mid,source_id=sid,source_record_id=im['commons_page']['title'],source_checksum=im['commons_receipt']['sha256'],source_image_url=im['source_image_url'],policy_url=im['license_url'],rights_basis='Source-linked Commons file, independently matched artwork identity, preserved per-file licence and attribution.',adapter_version='armenian-selected-20260920',checked_at=im['checked_at'],evidence_json=m.Jsonb(im)))
                    if not existing:
                        d = rec['date']
                        w.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+q.lower(),title=rec['title'],normalized_title=m.norm(rec['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=rec['work_type'],accession_number=rec['accession'],primary_media_id=mid,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR,unlinked_creator_label=None if artist else rec['creator_label'],cultural_context=None if artist else 'Armenian artist — supplied source identity awaiting profile reconciliation'))
                        if artist:
                            w.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist['id'],attribution_role='primary',attribution_note='Unqualified Wikidata creator statement preserved for editorial review.'))
                    elif mid:
                        db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,ACTOR,aid))
                    if mid:
                        w.base.insert(db,'artwork_media',dict(artwork_id=aid,media_id=mid,sort_order=0,view_label='Selected reproduction'))
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'wikidata',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(aid,q,'https://www.wikidata.org/wiki/'+q,sid,rec['entity_receipt']['retrieved_at']))
                    w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='armenian_selected_source_metadata',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note=json.dumps({'entity_receipt':rec['entity_receipt'],'creator_qid':aq,'collection_qids':rec['collection_qids'],'collection_statements':claims(rec['entity'],'P195'),'selection':rec['selection_note'],'holding_status':'Source statements retained; no accepted holding or current display assertion created.'}),retrieved_at=rec['entity_receipt']['retrieved_at'],created_by=ACTOR))
                    if not existing or (rec['date']['eligible'] and not db.execute('SELECT artline_has_selection_evidence(%s) selected',(aid,)).fetchone()['selected']):
                        db.execute("INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,(SELECT coalesce(max(position),0)+1 FROM curated_collection_items WHERE collection_id=%s),%s,%s,%s,%s) ON CONFLICT(collection_id,artwork_id) DO NOTHING",(collection_id,aid,collection_id,rec['selection_note'],sid,'https://www.wikidata.org/wiki/'+q,rec['entity_receipt']['retrieved_at']))
                        db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                    after = db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
                    if existing:
                        assert all(after[k]==v for k,v in existing.items() if k not in ('primary_media_id','revision','updated_at','updated_by'))
                save(receipt_path,{'qid':q,'artwork_id':aid,'artist_id':artist['id'] if artist else None,'created':not bool(existing),'image_attached':bool(mid),'media_id':mid,'after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
                counts['created' if not existing else 'existing']+=1
                counts['images_attached']+=bool(mid)
                if (counts['created']+counts['existing'])%25==0:
                    print('Museum delivery',target,dict(counts),flush=True)
        finished=RUN/('museum-'+target+'-finished.json')
        if finished.exists():finished=RUN/('museum-'+target+'-pass-'+str(int(time.time()))+'.json')
        save(finished,{'counts':dict(counts),'at':m.core.now()})
        return target,dict(counts)
    dsns={'local':'postgres://localhost/artline','cloud':m.core.cloud_dsn()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(apply_target,t,dsn) for t,dsn in dsns.items()]
        for future in futures:
            print('Museum delivery finished',future.result(),flush=True)


def artwork_bulk_metadata():
    """Copy already-validated local new metadata in bounded production batches.

    The ordinary delivery worker can continue; completed per-object receipts
    make it skip these records. Leave its next forty inputs untouched.
    """
    inputs=[json.loads(p.read_bytes()) for p in sorted((RUN/'museum-images/ready').glob('*.json'))]
    pending=[v for v in inputs if not (RUN/'museum-applied/cloud'/(v['record']['qid']+'.json')).exists()][40:]
    candidates=[]
    for item in pending:
        rec=item['record'];path=RUN/'museum-applied/local'/(rec['qid']+'.json')
        if item['image'] or not path.exists():continue
        local=json.loads(path.read_bytes())
        if not local['created'] or local['after']['primary_media_id'] or local['after']['current_institution_id']:continue
        candidates.append((rec,local))
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    total=0
    with m.psycopg.connect(m.core.cloud_dsn(),autocommit=True,row_factory=m.dict_row) as db:
        sid=source(db)
        for start in range(0,len(candidates),80):
            chunk=[v for v in candidates[start:start+80] if not (RUN/'museum-applied/cloud'/(v[0]['qid']+'.json')).exists()]
            if not chunk:continue
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL statement_timeout='45s'")
                collection=db.execute('SELECT to_jsonb(cc) record FROM curated_collections cc WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                ids=[v[1]['artwork_id'] for v in chunk]
                present=db.execute("SELECT a.id::text FROM artworks a WHERE a.id=ANY(%s::uuid[]) UNION SELECT e.entity_id::text FROM external_identifiers e WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.external_id=ANY(%s)",(ids,[v[0]['qid'] for v in chunk])).fetchall()
                if present:raise ValueError('Production batch has an existing identity; preserve ordinary reconciliation')
                artists=db.execute("SELECT e.external_id,a.id::text,a.display_name FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'",(list({v[0]['creator_qid'] for v in chunk}),)).fetchall()
                amap={v['external_id']:v for v in artists};assert len(amap)==len(artists)
                peer_rows=db.execute('SELECT aa.artist_id::text,a.id::text,a.title,a.alternate_title FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])',([v['id'] for v in artists],)).fetchall()
                names_by_artist=collections.defaultdict(set)
                for row in peer_rows:names_by_artist[row['artist_id']].update({m.norm(row['title']),m.norm(row['alternate_title'])}-{''})
                selected=[]
                for rec,local in chunk:
                    artist=amap.get(rec['creator_qid'])
                    if not artist:continue
                    titles={m.norm(v) for v in rec['titles']}-{''}
                    if titles & names_by_artist[artist['id']]:continue
                    names_by_artist[artist['id']].update(titles)
                    after=local['after']
                    selected.append({'qid':rec['qid'],'artist_id':artist['id'],'record':rec,'artwork':{k:after[k] for k in ('id','slug','title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','accession_number','unlinked_creator_label','cultural_context')},'checked_at':rec['entity_receipt']['retrieved_at']})
                if not selected:continue
                key=m.core.sha(m.core.encode([v['qid'] for v in selected]))[:16]
                backup=m.BACKUP/'bulk-museum-metadata'/'cloud'/(key+'.json')
                save(backup,{'kind':'new_metadata_batch','artwork':None,'collection':collection,'selected':selected,'existing_identities':present,'artists':artists})
                # Pipeline only independent writes; one sync point before the
                # bounded post-write read and durable per-object receipts.
                with db.pipeline():
                    for entry in selected:
                        a=entry['artwork'];rec=entry['record'];aid=a['id']
                        w.base.insert(db,'artworks',dict(a,status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                        w.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=entry['artist_id'],attribution_role='primary',attribution_note='Unqualified Wikidata creator statement preserved for editorial review.'))
                        w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=entry['qid'],canonical_url='https://www.wikidata.org/wiki/'+entry['qid'],source_id=sid,retrieved_at=entry['checked_at']))
                        w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='armenian_selected_source_metadata',source_record_id=entry['qid'],source_url='https://www.wikidata.org/wiki/'+entry['qid'],evidence_note=json.dumps({'entity_receipt':rec['entity_receipt'],'creator_qid':rec['creator_qid'],'collection_qids':rec['collection_qids'],'collection_statements':claims(rec['entity'],'P195'),'selection':rec['selection_note'],'holding_status':'Source statements retained; no accepted holding or current display assertion created.'}),retrieved_at=entry['checked_at'],created_by=ACTOR))
                members=[{'artwork_id':v['artwork']['id'],'source_url':'https://www.wikidata.org/wiki/'+v['qid'],'checked_at':v['checked_at'],'reason':v['record']['selection_note']} for v in selected]
                db.execute("""WITH input AS (SELECT * FROM jsonb_to_recordset(%s) x(artwork_id uuid,source_url text,checked_at timestamptz,reason text)),
                    positions AS (SELECT coalesce(max(position),0) n FROM curated_collection_items WHERE collection_id=%s)
                    INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at)
                    SELECT %s,i.artwork_id,p.n+row_number() OVER(ORDER BY i.artwork_id)::int,i.reason,%s,i.source_url,i.checked_at FROM input i CROSS JOIN positions p""",(m.Jsonb(members),collection_id,collection_id,sid))
                db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE a.id=ANY(%s::uuid[])',([v['artwork']['id'] for v in selected],)).fetchall()
                byid={v['record']['id']:v['record'] for v in after};assert len(byid)==len(selected)
            for entry in selected:
                aid=entry['artwork']['id']
                save(RUN/'museum-applied/cloud'/(entry['qid']+'.json'),{'qid':entry['qid'],'artwork_id':aid,'artist_id':entry['artist_id'],'created':True,'image_attached':False,'media_id':None,'after':byid[aid],'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now(),'batch':key})
            total+=len(selected)
            print('Production metadata batch',len(selected),'total',total,flush=True)
    save(RUN/'bulk-museum-metadata-finished.json',{'at':m.core.now(),'created':total})


def resolve_museum_titles():
    """Distinct source accession numbers disambiguate repeated series titles."""
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    held=[(p,json.loads(p.read_bytes())) for p in sorted((RUN/'museum-held/local').glob('*.json'))]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for path,hold in held:
                q=path.stem;receipt_path=RUN/'museum-applied'/target/path.name
                if receipt_path.exists():continue
                item=json.loads((RUN/'museum-images/ready'/path.name).read_bytes());rec=item['record']
                assert not item['image'] and rec['accession'] and hold['reason']=='Existing title needs reconciliation'
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    peer_rows=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(hold['ids'],)).fetchall()
                    peers=[v['record'] for v in peer_rows]
                    assert len(peers)==len(hold['ids'])
                    if any(not v['accession_number'] or v['accession_number']==rec['accession'] for v in peers):
                        print('Accession review remains unresolved',target,q,flush=True);continue
                    artist=db.execute("SELECT a.id::text FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id WHERE e.scheme='wikidata' AND e.external_id=%s AND a.status<>'archived'",(rec['creator_qid'],)).fetchone()
                    assert artist
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(q,)).fetchone()
                    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artwork/'+q))
                    collection=db.execute('SELECT to_jsonb(cc) record FROM curated_collections cc WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    backup=m.BACKUP/'resolved-museum-titles'/target/(q+'.json')
                    save(backup,{'artwork':None,'collection':collection,'same_title_peers':peers,'record':rec,'basis':'Distinct supplied accession numbers under separate source object identifiers; generic and series titles alone do not merge objects. Source collection and object identity remain in review.'})
                    d=rec['date']
                    w.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+q.lower(),title=rec['title'],normalized_title=m.norm(rec['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=rec['work_type'],accession_number=rec['accession'],status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                    w.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=artist['id'],attribution_role='primary',attribution_note='Unqualified Wikidata creator statement preserved for editorial review.'))
                    w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=sid,retrieved_at=rec['entity_receipt']['retrieved_at']))
                    w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='armenian_selected_source_metadata',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note=json.dumps({'entity_receipt':rec['entity_receipt'],'creator_qid':rec['creator_qid'],'collection_qids':rec['collection_qids'],'collection_statements':claims(rec['entity'],'P195'),'selection':rec['selection_note'],'identity_resolution':'Same-title records have different supplied accession numbers. Separate source records retained in review.','same_title_peer_ids':hold['ids'],'holding_status':'No accepted holding or current display assertion created.'}),retrieved_at=rec['entity_receipt']['retrieved_at'],created_by=ACTOR))
                    db.execute("INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,(SELECT coalesce(max(position),0)+1 FROM curated_collection_items WHERE collection_id=%s),%s,%s,%s,%s)",(collection_id,aid,collection_id,rec['selection_note'],sid,'https://www.wikidata.org/wiki/'+q,rec['entity_receipt']['retrieved_at']))
                    db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                    after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
                result={'qid':q,'artwork_id':aid,'artist_id':artist['id'],'created':True,'image_attached':False,'media_id':None,'after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now(),'title_resolution':'different_source_accessions'}
                save(receipt_path,result);save(RUN/'museum-title-resolved'/target/(q+'.json'),result)
                old=RUN/'museum-held'/target/(q+'.json')
                if old.exists():save(RUN/'museum-held-history'/target/(q+'.json'),old.read_bytes());old.unlink()
                print('Resolved museum source title',target,q,flush=True)


def directory_finish():
    qslugs={'Q22966703':'petros-malayan','Q966300':'alexander-boghossian','Q4523919':'gregorio-sciltian'}
    captures=entities(list(qslugs))
    directory=json.loads((RUN/'wikiart-armenian-directory.json').read_bytes())
    proof={q:{'profile':json.loads((RUN/'profiles'/(slug+'.json')).read_bytes())['source'],'directory':directory['receipt']} for q,slug in qslugs.items()}
    if not (RUN/'directory-extra-candidates.json').exists():
        authority_plan('directory-extra-candidates.json',list(qslugs),proof)
    plan=json.loads((RUN/'directory-extra-candidates.json').read_bytes())
    for q,e in captures.items():
        print(q,{p:values(e['entity'],p) for p in ['P569','P570','P6002','P2174','P245']},flush=True)
    print('Directory authority plan',[(v['qid'],v['action'],v['artist']['display_name']) for v in plan['selected']],plan['held'],flush=True)
    baseline=json.loads((RUN/'artist-baseline.json').read_bytes())['artists']
    sciltian=next(v['record'] for v in baseline if v['record']['id']=='3073c39a-31e2-40b9-822f-038472dcdf73')
    assert sciltian['birth_year']==1900 and sciltian['death_year']==1985
    assert values(captures['Q4523919']['entity'],'P245')==['500104961']
    for item in plan['selected']:
        if item['qid']=='Q4523919':item.update(artist=sciltian,action='existing')
    save(RUN/'directory-extra-plan.json',plan)
    authority_apply('directory-extra-plan.json','directory-extra')
    slug='andrey-allakhverdov-0';profile=json.loads((RUN/'profiles'/(slug+'.json')).read_bytes());src=profile['source']
    assert src['life_display']=='born 1947'
    aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikiart/artist/'+slug))
    mappings={v['affiliation_source']['profile']['url']:v['artist']['id'] for v in plan['selected']}
    mappings[src['url']]=aid
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        marker=RUN/'directory-final-applied'/(target+'.json')
        if marker.exists():continue
        mappings={proof[q]['profile']['url']:json.loads((RUN/'authorities-applied'/target/(q+'.json')).read_bytes())['artist_id'] for q in qslugs}
        mappings[src['url']]=aid
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            with db.transaction():
                sid=source(db)
                matches=db.execute("SELECT to_jsonb(a) record FROM artists a LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikiart-artist' WHERE a.id=%s OR a.normalized_name=%s OR e.external_id=%s",(aid,m.norm(src['name']),slug)).fetchall()
                assert not matches
                backup=m.BACKUP/'directory-final'/(target+'.json');save(backup,{'artist':None,'source':profile,'directory':directory})
                w.base.insert(db,'artists',dict(id=aid,slug='wikiart-artist-'+slug,display_name=src['name'],sort_name=src['name'],normalized_name=m.norm(src['name']),entity_type='person',birth_year=1947,birth_display='1947',birth_precision='exact',timeline_start_year=1947,timeline_end_year=1947,timeline_display='Born 1947; later activity undated',timeline_basis='life',status='review',created_by=ACTOR,updated_by=ACTOR))
                for url,artist_id in mappings.items():
                    profile_slug=url.rsplit('/',1)[-1]
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artist',%s,'wikiart-artist',%s,%s,%s,%s) ON CONFLICT DO NOTHING",(artist_id,profile_slug,url,sid,directory['receipt']['checked_at']))
                    db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,'AM','cultural_affiliation',false,%s) ON CONFLICT DO NOTHING",(artist_id,'WikiArt Armenian nationality directory; cultural affiliation retained alongside other country relationships.'))
                    note='WikiArt directory profile reconciled. Source life dates retained; no death or later activity year invented.'
                    if profile_slug=='gregorio-sciltian':note='Getty ULAN 500104961 and Wikidata Q4523919 reconcile the inverted name Sciltian, Gregorio and dates 1900–1985. WikiArt lists 1898–1985; existing birth year 1900 preserved. https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500104961'
                    w.base.insert(db,'citations',dict(entity_type='artist',entity_id=artist_id,source_id=sid,field_name='armenian_wikiart_directory_identity',source_record_id=profile_slug,source_url=url,evidence_note=note,retrieved_at=directory['receipt']['checked_at'],created_by=ACTOR))
                near=json.loads((RUN/'similar-authority-audit.json').read_bytes())['near']
                for v in near:
                    if v['new_qid']=='Q2379692':continue
                    artist=db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s",(v['new_qid'],)).fetchone()
                    w.base.insert(db,'citations',dict(entity_type='artist',entity_id=artist['entity_id'],source_id=sid,field_name='possible_duplicate_authority',source_record_id=v['new_qid'],source_url='https://www.wikidata.org/wiki/'+v['new_qid'],evidence_note='Similar transliterated name and chronology to '+v['existing_name']+' ('+v['existing_id']+'). Distinct source authority identifiers lack an explicit identity bridge; kept in review for reconciliation.',retrieved_at=m.core.now(),created_by=ACTOR))
                after=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=%s',(aid,)).fetchone()['record']
            save(marker,{'artist_id':aid,'created':True,'after':after,'matches':mappings,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
        print('Completed Armenian WikiArt directory',target,flush=True)


def directory_artworks():
    roster={v['artist']['value'].rsplit('/',1)[-1] for v in json.loads((RUN/'roster-discovery.json').read_bytes())['rows']}
    qids=sorted({p.stem for p in (RUN/'authorities-applied/local').glob('*.json')}-roster)
    output=RUN/'directory-extra-artwork-discovery.json'
    if output.exists():data=json.loads(output.read_bytes())
    else:
        query='SELECT DISTINCT ?work ?artist ?collection ?date ?image WHERE { VALUES ?artist { '+' '.join('wd:'+q for q in qids)+' } ?work wdt:P170 ?artist; wdt:P195 ?collection . OPTIONAL { ?work wdt:P571 ?date } OPTIONAL { ?work wdt:P18 ?image } } ORDER BY ?artist ?work'
        response,receipt=captured('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
        data={'artist_qids':qids,'rows':response['results']['bindings'],'receipt':receipt,'query':query};save(output,data)
    groups=collections.defaultdict(dict)
    prior=json.loads((RUN/'work-candidate-selection.json').read_bytes());known={v['qid'] for v in prior['selected']}
    for row in data['rows']:
        q=row['work']['value'].rsplit('/',1)[-1];aq=row['artist']['value'].rsplit('/',1)[-1]
        yr=int(row['date']['value'][:4]) if re.match(r'\d{4}-',row.get('date',{}).get('value','')) else None
        if q in known or (yr is not None and yr>1955):continue
        groups[aq][q]={'qid':q,'artist_qid':aq,'year':yr,'image':row.get('image'),'existing':None}
    selected=[]
    for group in groups.values():selected.extend(sorted(group.values(),key=lambda v:(v['year'] is None,not bool(v['image']),v['qid']))[:8])
    print('Additional directory museum discovery',len(data['rows']),'source rows;',len(selected),'candidates',flush=True)
    if not selected:return
    entities([v['qid'] for v in selected])
    save(RUN/'directory-candidate-history.json',prior)
    prior['selected'].extend(selected)
    path=RUN/'work-candidate-selection.json';temp=path.with_suffix('.replacement');temp.write_bytes(m.core.encode(prior));temp.replace(path)
    artwork_select(True,{v['qid'] for v in selected},'directory-extra.json')
    extra=json.loads((RUN/'selected-museum/directory-extra.json').read_bytes())
    path=RUN/'selected-museum/catalogue.json';original=json.loads(path.read_bytes());save(RUN/'directory-museum-history.json',original)
    original['selected'].extend(extra['selected']);original['held'].extend(extra['held'])
    temp=path.with_suffix('.replacement');temp.write_bytes(m.core.encode(original));temp.replace(path)
    print('Additional directory museum selections',len(extra['selected']),'held',len(extra['held']),flush=True)


def accession_probe():
    conflicts=json.loads((RUN/'accession-conflict-audit.json').read_bytes())['conflicts']
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            db.execute('SET default_transaction_read_only=on')
            sid=db.execute('SELECT id::text FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
            for conflict in conflicts:
                q=conflict['qid'];previous=json.loads((RUN/'museum-applied'/target/(q+'.json')).read_bytes())
                identifiers=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(q,)).fetchall()
                before=json.loads(Path(previous['backup']).read_bytes())
                print(json.dumps({'target':target,'qid':q,'campaign_source':sid,'old_id':previous['artwork_id'],'identifiers':identifiers,'previous_identifiers':before.get('identifiers')}),flush=True)


def correct_accession_matches():
    conflicts=json.loads((RUN/'accession-conflict-audit.json').read_bytes())['conflicts']
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for conflict in conflicts:
                q=conflict['qid'];output=RUN/'accession-corrections'/target/(q+'.json')
                if output.exists():continue
                rec=json.loads((RUN/'museum-images/ready'/(q+'.json')).read_bytes())['record']
                receipt_path=RUN/'museum-applied'/target/(q+'.json');previous=json.loads(receipt_path.read_bytes())
                assert not previous['created'] and not previous['image_attached']
                old_id=previous['artwork_id'];aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artwork/'+q))
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    old=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(old_id,)).fetchone()['record']
                    assert old==previous['after'] and old['accession_number']!=rec['accession']
                    identifiers=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s",(q,)).fetchall()
                    assert not identifiers or (len(identifiers)==1 and identifiers[0]['record']['entity_id']==old_id and identifiers[0]['record']['source_id']==str(sid))
                    citations=db.execute("SELECT to_jsonb(c) record FROM citations c WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s",(old_id,sid,q)).fetchall()
                    assert citations
                    collection=db.execute('SELECT to_jsonb(cc) record FROM curated_collections cc WHERE id=%s FOR UPDATE',(collection_id,)).fetchone()['record']
                    backup=m.BACKUP/'accession-corrections'/target/(q+'.json')
                    save(backup,{'artwork':None,'incorrect_target_unchanged':old,'identifiers':identifiers,'citations':citations,'collection':collection,'record':rec,'previous_receipt':previous})
                    d=rec['date']
                    w.base.insert(db,'artworks',dict(id=aid,slug='wikimedia-artwork-'+q.lower(),title=rec['title'],normalized_title=m.norm(rec['title']),date_display=d['display'],creation_year_start=d['first'],creation_year_end=d['last'],date_precision=d['precision'],work_type=rec['work_type'],accession_number=rec['accession'],status='review',research_candidate=True,created_by=ACTOR,updated_by=ACTOR))
                    w.base.insert(db,'artwork_artists',dict(artwork_id=aid,artist_id=previous['artist_id'],attribution_role='primary',attribution_note='Source identity distinguished from a same-title work by its different accession number.'))
                    if identifiers:
                        db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s AND entity_id=%s AND source_id=%s",(aid,q,old_id,sid))
                    else:
                        # The one-identifier-per-entity/scheme constraint had
                        # rejected the conflicting identity on the old object.
                        w.base.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='wikidata',external_id=q,canonical_url='https://www.wikidata.org/wiki/'+q,source_id=sid,retrieved_at=rec['entity_receipt']['retrieved_at']))
                    db.execute("UPDATE citations SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s",(aid,old_id,sid,q))
                    w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,source_id=sid,field_name='same_title_accession_resolution',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note='Distinct source accession '+rec['accession']+' versus '+old['accession_number']+'. Same title and year were insufficient for identity. Source identifier and citations moved to this separate review record; earlier artwork metadata and media preserved.',retrieved_at=m.core.now(),created_by=ACTOR))
                    db.execute("INSERT INTO curated_collection_items(collection_id,artwork_id,position,reason,source_id,source_url,checked_at) VALUES(%s,%s,(SELECT coalesce(max(position),0)+1 FROM curated_collection_items WHERE collection_id=%s),%s,%s,%s,%s)",(collection_id,aid,collection_id,rec['selection_note'],sid,'https://www.wikidata.org/wiki/'+q,rec['entity_receipt']['retrieved_at']))
                    db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(collection_id,))
                    after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
                    assert db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(old_id,)).fetchone()['record']==old
                result={'qid':q,'artwork_id':aid,'artist_id':previous['artist_id'],'created':True,'image_attached':False,'media_id':None,'after':after,'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now(),'identity_resolution':'distinct_source_accessions'}
                save(output,result);save(RUN/'accession-correction-history'/target/(q+'.json'),previous)
                temp=receipt_path.with_suffix('.replacement');temp.write_bytes(m.core.encode(result));temp.replace(receipt_path)
                print('Corrected same-title accession',target,q,flush=True)


def activity_authorities():
    path=RUN/'activity-authority-plan.json'
    if not path.exists():
        applied={p.stem for p in (RUN/'authorities-applied/local').glob('*.json')}
        selected=[]
        for item in json.loads((RUN/'authority-supplement-plan.json').read_bytes())['held']:
            q=item['qid']
            if q in applied:continue
            capture=json.loads((RUN/'entities'/(q+'.json')).read_bytes());e=capture['entity'];period=claims(e,'P1317')
            if len(period)!=1 or period[0].get('qualifiers'):continue
            v=period[0]['mainsnak']['datavalue']['value']
            if v.get('before') or v.get('after') or v['precision'] not in (7,8):continue
            yr=int(v['time'][1:5])
            if v['precision']==7:
                century=(yr+99)//100;first=(century-1)*100+1;last=century*100;display='Active in the '+str(century)+('th' if century%100 in (11,12,13) else {1:'st',2:'nd',3:'rd'}.get(century%10,'th'))+' century; life dates unknown'
            else:
                first=(yr//10)*10;last=first+9;display='Active in the '+str(first)+'s; life dates unknown'
            artist={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/artist/'+q)),'slug':'wikimedia-painter-'+q.lower(),'display_name':label(e),'sort_name':label(e),'normalized_name':m.norm(label(e)),'entity_type':'person','active_start_year':first,'active_end_year':last,'activity_display':display,'timeline_start_year':first,'timeline_end_year':last,'timeline_display':display,'timeline_basis':'activity','status':'review','created_by':ACTOR,'updated_by':ACTOR}
            selected.append({'qid':q,'capture':str(RUN/'entities'/(q+'.json')),'name':label(e),'artist':artist,'action':'new','country_relationships':['cultural_affiliation']})
        save(path,{'selected':selected,'held':[],'basis':'Explicit P1317 floruit century or decade retained as activity bounds. No birth/death years invented. Wikidata renders +1400 at precision 7 as the 14th century (1301–1400). These bounds classify the supplied period; they do not claim continuous activity.'})
    authority_apply(path.name,'activity-authorities')
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        with m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) as db:
            sid=source(db)
            for entry in json.loads(path.read_bytes())['selected']:
                aid=json.loads((RUN/'authorities-applied'/target/(entry['qid']+'.json')).read_bytes())['artist_id']
                cid=str(uuid.uuid5(uuid.NAMESPACE_URL,SOURCE+'/activity-period/'+target+'/'+entry['qid']))
                db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artist',%s,%s,'documented_activity_period',%s,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING",(cid,aid,sid,entry['qid'],'https://www.wikidata.org/wiki/'+entry['qid'],'P1317 source floruit retained at century/decade precision: '+entry['artist']['activity_display']+'. Timeline bounds represent the supplied period, not a lifespan or continuous activity.',m.core.now(),ACTOR))
            for p in (RUN/'museum-applied'/target).glob('*.json'):
                previous=json.loads(p.read_bytes());a=previous['after']
                if not a['unlinked_creator_label']:continue
                q=previous['qid'];marker=RUN/'creator-link-reconciled'/target/(q+'.json')
                if marker.exists():continue
                rec=json.loads((RUN/'museum-images/ready'/(q+'.json')).read_bytes())['record']
                artist=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND external_id=%s",(rec['creator_qid'],)).fetchone()
                if not artist:continue
                with db.transaction():
                    current=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(a['id'],)).fetchone()['record'];assert current==a
                    links=db.execute('SELECT to_jsonb(aa) record FROM artwork_artists aa WHERE artwork_id=%s',(a['id'],)).fetchall()
                    assert not links
                    backup=m.BACKUP/'creator-link-reconciliation'/target/(q+'.json');save(backup,{'artwork':current,'artist_links':links,'source_creator':rec['creator_qid'],'previous_receipt':previous})
                    w.base.insert(db,'artwork_artists',dict(artwork_id=a['id'],artist_id=artist['entity_id'],attribution_role='primary',attribution_note='Existing named creator reconciled through the supplied Wikidata creator identity. Original object-level label retained as provenance.'))
                    w.base.insert(db,'citations',dict(entity_type='artwork',entity_id=a['id'],source_id=sid,field_name='named_creator_reconciled',source_record_id=q,source_url='https://www.wikidata.org/wiki/'+q,evidence_note='Supplied creator '+rec['creator_qid']+' now resolves to artist '+artist['entity_id']+'. Original artwork metadata, named-creator label and media retained.',retrieved_at=m.core.now(),created_by=ACTOR))
                save(marker,{'qid':q,'artwork_id':a['id'],'artist_id':artist['entity_id'],'backup':str(backup),'backup_sha256':m.core.sha(backup.read_bytes()),'at':m.core.now()})
                print('Reconciled named creator',target,q,rec['creator_label'],flush=True)


def final_verify():
    errors=[];targets={};snapshots={};api=[]
    selected=json.loads((RUN/'selected-museum/catalogue.json').read_bytes())
    records={r['qid']:r for r in selected['selected']}
    wiki_verification=json.loads(sorted(RUN.glob('verification-99-*.json'))[-1].read_bytes())
    assert not wiki_verification['errors']
    wiki_images=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')]
    museum_inputs=[json.loads(p.read_bytes()) for p in (RUN/'museum-images/ready').glob('*.json')]
    media_inputs=[dict(v['image'],qid=v['record']['qid']) for v in museum_inputs if v['image']]
    alternate=json.loads(next((RUN/'duplicate-sources').glob('*.json')).read_bytes())
    collection_id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/personal-artwork-collection'))
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]:
        authorities=[json.loads(p.read_bytes()) for p in (RUN/'authorities-applied'/target).glob('*.json')]
        final_artist=json.loads((RUN/'directory-final-applied'/(target+'.json')).read_bytes())
        reconciled=json.loads((RUN/'identity-resolutions'/('mher-'+target+'.json')).read_bytes())
        artists=authorities+[final_artist]
        receipts=[json.loads(p.read_bytes()) for p in (RUN/'museum-applied'/target).glob('*.json')]
        if set(records)!={v['qid'] for v in receipts}:errors.append({'target':target,'missing_museum_receipts':sorted(set(records)-{v['qid'] for v in receipts})})
        ids=[v['artwork_id'] for v in receipts]
        with m.read_only(dsn) as db:
            artist_ids=list({v['artist_id'] for v in artists}|{reconciled['canonical_id']})
            rows=db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()
            current={v['record']['id']:v['record'] for v in rows}
            artist_qids=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND (entity_id=ANY(%s::uuid[]) OR external_id=ANY(%s))",(artist_ids,list({v['creator_qid'] for v in records.values()}))).fetchall()
            qmap={v['external_id']:v['entity_id'] for v in artist_qids}
            for receipt in artists:
                aid=receipt['artist_id'];expected=reconciled['archived_after'] if aid==reconciled['archived_id'] else receipt['after']
                if current.get(aid)!=expected:errors.append({'target':target,'artist_id':aid,'error':'Artist metadata differs from receipt'})
                if receipt.get('qid') and qmap.get(receipt['qid'])!=(reconciled['canonical_id'] if aid==reconciled['archived_id'] else aid):errors.append({'target':target,'qid':receipt['qid'],'error':'Artist identity reference differs'})
                if m.core.sha(Path(receipt['backup']).read_bytes())!=receipt['backup_sha256']:errors.append({'target':target,'artist_id':aid,'error':'Artist backup checksum differs'})
            rows=db.execute('SELECT to_jsonb(a) record,to_jsonb(ma) media FROM artworks a LEFT JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
            works={v['record']['id']:v for v in rows}
            identifiers=db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(list(records),)).fetchall()
            workqids={v['external_id']:v['entity_id'] for v in identifiers}
            links=db.execute('SELECT artwork_id::text,artist_id::text,attribution_role FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
            linked=collections.defaultdict(list)
            for v in links:linked[v['artwork_id']].append(v['artist_id'])
            selected_ids={v['artwork_id'] for v in db.execute('SELECT artwork_id::text FROM curated_collection_items WHERE collection_id=%s AND artwork_id=ANY(%s::uuid[])',(collection_id,ids)).fetchall()}
            claims_added=db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[]) AND (review_state='accepted' OR claim_type='display')",([v['artwork_id'] for v in receipts if v['created']],)).fetchone()['n']
            if claims_added:errors.append({'target':target,'error':'Unexpected accepted location/display assertion','count':claims_added})
            for receipt in receipts:
                aid=receipt['artwork_id'];rec=records[receipt['qid']];actual=works.get(aid)
                if not actual or actual['record']!=receipt['after']:errors.append({'target':target,'qid':receipt['qid'],'error':'Artwork metadata differs from receipt'});continue
                a=actual['record']
                if workqids.get(rec['qid'])!=aid:errors.append({'target':target,'qid':rec['qid'],'error':'Artwork source identity differs'})
                expected_artist=qmap.get(rec['creator_qid'])
                if (expected_artist and linked[aid]!=[expected_artist]) or (not expected_artist and (linked[aid] or a['unlinked_creator_label']!=rec['creator_label'])):errors.append({'target':target,'qid':rec['qid'],'error':'Creator identity differs'})
                if rec['accession'] and a['accession_number'] and rec['accession']!=a['accession_number']:errors.append({'target':target,'qid':rec['qid'],'error':'Accession differs'})
                if receipt['created']:
                    if a['status']!='review' or not a['research_candidate'] or a['current_institution_id'] or aid not in selected_ids:errors.append({'target':target,'qid':rec['qid'],'error':'Review or collection state differs'})
                    if (a['creation_year_start'],a['creation_year_end'])!=(rec['date']['first'],rec['date']['last']):errors.append({'target':target,'qid':rec['qid'],'error':'Source date differs'})
                if receipt['image_attached']:
                    im=json.loads((RUN/'museum-images/ready'/(rec['qid']+'.json')).read_bytes())['image'];media=actual['media']
                    if not media or media['checksum_sha256']!=im['sha256'] or media['storage_path']!=im['path'] or media['byte_size']!=im['bytes'] or media['rights_status']!=im['rights_status'] or a['creation_year_end']>1955:errors.append({'target':target,'qid':rec['qid'],'error':'Media or image date differs'})
                if m.core.sha(Path(receipt['backup']).read_bytes())!=receipt['backup_sha256']:errors.append({'target':target,'qid':rec['qid'],'error':'Artwork backup checksum differs'})
            catalogue=db.execute("""SELECT to_jsonb(a) artist,
                coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id),'[]') identifiers
                FROM artists a WHERE a.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code='AM') ORDER BY a.sort_name,a.id""").fetchall()
            all_ids=[v['artist']['id'] for v in catalogue]
            artwork_rows=db.execute("""SELECT aa.artist_id::text,a.id::text,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.status,a.primary_media_id::text,ma.storage_path,
                coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers
                FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id
                WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ORDER BY aa.artist_id,a.title,a.id""",(all_ids,)).fetchall()
            size_audit=db.execute("SELECT count(*) total,count(*) FILTER(WHERE byte_size>100000) oversized,count(*) FILTER(WHERE byte_size IS NULL) unknown,max(byte_size) max_bytes FROM media_assets WHERE mime_type LIKE 'image/%%'").fetchone()
            if size_audit['oversized'] or size_audit['unknown']:errors.append({'target':target,'error':'Catalogue image size audit failed','audit':size_audit})
            targets[target]={'new_artist_profiles':sum(v['created'] for v in artists)-1,'active_armenian_profiles':len(catalogue),'museum_records':len(receipts),'new_museum_artworks':sum(v['created'] for v in receipts),'existing_museum_artworks':sum(not v['created'] for v in receipts),'museum_images':sum(v['image_attached'] for v in receipts),'new_wikiart_artworks':wiki_verification['databases'][target]['new_artworks'],'wikiart_images':wiki_verification['databases'][target]['attached'],'new_artworks':sum(v['created'] for v in receipts)+wiki_verification['databases'][target]['new_artworks'],'image_attachments':sum(v['image_attached'] for v in receipts)+wiki_verification['databases'][target]['attached'],'catalogue_image_sizes':size_audit,'armenian_artworks':len({v['id'] for v in artwork_rows}),'armenian_artworks_with_images':len({v['id'] for v in artwork_rows if v['primary_media_id']})}
            snapshots[target]={'artists':catalogue,'artworks':artwork_rows}
        print('Final database verification',target,targets[target],flush=True)
    def check_image(im):
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        result={'path':im['path'],'bytes':len(raw),'local_verified':len(raw)<=100000 and m.core.sha(raw)==im['sha256']}
        try:
            response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app'+im['path'],timeout=(15,45))
            result.update(http_status=response.status_code,public_verified=response.status_code==200 and m.core.sha(response.content)==im['sha256'])
        except m.requests.RequestException as exc:result.update(public_verified=False,error=str(exc)[:180])
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check_image,media_inputs+[alternate]))
    errors.extend(v for v in checks if not v['local_verified'] or not v['public_verified'])
    for im in media_inputs:
        receipt=json.loads((RUN/'museum-applied/cloud'/(im['qid']+'.json')).read_bytes())
        response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/atlas/artworks/'+receipt['artwork_id'],timeout=(15,45))
        record=response.json() if response.status_code==200 else {}
        good=response.status_code==200 and record.get('media_url')==im['path']
        result={'qid':im['qid'],'http_status':response.status_code,'verified':good};api.append(result)
        if not good:errors.append(dict(result,error='Public artwork API differs'))
    response=m.requests.get('https://artline-web-lpuqqlugnq-ew.a.run.app/api/backend/v1/timeline?country=AM&popular=false',timeout=(15,45))
    public_timeline={'http_status':response.status_code,'body':response.json()}
    if response.status_code!=200:errors.append({'error':'Public Armenian timeline failed','http_status':response.status_code})
    memberships={v['wikiart']['url']:v['artist']['id'] for v in json.loads((RUN/'wikiart-artist-selection.json').read_bytes())['pairs']}
    memberships.update({v['source_url']:v['artist_id'] for v in json.loads((RUN/'wikiart-extra-matches.json').read_bytes())['matches']})
    memberships.update(json.loads((RUN/'directory-final-applied/local.json').read_bytes())['matches'])
    national=json.loads((RUN/'wikiart-armenian-directory.json').read_bytes())['artists']
    unresolved_directory=[v for v in national if v['url'] not in memberships]
    if unresolved_directory:errors.append({'error':'Unresolved Armenian directory profiles','profiles':unresolved_directory})
    result={'at':m.core.now(),'databases':targets,'wikiart_directory_profiles':len(national),'wikiart_directory_resolved':len(national)-len(unresolved_directory),'public_uploaded_files':len(wiki_images)+len(media_inputs)+1,'max_uploaded_bytes':max(v['bytes'] for v in wiki_images+media_inputs+[alternate]),'new_museum_unknown_dates':sum(not v['date']['eligible'] for v in records.values()),'museum_selection_held':selected['held'],'file_checks':checks,'wikiart_verification':wiki_verification,'api_checks':api,'public_timeline':public_timeline,'snapshots':snapshots,'errors':errors}
    output=RUN/('final-verification-'+str(int(time.time()))+'.json');save(output,result)
    print('Final verification',output,'errors',len(errors),flush=True)
    for error in errors:print(json.dumps(error),flush=True)
    if errors:raise SystemExit(1)


def report():
    verification_path=sorted(RUN.glob('final-verification-*.json'))[-1]
    result=json.loads(verification_path.read_bytes());assert not result['errors']
    cloud=result['databases']['cloud'];snapshot=result['snapshots']['cloud'];base='https://artline-web-lpuqqlugnq-ew.a.run.app'
    def md(value):return str(value or 'Unknown').replace('|','\\|').replace('\n',' ')
    works=collections.defaultdict(list)
    for work in snapshot['artworks']:works[work['artist_id']].append(work)
    artist_rows=['# Armenian painter catalogue — 20 September 2026','','All active Armenian-linked source profiles in the live database after this pass. A profile is a retained source identity; two possible duplicate authority pairs remain flagged for review. Counts include earlier catalogue records, including undated and later works. Only selected images dated through 1955 were added in this pass.','','| Painter | Supplied life/activity dates | Artworks | With image | Source |','| --- | --- | ---: | ---: | --- |']
    artwork_rows=['# Armenian painter artworks — 20 September 2026','','Existing and newly retained catalogue records, grouped by painter. Unknown metadata remains unknown. Source collection links do not establish accepted holdings or current display.','','| Painter | Artwork | Supplied date | Image | Source |','| --- | --- | --- | --- | --- |']
    for row in snapshot['artists']:
        artist=row['artist'];group=works[artist['id']]
        url=base+'/?'+urlencode({'country':'AM','popular':'false','artist':artist['slug']})
        identity=next((v for v in row['identifiers'] if v['scheme']=='wikidata'),next(iter(row['identifiers']),None))
        source_link='['+md(identity['id'])+']('+identity['url']+')' if identity and identity['url'] else 'Source retained in catalogue'
        artist_rows.append('| ['+md(artist['display_name'])+']('+url+') | '+md(artist['timeline_display'])+' | '+str(len(group))+' | '+str(sum(bool(w['primary_media_id']) for w in group))+' | '+source_link+' |')
        for work in group:
            identity=next(iter(work['identifiers']),None)
            source_link='['+md(identity['id'])+']('+identity['url']+')' if identity and identity['url'] else 'Source retained in catalogue'
            image_link='[View image]('+base+work['storage_path']+')' if work['storage_path'] else 'No image'
            artwork_rows.append('| '+md(artist['display_name'])+' | '+md(work['title'])+' | '+md(work['date_display'])+' | '+image_link+' | '+source_link+' |')
    (RUN/'ARTISTS.md').write_text('\n'.join(artist_rows)+'\n')
    (RUN/'ARTWORKS.md').write_text('\n'.join(artwork_rows)+'\n')
    applied={p.stem for p in (RUN/'authorities-applied/local').glob('*.json')}
    held=[v for v in json.loads((RUN/'authority-supplement-plan.json').read_bytes())['held'] if v['qid'] not in applied]
    review=['# Retained research and unresolved identities','','## Source artist records awaiting reconciliation','','No dates were invented to force these identities into a timeline. Source captures are preserved. A nonhuman list item is excluded.','','| Source identity | Name | Review reason |','| --- | --- | --- |']
    for v in held:review.append('| ['+v['qid']+'](https://www.wikidata.org/wiki/'+v['qid']+') | '+md(v['name'])+' | '+md(v['reason'])+' |')
    review.extend(['','## Artwork source records not imported in this pass','','| Source | Reason |','| --- | --- |'])
    for v in result['museum_selection_held']:review.append('| ['+v['qid']+'](https://www.wikidata.org/wiki/'+v['qid']+') | '+md(v['reason'])+' |')
    review.extend(['','## Public alternate images','','Two Kochar 1929 views remain unresolved as separate physical objects. The files are public; no duplicate artwork record was invented.'])
    for p in (RUN/'delivery').glob('*.json'):
        receipt=json.loads(p.read_bytes())
        if receipt['targets']['cloud']['outcome']=='held':
            im=json.loads((RUN/'images'/p.name).read_bytes());review.append('\n- ['+md(im['artist']+' — '+im['title'])+']('+im['page']+'): [public image]('+base+im['path']+').')
    alternate=json.loads(next((RUN/'duplicate-sources').glob('*.json')).read_bytes())
    review.append('\nThe Bashinjaghian house image matches an existing artwork. Its source identifier and citation were added to the existing record; [the alternate image remains public]('+base+alternate['path']+').')
    review.extend(['','## Possible duplicate artist authorities','','Ohannès Alhazian (Q110176303) / Hovhannes Alkhazian (Q20511817), and Serac Arakelian (Q131582422) / Sedrak Arakelyan (Q18019593), have similar names and chronologies but distinct source identities. Both pairs retain explicit review citations; they were not merged using name similarity alone.','','## Image source decisions','','Ten selected Commons candidates remain metadata-only after file identity or rights checks. Original per-file outcomes and reasons are in `museum-images/ready/`. WikiArt public images retain the source’s actual rights label, including restricted labels; age was not relabelled as a public-domain licence.'])
    (RUN/'REVIEW.md').write_text('\n'.join(review)+'\n')
    rows=[]
    for key,title in [('new_artist_profiles','New active artist profiles'),('active_armenian_profiles','Active Armenian-linked profiles after this pass'),('new_artworks','New artwork records'),('existing_museum_artworks','Existing museum-source records enriched'),('image_attachments','New image attachments'),('armenian_artworks','Total Armenian-linked artwork records'),('armenian_artworks_with_images','Total Armenian-linked artworks with images')]:
        rows.append('| '+title+' | '+f"{result['databases']['local'][key]:,}"+' | '+f"{cloud[key]:,}"+' |')
    museum=[json.loads(p.read_bytes()) for p in (RUN/'museum-applied/cloud').glob('*.json')]
    unknown_new=sum(v['created'] and v['after']['creation_year_start'] is None for v in museum)
    source_identities=len({v['artist']['value'].rsplit('/',1)[-1] for v in json.loads((RUN/'roster-discovery.json').read_bytes())['rows']}|applied)+1
    readme='''# Armenian painters and selected artworks — 20 September 2026

Delivered to both the real local catalogue and live Artline collection.

[Open Armenian painters](https://artline-web-lpuqqlugnq-ew.a.run.app/?country=AM&popular=false) · [Full painter list](ARTISTS.md) · [Artworks and public images](ARTWORKS.md) · [Unresolved research and alternate images](REVIEW.md)

| Verified result | Local | Live |
| --- | ---: | ---: |
'''+ '\n'.join(rows)+f'''

## Coverage

Surveyed {source_identities:,} source identities: an uncapped Wikidata discovery of 567 Armenian-affiliated painter authorities, supplemented by WikiArt directory identities. All 48 profiles in [WikiArt’s Armenian nationality directory](https://www.wikiart.org/en/artists-by-nation/armenian) were reconciled. This is source coverage, not a claim that every Armenian painter in history has a complete catalogue.

The museum-source discovery captured 14,855 initial rows plus 61 supplemental rows. Selected at most eight further museum-connected records per painter and up to twelve further featured historical WikiArt works per matched profile. Existing earlier catalogue works and images were preserved.

Added {cloud['new_museum_artworks']:,} museum-source artwork records and {cloud['new_wikiart_artworks']} WikiArt artwork records. {unknown_new} new records have unknown creation dates and remain review metadata. Broad source object types, manuscripts and graphic works retain `unknown` catalogue types where mapping is unresolved. Source collection statements remain citations, not accepted holdings or on-view claims.

Eleven medieval source identities use documented activity centuries or decades. The timeline bounds describe those supplied periods; no birth or death years were invented. {len(held)-1} further named source identities and one nonhuman list item remain in the research queue. Two possible duplicate artist-authority pairs are explicitly flagged.

## Images and public delivery

Uploaded {result['public_uploaded_files']} public image files: 99 selected WikiArt files, one alternate for an already represented artwork, and 37 Commons files. Attached 97 WikiArt and 37 Commons images to artwork records. Two public Kochar views remain unresolved as separate objects; their direct image links are in the review report.

All added image dates end by 1955. Every uploaded derivative is at most 100,000 bytes; the largest is {result['max_uploaded_bytes']:,} bytes. Public files were checked against their local SHA-256 digests. Original downloads remain separately archived. Actual source rights labels and credits are retained; 26 WikiArt files still carry the source’s restricted label.

## Identity and preservation checks

- Reconciled the Mher Abeghyan/Abeghian duplicate through its explicit WikiArt identifier; archived only the newly created empty duplicate profile, preserving the established artist and artwork records.
- Preserved the Marcos Grigorian 1924/1925 and Gregorio Sciltian 1900/1898 source birth-date disagreements as review citations without replacing existing dates. [MoMA’s Grigorian authority](https://www.moma.org/artists/2341-marcos-grigorian) and [Getty’s Sciltian authority](https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500104961) supplied identity cross-checks.
- Separated repeated titles when distinct museum accession numbers establish different source objects. Six provisional same-title matches were corrected with exact recovery records; existing artwork metadata and images were preserved.
- Linked three existing Hovsep Pushman records and three Sargis Pitsak records to reconciled named-creator profiles while preserving their original object-level labels.
- Kept all newly created artists and artworks in review. Added owner collection selections separately from museum designations. No deployment, commit, accepted holding or current-display claim was made.

## Verification and recovery

Final verification: `{verification_path.name}` — zero errors. Includes exact database/receipt comparisons, authority and creator references, accession checks, review states, personal collection membership, backup hashes, public image checks and artwork API checks. The public Armenian timeline returned HTTP 200 with {result['public_timeline']['body'].get('total')} profiles in its supported range and filters. Full source-profile count above also includes records outside the timeline’s range.

Whole-catalogue image-size metadata audits found zero oversized or unknown-size images in both databases (local {result['databases']['local']['catalogue_image_sizes']['total']:,}; live {cloud['catalogue_image_sizes']['total']:,}). Existing WikiArt identity/date/compression tests: 20 passed in the project’s prepared Python environment. No fixture data or test database was created.

Exact per-target preimages, collection revisions, identity corrections and source originals:

- `/Users/vadimdulub/Library/Application Support/Artline/backups/armenian-painters-20260920/`
- `/Users/vadimdulub/Library/Application Support/Artline/source-images/armenian-painters-20260920/`
- Selected Commons originals: the backup directory’s `museum-images/selected-originals/` subdirectory.

Source captures, immutable selection evidence and individual transaction receipts remain alongside this report. The phase runner is `ops/armenian-painters-20260920.py`; final operation scripts are archived with their SHA-256 digests under the recovery directory. Earlier unsuccessful verification receipts remain preserved beside the successful final receipt.
'''
    (RUN/'README.md').write_text(readme)
    scripts=[]
    for name in ['armenian-painters-20260920.py','wikiart-artist-coverage.py','wikiart-selected-images.py','research-wikimedia-catalogues.py','prepare-wikimedia-catalogue-images.py']:
        raw=(ROOT/'ops'/name).read_bytes();digest=m.core.sha(raw);path=m.BACKUP/'operation-scripts'/(name+'.'+digest[:16]);save(path,raw);scripts.append({'name':name,'sha256':digest,'archive':str(path)})
    save(RUN/'final-operation-script-archive.json',scripts)
    print(json.dumps({'report':str(RUN/'README.md'),'verified':cloud,'public_files':result['public_uploaded_files'],'unresolved_source_identities':len(held),'max_bytes':result['max_uploaded_bytes']}),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['discover', 'source_probe', 'image_duplicate_audit', 'deduplicate_source', 'authority_plan', 'authority_apply', 'authority_supplement', 'authority_final_reconcile', 'identity_review', 'resolve_titles', 'resolve_museum_titles', 'directory_finish', 'directory_artworks', 'accession_probe', 'correct_accession_matches', 'artwork_discover', 'artwork_select', 'artwork_expand', 'artwork_prepare', 'artwork_apply', 'artwork_bulk_metadata', 'wikiart_select', 'wikiart_expand', 'wikiart_prepare', 'wikiart_deliver', 'wikiart_selection', 'wikiart_verify', 'activity_authorities', 'final_verify', 'report'])
    args = p.parse_args()
    globals()[args.phase]()
