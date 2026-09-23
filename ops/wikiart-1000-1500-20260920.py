#!/usr/bin/env python3
"""Review 1000–1500 inclusive and add a bounded selection of WikiArt highlights."""
import argparse
import collections
import csv
import difflib
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('coverage', ROOT/'ops/wikiart-artist-coverage.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
m = c.m
PRIOR = c.RUN
RUN = ROOT/'docs/research/wikiart-1000-1500-20260920'
c.RUN = m.RUN = RUN
m.BACKUP = Path.home()/'Library/Application Support/Artline/backups'/RUN.name
m.ORIGINALS = Path.home()/'Library/Application Support/Artline/source-images'/RUN.name
PREVIOUS = [PRIOR, ROOT/'docs/research/wikiart-artist-followup-20260920',
            ROOT/'docs/research/women-wikiart-20260920', c.PREVIOUS]
BaseFetcher = m.Fetcher


class Fetcher(BaseFetcher):
    def get(self, url, limit=5_000_000, image=False):
        key = m.core.sha(url.encode())
        for previous in PREVIOUS:
            receipt = previous/'captures'/(key+'.json')
            body = ((Path.home()/'Library/Application Support/Artline/source-images'/previous.name)
                    if image else previous/'captures')/(key+'.body')
            if body.exists() and receipt.exists():
                raw, record = body.read_bytes(), json.loads(receipt.read_bytes())
                if m.core.sha(raw) != record['sha256']:
                    raise ValueError('Prior source capture checksum differs')
                m.save_atomic((m.ORIGINALS if image else RUN/'captures')/body.name, raw)
                m.save_atomic(RUN/'captures'/receipt.name, record)
                return raw, record
        return super().get(url, limit, image)


c.SharedFetcher = Fetcher


def period_date(value):
    d = m.creation_date(value)
    return d if d and 1000 <= d['creation_year_start'] <= d['creation_year_end'] <= 1500 else None


c.dated = period_date


def cultural_group(source):
    return {'id':str(c.uuid.uuid5(c.uuid.NAMESPACE_URL,source['url']+'/source-group')),
        'slug':'wikiart-group-'+source['url'].rsplit('/',1)[-1],
        'display_name':'Creator not recorded — '+source['name'],'object_level_creator':True,
        'source_group':source['name'],'source_url':source['url'],'status':'review','priority':True}


def catalogue(db):
    return db.execute("""SELECT to_jsonb(a) artwork,
        coalesce((SELECT jsonb_agg(jsonb_build_object('id',p.id,'name',p.display_name,'role',aa.attribution_role))
          FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creators
        FROM artworks a WHERE a.status<>'archived' AND a.creation_year_start<=1500
        AND a.creation_year_end>=1000 ORDER BY a.id""").fetchall()


def counts(rows):
    within = [r['artwork'] for r in rows if r['artwork']['creation_year_start']>=1000 and r['artwork']['creation_year_end']<=1500]
    return {'works':len(within),'images':sum(r['primary_media_id'] is not None for r in within),
            'boundary_crossing_review':len(rows)-len(within),
            'periods':{str(y):{'works':sum(y<=r['creation_year_start']<=min(y+99,1500) for r in within),
                'images':sum(y<=r['creation_year_start']<=min(y+99,1500) and r['primary_media_id'] is not None for r in within)}
                for y in range(1000,1501,100)}}


def audit_select():
    baseline_path = RUN/'catalogue-baseline.json'
    with m.read_only() as db:
        if not baseline_path.exists():
            m.save_atomic(baseline_path, {'at':m.core.now(),'rows':catalogue(db)})
        artists = {r['record']['id']:r['record'] for r in db.execute(
            "SELECT to_jsonb(a) record FROM artists a WHERE status<>'archived'").fetchall()}
        ids = db.execute("""SELECT external_id FROM external_identifiers WHERE entity_type='artwork'
            AND scheme='wikiart-artwork' UNION SELECT source_record_id FROM citations
            WHERE entity_type='artwork' AND source_url LIKE 'https://www.wikiart.org/%%'
            AND source_record_id IS NOT NULL""").fetchall()
        excluded = {r['external_id'] for r in ids}
        pairs = {}
        for name in ('artist-matches.json','extra-artist-matches.json','priority-group-matches.json','supplemental-artist-matches.json'):
            for p in json.loads((PRIOR/name).read_bytes())['matches']:
                pairs[p['wikiart']['url']] = p
        # Delivery manifests preserve identities reconciled after the original directory audit.
        for previous in PREVIOUS:
            for path in (previous/'images').glob('*.json'):
                im = json.loads(path.read_bytes())
                if not im.get('selection_receipt'):continue
                url = im['selection_receipt']['final_url'].replace('/ru/','/en/')
                if url in pairs:
                    pairs[url]['artist'] = im['work']['artist']
        reviewed = []; selected_pairs = []; chosen = set()
        for path in sorted((PRIOR/'profiles').glob('*.json')):
            if path.name.endswith('.ru.json'):continue
            profile = json.loads(path.read_bytes()); source = profile['source']
            works = [w for w in profile['featured'] if period_date(w.get('year'))]
            if not works:continue
            pair = pairs.get(source['url']); row = {'source':source,'featured_in_period':works,
                'already_recorded':sum(w['_id'] in excluded for w in works)}
            if not pair:
                row['outcome'] = 'creator_identity_unresolved'; reviewed.append(row);continue
            artist = pair['artist']
            if source['url'].endswith('/viking-art'):
                artist=cultural_group(source)
            if not artist.get('object_level_creator'):
                if artist['id'] not in artists:
                    row['outcome'] = 'creator_authority_absent';reviewed.append(row);continue
                artist = artists[artist['id']]
            if artist['id'] in chosen:
                row['outcome'] = 'duplicate_source_profile';reviewed.append(row);continue
            chosen.add(artist['id'])
            early = any(period_date(w['year'])['creation_year_end']<1300 for w in works)
            limit = 12 if early or artist.get('priority') else 8
            artist = {**artist,'selection_limit':limit}
            pair = {'artist':artist,'wikiart':source}
            row.update(outcome='reviewed',artist_id=artist['id'],selection_limit=limit)
            reviewed.append(row); selected_pairs.append(pair)
            m.save_atomic(RUN/'profiles'/path.name,path.read_bytes())
            ru = path.with_name(path.stem+'.ru.json')
            if ru.exists():m.save_atomic(RUN/'profiles'/ru.name,ru.read_bytes())
            c.select_one(pair,db,excluded)
        # Hold close titles and coincident source titles before downloading.
        identity_holds = []
        for path in sorted((RUN/'discovery-v2').glob('*.json')):
            data = json.loads(path.read_bytes()); artist = data['artist']
            existing = c.artist_works(db,artist['id']) if not artist.get('object_level_creator') else [
                {'artwork_id':r['artwork']['id'],**r['artwork']} for r in json.loads(baseline_path.read_bytes())['rows']
                if r['artwork'].get('cultural_context')==artist.get('source_group')]
            title_counts = collections.Counter(m.norm(x['work']['title']) for x in data['matches'])
            kept = []
            for match in data['matches']:
                w = match['work']; reasons = []
                if w['creation_year_start']<1000 or w['creation_year_end']>1500:
                    reasons.append({'reason':'Existing catalogue creation range crosses period boundary'})
                if w.get('new_record'):
                    if title_counts[m.norm(w['title'])]>1:
                        reasons.append({'reason':'Multiple selected source objects share this title; individual identity review required'})
                    for other in existing:
                        if other['status']=='archived':continue
                        def name(v):return m.norm(re.sub(r'\([^)]*\)','',v or ''))
                        a = name(w['title'])
                        score = max((difflib.SequenceMatcher(None,a,name(t)).ratio() for t in
                            (other['title'],other.get('alternate_title')) if t),default=0)
                        overlap = (other['creation_year_start'] is None or other['creation_year_end'] is None or
                            w['creation_year_start']<=other['creation_year_end'] and other['creation_year_start']<=w['creation_year_end'])
                        if score>=0.8 and overlap:
                            reasons.append({'reason':'Possible existing title variant','artwork_id':other['artwork_id'],
                                'title':other['title'],'similarity':round(score,3)})
                if reasons:
                    identity_holds.append({'match':match,'reasons':reasons})
                else:
                    match['selection_basis'] = ('Owner-requested 1000–1500 historical coverage, selected from WikiArt famous-works; '
                        'up to eight additions per creator, up to twelve for early or priority traditions. '
                        'Source creation range lies wholly within 1000–1500; personal selection, no museum designation inferred.')
                    kept.append(match)
            # Immutable first selection retained before creating the reviewed manifest.
            m.save_atomic(RUN/'selection-history'/path.name,path.read_bytes())
            data['matches']=kept
            path.write_bytes(m.core.encode(data))
        m.save_atomic(RUN/'identity-holds.json',{'held':identity_holds})
        m.save_atomic(RUN/'source-review.json',{'at':m.core.now(),'profiles_scanned':len(list((PRIOR/'profiles').glob('*.json'))),
            'profiles_in_period':len(reviewed),'featured_in_period':sum(len(r['featured_in_period']) for r in reviewed),
            'reviewed':reviewed,'excluded_source_ids':sorted(excluded)})
        matches = m.discovered_matches()
        m.save_atomic(RUN/'discovered-v2.json',{'at':m.core.now(),'matches':matches})
    print(json.dumps({'baseline':counts(json.loads(baseline_path.read_bytes())['rows']),
        'profiles':len(reviewed),'selected':len(matches),'identity_holds':len(identity_holds),
        'unresolved_profiles':[r['source']['name'] for r in reviewed if r['outcome']!='reviewed']},ensure_ascii=False),flush=True)


def prepare():
    c.prepare()


def supplement():
    # Leonardo is absent from the captured A–Z directory but has a public profile.
    profile=c.profile_one({'url':'https://www.wikiart.org/en/leonardo-da-vinci',
        'name':'Leonardo da Vinci','life_display':'','birth_year':None,'death_year':None})
    stage=RUN/'supplement-selection'
    source=profile['source']
    m.save_atomic(stage/'profiles/leonardo-da-vinci.json',(RUN/'profiles/leonardo-da-vinci.json').read_bytes())
    excluded=set(json.loads((RUN/'source-review.json').read_bytes())['excluded_source_ids'])
    with m.read_only() as db:
        artist=db.execute("SELECT to_jsonb(a) record FROM artists a WHERE slug='leonardo-da-vinci'").fetchone()['record']
        if m.norm(artist['display_name'])!=m.norm(profile['name']):raise ValueError('Supplement identity differs')
        c.RUN=stage
        try:c.select_one({'artist':{**artist,'selection_limit':8},'wikiart':source},db,excluded)
        finally:c.RUN=RUN
    path=stage/'discovery-v2'/(artist['id']+'.json');data=json.loads(path.read_bytes());kept=[];held=[]
    for match in data['matches']:
        title=match['work']['title']
        if title in ('The Madonna of the Carnation','Madonna Litta (Madonna and the Child)'):
            held.append({'match':match,'reason':'Existing or cross-artist composition identity/date/attribution needs reconciliation'});continue
        match['selection_basis']='Owner-requested 1000–1500 expansion; public WikiArt famous-works selection with creation interval wholly within requested years. Personal collection highlight; no museum designation inferred.'
        kept.append(match)
    data['matches']=kept;m.save_atomic(RUN/'discovery-v2'/path.name,data)
    m.save_atomic(RUN/'supplement-source-review.json',{'source':source,'profile_receipt':profile['receipt'],
        'featured_in_period':[w for w in profile['featured'] if period_date(w.get('year'))],
        'outcome':'reviewed','artist_id':artist['id'],'held':held})
    print('Supplement reviewed',len(profile['featured']),'selected',len(kept),flush=True)


def reconcile():
    """Resolve source aliases and differing life dates without changing artists."""
    names={'domenico-ghirlandaio':'Domenico Ghirlandaio','giotto':'Giotto di Bondone',
        'jean-fouquet':'Jean Fouquet','paolo-uccello':'Paolo Uccello',
        'piero-della-francesca':'Piero della Francesca','pietro-perugino':'Pietro Perugino',
        'sassetta':'Stefano di Giovanni'}
    review=json.loads((RUN/'source-review.json').read_bytes());resolutions=[];held=[]
    stage=RUN/'reconciliation-selection'
    with m.read_only() as db:
        for row in review['reviewed']:
            if row['outcome']=='reviewed':continue
            source=row['source'];slug=source['url'].rsplit('/',1)[-1];name=names[slug]
            candidates=db.execute("SELECT to_jsonb(a) record FROM artists a WHERE display_name=%s AND status<>'archived'",(name,)).fetchall()
            if len(candidates)!=1:raise ValueError('Reviewed creator identity no longer unique')
            artist={**candidates[0]['record'],'selection_limit':12 if slug=='giotto' else 8}
            profile=json.loads((PRIOR/'profiles'/(slug+'.json')).read_bytes())
            raw,receipt=Fetcher().get(source['url']);soup=c.BeautifulSoup(raw,'html.parser')
            labels=[x.get_text(' ',strip=True) for x in soup.select('h1,h2')]
            wikipedia=[a['href'] for a in soup.select('a[href]') if 'en.wikipedia.org/wiki/' in a['href']]
            terms=labels+[u.rsplit('/',1)[-1].replace('_',' ') for u in wikipedia]
            if m.norm(name) not in {m.norm(t) for t in terms}:raise ValueError('Exact creator alias not corroborated by profile')
            resolution={'artist_id':artist['id'],'name':name,'source_url':source['url'],'source_labels':labels,
                'source_life':source['life_display'],'catalogue_life':[artist['birth_year'],artist['death_year']],
                'profile_receipt':receipt,'wikipedia_identity_links':sorted(set(wikipedia)),
                'decision':'Unique existing authority matches exact source name/alias or linked identity. Life-date disagreement retained for review; no artist metadata changes.'}
            resolutions.append(resolution)
            m.save_atomic(stage/'profiles'/(slug+'.json'),(PRIOR/'profiles'/(slug+'.json')).read_bytes())
            m.save_atomic(RUN/'profiles'/(slug+'.json'),(PRIOR/'profiles'/(slug+'.json')).read_bytes())
            c.RUN=stage
            try:c.select_one({'artist':artist,'wikiart':source},db,set(review['excluded_source_ids']))
            finally:c.RUN=RUN
            path=stage/'discovery-v2'/(artist['id']+'.json');data=json.loads(path.read_bytes())
            existing=c.artist_works(db,artist['id']);kept=[]
            totals=collections.Counter(m.norm(x['work']['title']) for x in data['matches'])
            for match in data['matches']:
                w=match['work'];reasons=[]
                if w['creation_year_start']<1000 or w['creation_year_end']>1500:reasons.append('Existing date crosses requested period')
                if w.get('new_record'):
                    if totals[m.norm(w['title'])]>1:reasons.append('Coincident selected title')
                    for other in existing:
                        overlap=other['creation_year_start'] is None or other['creation_year_end'] is None or w['creation_year_start']<=other['creation_year_end'] and other['creation_year_start']<=w['creation_year_end']
                        score=max((difflib.SequenceMatcher(None,m.norm(w['title']),m.norm(t)).ratio() for t in (other['title'],other.get('alternate_title')) if t),default=0)
                        if overlap and score>=0.8:reasons.append({'reason':'Possible existing title variant','id':other['artwork_id'],'title':other['title']})
                if reasons:held.append({'match':match,'reasons':reasons});continue
                match['selection_basis']='Owner-requested 1000–1500 period expansion, selected WikiArt famous-works with full creation interval within requested years. Personal selection; no museum designation or holding inferred.'
                match['creator_identity_review']=resolution
                kept.append(match)
            data['matches']=kept
            m.save_atomic(RUN/'discovery-v2'/path.name,data)
            print('Reconciled',name,'selected',len(kept),flush=True)
    m.save_atomic(RUN/'creator-reconciliation.json',{'resolutions':resolutions,'held':held})
    m.save_atomic(RUN/'discovered-final.json',{'matches':m.discovered_matches(),'at':m.core.now()})


def preflight():
    images = [json.loads(p.read_bytes()) for p in sorted((RUN/'images').glob('*.json'))]
    hashes = collections.defaultdict(list)
    for im in images:hashes[im['sha256']].append(im)
    held=[];approved=[]
    visual=json.loads((RUN/'visual-review.json').read_bytes()) if (RUN/'visual-review.json').exists() else {'pairs':[]}
    visual_holds={p['candidate']['artwork_id'] for p in visual['pairs']}
    with m.read_only() as db:
        rows=db.execute("""SELECT a.id::text,a.title,m.checksum_sha256 FROM media_assets m
            JOIN artworks a ON a.primary_media_id=m.id WHERE m.checksum_sha256=ANY(%s)
            AND a.status<>'archived'""",(list(hashes),)).fetchall()
        existing=collections.defaultdict(list)
        for r in rows:existing[r['checksum_sha256']].append(r)
        for im in images:
            reasons=[]
            if im['work'].get('new_record') and re.search(r'\bdetail\b',im['title'],re.I):
                reasons.append({'reason':'Source labels a detail view; parent object identity needs reconciliation before creating another artwork'})
            if im['artwork_id'] in visual_holds:
                reasons.append({'reason':'Similar reproduction flagged for individual identity review; see visual-review.json'})
            if existing[im['sha256']]:reasons.append({'reason':'Exact reproduction already attached','records':existing[im['sha256']]})
            if len(hashes[im['sha256']])>1:reasons.append({'reason':'Multiple selected objects share identical reproduction','ids':[x['artwork_id'] for x in hashes[im['sha256']]]})
            state=c.target_before(db,im)
            if state['outcome']=='held':reasons.append(state)
            if not 1000<=im['work']['creation_year_start']<=im['work']['creation_year_end']<=1500:
                reasons.append({'reason':'Prepared date outside requested period'})
            if reasons:
                path=RUN/'images'/(im['artwork_id']+'.json')
                m.save_atomic(RUN/'prepared-held'/path.name,{'image':im,'reasons':reasons})
                path.unlink() # Manifest quarantined with evidence; artwork/assets preserved.
                held.append({'artwork_id':im['artwork_id'],'reasons':reasons})
            else:approved.append(im['artwork_id'])
    m.save_atomic(RUN/'preflight.json',{'at':m.core.now(),'approved':approved,'held':held})
    print('Preflight approved',len(approved),'held',len(held),flush=True)


def visual_review():
    from PIL import Image, ImageDraw, ImageOps
    def fingerprint(path):
        with Image.open(path) as im:
            ratio=im.width/im.height
            gray=ImageOps.grayscale(im)
            a=list(gray.resize((9,8)).getdata());b=list(gray.resize((8,9)).getdata())
            bits=[a[y*9+x]>a[y*9+x+1] for y in range(8) for x in range(8)]
            bits += [b[y*8+x]>b[(y+1)*8+x] for y in range(8) for x in range(8)]
            value=0
            for bit in bits:value=(value<<1)|int(bit)
        return ratio,value
    images=[json.loads(p.read_bytes()) for p in sorted((RUN/'images').glob('*.json'))]
    with m.read_only() as db:
        rows=db.execute("""SELECT a.id::text artwork_id,a.title,m.storage_path path,m.checksum_sha256 sha256
            FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.status<>'archived'
            AND a.creation_year_start<=1500 AND a.creation_year_end>=1000""").fetchall()
    pool=[];missing=[]
    for r in rows:
        path=ROOT/'apps/web/public'/r['path'].lstrip('/')
        if not path.is_file():missing.append(r['artwork_id']);continue
        pool.append((r,*fingerprint(path)))
    pairs=[]
    for im in images:
        path=ROOT/'apps/web/public'/im['path'].lstrip('/');ratio,value=fingerprint(path)
        for other,other_ratio,other_value in pool:
            if abs(ratio/other_ratio-1)>0.04:continue
            distance=(value^other_value).bit_count()
            if distance<=10:
                pairs.append({'candidate':{k:im[k] for k in ('artwork_id','title','path','sha256')},
                    'other':other,'distance':distance,'decision':'Held for composition identity review; no automatic merge'})
        pool.append(({k:im[k] for k in ('artwork_id','title','path','sha256')},ratio,value))
    m.save_atomic(RUN/'visual-review.json',{'at':m.core.now(),'method':'128-bit horizontal/vertical difference hash; distance <=10 and aspect difference <=4%; flag only',
        'existing_local_images_reviewed':len(rows)-len(missing),'missing_local_images':missing,'pairs':pairs})
    for start in range(0,len(pairs),8):
        group=pairs[start:start+8];canvas=Image.new('RGB',(1100,250*len(group)),'white');draw=ImageDraw.Draw(canvas)
        for i,pair in enumerate(group):
            for j,key in enumerate(('candidate','other')):
                item=pair[key]
                with Image.open(ROOT/'apps/web/public'/item['path'].lstrip('/')) as source:
                    thumb=ImageOps.contain(source,(320,208));canvas.paste(thumb,(j*550+5,i*250+30))
                draw.text((j*550+5,i*250+4),str(start+i)+' '+item['title'][:68],fill='black')
                draw.text((j*550+335,i*250+40),item['artwork_id'][:12],fill='black')
        canvas.save('/tmp/artline-period-visual-'+str(start//8)+'.jpg')
    print('Visual comparison pairs',len(pairs),'missing local references',len(missing),flush=True)


def correct_creator_kind():
    """Correct only this run's new works that inherited an older false person mapping."""
    if not (RUN/'delivery-finished.json').exists():raise ValueError('Wait until delivery finishes')
    paths=[p for p in (RUN/'images').glob('*.json')
        if json.loads(p.read_bytes())['artist_slug']=='wikiart-artist-viking-art']
    dbs={t:m.psycopg.connect(dsn,autocommit=True,row_factory=m.dict_row) for t,dsn in
        [('local','postgres://localhost/artline'),('cloud',m.core.cloud_dsn())]}
    corrected=[]
    try:
        for path in paths:
            im=json.loads(path.read_bytes());aid=im['artwork_id']
            delivery=json.loads((RUN/'delivery'/path.name).read_bytes())
            if all(not result.get('created') for result in delivery['targets'].values()):
                continue
            if not im['work'].get('new_record'):raise ValueError('Correction scope excludes earlier artworks')
            source={'url':'https://www.wikiart.org/en/viking-art','name':'Viking art'}
            label='Creator not recorded — Viking art'
            note={'reason':'Viking art identifies a cultural tradition, not a named person. This run inherited an older person-authority mapping; retain source tradition at object level.',
                'source_profile':im['selection_receipt'],'prior_artist':im['work']['artist'],
                'scope':'Only new artworks created by this campaign; earlier authority and artworks preserved.'}
            m.save_atomic(RUN/'creator-kind-history/images'/path.name,im)
            m.save_atomic(RUN/'creator-kind-history/delivery'/path.name,delivery)
            for target,db in dbs.items():
                result=delivery['targets'][target]
                if result['outcome'] not in ('attached','already_attached') or not result.get('created'):
                    raise ValueError('Correction requires this run created the target artwork')
                with db.transaction():
                    artwork=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['record']
                    if artwork!=result['after']:raise ValueError('Artwork changed before creator correction')
                    links=db.execute('SELECT to_jsonb(a) record FROM artwork_artists a WHERE artwork_id=%s',(aid,)).fetchall()
                    if len(links)!=1 or links[0]['record']['artist_id']!=im['work']['artist']['id']:
                        raise ValueError('Unexpected creator mapping')
                    media=db.execute('SELECT to_jsonb(a) record FROM media_assets a WHERE id=%s FOR UPDATE',(im['media_id'],)).fetchone()['record']
                    backup=m.BACKUP/'creator-kind-correction'/target/path.name
                    m.save_atomic(backup,{'artwork':artwork,'creators':links,'media':media,'note':note})
                    db.execute('DELETE FROM artwork_artists WHERE artwork_id=%s AND artist_id=%s',(aid,im['work']['artist']['id']))
                    db.execute("""UPDATE artworks SET unlinked_creator_label='Creator not recorded',cultural_context='Viking art',
                        revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s""",(m.ACTOR,aid))
                    db.execute('UPDATE media_assets SET creator_credit=%s,alt_text=%s,attribution_text=%s WHERE id=%s',
                        (label+'; WikiArt',im['title']+' — '+label,im['attribution_text'].replace(im['artist']+'.',label+'.',1),im['media_id']))
                    sid=db.execute("SELECT id FROM sources WHERE slug='wikiart-artist-coverage-20260920'").fetchone()['id']
                    db.execute("""INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                        VALUES('artwork',%s,%s,'creator_kind_review',%s,%s,%s,now(),%s)""",
                        (aid,sid,im['source_id'],source['url'],json.dumps(note,ensure_ascii=False),m.ACTOR))
                    after=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s',(aid,)).fetchone()['record']
                old=RUN/'applied'/target/path.name
                m.save_atomic(RUN/'creator-kind-history/applied'/target/path.name,old.read_bytes())
                result.update(after=after,creator_kind_correction={'backup':str(backup),'sha256':m.core.sha(backup.read_bytes())})
                old.write_bytes(m.core.encode(result))
            im['work'].update(artist=cultural_group(source),creators=[],unlinked_creator_label='Creator not recorded',cultural_context='Viking art')
            im.update(artist=label,artist_slug=im['work']['artist']['slug'],attribution_text=im['attribution_text'].replace(im['artist']+'.',label+'.',1))
            path.write_bytes(m.core.encode(im));(RUN/'delivery'/path.name).write_bytes(m.core.encode(delivery))
            corrected.append(aid)
    finally:
        for db in dbs.values():db.close()
    m.save_atomic(RUN/'creator-kind-correction.json',{'at':m.core.now(),'artwork_ids':corrected,
        'decision':'Viking art retained as cultural context, creators unrecorded; no invented person or lifespan.'})
    print('Corrected cultural-group attribution',len(corrected),'in both databases',flush=True)


def report():
    baseline=json.loads((RUN/'catalogue-baseline.json').read_bytes())['rows']
    latest=sorted(RUN.glob('verification-*.json'),key=lambda p:p.stat().st_mtime)[-1]
    verification=json.loads(latest.read_bytes())
    if verification['errors']:raise ValueError('Delivery verification has unresolved errors')
    with m.read_only() as db:after=catalogue(db)
    before=counts(baseline);current=counts(after)
    images=[json.loads(p.read_bytes()) for p in (RUN/'images').glob('*.json')]
    source=json.loads((RUN/'source-review.json').read_bytes())
    if (RUN/'supplement-source-review.json').exists():
        extra=json.loads((RUN/'supplement-source-review.json').read_bytes())
        source['reviewed'].append(extra);source['profiles_in_period']+=1
        source['featured_in_period']+=len(extra['featured_in_period'])
    review=[]
    for year in range(1000,1501):
        row={'year':year}
        for label,rows in [('before',baseline),('after',after)]:
            within=[r['artwork'] for r in rows if 1000<=r['artwork']['creation_year_start']<=r['artwork']['creation_year_end']<=1500]
            # Circa and ranges are never represented as confirmed exact dates.
            row[label+'_exact_year_works']=sum(w['creation_year_start']==w['creation_year_end']==year and w['date_precision']=='exact' for w in within)
            row[label+'_dated_to_year_works']=sum(w['creation_year_start']==w['creation_year_end']==year for w in within)
            row[label+'_interval_includes_year']=sum(w['creation_year_start']<=year<=w['creation_year_end'] for w in within)
            row[label+'_illustrated_interval_includes_year']=sum(w['creation_year_start']<=year<=w['creation_year_end'] and w['primary_media_id'] is not None for w in within)
        row['wikiart_featured_intervals_including_year']=sum(period_date(w['year'])['creation_year_start']<=year<=period_date(w['year'])['creation_year_end'] for r in source['reviewed'] for w in r['featured_in_period'])
        review.append(row)
    with (RUN/'year-by-year-review.csv').open('w',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(review[0]));writer.writeheader();writer.writerows(review)
    receipts=[json.loads(p.read_bytes()) for p in (RUN/'delivery').glob('*.json')]
    new_ids={r['targets']['local']['after']['id'] for r in receipts if r['targets']['local'].get('created')}
    with m.read_only() as db:
        institutional=db.execute('SELECT count(*) n FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(list(new_ids),)).fetchone()['n']
    if institutional:raise ValueError('Unexpected holding assertions')
    prior={r['artwork']['id']:r['artwork'] for r in baseline};now={r['artwork']['id']:r['artwork'] for r in after}
    changed=[]
    for aid,w in prior.items():
        if aid not in now or not m.same_artwork(w,now[aid]) or w['current_institution_id']!=now[aid]['current_institution_id']:
            changed.append(aid)
    delivered_ids={r['targets']['local']['after']['id'] for r in receipts
        if r['targets']['local']['outcome'] in ('attached','already_attached')}
    if set(changed)&delivered_ids:raise ValueError('Campaign artwork metadata changed outside recorded delivery')
    concurrent_changes=[{'artwork_id':aid,'before':prior[aid],'current':now.get(aid),
        'scope':'Outside every artwork targeted by this campaign; concurrent change preserved.'} for aid in changed]
    before_creators={r['artwork']['id']:r['creators'] for r in baseline}
    if any(r['creators']!=before_creators[r['artwork']['id']] for r in after if r['artwork']['id'] in before_creators):
        raise ValueError('Existing creator attribution changed')
    summary={'at':m.core.now(),'requested_years':[1000,1500],'years_reviewed':len(review),'baseline':before,'after':current,
        'source_profiles_in_period':source['profiles_in_period'],'source_featured_in_period':source['featured_in_period'],
        'verification':str(latest.relative_to(ROOT)), 'delivery':{k:v for k,v in verification.items() if k not in ('file_checks','api_checks')},
        'new_before_1300':sum(im['artwork_id'] in new_ids and im['work']['creation_year_end']<1300 for im in images),
        'concurrent_additions_outside_this_delivery':sorted(set(now)-set(prior)-new_ids),
        'years_without_dated_to_year_work':sum(r['after_dated_to_year_works']==0 for r in review),
        'baseline_records_unchanged':len(prior)-len(changed),'concurrent_metadata_changes':concurrent_changes,
        'new_holding_assertions':institutional}
    if (RUN/'completed-summary.json').exists():
        summary['at']=json.loads((RUN/'completed-summary.json').read_bytes())['at']
    m.save_atomic(RUN/'completed-summary.json',summary)
    text=['# WikiArt 1000–1500 review — 20 September 2026','',
        f"Reviewed all 501 years, inclusive, against the local catalogue and {source['featured_in_period']:,} dated WikiArt famous-works entries across {source['profiles_in_period']} creator/tradition profiles.", '',
        f"Added {verification['databases']['local']['new_artworks']} review artwork records with images in local and production databases. Verified {verification['uploaded']} selected image associations, including one already-attached record preserved during delivery. All public image files were fetched and verified by SHA-256; maximum {verification['max_bytes']:,} bytes.", '',
        'Catalogue snapshot counts also include concurrent additions outside this delivery; this campaign’s additions are listed separately.', '',
        '| Creation start | New in this pass | Works before | Works after | Images before | Images after |','|---|---:|---:|---:|---:|---:|']
    for p in before['periods']:
        b,a=before['periods'][p],current['periods'][p]
        added=sum(im['artwork_id'] in new_ids and int(p)<=im['work']['creation_year_start']<=min(int(p)+99,1500) for im in images)
        label=p if p=='1500' else p+'–'+str(int(p)+99)
        text.append(f"| {label} | {added} | {b['works']} | {a['works']} | {b['images']} | {a['images']} |")
    text += ['', 'The [year-by-year audit](year-by-year-review.csv) distinguishes exact dates, source dates including circa, and intervals that intersect each year. Ranges do not establish that a work was made in every year they span. Remaining empty years are recorded; no years, biographies, types, museum holdings, or display claims were invented.', '',
        'New works retain review status and enter the personal owner collection, distinct from a museum designation. Object-level creator labels preserve traditions without inventing person authorities. Source rights labels, original captures, rejected identity candidates, and per-target recovery receipts are retained. Existing catalogue metadata and primary images were preserved.', '',
        'Selection is bounded to up to eight additional featured works per creator and up to twelve for early/priority profiles, after date and identity checks. This is a review and selected expansion, not an exhaustive collection of every artwork created during these centuries. Similar-title identities and identical reproductions remain held when unresolved.', '',
        'Evidence: [source review](source-review.json), [identity holds](identity-holds.json), [preflight](preflight.json), [verified totals](completed-summary.json).', '',
        f'Recovery backups: `{m.BACKUP}`. Source originals: `{m.ORIGINALS}`.', '']
    if concurrent_changes:
        text += [f"The final read-only audit also observed {len(concurrent_changes)} concurrent metadata updates to existing artworks outside this campaign's delivery list. These were preserved and recorded in the completion summary; this campaign did not write those records.", '']
    (RUN/'README.md').write_text('\n'.join(text))
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['audit_select','reconcile','supplement','prepare','visual_review','preflight','deliver_ready','correct_creator_kind','sync_selection','verify','report'])
    args=parser.parse_args()
    (globals().get(args.phase) or getattr(c,args.phase))()
