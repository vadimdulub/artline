#!/usr/bin/env python3
"""Selected corrections and three licensed images from the 2026-09-20 review.

No publication, deletion, new artwork, schema change or existing-image replacement.
Research, exact recovery preimages, pinned visual approval and apply are separate.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import uuid
from urllib.parse import urlencode, urljoin, urlparse

from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql
from PIL import Image
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
RUN=ROOT/'docs/research/byzantine-russian-icons-review-20260920/delivery'
AUDIT=RUN.parent
BACKUP=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/byzantine-icon-review-delivery-20260920')
ORIGINALS=Path('/Users/vadimdulub/Library/Application Support/Artline/source-images/byzantine-icon-review-delivery-20260920')
SITE='https://artline-web-lpuqqlugnq-ew.a.run.app'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
CCBY='https://creativecommons.org/licenses/by/4.0/'
SOURCE='byzantine-icon-review-delivery-20260920'
core.HOSTS.update({'art.thewalters.org','www.nasjonalmuseet.no','thumb.wikimedia.org'})
OSLO='wikimedia-artwork-q113396603'
WALTERS={
 'research-candidate-2980e0b0841b2367cf7535605d8677e47dcd2dc8ef7cc42ec117ab3bb4659982':('44.817','82415'),
 'research-candidate-3071ec6ea5825f28d4eb9c22f32a238d5395af3c3d7fbfa72acc8937564ef13f':('44.819','82414'),
}
COMMONS_TITLE='File:Emmanuel Tzanes - Dionysius the Areopagite - NG.M.01774 - National Museum of Art, Architecture and Design.jpg'
MENA='wikiart-60508052edc2c914901fd40d'
BLACH='wikiart-605723a8edc2c958905acf64'
NATIVITY='wikiart-6050906cedc2c914909932ac'


def read(path):
    return json.loads(path.read_text())


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/'+SOURCE+'/'+value))


def dbconn(dsn,readonly=True):
    return psycopg.connect(dsn,row_factory=dict_row,
        options='-c statement_timeout=60000 -c lock_timeout=3000'+(' -c default_transaction_read_only=on' if readonly else ''))


def capture(url):
    key=core.sha(url.encode());path=RUN/'sources'/(key+'.body');receipt=path.with_suffix('.json')
    if path.exists():
        saved=read(receipt);raw=path.read_bytes()
        assert saved['url']==url and core.sha(raw)==saved['sha256']
        return raw,saved
    raw,headers=core.Fetcher(RUN/'sources').get(url)
    saved={'url':url,'retrieved_at':core.now(),'sha256':core.sha(raw),'bytes':len(raw),'headers':headers,'path':str(path.relative_to(ROOT))}
    core.save_new(path,raw);core.save_new(receipt,saved)
    return raw,saved


def research():
    if (RUN/'source-selection.json').exists():
        print('Pinned source selection already exists');return
    result={}
    for slug,(acc,native) in WALTERS.items():
        url='https://art.thewalters.org/object/'+acc+'/'
        raw,receipt=capture(url);soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True)
        assert acc in text and 'Vasilii Semenov' in text and 'Creative Commons Zero' in text
        assert '1891-1899' in text if acc=='44.817' else '1899-1908' in text
        downloads=[urljoin(url,a['href']) for a in soup.select('a[href]') if 'Download Image' in a.get_text()]
        licensed=[u for u in downloads if '?download=' in u and acc in u and '_Fnt_' in u]
        assert len(licensed)==1 and urlparse(licensed[0]).hostname=='art.thewalters.org'
        assert any(a.get('href','').rstrip('/')==CC0.rstrip('/') for a in soup.select('a[href]'))
        if acc=='44.819':assert 'Oklad:' in text
        result[slug]={'page':url,'native_id':native,'accession':acc,'capture':receipt,
            'source_image_url':licensed[0],'rights_status':'cc0','license_label':'CC0','license_url':CC0,
            'credit':'The Walters Art Museum; Bequest of Mrs. Jean M. Riddell, 2010',
            'rights_basis':'Exact object page labels its selected front photograph Creative Commons Zero; image selected from that page, not inferred from artwork age.',
            'facts':{'title':soup.find('h1').get_text(' ',strip=True),'creation_place':'Moscow, Russia'}}
    url='https://www.nasjonalmuseet.no/en/collection/object/NG.M.01774'
    raw,receipt=capture(url);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    for phrase in ('Dionysius the Areopagite','Emmanuel Tzanes','NG.M.01774','Midten av 1600-tallet','Tempera på plate','Anne Hansteen'):
        assert phrase in text,phrase
    params={'action':'query','format':'json','titles':COMMONS_TITLE,'prop':'imageinfo|revisions',
            'iiprop':'url|extmetadata|sha1|size|mime','rvprop':'ids|content','rvslots':'main','maxlag':5}
    raw,file_receipt=capture('https://commons.wikimedia.org/w/api.php?'+urlencode(params))
    data=json.loads(raw);assert 'error' not in data
    pages=list(data['query']['pages'].values());assert len(pages)==1
    page=pages[0];info=page['imageinfo'][0];wt=page['revisions'][0]['slots']['main']['*']
    assert page['title']==COMMONS_TITLE and 'Q113396603' in wt and 'NG.M.01774' in wt
    assert 'cc-by-4.0' in wt.lower() and 'nasjonalmuseet.no/en/collection/object/NG.M.01774' in wt
    assert not re.search(r'\{\{\s*(copyvio|no permission|delete|disputed|wrong license)',wt,re.I)
    assert not info.get('extmetadata',{}).get('Restrictions',{}).get('value')
    assert urlparse(info['url']).hostname=='upload.wikimedia.org' and info['mime']=='image/jpeg'
    result[OSLO]={'page':url,'image_page':info['descriptionurl'],'native_id':'NG.M.01774','accession':'NG.M.01774',
        'capture':receipt,'file_capture':file_receipt,'commons_page':page,'source_image_url':info['url'],
        'source_sha1':info['sha1'],'rights_status':'cc_by','license_label':'CC BY 4.0','license_url':CCBY,
        'credit':'Anne Hansteen / Nasjonalmuseet; exact museum reproduction via Wikimedia Commons',
        'rights_basis':'Exact accession and Wikidata object matched between official museum and Commons file; the reproduction explicitly carries CC BY 4.0. Photographer credited; licence and full-frame compression notice retained.',
        'facts':{'title':'Dionysius the Areopagite','date_literal':'Midten av 1600-tallet',
                 'date_review':'Museum explicitly supplies mid-17th century. Numeric 1600–1699 is a conservative century containment interval, not a claim of precise endpoints or an inferred artist lifespan.'}}
    core.save_new(RUN/'source-selection.json',{'at':core.now(),'selected':result})
    print('Selected three exact licensed museum reproductions',flush=True)


def before(db,slugs):
    rows=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE slug=ANY(%s::text[]) ORDER BY slug',(slugs,)).fetchall()
    assert len(rows)==len(slugs)
    ids=[r['row']['id'] for r in rows]
    result={'artworks':[r['row'] for r in rows]}
    for table,column in [('artwork_artists','artwork_id'),('artwork_location_assertions','artwork_id'),('artwork_media','artwork_id')]:
        result[table]=[r['row'] for r in db.execute(sql.SQL('SELECT to_jsonb(t) row FROM {} t WHERE {}=ANY(%s::uuid[])').format(sql.Identifier(table),sql.Identifier(column)),(ids,)).fetchall()]
    for table in ('citations','external_identifiers'):
        result[table]=[r['row'] for r in db.execute(sql.SQL("SELECT to_jsonb(t) row FROM {} t WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])").format(sql.Identifier(table)),(ids,)).fetchall()]
    mids={r['primary_media_id'] for r in result['artworks'] if r['primary_media_id']}|{r['media_id'] for r in result['artwork_media']}
    result['media_assets']=[r['row'] for r in db.execute('SELECT to_jsonb(m) row FROM media_assets m WHERE id=ANY(%s::uuid[])',(list(mids),)).fetchall()]
    result['media_rights_evidence']=[r['row'] for r in db.execute('SELECT to_jsonb(m) row FROM media_rights_evidence m WHERE media_id=ANY(%s::uuid[])',(list(mids),)).fetchall()]
    result['institutions']=[r['row'] for r in db.execute("SELECT to_jsonb(i) row FROM institutions i WHERE wikidata_id='Q210081' OR slug='national-museum-oslo'").fetchall()]
    assert len(result['institutions'])==2
    return result


def proposals():
    old=read(AUDIT/'unicode-recheck/local-snapshot.json')['records'];changes=[]
    for r in old:
        s=r['slug'];patch={};note=None;url=None;creator_note=None
        if s.startswith('cypriot-artwork-chourri-'):
            evidence=json.loads(r['citations'][0]['evidence_note']);raw=evidence['raw_metadata']
            assert any('Icons--post-Byzantine--Cyprus' in x for x in raw['Subject'])
            assert 'permission' in evidence['image_hold']
            patch={'object_form':'icon','cultural_context':'Post-Byzantine icons — Cyprus'}
            url=evidence['source_url'];note='Source object record explicitly classifies a post-Byzantine icon in Cyprus. Named creator, supplied date, unknown medium and reproduction-permission hold retained.'
        elif s in WALTERS:
            acc,_=WALTERS[s];url='https://art.thewalters.org/object/'+acc+'/'
            patch={'object_form':'icon','cultural_context':'Russian icon with oklad (metal cover)','creation_place_display':'Moscow, Russia'}
            note='Exact museum accession, title, maker credit, pre-1971 date and collection ownership checked against the official object page. Holding only; no current display claim.'
            if acc=='44.819':
                creator_note='Component-specific museum credit: Oklad (metal cover): Vasilii Semenov. This association does not identify the painter of the underlying icon. Existing primary association retained for the composite object because the current schema has no component-maker role.'
                patch['description_md']='Russian icon with a metal cover (oklad). The Walters Art Museum credits Vasilii Semenov specifically for the oklad; the painter of the underlying icon is not identified by this credit. Catalogue record remains in review.'
            else:
                patch['description_md']='Russian icon with a metal cover (oklad), catalogued by the Walters Art Museum under Vasilii Semenov. The museum page does not specify the maker credit by component; the identity of the underlying icon painter remains under review.'
        elif s==OSLO:
            url='https://www.nasjonalmuseet.no/en/collection/object/NG.M.01774'
            patch={'work_type':'painting','object_form':'icon','cultural_context':'Post-Byzantine Greek icon',
                   'date_display':'Mid-17th century (museum: Midten av 1600-tallet)',
                   'creation_year_start':1600,'creation_year_end':1699,'date_precision':'century',
                   'medium_text':'Tempera on wood panel','dimensions_text':'23.5 × 15.4 × 0.7 cm',
                   'description_md':'Icon of Dionysius the Areopagite by Emmanuel Tzanes, Nasjonalmuseet, accession NG.M.01774. The museum dates the object to the mid-17th century. Numeric bounds retain a conservative century interval, not artist lifespan dates. Record remains in review.'}
            note='Exact museum accession, named artist, icon type, tempera/wood medium, dimensions, ownership and object-level mid-17th-century date verified. Conservative century bounds preserve uncertainty. No on-view assertion imported.'
        elif s.startswith('greek-met-'):
            url='https://www.metmuseum.org/art/collection/search/'+s.rsplit('-',1)[1]
            patch={'cultural_context':'Post-Byzantine Greek icon'}
            note='Museum text establishes post-Byzantine context. Unknown artwork dates are intentionally unchanged; artist activity is not substituted.'
        elif s.startswith('wikiart-57727502'):
            url=next(e['canonical_url'] for e in r['identifiers'] if e['scheme']=='wikiart-artwork')
            patch={'work_type':'manuscript_illumination',
                'description_md':'Manuscript miniature, attributed to Andrei Rublev by the recorded secondary source. The exact manuscript, folio, date and authorship remain under review; no new museum holding is asserted.'}
            creator_note='Secondary-source attribution to Andrei Rublev retained for review, not authenticated sole authorship. Visual review establishes manuscript miniature format; exact manuscript and folio identification remain unresolved.'
            note='Existing image visually reviewed as manuscript miniature, not a portable panel icon. Possible Khitrovo Gospel connection is not accepted as an exact object identification; existing numerical date retained pending reconciliation.'
        elif s in (MENA,BLACH,NATIVITY):
            if s==MENA:
                url='https://collections.louvre.fr/en/ark:/53355/cl010048163'
                note='Dating review: Louvre E 11565 / X 5178 currently gives 700–799. Existing secondary-source year 750 is retained pending exact reproduction/object reconciliation, not freshly authenticated.'
            elif s==BLACH:
                url='https://kreml.ru/storage/files/kontseptsiyakomplektovaniya.pdf#page=26'
                note='Dating review: the Kremlin describes its relief Blachernitissa as late fifteenth–early sixteenth century. Match this reproduction to an exact accession before changing the existing secondary-source 439 date; a devotional prototype is not necessarily the surviving object.'
            else:
                url=next(e['canonical_url'] for e in r['identifiers'] if e['scheme']=='wikiart-artwork')
                note='The recorded 500–600 date and precise object identity are unresolved. No museum attribution or replacement date is asserted by this review.'
            patch={'description_md':note+' Record remains in review.'}
        if note:
            changes.append({'id':r['id'],'slug':s,'patch':patch,'note':note,'source_url':url,'creator_note':creator_note})
    assert len(changes)==19
    return changes


def plan():
    if (RUN/'plan.json').exists():print('Immutable plan already exists');return
    selected=read(RUN/'source-selection.json');changes=proposals();targets={};slugs=[r['slug'] for r in changes];local_rows={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with dbconn(dsn) as db:
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            data=before(db,slugs)
            for row in data['artworks']:
                assert row['status']=='review' and row['published_at'] is None
                change=next(c for c in changes if c['slug']==row['slug'])
                if target=='local':assert row['id']==change['id']
                change.setdefault('target_ids',{})[target]=row['id']
                if row['slug'] in selected['selected']:assert row['primary_media_id'] is None
                change=next(c for c in changes if c['slug']==row['slug'])
                if target=='local':
                    local_rows[row['slug']]=row
                    if 'description_md' in change['patch'] and row['description_md']:
                        change['patch']['description_md']=row['description_md']+'\n\nReview update — 20 September 2026: '+change['patch']['description_md']
                else:
                    assert row['description_md']==local_rows[row['slug']]['description_md'],'Description differs across targets; separate editorial reconciliation required'
            for slug,evidence in selected['selected'].items():
                row=next(r for r in data['artworks'] if r['slug']==slug)
                assert row['accession_number']==evidence['accession']
                assert row['title']==evidence['facts']['title']
                ids=[e for e in data['external_identifiers'] if e['entity_id']==row['id']]
                if slug in WALTERS:
                    acc,native=WALTERS[slug]
                    assert any(e['scheme']=='walters-object' and e['external_id']==native for e in ids)
                    assert (row['creation_year_start'],row['creation_year_end'])==((1891,1899) if acc=='44.817' else (1899,1908))
                else:
                    assert any(e['scheme']=='wikidata' and e['external_id']=='Q113396603' for e in ids)
            walters=next(r for r in data['institutions'] if r['wikidata_id']=='Q210081')
            for s in WALTERS:
                acc,_=WALTERS[s]
                duplicates=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=%s AND status<>%s',(walters['id'],acc,'archived')).fetchall()
                assert all(x['id']==next(c['target_ids'][target] for c in changes if c['slug']==s) for x in duplicates)
        path=BACKUP/(target+'-before.json');core.save_new(path,data)
        targets[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
    core.save_new(RUN/'plan.json',{'at':core.now(),'changes':changes,'backups':targets,
        'source_selection_sha256':core.sha((RUN/'source-selection.json').read_bytes()),
        'prior_review_sha256':core.sha((AUDIT/'primary-source-review.json').read_bytes()),
        'no_publication':True,'no_new_artworks':True})
    print('Pinned 19-record plan with exact local/cloud recovery preimages',flush=True)


def prepare():
    plan_data=read(RUN/'plan.json');selected=read(RUN/'source-selection.json')['selected'];images=[]
    assert plan_data['source_selection_sha256']==core.sha((RUN/'source-selection.json').read_bytes())
    for slug,item in selected.items():
        path=RUN/'prepared'/(slug+'.json')
        if path.exists():images.append(read(path));continue
        raw,headers=core.Fetcher(RUN/'image-downloads').get(item['source_image_url'])
        if item.get('source_sha1'):assert hashlib.sha1(raw).hexdigest()==item['source_sha1']
        original=ORIGINALS/(item['accession']+'-'+core.sha(raw)[:16]+'.jpg');core.save_new(original,raw)
        data,width,height,quality=core.compress(raw);digest=core.sha(data)
        served='/assets/artworks/reviewed-icons-20260920/'+item['accession']+'-'+digest[:16]+'.jpg'
        core.save_new(ROOT/'apps/web/public'/served.lstrip('/'),data)
        im={**item,'slug':slug,'artwork_id':next(c['id'] for c in plan_data['changes'] if c['slug']==slug),
            'target_ids':next(c['target_ids'] for c in plan_data['changes'] if c['slug']==slug),
            'media_id':uid(served),'path':served,'sha256':digest,'bytes':len(data),'width':width,'height':height,'quality':quality,
            'downloaded_at':core.now(),'original_path':str(original),'original_sha256':core.sha(raw),'original_bytes':len(raw),'headers':headers,
            'transform':'Full-frame proportional resize and JPEG compression; no crop or generated content'}
        core.save_new(path,im);images.append(im)
        print('Prepared',item['accession'],len(data),'bytes',flush=True)
    core.save_new(RUN/'prepared-manifest.json',{'plan_sha256':core.sha((RUN/'plan.json').read_bytes()),'images':images})


def validate_pins():
    p=read(RUN/'plan.json');m=read(RUN/'prepared-manifest.json');qa=read(RUN/'visual-approval.json')
    assert m['plan_sha256']==core.sha((RUN/'plan.json').read_bytes())
    assert p['source_selection_sha256']==core.sha((RUN/'source-selection.json').read_bytes())
    assert p['prior_review_sha256']==core.sha((AUDIT/'primary-source-review.json').read_bytes())
    assert qa['approved'] and qa['manifest_sha256']==core.sha((RUN/'prepared-manifest.json').read_bytes())
    assert set(qa['accepted_sha256'])=={im['sha256'] for im in m['images']}
    for im in m['images']:
        data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        assert len(data)==im['bytes']<=100000 and core.sha(data)==im['sha256']
        with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')) as image:
            assert list(image.size)==[im['width'],im['height']];image.verify()
    for recovery in p['backups'].values():
        path=Path(recovery['path']);assert path.is_relative_to(BACKUP) and core.sha(path.read_bytes())==recovery['sha256']
    return p,m


def source(db,url):
    host=urlparse(url).hostname;slug=SOURCE+'-'+host.replace('.','-');sid=uid(slug)
    db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page',%s) ON CONFLICT(slug) DO NOTHING",(sid,slug,'Selected icon review: '+host,'https://'+host+'/'))
    assert db.execute('SELECT id::text FROM sources WHERE slug=%s',(slug,)).fetchone()['id']==sid
    return sid


def apply():
    p,m=validate_pins();bucket=core.storage.Client(project='artline-508319',credentials=core.GcloudCredentials()).bucket(core.BUCKET)
    uploads=[]
    for im in m['images']:
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();blob=bucket.blob(im['path'].lstrip('/'))
        if not blob.exists():
            blob.metadata={'sha256':im['sha256'],'license':im['license_label'],'artwork-id':im['artwork_id']}
            blob.cache_control='public,max-age=31536000,immutable'
            blob.upload_from_string(raw,content_type='image/jpeg',if_generation_match=0,timeout=60)
        blob.reload();assert blob.size==len(raw) and blob.md5_hash==base64.b64encode(hashlib.md5(raw).digest()).decode()
        uploads.append({'path':im['path'],'sha256':im['sha256'],'bytes':len(raw),'generation':blob.generation})
    core.save_new(RUN/'uploads.json',uploads)
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        receipt=RUN/(target+'-applied.json')
        if receipt.exists():continue
        recovery=read(Path(p['backups'][target]['path']));old={r['slug']:r for r in recovery['artworks']}
        with dbconn(dsn,False) as db,db.transaction():
            db.execute('SELECT pg_advisory_xact_lock(55922026092003)')
            locked=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE slug=ANY(%s::text[]) ORDER BY slug FOR UPDATE',([c['slug'] for c in p['changes']],)).fetchall()
            assert len(locked)==len(old) and all(r['row']==old[r['row']['slug']] for r in locked),'Target artwork changed since preflight'
            for change in p['changes']:
                row=old[change['slug']];aid=row['id'];sid=source(db,change['source_url'])
                patch=change['patch'];assignments=sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in patch)
                db.execute(sql.SQL('UPDATE artworks SET {},revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s').format(assignments),(*patch.values(),core.ACTOR,aid))
                if change['creator_note']:
                    previous=[r for r in recovery['artwork_artists'] if r['artwork_id']==aid]
                    current=[r['row'] for r in db.execute('SELECT to_jsonb(aa) row FROM artwork_artists aa WHERE artwork_id=%s FOR UPDATE',(aid,)).fetchall()]
                    assert len(current)==len(previous)==1 and current==previous
                    combined=(previous[0].get('attribution_note') or '')+'\n\nReview 20 September 2026: '+change['creator_note']
                    db.execute('UPDATE artwork_artists SET attribution_note=%s WHERE artwork_id=%s',(combined,aid))
                if change['slug'] in WALTERS:
                    iid=next(i['id'] for i in recovery['institutions'] if i['wikidata_id']=='Q210081')
                    assert row['current_institution_id'] in (None,iid)
                    active=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL FOR UPDATE",(aid,)).fetchall()
                    assert not active or (len(active)==1 and active[0]['institution_id']==iid)
                    if not active:db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(uid('holding/'+aid),aid,iid,sid,change['source_url'],change['note'],core.now()))
                evidence={'plan_sha256':core.sha((RUN/'plan.json').read_bytes()),'changes':patch,'review_note':change['note'],'creator_note':change['creator_note'],'prior_review':str(AUDIT/'primary-source-review.json')}
                if change['slug'] in WALTERS or change['slug']==OSLO:evidence['primary_source']=read(RUN/'source-selection.json')['selected'][change['slug']]
                db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'byzantine_icon_review_20260920',%s,%s,%s,%s,%s)",(uid('citation/'+aid),aid,sid,row.get('accession_number') or change['slug'],change['source_url'],json.dumps(evidence,ensure_ascii=False),core.now(),core.ACTOR))
            for im in m['images']:
                aid=im['target_ids'][target];sid=source(db,im['page'])
                assert db.execute('SELECT primary_media_id FROM artworks WHERE id=%s',(aid,)).fetchone()['primary_media_id'] is None
                attribution=im['credit']+'. '+im['facts']['title']+'. '+im['license_label']+' ('+im['license_url']+'). '+im.get('image_page',im['page'])+'. '+im['transform']+'.'
                db.execute("""INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
                    VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(im['media_id'],im['path'],im.get('image_page',im['page']),'The Walters Art Museum' if im['slug'] in WALTERS else 'Nasjonalmuseet via Wikimedia Commons',im['width'],im['height'],im['bytes'],im['sha256'],im['facts']['title'],im['rights_status'],im['license_label'],im['license_url'],im['credit'],attribution,im['downloaded_at'],core.now(),core.ACTOR))
                db.execute('INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(im['media_id'],sid,im['native_id'],im.get('file_capture',im['capture'])['sha256'],im['source_image_url'],im['license_url'],im['rights_basis'],SOURCE,core.now(),Jsonb(im)))
                db.execute("INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,'Full-frame licensed museum reproduction')",(aid,im['media_id']))
                db.execute('UPDATE artworks SET primary_media_id=%s WHERE id=%s',(im['media_id'],aid))
        core.save_new(receipt,{'at':core.now(),'target':target,'plan_sha256':core.sha((RUN/'plan.json').read_bytes()),'records_updated':len(p['changes']),'images_attached':len(m['images']),'published':0})
        print(target,'committed 19 catalogue updates and 3 images',flush=True)


def verify():
    p,m=validate_pins();summaries={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        old=read(Path(p['backups'][target]['path']));before_rows={r['slug']:r for r in old['artworks']}
        with dbconn(dsn) as db:
            after=before(db,[c['slug'] for c in p['changes']]);actual={r['slug']:r for r in after['artworks']}
            for change in p['changes']:
                row=actual[change['slug']];prior=before_rows[change['slug']]
                assert row['status']=='review' and row['published_at'] is None
                assert all(row[k]==v for k,v in change['patch'].items())
                allowed=set(change['patch'])|{'updated_at','updated_by','revision'}
                if change['slug'] in WALTERS:allowed|={'current_institution_id','location_checked_at','location_source_url'}
                if any(im['slug']==change['slug'] for im in m['images']):allowed.add('primary_media_id')
                assert {k:v for k,v in row.items() if k not in allowed}=={k:v for k,v in prior.items() if k not in allowed},change['slug']
                assert any(c['id']==uid('citation/'+row['id']) for c in after['citations'])
            for im in m['images']:
                assert actual[im['slug']]['primary_media_id']==im['media_id']
                asset=next(x for x in after['media_assets'] if x['id']==im['media_id'])
                assert asset['byte_size']==im['bytes']<=100000 and asset['checksum_sha256']==im['sha256']
                assert asset['rights_status']==im['rights_status'] and asset['license_url']==im['license_url']
                assert any(x['media_id']==im['media_id'] for x in after['media_rights_evidence'])
            prior_display={x['id'] for x in old['artwork_location_assertions'] if x['claim_type']=='display'}
            assert {x['id'] for x in after['artwork_location_assertions'] if x['claim_type']=='display'}==prior_display
        core.save_new(RUN/(target+'-after.json'),after)
        summaries[target]={'records_verified':len(actual),'images_verified':len(m['images']),'review_status_preserved':True,'unplanned_artwork_fields_unchanged':True,'new_display_claims':0}
    public=[]
    for im in m['images']:
        response=requests.get(SITE+im['path'],timeout=60);response.raise_for_status()
        assert len(response.content)==im['bytes'] and core.sha(response.content)==im['sha256']
        public.append({'url':SITE+im['path'],'status':response.status_code,'bytes':len(response.content),'sha256':im['sha256']})
    core.save_new(RUN/'verified.json',{'at':core.now(),'databases':summaries,'public_images':public})
    print(json.dumps(summaries),flush=True)


def check_api():
    _,manifest=validate_pins();ids=[im['target_ids']['cloud'] for im in manifest['images']]
    with dbconn(core.cloud_dsn()) as db:
        links=db.execute('SELECT aa.artwork_id::text,p.slug FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
    checks=[]
    for im in manifest['images']:
        matches=[r for r in links if r['artwork_id']==im['target_ids']['cloud']];assert len(matches)==1
        url=SITE+'/api/backend/v1/artists/'+matches[0]['slug']+'/works/'+im['target_ids']['cloud']
        response=requests.get(url,timeout=60);response.raise_for_status();record=response.json()
        expected={'title':im['facts']['title'],'media_url':im['path'],'status':'review',
                  'license_url':im['license_url'],'source_page_url':im.get('image_page',im['page'])}
        assert all(record.get(k)==v for k,v in expected.items()),{'slug':im['slug'],'fields':[k for k,v in expected.items() if record.get(k)!=v]}
        checks.append({'slug':im['slug'],'url':url,'status':response.status_code,'verified':expected})
    core.save_new(RUN/'public-api-verified.json',{'at':core.now(),'checks':checks})
    print('Public catalogue API verified for all three new image attachments',flush=True)


def check_gaps():
    dispositions=read(RUN/'image-gap-dispositions.json');slugs=[r['slug'] for r in dispositions['records']];checks={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with dbconn(dsn) as db:
            rows=db.execute('SELECT slug,primary_media_id::text FROM artworks WHERE slug=ANY(%s::text[]) ORDER BY slug',(slugs,)).fetchall()
        assert len(rows)==25
        held={r['slug'] for r in dispositions['records'] if r['outcome']=='held'}
        assert {r['slug'] for r in rows if r['primary_media_id'] is None}==held
        checks[target]={'original_gap_records':25,'now_with_images':3,'remaining_gaps':22,'records':rows}
    core.save_new(RUN/'image-gap-verification.json',{'at':core.now(),'databases':checks})
    print('Remaining 22 selected image gaps confirmed in both databases',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['research','plan','prepare','apply','verify','check_api','check_gaps'])
    args=parser.parse_args();RUN.mkdir(parents=True,exist_ok=True);globals()[args.phase]()
