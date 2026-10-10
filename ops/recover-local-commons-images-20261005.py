#!/usr/bin/env python3
"""Selected local-only Commons recovery using established identity/rights checks."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from PIL import Image, ImageDraw, ImageOps

spec = importlib.util.spec_from_file_location('commons', Path(__file__).with_name('overnight-commons-images.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
core = m.core
DSN = 'postgres://localhost/artline'
RUN = core.ROOT / 'docs/research/local-commons-recovery-20261005'
ARCHIVE = Path.home() / 'Library/Application Support/Artline'
original_entity_match=m.entity_match


def selected_entity_match(c,e,require_primary_image=True):
    filename=c.get('selected_commons_filename')
    if not filename:return original_entity_match(c,e,require_primary_image)
    original_entity_match(c,e,require_primary_image=False)
    if filename not in m.values(e,'P18') or re.search(r'\b(detail|collage|montage|verso|reverse)\b',filename,re.I):
        raise ValueError('Selected alternate is not an eligible authority-linked image')
    return filename


m.entity_match=selected_entity_match


def policy_hold(im):
    if 'commons' not in im['raw']:return None
    meta=im['raw']['commons'].get('imageinfo',[{}])[0].get('extmetadata',{})
    credit=' '.join(meta.get(k,{}).get('value','') for k in ('Credit','Attribution'))
    independent=bool(re.search(r'own work|own photo|self-photographed|photographie personnelle',credit,re.I))
    if im['rights_status']=='public_domain' and not independent and re.search(r'foto\.munchmuseet\.no',credit,re.I):
        return {'source_url':'https://foto.munchmuseet.no/fotoweb/views/terms-and-conditions',
            'finding':'The originating MUNCH photograph archive specifies CC BY-NC-SA 4.0, with limited publication exceptions. A Commons underlying-work public-domain label does not establish an unrestricted photograph-specific grant.',
            'decision':'Hold this museum-archive reproduction; an independently licensed photograph can be assessed separately.'}
    if im['rights_status']=='public_domain' and not independent and re.search(r'ebyzantinemuseum\.gr',credit,re.I):
        return {'source_url':'https://www.ebyzantinemuseum.gr/?i=bxm.en.terms',
            'finding':'The originating Athens virtual museum limits content downloads to personal and noncommercial use and requires prior written approval for other uses. No unrestricted photograph-specific exception was established.',
            'decision':'Hold this museum-supplied reproduction while preserving anonymous/workshop attribution; review an independent photograph separately.'}
    if im['rights_status']=='public_domain' and re.search(r'(?:www\.)?museum-joanneum\.at',credit,re.I):
        return {'source_url':'https://www.museum-joanneum.at/presse/foto-und-drehanfragen-1',
            'finding':'Originating museum permits editorial reporting about the museum and requires written consent for other image uses; its current terms also restrict redistribution and electronic alteration. Commons PD-Art labels do not resolve this source-use conflict.',
            'decision':'Hold museum-supplied reproduction for independent clearance; preserve catalogue metadata and private source evidence.'}
    if im['rights_status']=='public_domain' and re.search(r'(?:www\.)?salzburgmuseum\.at',credit,re.I):
        return {'source_url':'https://sammlung-online.salzburgmuseum.at/service/impressum',
            'finding':'Originating museum limits website photographs to personal use and requires consent for further reproduction/publication, with a narrow museum-reporting exception. No unrestricted photograph-specific grant was established.',
            'decision':'Hold museum-supplied reproduction for independent clearance; preserve catalogue metadata and private source evidence.'}
    if im['artwork_id']=='4ba9c01a-2f59-584e-857d-64c08b904da0' and im['rights_status']=='public_domain' and re.search(r'sammlung\.wienmuseum\.at',credit,re.I):
        return {'source_url':'https://sammlung.wienmuseum.at/en/object/467916-bertha-mueller-die-schwester-des-kuenstlers/',
            'finding':'The originating museum licenses the Bertha Müller photographs CC BY 4.0 with photographer credit. A Commons underlying-work public-domain label is not sufficient to retain the photograph attribution correctly.',
            'decision':'Use a separately verified native photograph with its exact CC BY 4.0 credit; do not attach this candidate as public domain.'}
    if im['institution_slug']=='kunsthistorisches-museum' and re.search(r'khm\.at|Kunsthistorisches Museum',credit,re.I):
        return {'source_url':'https://www.khm.at/fileadmin/pdf_KHM/agb/AGB_Bilddatenbank.pdf',
            'prior_evidence':'docs/research/italy-images-4h-20260916/institution-rights-holds/khm.json',
            'finding':'Museum-supplied source has explicit CC BY-NC-SA 4.0 terms; per-file Commons public-domain label does not resolve existing operational clearance conflict.',
            'decision':'Hold museum-supplied reproduction for source-use clearance. Preserve artwork metadata and private evidence.'}
    if im['institution_slug']=='wikimedia-museum-q2051997' and re.search(r'artuk\.org|nationalgalleries\.org',credit,re.I):
        return {'source_url':'https://www.nationalgalleries.org/copyright-image-licensing',
            'finding':'National Galleries of Scotland permits personal/noncommercial reuse. A current explicit unrestricted licence on the exact originating Art UK image could not be verified.',
            'decision':'Hold these museum/Art UK source reproductions pending exact primary-source image-use clearance.'}
    if im['artwork_id']=='8ba09e60-e90f-5196-a07f-70bf9b0d363f' and im['rights_status']=='public_domain' and re.search(r'artuk\.org',credit,re.I):
        return {'source_url':'https://www.ashmolean.org/ordering-images',
            'finding':'The exact Commons file credits the Ashmolean reproduction on Art UK. The originating museum reserves its collection photographs and requires clearance from its Picture Library; no unrestricted photograph-specific grant was established for this file.',
            'decision':'Hold this museum/Art UK photograph for independent clearance; retain the Commons public-domain claim and native policy evidence.'}
    return None


def connect(readonly=True):
    return psycopg.connect(DSN, row_factory=dict_row, autocommit=True,
        options='-c statement_timeout=60000' + (' -c default_transaction_read_only=on' if readonly else ''))


def select(limit,institution=None,exclude_run=None,exclude_institutions=None):
    excluded=[]
    if exclude_run:
        excluded=[c['artwork_id'] for c in json.loads((exclude_run/'candidates.json').read_bytes())['candidates']]
    with connect() as db:
        baseline = db.execute("SELECT count(*) total, count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks").fetchone()
        rows = db.execute('''WITH candidates AS (
          SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.accession_number,
            a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,
            to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,
            i.name museum,i.wikidata_id institution_qid,i.website_url,
            e.external_id qid,e.source_id::text,e.canonical_url page,
            ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
            (SELECT jsonb_agg(jsonb_build_object('qid',ae.external_id,'name',ar.display_name,'death',ar.death_year) ORDER BY ar.id)
             FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
             LEFT JOIN external_identifiers ae ON ae.entity_type='artist' AND ae.entity_id=ar.id AND ae.scheme='wikidata'
             WHERE aa.artwork_id=a.id) creators,
            (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
            (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
            EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_countries ac ON ac.artist_id=aa.artist_id
                   WHERE aa.artwork_id=a.id AND ac.country_code IN ('RU','GR','CY')) priority,
            EXISTS(SELECT 1 FROM artwork_artists aa JOIN artist_discovery_selection ds ON ds.artist_id=aa.artist_id
                   WHERE aa.artwork_id=a.id AND ds.is_popular) popular
          FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
          JOIN institutions i ON i.id=a.current_institution_id
          WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.source_id IS NOT NULL
            AND (%s::text IS NULL OR i.slug=%s) AND NOT(a.id=ANY(%s::uuid[]))
            AND NOT(i.slug=ANY(%s::text[]))
            AND a.primary_media_id IS NULL AND a.status='review' AND i.wikidata_id IS NOT NULL
            AND a.work_type IN ('painting','watercolor','drawing','fresco')
            AND a.creation_year_start>=1000
            AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
            AND artline_has_selection_evidence(a.id)), ranked AS (
          SELECT *,row_number() OVER(PARTITION BY creators ORDER BY priority DESC,artwork_id) creator_rank
          FROM candidates WHERE roles=ARRAY['primary']::text[] AND jsonb_array_length(creators)=1
            AND creators->0->>'qid' IS NOT NULL)
          SELECT * FROM ranked WHERE creator_rank<=3
          ORDER BY priority DESC,creator_rank,popular DESC,artwork_id LIMIT %s''', (institution,institution,excluded,exclude_institutions or [],limit)).fetchall()
    for c in rows:
        c.update(external_id=c['qid'],scheme='wikidata',provider='night-commons',
                 artist='; '.join(a['name'] for a in c['creators']),target_ids={'local':c['artwork_id']})
        c['native_identifiers'] = [dict(scheme=e['scheme'],external_id=e['external_id'],url=e['canonical_url'])
                                   for e in c['identifiers'] if e['scheme']!='wikidata']
    core.save_new(RUN/'candidates.json', {'at':core.now(),'baseline':baseline,'candidates':rows})
    print(json.dumps({'baseline':baseline,'selected':len(rows),'priority':sum(c['priority'] for c in rows),
                      'artists':len({c['artist'] for c in rows})}),flush=True)


def research():
    rows = json.loads((RUN/'candidates.json').read_bytes())['candidates']
    done = core.latest_events(RUN)
    rows = [c for c in rows if c['artwork_id'] not in done and not (RUN/'selected/night-commons'/(c['artwork_id']+'.json')).exists()]
    fetcher = core.Fetcher(RUN/'metadata/commons-evidence')
    index_path=RUN/'existing-authority-cache-index.json'
    index=json.loads(index_path.read_bytes()) if index_path.exists() else {}
    for start in range(0,len(rows),10):
        group=rows[start:start+10]
        # Published entity JSON remains available while the Action API reports
        # replication lag. Serial, cached public reads retain exact revisions.
        for c in group:
            if c['qid'] in index:continue
            url='https://www.wikidata.org/wiki/Special:EntityData/'+c['qid']+'.json'
            raw=fetcher.metadata(url)
            entity=raw.get('entities',{}).get(c['qid'])
            if not entity:raise ValueError('Published authority entity missing')
            receipt=json.loads((fetcher.cache/(core.sha(url.encode())+'.receipt.json')).read_bytes())
            path=RUN/'authorities'/(c['qid']+'.json')
            core.save_new(path,dict(entity=entity,receipt=receipt))
            index[c['qid']]=[str(path.relative_to(core.ROOT))]
        index_path.write_bytes(core.encode(index))
        ready=m.research_chunk(group,RUN,fetcher)
        print(json.dumps({'checked':min(start+10,len(rows)),'total':len(rows),'rights_verified':len(ready)}),flush=True)


def alternatives(from_runs):
    rows=[];index={};seen=set()
    for source_run in from_runs:
        for c in json.loads((source_run/'candidates.json').read_bytes())['candidates']:
            authority=source_run/'authorities'/(c['qid']+'.json')
            if not authority.exists() or c['artwork_id'] in seen:continue
            entity=json.loads(authority.read_bytes())['entity']
            filenames=m.values(entity,'P18')
            if len(filenames)<2:continue
            choices=[f for f in filenames if isinstance(f,str) and not re.search(
                r'google|\b(detail|collage|montage|verso|reverse)\b',f,re.I)]
            if not choices:continue
            # Discovery prioritizes the accession-labelled museum reproduction;
            # normal identity, provenance and licensing checks still apply.
            choices.sort(key=lambda f:(bool(c['accession_number'] and c['accession_number'] in f),
                'museum' in f.lower(),len(f)),reverse=True)
            c['selected_commons_filename']=choices[0]
            c['alternate_discovery']={'authority_images':filenames,'selection_basis':
                'Prefer an accession-labelled museum reproduction among authority-linked files; fresh file-level review required.'}
            rows.append(c);seen.add(c['artwork_id'])
            index[c['qid']]=[str(authority.resolve().relative_to(core.ROOT))]
    with connect() as db:
        remaining={r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[]) AND primary_media_id IS NULL',
                                              ([c['artwork_id'] for c in rows],)).fetchall()}
    rows=[c for c in rows if c['artwork_id'] in remaining]
    core.save_new(RUN/'candidates.json',dict(at=core.now(),candidates=rows))
    core.save_new(RUN/'existing-authority-cache-index.json',index)
    print('Selected authority-linked alternate files',len(rows),flush=True)


def prepared():
    return [json.loads(p.read_bytes()) for p in sorted((RUN/'images').glob('*.json'))]


def prepare(provider='night-commons'):
    fetcher=core.Fetcher(RUN/'metadata/downloads')
    fetcher.defer_long_cooldowns=True
    for p in sorted((RUN/'selected'/provider).glob('*.json')):
        im=json.loads(p.read_bytes())
        receipt=RUN/'images'/(im['artwork_id']+'.json')
        if receipt.exists():continue
        hold=policy_hold(im)
        if hold:
            core.event(RUN,dict(provider=im['provider'],artwork_id=im['artwork_id'],outcome='source_policy_hold',policy=hold));continue
        core.validate_source_image_identity(im)
        with connect() as db:
            held=db.execute("SELECT id,rights_status FROM media_assets WHERE source_page_url=%s AND rights_status NOT IN ('public_domain','cc0','cc_by','cc_by_sa')",(im['page'],)).fetchall()
            current=db.execute('SELECT primary_media_id FROM artworks WHERE id=%s',(im['artwork_id'],)).fetchone()
        if held or current['primary_media_id']:
            core.event(RUN,dict(provider=im['provider'],artwork_id=im['artwork_id'],outcome='held_existing_media_or_rights'));continue
        try:
            data,headers=fetcher.get(im['source_image_url'])
            if im.get('commons_original_sha1') and hashlib.sha1(data).hexdigest()!=im['commons_original_sha1']:
                raise ValueError('Original Commons checksum differs')
            digest=core.sha(data)
            archive=ARCHIVE/'source-images'/RUN.name/(im['artwork_id']+'-'+digest[:16]+'.image')
            core.save_new(archive,data)
            compressed,width,height,quality=core.compress(data)
            derivative_sha=core.sha(compressed)
            path='/assets/artworks/imported/'+RUN.name+'/'+im['artwork_id']+'-'+derivative_sha[:16]+'.jpg'
            core.save_new(core.ROOT/'apps/web/public'/path.lstrip('/'),compressed)
            im.update(path=path,sha256=derivative_sha,bytes=len(compressed),width=width,height=height,jpeg_quality=quality,
                source_sha256=digest,source_bytes=len(data),source_archive=str(archive),downloaded_at=core.now(),
                response_headers=headers,transform='Full-frame proportional resize and JPEG compression; no crop or generated content',
                media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
            core.save_new(receipt,im)
            core.event(RUN,dict(provider=im['provider'],artwork_id=im['artwork_id'],outcome='prepared',path=path))
            print('Prepared',im['artist'],im['title'],flush=True)
        except Exception as error:
            core.event(RUN,dict(provider=im['provider'],artwork_id=im['artwork_id'],outcome='download_deferred',reason=str(error)[:400]))
    sheets=Path('/private/tmp')/RUN.name
    sheets.mkdir(parents=True,exist_ok=True)
    rows=prepared()
    for offset in range(0,len(rows),20):
        sheet=Image.new('RGB',(1400,5*270),'#eee9df');draw=ImageDraw.Draw(sheet)
        for index,im in enumerate(rows[offset:offset+20]):
            x=(index%4)*350;y=(index//4)*270
            with Image.open(core.ROOT/'apps/web/public'/im['path'].lstrip('/')) as picture:
                picture.thumbnail((336,215));sheet.paste(picture,(x+(350-picture.width)//2,y))
            draw.text((x+7,y+217),f'{offset+index+1}. {im["artist"][:42]}',fill='black')
            draw.text((x+7,y+233),im['title'][:46],fill='black')
            authority=im.get('qid') or im['scheme']+':'+im['external_id']
            draw.text((x+7,y+249),authority+' / '+im['artwork_id'][:8],fill='black')
        sheet.save(sheets/f'contact-{offset//20+1:02}.jpg')
    print('Prepared total',len(rows),'sheets',str(sheets),flush=True)


def apply():
    review=json.loads((RUN/'visual-review.json').read_bytes())
    images={im['artwork_id']:im for im in prepared()}
    approved=[images[x['artwork_id']] for x in review['images'] if x['decision']=='approved']
    pinned={x['artwork_id']:x['sha256'] for x in review['images']}
    for im in approved:
        if policy_hold(im):raise ValueError('Known source-policy conflict requires independent clearance')
        data=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if core.sha(data)!=im['sha256'] or im['sha256']!=pinned[im['artwork_id']] or len(data)>100000:
            raise ValueError('Reviewed derivative changed')
        if core.sha(Path(im['source_archive']).read_bytes())!=im['source_sha256']:
            raise ValueError('Archived source changed')
    receipts=[]
    with connect(False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='3s'")
        db.execute('SELECT pg_advisory_xact_lock(610052026)')
        before=[]
        for im in sorted(approved,key=lambda x:x['artwork_id']):
            current=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(im['artwork_id'],)).fetchone()['record']
            if current['primary_media_id']:
                receipts.append(dict(artwork_id=im['artwork_id'],result='existing_media_preserved'));continue
            if current!=im['before_record']:raise ValueError('Artwork changed since selection: '+im['artwork_id'])
            links=db.execute('SELECT to_jsonb(aa) record FROM artwork_artists aa WHERE artwork_id=%s ORDER BY artist_id',(im['artwork_id'],)).fetchall()
            identifiers=db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=%s ORDER BY id",(im['artwork_id'],)).fetchall()
            if [x['record'] for x in links]!=im['creator_links'] or [x['record'] for x in identifiers]!=im['identifiers']:
                raise ValueError('Artwork identity links changed')
            before.append(dict(artwork=current,creators=links,identifiers=identifiers))
        backup=ARCHIVE/'backups'/RUN.name/('locked-preimages-'+str(uuid.uuid4())+'.json')
        core.save_new(backup,before)
        core.save_new(RUN/('backup-'+backup.stem+'.json'),dict(path=str(backup),sha256=core.sha(backup.read_bytes()),records=len(before)))
        skip={r['artwork_id'] for r in receipts}
        for im in approved:
            if im['artwork_id'] not in skip:
                result=m.attach(db,im,'local')
                if result!='attached':raise ValueError('Attachment was not completed: '+result)
                db.execute('''INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label)
                    VALUES(%s,%s,0,'Full composition') ON CONFLICT(artwork_id,media_id) DO NOTHING''',
                    (im['artwork_id'],im['media_id']))
                stored=db.execute('''SELECT storage_path,checksum_sha256,license_url,creator_credit
                    FROM media_assets WHERE id=%s''',(im['media_id'],)).fetchone()
                if stored!=dict(storage_path=im['path'],checksum_sha256=im['sha256'],
                    license_url=im['policy_url'],creator_credit=im['creator_credit']):
                    raise ValueError('Stored media differs from reviewed image')
                receipts.append(dict(artwork_id=im['artwork_id'],result=result,media_id=im['media_id'],path=im['path']))
    core.save_new(RUN/'apply-receipt.json',dict(at=core.now(),local_only=True,receipts=receipts))
    print('Committed local attachments',sum(r['result']=='attached' for r in receipts),flush=True)


def hold_sources():
    receipt=json.loads((RUN/'apply-receipt.json').read_bytes())
    attached={r['artwork_id'] for r in receipt['receipts'] if r['result']=='attached'}
    previous=sorted(RUN.glob('source-policy-correction*.json'))
    withdrawn={aid for p in previous for aid in json.loads(p.read_bytes())['artwork_ids']}
    attached-=withdrawn
    selected=[im for im in prepared() if im['artwork_id'] in attached and policy_hold(im)]
    if not selected:
        print('No additional own attachments require a source-policy hold',flush=True);return
    suffix='-'+str(len(previous)+1).zfill(3) if previous else ''
    backup=ARCHIVE/'backups'/RUN.name/('source-policy-correction'+suffix)
    for im in selected:
        data=(core.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        if core.sha(data)!=im['sha256']:raise ValueError('Own derivative changed')
        core.save_new(backup/'derivatives'/Path(im['path']).name,data)
    with connect(False) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='3s'")
        before=[]
        for im in sorted(selected,key=lambda x:x['artwork_id']):
            row=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence
                FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
                JOIN media_rights_evidence e ON e.media_id=m.id
                WHERE a.id=%s AND m.id=%s FOR UPDATE OF a,m,e''',(im['artwork_id'],im['media_id'])).fetchone()
            if not row or row['media']['checksum_sha256']!=im['sha256']:raise ValueError('Own attachment changed')
            excluded={'primary_media_id','updated_at','updated_by','revision'}
            if {k:v for k,v in row['artwork'].items() if k not in excluded}!={k:v for k,v in im['before_record'].items() if k not in excluded}:
                raise ValueError('Artwork metadata changed')
            before.append(row)
        core.save_new(backup/'locked-before.json',before)
        for im in selected:
            hold=policy_hold(im)
            db.execute('UPDATE artworks SET primary_media_id=NULL,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id=%s',
                       (core.ACTOR,im['artwork_id'],im['media_id']))
            db.execute('DELETE FROM artwork_media WHERE artwork_id=%s AND media_id=%s',(im['artwork_id'],im['media_id']))
            db.execute("UPDATE media_assets SET rights_status='unknown',verified_at=NULL,verified_by=NULL,storage_kind='placeholder',storage_path=NULL,updated_at=now() WHERE id=%s",(im['media_id'],))
            db.execute('UPDATE media_rights_evidence SET rights_basis=%s,evidence_json=evidence_json || %s,checked_at=now() WHERE media_id=%s',
                ('HOLD: '+hold['finding'],Jsonb({'source_policy_correction':hold}),im['media_id']))
    for im in selected:
        local=core.ROOT/'apps/web/public'/im['path'].lstrip('/')
        # Only files created by this run are removed from serving; identical
        # bytes have already been verified in the private recovery archive.
        local.unlink()
        core.event(RUN,dict(provider='night-commons',artwork_id=im['artwork_id'],outcome='source_policy_hold',policy=policy_hold(im)))
    core.save_new(RUN/('source-policy-correction'+suffix+'.json'),dict(at=core.now(),artwork_ids=[im['artwork_id'] for im in selected],backup=str(backup)))
    print('Held own source-conflicting attachments; private bytes preserved:',len(selected),flush=True)


def verify():
    receipt=json.loads((RUN/'apply-receipt.json').read_bytes())
    images={im['artwork_id']:im for im in prepared()}
    corrections=sorted(RUN.glob('source-policy-correction*.json'))
    withdrawn={aid for p in corrections for aid in json.loads(p.read_bytes())['artwork_ids']}
    checks=[]
    with connect() as db:
        for r in receipt['receipts']:
            if r['result']!='attached':continue
            im=images[r['artwork_id']]
            if im['artwork_id'] in withdrawn:
                held=db.execute('''SELECT a.primary_media_id,m.rights_status,m.storage_path FROM artworks a
                    JOIN media_assets m ON m.id=%s WHERE a.id=%s''',(im['media_id'],im['artwork_id'])).fetchone()
                if not held or held['primary_media_id']==im['media_id'] or held['rights_status']!='unknown' or held['storage_path']:
                    raise ValueError('Source-policy hold not enforced')
                continue
            row=db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,to_jsonb(e) evidence
                FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
                JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=%s''',(im['artwork_id'],)).fetchone()
            if not row:raise ValueError('Missing image/evidence')
            excluded={'primary_media_id','updated_at','updated_by','revision'}
            if {k:v for k,v in row['artwork'].items() if k not in excluded}!={k:v for k,v in im['before_record'].items() if k not in excluded}:
                raise ValueError('Catalogue metadata or status changed')
            data=(core.ROOT/'apps/web/public'/row['media']['storage_path'].lstrip('/')).read_bytes()
            if row['media']['id']!=im['media_id'] or core.sha(data)!=im['sha256'] or row['media']['checksum_sha256']!=im['sha256']:
                raise ValueError('Database/file checksum differs')
            if row['evidence']['source_image_url']!=im['source_image_url'] or row['media']['license_url']!=im['policy_url']:
                raise ValueError('Rights evidence differs')
            if not db.execute('SELECT 1 FROM artwork_media WHERE artwork_id=%s AND media_id=%s',
                              (im['artwork_id'],im['media_id'])).fetchone():
                raise ValueError('Artwork/media association missing')
            with Image.open(io.BytesIO(data)) as picture:
                picture.verify()
            checks.append(dict(artwork_id=im['artwork_id'],title=im['title'],artist=im['artist'],bytes=len(data),status=row['artwork']['status'],source_url=im['page']))
    suffix='-'+str(len(corrections)).zfill(3) if len(corrections)>1 else ''
    name='verification-after-source-review'+suffix+'.json' if withdrawn else 'verification.json'
    core.save_new(RUN/name,dict(at=core.now(),passed=True,verified=len(checks),withdrawn=len(withdrawn),checks=checks))
    with (RUN/'attached-images.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['artwork_id','title','artist','bytes','status','source_url']);writer.writeheader();writer.writerows(checks)
    print('Verified files, database, rights and unchanged metadata:',len(checks),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['select','alternatives','research','prepare','apply','hold_sources','verify'])
    parser.add_argument('--limit',type=int,default=120)
    parser.add_argument('--institution')
    parser.add_argument('--exclude-institution',action='append',default=[])
    parser.add_argument('--exclude-run',type=Path)
    parser.add_argument('--run-name',default=RUN.name)
    parser.add_argument('--from-run',type=Path,action='append',default=[])
    args=parser.parse_args()
    if not re.fullmatch(r'local-commons-[a-z0-9-]+',args.run_name):parser.error('Invalid run name')
    if not 1<=args.limit<=500:parser.error('Select 1–500 existing records per reviewed batch')
    RUN=core.ROOT/'docs/research'/args.run_name
    RUN.mkdir(parents=True,exist_ok=True)
    if args.phase=='select':select(args.limit,args.institution,args.exclude_run,args.exclude_institution)
    elif args.phase=='alternatives':alternatives(args.from_run)
    else:globals()[args.phase]()
