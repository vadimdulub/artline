#!/usr/bin/env python3
"""Bounded primary-source research; application phases require pinned review."""
import argparse
import base64
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import subprocess
import unicodedata
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse

import psycopg
import requests
from bs4 import BeautifulSoup
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/dutch-german-museums-20260917'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/dutch-german-museums-20260917')
spec = importlib.util.spec_from_file_location('image_core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
SOURCE = 'dutch-german-selected-museums-20260917'
CREATOR_CROSSWALKS = {
    'Raffael': ('Raphael',1483,1520),
    'Jan Vermeer': ('Johannes Vermeer',1632,1675),
    'Jan Brueghel d. Ä.': ('Jan Brueghel the Elder',1568,1625),
}
GEO = {
 'Q700959': ('Cologne','Köln','https://www.wallraf.museum/das-museum/besucherinformationen/kontakt/'),
 'Q11722011': ('The Hague','Den Haag',None),
 'Q125634': ('Essen','45128 Essen',None),
 'Q1287950': ('Dachau','85221 Dachau',None),
 'Q1501219': ('Kassel','Kassel','https://www.heritage-kassel.de/standorte/gemaeldegalerie-alte-meister'),
 'Q1505892': ('Enschede','7514 BP Enschede',None),
 'Q154568': ('Munich','München',None),
 'Q162610': ('Berlin','Berlin',None),
 'Q2324618': ('Schwerin','19055 Schwerin',None),
 'Q250195': ('Munich','80333 München',None),
 'Q260913': ('Utrecht','Utrecht','https://www.centraalmuseum.nl/nl/over-het-museum/contact'),
 'Q318859': ('Bonn','53113 Bonn',None),
 'Q32659772': ('Berlin','Berlin','https://www.smb.museum/en/museums-institutions/neue-nationalgalerie/plan-your-visit/'),
 'Q461277': ('Düsseldorf','Düsseldorf',None),
 'Q472706': ('Dresden','Dresden','https://albertinum.skd.museum/besuch/'),
 'Q542932': ('Freiburg im Breisgau','79098 Freiburg im Breisgau',None),
 'Q573656': ('Schwerin','19053 Schwerin',None),
 'Q574961': ('Haarlem','Groot Heiligland 62, Haarlem',None),
 'Q665171': ('Hamburg','Hamburg',None),
 'Q830042': ('Dresden','Dresden','https://galerie-dresden.de/besuch/lage-anreise'),
 'Q924335': ('Amsterdam','1071 DJ Amsterdam',None),
}


def backup_verify():
    path = BACKUP / 'local-before.dump'
    listing = subprocess.check_output(['pg_restore', '--list', str(path)], text=True)
    assert 'TABLE DATA public artworks' in listing and 'TABLE DATA public media_assets' in listing
    cloud = json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1789643238621','--instance=artline-postgres','--project=artline-508319','--format=json'], text=True))
    assert cloud['status'] == 'SUCCESSFUL'
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    save(RUN/'backups.json', {'at':core.now(),'local':{'path':str(path),'bytes':path.stat().st_size,'sha256':digest,'directory_verified':True},'cloud':cloud})
    print('Both pre-mutation backups verified', flush=True)


def geography_plan():
    facts = []
    for row in load(RUN/'geography-captures.json'):
        i = row['institution']; q = i['wikidata_id']; city, needle, follow = GEO[q]
        if follow:
            soup, receipt = capture(follow, 'geo-follow-'+q)
            for t in soup(['script','style','noscript']): t.decompose()
            text = soup.get_text(' ',strip=True)
        else:
            assert not row.get('error')
            text, receipt = row['text'], row['receipt']
        assert needle in text, (q, needle, 'Required geographic source text absent')
        at = text.index(needle)
        facts.append({'slug':i['slug'],'qid':q,'name':i['name'],'city':city,'country':i['research_country'],
            'source':receipt,'evidence_excerpt':text[max(0,at-100):at+len(needle)+140],
            'venue_name': 'Albertinum' if q=='Q472706' else i['name'],
            'create_venue':q not in ('Q162610','Q11722011'),
            'note':'Institution geography only. Composite/umbrella venue identity held.' if q in ('Q162610','Q11722011') else 'Physical museum venue; no object display or opening-status assertion.'})
    result = {'at':core.now(),'facts':facts,'targets':{}}
    for target in ('local','cloud'):
        with connect(target) as db:
            rows=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=ANY(%s) ORDER BY slug',([f['slug'] for f in facts],)).fetchall()
            assert len(rows)==len(facts) and all(r['row']['place_id'] is None for r in rows)
            places=db.execute('SELECT id::text,name,country_code FROM places WHERE country_code IN (\'NL\',\'DE\') ORDER BY id').fetchall()
            target_rows=[]
            for f in facts:
                before=next(r['row'] for r in rows if r['row']['slug']==f['slug'])
                assert before['wikidata_id']==f['qid'] and before['status']!='archived'
                assert not db.execute('SELECT 1 FROM institution_venues WHERE institution_id=%s',(before['id'],)).fetchone()
                peers=[p for p in places if p['country_code']==f['country'] and norm(p['name'])==norm(f['city'])]
                place=peers[0] if peers else {'id':uid('place/'+f['country']+'/'+f['city']),'name':f['city'],'country_code':f['country']}
                target_rows.append({'fact':f,'before':before,'place':place,'place_new':not bool(peers)})
            result['targets'][target]=target_rows
            save(BACKUP/(target+'-geography-preimages.json'),target_rows)
    save(RUN/'geography-plan.json',result)
    print('Geography plan:',len(facts),'places;',sum(f['create_venue'] for f in facts),'physical venues',flush=True)


def ensure_source(db):
    sid=uid('source')
    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,'Dutch and German museums — selected primary-source review','collection_page','https://www.sammlung.pinakothek.de/') ON CONFLICT(slug) DO NOTHING",(sid,SOURCE))
    assert str(db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id'])==sid
    return sid


def reviewed_plan(name):
    backup=load(RUN/'backups.json')
    assert backup['local']['directory_verified'] and backup['cloud']['status']=='SUCCESSFUL'
    assert Path(backup['local']['path']).stat().st_size==backup['local']['bytes']
    raw=(RUN/(name+'-plan.json')).read_bytes(); review=load(RUN/(name+'-review.json'))
    assert review['approved'] is True and review['plan_sha256']==core.sha(raw)
    return json.loads(raw), review


def geography_apply(target):
    plan,review=reviewed_plan('geography');result=[]
    with connect(target,False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'")
        db.execute('SELECT pg_advisory_xact_lock(559320260917)')
        sid=ensure_source(db)
        for item in plan['targets'][target]:
            before=item['before'];f=item['fact'];p=item['place'];iid=before['id']
            now=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s FOR UPDATE',(iid,)).fetchone()['row']
            assert now==before, 'Institution changed after preflight: '+f['slug']
            assert db.execute('SELECT 1 FROM countries WHERE code=%s',(p['country_code'],)).fetchone()
            if item['place_new']:
                db.execute('INSERT INTO places(id,name,normalized_name,country_code) VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING',(p['id'],p['name'],norm(p['name']),p['country_code']))
            current=db.execute('SELECT name,country_code FROM places WHERE id=%s',(p['id'],)).fetchone()
            assert current and current['name']==p['name'] and current['country_code']==p['country_code']
            db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s AND place_id IS NULL',(p['id'],iid))
            if f['create_venue']:
                # Preserve the successfully fetched HTTPS entry point when a
                # museum's own redirect downgrades to HTTP. Receipt retains both.
                venue_url=f['source']['url'] if f['source']['url'].startswith('https://') else f['source']['requested_url']
                assert venue_url.startswith('https://')
                db.execute('''INSERT INTO institution_venues(id,institution_id,slug,name,place_id,visit_url,source_url,checked_at,status)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'review')''',
                  (uid('venue/'+f['slug']),iid,f['slug']+'-verified-location',f['venue_name'],p['id'],venue_url,venue_url,f['source']['at']))
            db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_url,evidence_note,retrieved_at,created_by)
              VALUES('institution',%s,'country_city_venue',%s,%s,%s,%s,%s)''',
              (iid,sid,f['source']['url'],json.dumps(f,ensure_ascii=False),f['source']['at'],core.ACTOR))
            db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,iid))
            after=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(iid,)).fetchone()['row']
            assert {k:v for k,v in after.items() if k not in ('place_id','updated_at')}=={k:v for k,v in before.items() if k not in ('place_id','updated_at')}
            result.append({'slug':f['slug'],'institution_id':iid,'place_id':p['id'],'venue_created':f['create_venue'],'status_preserved':after['status']})
    save(RUN/(target+'-geography-applied.json'),{'at':core.now(),'plan_sha256':review['plan_sha256'],'records':result})
    print(target,'geography applied',len(result),'venues',sum(r['venue_created'] for r in result),flush=True)


def parse_date(raw):
    """Conservative source-date parser. Slash-separated phases stay uncertain."""
    m=re.fullmatch(r'(?:(c\.|ca\.|um)\s*)?(\d{4})(?:\s*[-–]\s*(\d{4}))?',raw.strip())
    if not m:
        return {'first':None,'last':None,'precision':'unknown','display':raw}
    first,last=int(m[2]),int(m[3] or m[2])
    assert first<=last
    return {'first':first,'last':last,'precision':('circa_range' if m[1] else 'range') if first!=last else ('circa' if m[1] else 'exact'),'display':raw}


def parse_objects():
    out=[]
    for item in load(RUN/'object-captures.json'):
        assert not item.get('error')
        path=RUN/'captures'/(item['key']+'.html'); assert core.sha(path.read_bytes())==item['receipt']['sha256']
        soup=BeautifulSoup(path.read_bytes(),'html.parser'); fields={}
        if item['museum']=='pinakothek':
            for label in soup.select('.artwork__data .label-header'):
                name=label.get_text(' ',strip=True); parent=label.parent; label.extract();fields[name]=parent.get_text(' ',strip=True)
            title=soup.select_one('.artwork__title').get_text(' ',strip=True).rstrip(',')
            creator=soup.select_one('.artwork__artist').get_text(' ',strip=True)
            dates=soup.select('.artwork__main .artwork__dates'); life=dates[0].get_text(' ',strip=True); raw=dates[-1].get_text(' ',strip=True) if len(dates)>1 else 'Not stated'
            accession=fields.get('Inventory number'); medium=fields.get('Material / Technology / Carrier'); kind='painting' if fields.get('Genre')=='Malerei' else 'unknown'
            download=soup.select_one('a.artwork__action.action--download[href]')
            license_tag=soup.select_one('a.action--creativecommons[href]')
            image_url=download['href'] if download else None
            license_url=license_tag['href'] if license_tag else None
            image_hold=None if license_url=='https://creativecommons.org/licenses/by-sa/4.0/' else 'No explicit supported object-level image licence'
            collection=fields.get('Collection',''); displayed=fields.get('Displayed','')
            # Collection is authoritative for museum association. Displayed may
            # name a different building (e.g. Neue works temporarily in Alte).
            institution=('sammlung-schack' if 'Sammlung Schack' in collection else 'alte-pinakothek' if 'Alte Pinakothek' in collection else 'neue-pinakothek' if 'Neue Pinakothek' in collection else 'wikimedia-museum-q250195' if 'Pinakothek der Moderne' in collection else None)
            native=re.search(r'/artwork/([^/]+)',item['url'])[1]
        else:
            for tr in soup.select('tr'):
                cells=tr.find_all(['td','th'],recursive=False)
                if len(cells)==2: fields[cells[0].get_text(' ',strip=True)]=cells[1].get_text(' ',strip=True)
            title=fields.get('Title'); maker=fields.get('Artist',''); creator=re.sub(r'\s*\([^)]*\d{4}[^)]*\)','',maker).strip(); life=maker
            raw=fields.get('Dated',''); accession=fields.get('Inventory number');medium=' '.join(filter(None,[fields.get('Technique'),fields.get('Material')]))
            kind='painting' if fields.get('Object name')=='painting' else 'unknown'
            image_url=None;license_url=None;image_hold='Object download modal limits non-commercial reuse; conflicts with general Dutch image policy. No direct image download authorized by this review.'
            collection='Mauritshuis';displayed=fields.get('On view','');institution='mauritshuis';native=re.search(r'/artworks/(\d+)',item['url'])[1]
        assert title and creator and accession and raw, (item['key'],fields)
        out.append({'key':item['key'],'museum':item['museum'],'native_id':native,'title':title,'creator_label':creator,'creator_source':life,
            'date':parse_date(raw),'work_type':kind,'medium':medium,'dimensions':fields.get('Dimensions of the object') or fields.get('Dimensions'),
            'accession':accession,'institution_slug':institution,'collection_label':collection,'display_text_not_asserted':displayed,
            'url':item['url'],'source':item['receipt'],'fields':fields,'image_url':image_url,'license_url':license_url,'image_hold':image_hold})
    save(RUN/'parsed-objects-v2.json',out)
    for r in out: print(r['museum'],r['native_id'],r['institution_slug'],r['accession'],r['creator_label'],r['title'],r['date']['display'],r['work_type'],flush=True)


def berlin_capture():
    rows=[]
    # Bounded, individually selected collection records, not a museum crawl.
    for ident in ['868435','870129','863178','870774']:
        soup,receipt=capture('https://search.smb.museum/object/obj-'+ident,'berlin-'+ident)
        fields={}
        for dt in soup.select('dt'):
            dd=dt.find_next_sibling('dd')
            if dd: fields[dt.get_text(' ',strip=True)]=dd.get_text(' ',strip=True)
        title=soup.h1.get_text(' ',strip=True);text=soup.get_text(' ',strip=True)
        accession=re.search(r'Ident\. Nr\.:\s*(.*?)\s*ObjID:',text)[1]
        creator_node=next(dt.find_next_sibling('dd') for dt in soup.select('dt') if dt.get_text(' ',strip=True)=='Beteiligte')
        creator=creator_node.find('a').get_text(' ',strip=True)
        raw=fields['Datierung'].removeprefix('Ausführung: ')
        expanded=re.sub(r'(\d{2})(\d{2})/(\d{2})(?!\d)',r'\1\2-\1\3',raw)
        date=parse_date(expanded);date['display']=raw
        photo=soup.find('img',alt=title)
        rights=[]
        for el in soup.find_all(string=re.compile('Fotonachweis:')):
            rights.append(el.parent.get_text(' ',strip=True))
        assert 'Gemäldegalerie' in text and 'Gemälde' in text and creator and photo and len(rights)>=1
        rows.append({'key':'berlin-'+ident,'museum':'berlin','native_id':ident,'title':title,'creator_label':creator,'creator_source':fields['Beteiligte'],
            'date':date,'work_type':'painting','medium':fields.get('Material / Technik'),'dimensions':fields.get('Abmessungen'),
            'accession':accession,'institution_slug':'gemaldegalerie-berlin','collection_label':'Gemäldegalerie, Staatliche Museen zu Berlin',
            'display_text_not_asserted':None,'url':receipt['url'],'source':receipt,'fields':fields,
            'image_url':urljoin(receipt['url'],photo['src']),'image_credit_text':rights,
            'license_url':None,'image_hold':'Per-image rights element still requires manual review'})
    save(RUN/'berlin-selected-objects.json',rows)
    print(json.dumps(rows,ensure_ascii=False,indent=2),flush=True)


def accession_key(s):
    return re.sub(r'[^a-z0-9]','',norm(s or ''))


def metadata_plan():
    rows=load(RUN/'parsed-objects-v2.json')+load(RUN/'berlin-selected-objects.json')
    assert 1<=len(rows)<=100
    result={'at':core.now(),'records':rows,'targets':{}}
    for target in ('local','cloud'):
        with connect(target) as db:
            institutions=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE slug=ANY(%s)',(list({r['institution_slug'] for r in rows if r['institution_slug']})+['wikimedia-museum-q154568'],)).fetchall()
            imap={i['row']['slug']:i['row'] for i in institutions}
            names=list({r['creator_label'] for r in rows}|{x[0] for x in CREATOR_CROSSWALKS.values()})
            keys=[norm(n) for n in names]; lower=[n.casefold() for n in names]
            artists=db.execute('''SELECT a.id::text,a.slug,a.display_name,a.birth_year,a.death_year,a.status,
              ARRAY(SELECT x.alias FROM artist_aliases x WHERE x.artist_id=a.id) aliases
              FROM artists a WHERE a.status<>'archived' AND (a.normalized_name=ANY(%s) OR lower(a.display_name)=ANY(%s)
              OR EXISTS(SELECT 1 FROM artist_aliases x WHERE x.artist_id=a.id AND (x.normalized_alias=ANY(%s) OR lower(x.alias)=ANY(%s)))) LIMIT 1001''',(keys,lower,keys,lower)).fetchall()
            assert len(artists)<=1000
            patterns=[]
            for r in rows:
                patterns += (['%sammlung.pinakothek.de/%/artwork/'+r['native_id']+'%'] if r['museum']=='pinakothek' else ['%mauritshuis.nl/%/our-collection/artworks/'+r['native_id']+'-%'] if r['museum']=='mauritshuis' else ['%smb.museum/%'+r['native_id']+'%'])
            ii=[i['row']['id'] for i in institutions];aa=[a['id'] for a in artists]
            works=db.execute('''WITH chosen AS MATERIALIZED (
              SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
              UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
              UNION SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])
              UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url LIKE ANY(%s)
              UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE ANY(%s)
            ) SELECT to_jsonb(a) row,
              ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) urls,
              ARRAY(SELECT e.canonical_url FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) external_urls,
              ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
              ARRAY(SELECT l.institution_id::text FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.superseded_by IS NULL) institution_ids
              FROM chosen s JOIN artworks a ON a.id=s.id WHERE a.status<>'archived' ORDER BY a.id LIMIT 30001''',(ii,ii,aa,patterns,patterns)).fetchall()
            assert len(works)<=30000
            save(BACKUP/(target+'-metadata-v2-scoped-preimages.json'),{'at':core.now(),'institutions':institutions,'artists':artists,'works':works})
            planned=[]
            for r in rows:
                matches=[a for a in artists if norm(r['creator_label']) in {norm(n) for n in [a['display_name']]+a['aliases']}]
                # Exact unqualified source name/alias only. Never invent a person
                # or change existing lifespan or nationality to make it fit.
                creator=matches[0] if len(matches)==1 else None
                crosswalk=CREATOR_CROSSWALKS.get(r['creator_label'])
                if crosswalk:
                    name,born,died=crosswalk
                    matches=[a for a in artists if a['display_name']==name and a['birth_year']==born and a['death_year']==died]
                    assert len(matches)==1 and str(born) in r['creator_source'] and str(died) in r['creator_source'], 'Reviewed creator identity changed'
                    creator=matches[0]
                q=dict(record=r,artist=creator,institution=imap.get(r['institution_slug']))
                if re.search(r'Kopie nach|and studio|attributed|workshop|circle of|follower',r['creator_label'],re.I):
                    q.update(action='hold',reason='Qualified creator attribution requires separate reconciliation')
                    planned.append(q);continue
                if r['work_type']!='painting':
                    q.update(action='hold',reason='Non-painting type is outside this selected painting batch')
                    planned.append(q);continue
                if not q['institution']:
                    q.update(action='hold',reason='Institution identity not yet created: '+str(r['institution_slug']))
                    planned.append(q);continue
                if r['date']['last'] and r['date']['last']>1970:
                    q.update(action='hold',reason='Date exceeds creation cutoff');planned.append(q);continue
                related={q['institution']['id']}
                if r['museum']=='pinakothek': related.update(i['row']['id'] for i in institutions if 'pinakothek' in i['row']['slug'] or i['row']['slug']=='wikimedia-museum-q250195')
                def url_same(u):
                    if not u:return False
                    if r['museum']=='pinakothek':return 'sammlung.pinakothek.de/' in u and '/artwork/'+r['native_id'] in u
                    if r['museum']=='mauritshuis':return 'mauritshuis.nl/' in u and '/artworks/'+r['native_id']+'-' in u
                    return 'smb.museum/' in u and bool(re.search(r'(?:object/|obj-)'+r['native_id']+r'(?:\D|$)',u))
                exact=[w for w in works if any(url_same(u) for u in w['urls']+w['external_urls']) or
                    ((set(w['institution_ids'])|{w['row']['current_institution_id']})&related and accession_key(w['row']['accession_number'])==accession_key(r['accession']))]
                if len(exact)==1:
                    q.update(action='existing',work=exact[0]['row'],reason='Exact native source URL or museum accession')
                elif len(exact)>1:
                    q.update(action='hold',reason='Multiple existing native identities',leads=[w['row']['slug'] for w in exact])
                else:
                    similar=[w for w in works if norm(r['title']) in {norm(w['row']['title']),norm(w['row']['alternate_title'] or '')} and
                        (not creator or creator['id'] in w['artist_ids'])]
                    if similar:q.update(action='hold',reason='Possible existing title identity; no duplicate inserted',leads=[w['row']['slug'] for w in similar])
                    else:q.update(action='new',artwork_id=uid('artwork/'+r['museum']+'/'+r['native_id']),slug='nl-de-museum-'+r['museum']+'-'+r['native_id'].lower())
                planned.append(q)
            result['targets'][target]=planned
            print(target, 'scoped works',len(works),'actions',{a:sum(p['action']==a for p in planned) for a in ('new','existing','hold')},flush=True)
    save(RUN/'metadata-v2-plan.json',result)


def metadata_apply(target):
    plan,review=reviewed_plan('metadata-v2');allowed=set(review['selected_keys']);receipts=[]
    planned=[p for p in plan['targets'][target] if p['record']['key'] in allowed]
    assert len(planned)==len(allowed) and all(p['action'] in ('new','existing') for p in planned)
    with connect(target,False) as db:
        for item in planned:
            r=item['record'];key=r['key'];date=r['date'];aid=item.get('artwork_id') or item['work']['id']
            html=RUN/'captures'/(key+'.html');assert core.sha(html.read_bytes())==r['source']['sha256']
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559320260917)')
                sid=ensure_source(db)
                prior=db.execute("SELECT id FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND source_record_id=%s AND field_name='selected_museum_object'",(aid,sid,key)).fetchone()
                if prior:
                    print(target,key,'already applied',flush=True);continue
                inst=db.execute('SELECT slug,status FROM institutions WHERE id=%s FOR SHARE',(item['institution']['id'],)).fetchone()
                assert inst and inst['slug']==r['institution_slug'] and inst['status']!='archived'
                if item['action']=='new':
                    assert not db.execute('SELECT 1 FROM artworks WHERE id=%s OR slug=%s',(aid,item['slug'])).fetchone()
                    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=%s",(r['url'],)).fetchone(), 'Concurrent source citation'
                    assert not db.execute('''SELECT 1 FROM artworks a WHERE a.accession_number=%s AND
                      (a.current_institution_id=%s OR EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.institution_id=%s AND l.superseded_by IS NULL))''',
                      (r['accession'],item['institution']['id'],item['institution']['id'])).fetchone(), 'Concurrent museum accession'
                    db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
                      work_type,medium_text,dimensions_text,accession_number,unlinked_creator_label,status,research_candidate,created_by,updated_by)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',
                      (aid,item['slug'],r['title'],norm(r['title']),date['display'],date['first'],date['last'],date['precision'],r['work_type'],r['medium'],r['dimensions'],r['accession'],r['creator_label'],core.ACTOR,core.ACTOR))
                    if item['artist']:
                        artist=item['artist'];now=db.execute('SELECT display_name,birth_year,death_year,status FROM artists WHERE id=%s FOR SHARE',(artist['id'],)).fetchone()
                        assert now and all(now[k]==artist[k] for k in now), 'Creator authority changed'
                        db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",
                          (aid,artist['id'],'Unqualified primary museum attribution; source creator label retained: '+r['creator_label']))
                    db.execute('''INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                      VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'review')''',
                      (aid,item['institution']['id'],sid,r['url'],'Museum collection association from selected native object record: '+r['collection_label']+'. Review only; no accepted custody or current display asserted.',r['source']['at']))
                else:
                    now=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']
                    assert now==item['work'], 'Existing record changed; preserve concurrent edits'
                evidence={'record':r,'plan_sha256':review['plan_sha256'],'action':item['action'],'policy':'Source evidence only. New records stay in review. Existing fields, media and statuses unchanged. No display claim or artist biography invented.'}
                db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                  VALUES('artwork',%s,'selected_museum_object',%s,%s,%s,%s,%s,%s)''',(aid,sid,key,r['url'],json.dumps(evidence,ensure_ascii=False),r['source']['at'],core.ACTOR))
                scheme='nl-de-selected-'+r['museum']+'-object'
                db.execute('''INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at)
                  VALUES('artwork',%s,%s,%s,%s,%s,%s)''',(aid,scheme,r['native_id'],r['url'],sid,r['source']['at']))
                after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
                if item['action']=='new':
                    assert after['status']=='review' and after['research_candidate'] and after['published_at'] is None and after['current_institution_id'] is None
                else:assert after==item['work']
            receipt={'at':core.now(),'target':target,'key':key,'action':item['action'],'artwork_id':aid,'slug':after['slug'],'plan_sha256':review['plan_sha256']}
            save(RUN/'metadata-applied'/target/(key+'.json'),receipt);receipts.append(receipt)
            print(target,key,item['action'],flush=True)
    save(RUN/(target+'-metadata-applied.json'),receipts)


def image_plan():
    plan,review=reviewed_plan('metadata-v2');allowed=set(review['selected_keys']);images=[];held=[]
    for item in plan['targets']['local']:
        r=item['record'];key=r['key']
        if key not in allowed:continue
        if r['museum'] not in ('pinakothek','berlin') or not r['image_url']:
            held.append({'key':key,'reason':r['image_hold'] or 'No selected primary image'});continue
        if r['date']['last'] is None or r['date']['last']>1970:
            held.append({'key':key,'reason':'Source creation date requires editorial review before image selection'});continue
        if r['museum']=='pinakothek':
            assert r['license_url']=='https://creativecommons.org/licenses/by-sa/4.0/'
            status='cc_by_sa';uri=r['license_url'];label='CC BY-SA 4.0';credit=r['collection_label']
        else:
            assert all('Public Domain Mark 1.0' in t for t in r['image_credit_text'])
            status='public_domain';uri='https://creativecommons.org/publicdomain/mark/1.0/';label='Public Domain Mark 1.0'
            credit=r['image_credit_text'][0].removeprefix('Fotonachweis: ').removesuffix(' Public Domain Mark 1.0')
        im={'key':key,'title':r['title'],'artist':r['creator_label'],'external_id':r['native_id'],'provider':'dutch-german-primary',
            'source_image_url':r['image_url'],'page':r['url'],'policy_url':uri,'rights_status':status,'license_label':label,
            'creator_credit':credit,'checked_at':r['source']['at'],'source_evidence_sha256':r['source']['sha256'],
            'identity_basis':'Exact selected official collection object '+r['native_id']+', accession '+r['accession']+'. The source embeds this image beside its creator, title, date and explicit per-image rights statement. No current-display claim.',
            'attribution_text':r['creator_label']+'. '+r['title']+'. '+credit+'. '+label+' ('+uri+'). '+r['url']+'. Full-frame proportional resize and JPEG compression; ShareAlike retained where applicable.',
            'source_record':r,'targets':{}}
        skip=False
        for target in ('local','cloud'):
            receipt=load(RUN/'metadata-applied'/target/(key+'.json'))
            with connect(target) as db:
                row=db.execute('SELECT to_jsonb(a) row,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope FROM artworks a WHERE id=%s',(receipt['artwork_id'],)).fetchone()
                assert row and row['date_scope']=='eligible' and row['row']['status']!='archived'
                if row['row']['primary_media_id']:
                    skip=True;break
                im['targets'][target]={'id':receipt['artwork_id'],'before':row['row']}
        if skip:
            held.append({'key':key,'reason':'Existing primary image preserved'});continue
        im['artwork_id']=im['targets']['local']['id'];images.append(im)
    assert 1<=len(images)<=40
    save(RUN/'image-selection.json',images);save(RUN/'image-held.json',held)
    save(BACKUP/'image-target-preimages.json',images)
    print('Selected rights-cleared images',len(images),'sha256',core.sha((RUN/'image-selection.json').read_bytes()),flush=True)


def image_upload(adapter_version='dutch-german-selected-v1', selection_name='image-selection.json'):
    selection=load(RUN/selection_name);review=load(RUN/'image-visual-review.json')
    assert review['approved'] is True and review['selection_sha256']==core.sha((RUN/selection_name).read_bytes())
    assert set(review['accepted']) <= {i['key'] for i in selection}
    bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    dbs={t:connect(t,False) for t in ('local','cloud')};results=[]
    try:
        for selected in selection:
            if selected['key'] not in review['accepted']:continue
            receipt=RUN/'images-prepared'/(selected['artwork_id']+'.json');im=load(receipt)
            assert im['key']==selected['key'] and im['selection_sha256']==review['selection_sha256']
            data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
            assert len(data)==im['bytes']<=100000 and core.sha(data)==im['sha256']==review['accepted'][im['key']]
            mid=uid('media/'+im['sha256']);blob=bucket.blob(im['path'].lstrip('/'))
            blob.metadata={'sha256':im['sha256'],'source-record':im['external_id'],'license':im['license_label']}
            blob.cache_control='public,max-age=31536000,immutable'
            try:blob.upload_from_string(data,content_type='image/jpeg',if_generation_match=0,timeout=45)
            except core.PreconditionFailed:blob.reload(timeout=30)
            assert blob.size==len(data) and blob.md5_hash==base64.b64encode(hashlib.md5(data).digest()).decode()
            assert core.sha(blob.download_as_bytes(timeout=45))==im['sha256']
            targets={}
            for target,db in dbs.items():
                expected=im['targets'][target]['before'];aid=im['targets'][target]['id']
                with db.transaction():
                    db.execute("SET LOCAL lock_timeout='5s'")
                    now=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()['row']
                    if now['primary_media_id']==mid:
                        targets[target]='already attached';continue
                    assert now==expected and now['primary_media_id'] is None, 'Artwork changed; uploaded object retained but attachment held'
                    sid=ensure_source(db)
                    db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,
                      checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                      VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                      (mid,im['path'],im['page'],im['source_record']['collection_label'],im['width'],im['height'],im['bytes'],im['sha256'],
                       im['title']+' — '+im['artist'],im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],im['attribution_text'],im['downloaded_at'],im['checked_at'],core.ACTOR))
                    db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                      (mid,sid,im['external_id'],im['source_evidence_sha256'],im['source_image_url'],im['policy_url'],im['identity_basis'],adapter_version,im['checked_at'],Jsonb(im)))
                    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(mid,core.ACTOR,aid))
                    after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
                    skip={'primary_media_id','revision','updated_at','updated_by'}
                    assert {k:v for k,v in now.items() if k not in skip}=={k:v for k,v in after.items() if k not in skip}
                    targets[target]='attached; non-image metadata preserved'
            result={'at':core.now(),'key':im['key'],'media_id':mid,'path':im['path'],'sha256':im['sha256'],'bytes':im['bytes'],'generation':blob.generation,'remote_bytes_verified':True,'targets':targets}
            save(RUN/'image-uploaded'/(im['key']+'.json'),result);results.append(result)
            print(im['key'],'uploaded and attached in both targets',flush=True)
    finally:
        for db in dbs.values():db.close()
    save(RUN/'image-upload-summary.json',results)


def verify():
    plan,review=reviewed_plan('metadata-v2');geo=load(RUN/'geography-plan.json');images=load(RUN/'image-upload-summary.json')
    result={'at':core.now(),'targets':{},'limits':'No publication, accepted holding, display claim, or load-test assertion. Country totals are not nationwide completeness.'}
    for target in ('local','cloud'):
        with connect(target) as db:
            selected=[p for p in plan['targets'][target] if p['record']['key'] in review['selected_keys']]
            ids=[p.get('artwork_id') or p['work']['id'] for p in selected]
            rows=db.execute('''SELECT a.id::text,a.slug,a.title,a.status,a.published_at,a.research_candidate,a.primary_media_id::text,a.unlinked_creator_label,
              a.creation_year_start,a.creation_year_end,a.date_precision,a.current_institution_id::text,
              (SELECT count(*) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id AND c.source_id=%s AND c.field_name='selected_museum_object') source_citations,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='review') review_holdings,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND (l.claim_type='display' OR l.review_state='accepted')) accepted_or_display_claims,
              m.storage_path,m.checksum_sha256,m.byte_size,m.rights_status,m.license_url,
              (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=m.id) rights_evidence
              FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.slug''',(uid('source'),ids)).fetchall()
            byid={r['id']:r for r in rows};assert len(rows)==55 and all(r['source_citations']==1 for r in rows)
            new=[byid[p['artwork_id']] for p in selected if p['action']=='new']
            assert len(new)==43 and all(r['status']=='review' and r['research_candidate'] and r['published_at'] is None and r['current_institution_id'] is None and r['review_holdings']==1 and r['accepted_or_display_claims']==0 for r in new)
            for p in selected:
                if p['action']=='existing':
                    after=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(p['work']['id'],)).fetchone()['row']
                    assert after==p['work'], 'Existing catalogue metadata changed'
            delivered=[r for r in rows if r['primary_media_id'] in {i['media_id'] for i in images}]
            assert len(delivered)==len(images)==17
            assert all(r['byte_size']<=100000 and r['rights_evidence']==1 and r['license_url'] for r in delivered)
            institution_ids=[p['before']['id'] for p in geo['targets'][target]]
            museums=db.execute('''SELECT i.slug,i.status,p.name city,p.country_code,
              ARRAY(SELECT vp.country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id) venue_countries
              FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.id=ANY(%s::uuid[]) ORDER BY i.slug''',(institution_ids,)).fetchall()
            assert len(museums)==21 and sum(bool(i['venue_countries']) for i in museums)==19
            for before in geo['targets'][target]:
                f=before['fact'];m=next(i for i in museums if i['slug']==f['slug'])
                assert m['country_code']==f['country'] and m['status']==before['before']['status']
            result['targets'][target]={'new_artworks':len(new),'existing_enriched':12,'new_images':len(delivered),'geography_records':len(museums),'physical_venues_added':19,'museums':museums,'artworks':rows}
            print(target,'verified 21 geography fixes, 19 venues, 43 new review artworks, 12 evidence enrichments, 17 images',flush=True)
    def canonical(t):
        return [{k:v for k,v in r.items() if k not in ('id','primary_media_id')} for r in result['targets'][t]['artworks']]
    assert canonical('local')==canonical('cloud')
    save(RUN/'verification.json',result)


def public_verify():
    site='https://artline-web-lpuqqlugnq-ew.a.run.app';images=load(RUN/'image-upload-summary.json')
    def check(im):
        r=requests.get(site+im['path'],timeout=(10,45));r.raise_for_status()
        assert len(r.content)==im['bytes'] and core.sha(r.content)==im['sha256'] and r.headers.get('Content-Type','').startswith('image/jpeg')
        return {'url':r.url,'status':r.status_code,'sha256':core.sha(r.content),'bytes':len(r.content),'verified':True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(check,images))
    museums=[]
    for slug,country in [('wikimedia-museum-q574961','NL'),('wikimedia-museum-q125634','DE'),('wikimedia-museum-q32659772','DE')]:
        r=requests.get(site+'/api/backend/v1/museums/'+slug,timeout=(10,30));r.raise_for_status();body=r.json()
        assert body['slug']==slug and any(v['country']==country for v in body['venues'])
        museums.append({'slug':slug,'status':r.status_code,'venues':body['venues'],'verified':True})
    save(RUN/'public-verification.json',{'at':core.now(),'images':results,'museum_details':museums})
    print('Verified all',len(results),'public image byte streams and',len(museums),'live museum geography responses',flush=True)


def load(p):
    return json.loads(p.read_text())


def save(p, v):
    core.save_new(p, v)


def uid(k):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/' + SOURCE + '/' + k))


def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFKD', s.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', s))


def connect(target, readonly=True):
    return psycopg.connect('postgres://localhost/artline' if target == 'local' else core.cloud_dsn(),
        row_factory=dict_row, autocommit=True,
        options='-c statement_timeout=120000' + (' -c default_transaction_read_only=on' if readonly else ''))


def capture(url, key):
    path = RUN / 'captures' / (key + '.html')
    rp = path.with_suffix('.receipt.json')
    if path.exists():
        raw = path.read_bytes()
        receipt = load(rp)
        assert core.sha(raw) == receipt['sha256']
    else:
        response = requests.get(url, timeout=(12, 35), headers={'User-Agent': 'Artline/1.0 (selected museum catalogue research; https://github.com/vadimdulub/artline)'})
        response.raise_for_status()
        raw = response.content
        assert len(raw) < 6_000_000 and 'html' in response.headers.get('Content-Type', '')
        receipt = {'requested_url': url, 'url': response.url, 'at': core.now(), 'sha256': core.sha(raw), 'bytes': len(raw), 'status': response.status_code}
        save(path, raw)
        save(rp, receipt)
    return BeautifulSoup(raw, 'html.parser'), receipt


def geography_capture():
    rows = load(ROOT / 'docs/research/dutch-german-museum-gaps-20260917/local-institutions.json')
    rows = [r for r in rows if r['scope_basis'] != 'stored_geography']
    def one(row):
        url = row['website_url'].replace('http://', 'https://')
        try:
            soup, receipt = capture(url, 'geo-' + row['wikidata_id'])
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            text = soup.get_text(' ', strip=True)
            return {'institution': row, 'receipt': receipt, 'text': text}
        except Exception as error:
            return {'institution': row, 'error': str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        result = list(pool.map(one, rows))
    save(RUN / 'geography-captures.json', result)
    for r in result:
        print(r['institution']['wikidata_id'], r.get('error') or r['text'][-1800:], flush=True)


def discover():
    out = []
    for museum, url in [('pinakothek', 'https://www.sammlung.pinakothek.de/en'), ('mauritshuis', 'https://www.mauritshuis.nl/en/our-collection')]:
        soup, receipt = capture(url, museum + '-selection-index')
        links = []
        for a in soup.select('a[href]'):
            u = urljoin(url, a['href'])
            path = urlparse(u).path
            wanted = '/en/artwork/' in path if museum == 'pinakothek' else re.search(r'/en/our-collection/artworks/\d', path)
            if wanted and u not in [x['url'] for x in links]:
                links.append({'url': u, 'label': a.get_text(' ', strip=True), 'museum': museum})
        assert 1 <= len(links) <= 80, (museum, len(links))
        out.extend(links)
        print(museum, len(links), json.dumps(links[:3], ensure_ascii=False), flush=True)
    save(RUN / 'discovered-selected-objects.json', out)


def object_capture():
    rows = load(RUN / 'discovered-selected-objects.json')
    assert len(rows) <= 120
    def one(row):
        key = row['museum'] + '-' + hashlib.sha256(row['url'].encode()).hexdigest()[:16]
        try:
            soup, receipt = capture(row['url'], key)
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            return dict(row, key=key, receipt=receipt, text=soup.get_text(' ', strip=True))
        except Exception as error:
            return dict(row, key=key, error=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        result = list(pool.map(one, rows))
    save(RUN / 'object-captures.json', result)
    print('Captured', len(result), 'selected object pages; errors', sum('error' in r for r in result), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['geography-capture', 'discover', 'object-capture','backups','geography-plan','geography-apply','parse','berlin-capture','metadata-plan','metadata-apply','image-plan','image-upload','verify','public-verify'])
    p.add_argument('--target',choices=['local','cloud'])
    a = p.parse_args()
    if a.phase in ('geography-apply','metadata-apply'):
        assert a.target
        {'geography-apply':geography_apply,'metadata-apply':metadata_apply}[a.phase](a.target)
    else:
        {'geography-capture': geography_capture, 'discover': discover, 'object-capture': object_capture,'backups':backup_verify,'geography-plan':geography_plan,'parse':parse_objects,'berlin-capture':berlin_capture,'metadata-plan':metadata_plan,'image-plan':image_plan,'image-upload':image_upload,'verify':verify,'public-verify':public_verify}[a.phase]()


if __name__ == '__main__':
    main()
