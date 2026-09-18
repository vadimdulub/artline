#!/usr/bin/env python3
"""Bounded France campaign: read-only planning, immutable evidence, review writes.

Never publishes or invents artist biographies. Existing artworks are not changed
by the metadata importer. Ambiguous identities stay in a separate review queue.
"""
import argparse
import collections
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import unicodedata
import uuid
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/france-catalogue-20260916'
RESEARCH = ROOT / 'docs/research/france-museums-deep-20260916'
BACKUP = Path('/Users/vadimdulub/Library/Application Support/Artline/backups/france-catalogue-20260916')
spec = importlib.util.spec_from_file_location('france_images_core', ROOT / 'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
SOURCE = 'france-joconde-selected-20260916'
SNAPSHOT_SHA = '499aab59e4c9fb4bea94ed7066d4dce1f51092c74d3c8a370b8fab53039767ef'
PRIORITY = ['M0712', 'M0720', 'M0880', 'M0884', 'M0888', 'M5029', 'M5031', 'M5060', 'M1101', 'M1111']


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    core.save_new(path, value)


def uid(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://artline.local/france-20260916/' + key))


def norm(text):
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c))))


def tokenkey(text):
    return ' '.join(sorted(norm(text).split()))


def acckeys(text):
    return {re.sub(r'[^a-z0-9]', '', norm(x.split('(')[0])) for x in (text or '').split(';') if x.strip()}


def connect(target, readonly=True):
    return psycopg.connect('postgres://localhost/artline' if target == 'local' else core.cloud_dsn(),
        autocommit=True, row_factory=dict_row,
        options='-c statement_timeout=120000' + (' -c default_transaction_read_only=on' if readonly else ''))


def backups():
    path = BACKUP / 'local-before.dump'
    listing = subprocess.check_output(['pg_restore', '--list', str(path)], text=True)
    assert 'TABLE DATA public artworks' in listing and 'TABLE DATA public media_assets' in listing
    remote = json.loads(subprocess.check_output(['gcloud', 'sql', 'backups', 'describe', '1789590593680',
        '--instance=artline-postgres', '--project=artline-508319', '--format=json'], text=True))
    assert remote['status'] == 'SUCCESSFUL', 'Cloud backup is not complete'
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = {'at': core.now(), 'local': {'path': str(path), 'bytes': path.stat().st_size,
        'sha256': digest, 'archive_directory_validated': True}, 'cloud': remote}
    save(RUN / 'backups.json', result)
    print('Verified full local archive and successful Cloud SQL backup', flush=True)


def image_plan(batch, limit):
    assert 1 <= limit <= 250
    run = RUN / batch
    assert not (run / 'candidates-local.json').exists(), 'Existing immutable selection'
    institutions = load(RESEARCH / 'local-institutions.json')
    wanted = [i for i in institutions if i['status'] != 'archived']
    ids = [i['id'] for i in wanted]
    priority_ids = [i['id'] for i in wanted if set(i['museofile_codes']) & set(PRIORITY)]
    with connect('local') as db:
        rows = db.execute('''WITH selected AS MATERIALIZED (
          SELECT a.id FROM artworks a WHERE a.current_institution_id=ANY(%s::uuid[])
          AND a.primary_media_id IS NULL AND a.status<>'archived' AND a.work_type='painting'
          AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible'
          AND EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata')
          AND artline_has_selection_evidence(a.id)
          ORDER BY (a.current_institution_id=ANY(%s::uuid[])) DESC,a.id LIMIT %s
        ) SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.date_display,
          a.creation_year_start,a.creation_year_end,a.work_type,a.accession_number,
          i.slug institution_slug,i.wikidata_id institution_qid,i.website_url,e.external_id qid,
          (SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'qid',ae.external_id,'death',ar.death_year))
           FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id
           JOIN external_identifiers ae ON ae.entity_type='artist' AND ae.entity_id=ar.id AND ae.scheme='wikidata'
           WHERE aa.artwork_id=a.id AND aa.attribution_role='primary') creators
          FROM selected s JOIN artworks a ON a.id=s.id JOIN institutions i ON i.id=a.current_institution_id
          JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata'
          ORDER BY (a.current_institution_id=ANY(%s::uuid[])) DESC,a.id''', (ids, priority_ids, limit, priority_ids)).fetchall()
        save(run / 'candidates-local.json', rows)
    print('Selected existing France image gaps:', len(rows), collections.Counter(r['institution_slug'] for r in rows), flush=True)


def select(batch, codes):
    run = RUN / batch
    candidates = [x for x in load(RESEARCH / 'bounded-joconde-candidates.json') if x['museofile_id'] in codes]
    assert 1 <= len(candidates) <= 250, 'Bounded batch requires 1–250 selected works'
    wanted = {x['source_reference'] for x in candidates}
    path = ROOT / 'content/imports/joconde-20260910/joconde.csv'
    with path.open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == SNAPSHOT_SHA
    csv.field_size_limit(8_000_000)
    rows = []
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream, delimiter='|'):
            if row['Reference'] in wanted:
                rows.append(row)
    assert len(rows) == len(wanted) and len({x['Reference'] for x in rows}) == len(rows)
    save(run / 'selected-source-rows.json', {'at': core.now(), 'snapshot_sha256': SNAPSHOT_SHA,
        'snapshot_path': str(path.relative_to(ROOT)), 'source_snapshot_date': '2026-09-10',
        'museum_codes': codes, 'rows': rows})
    print('Pinned selected Joconde rows:', len(rows), flush=True)


def image_targets(batch):
    s = importlib.util.spec_from_file_location('france_commons', ROOT / 'ops/overnight-commons-images.py')
    common = importlib.util.module_from_spec(s)
    s.loader.exec_module(common)
    rows = common.prepare_targets(RUN / batch, core.cloud_dsn())
    print('Matched image candidates across local and production:', len(rows), flush=True)


def facts(row):
    """Preserve doubtful date/type semantics rather than manufacture certainty."""
    creator = row['Auteur'].strip()
    assert creator and not re.search(r'anonyme|inconnu|attribu|atelier|école de|entourage|d.après', creator, re.I), 'Creator attribution held; source retained'
    title = row['Titre'].strip()
    assert title, 'Missing source title'
    assert not row['MANQUANT'], 'Source says missing: museum context requires review'
    raw = row['Millesime_de_creation'].strip()
    assert re.fullmatch(r'\d{3,4}(?:\s*;\s*\d{3,4})*', raw), 'Creation date qualifiers require individual review'
    years = [int(x.strip()) for x in raw.split(';')]
    assert 100 <= min(years) <= max(years) <= 1970
    precision = 'exact' if len(set(years)) == 1 else 'unknown'
    first = last = years[0] if precision == 'exact' else None
    notes = []
    period = row['Periode_de_creation']
    centuries = [int(v) for v in re.findall(r'(\d{1,2})e\s+siècle', period)]
    if centuries and any(not (c-1)*100 < y <= c*100 for c in centuries for y in years):
        first = last = None
        precision = 'unknown'
        notes.append('Source millesime and century conflict; no eligible numeric date asserted')
    life = re.search(r'\((\d{4})-(\d{4})\)', creator)
    if life and not int(life[1]) <= min(years) <= max(years) <= int(life[2]):
        first = last = None
        precision = 'unknown'
        notes.append('Creation date contradicts supplied creator lifespan; retained for review')
    kind = 'painting'
    if re.search(r'collage|relief|assemblage|néon|neon|découp|papier découp|sculpture', row['Denomination']+' '+row['Materiaux_techniques'], re.I):
        kind = 'unknown'
        notes.append('Mixed-media or dimensional work; painting-domain label is not a sufficient type assertion')
    return {'title': title, 'creator_label': creator, 'date_display': raw if precision != 'unknown' else 'Source date (review): '+raw+'; '+period,
        'first': first, 'last': last, 'precision': precision, 'work_type': kind,
        'medium': row['Materiaux_techniques'] or None, 'dimensions': row['Mesures'] or None,
        'accession': row['Numero_inventaire'].strip() or None, 'review_notes': notes}


def metadata_plan(batch):
    run = RUN / batch
    path = run / 'selected-source-rows.json'
    source = load(path)
    assert source['snapshot_sha256'] == SNAPSHOT_SHA
    refs = [r['Reference'] for r in source['rows']]
    urls = [prefix + ref for ref in refs for prefix in ('https://pop.culture.gouv.fr/notice/joconde/', 'https://www.pop.culture.gouv.fr/notice/joconde/', 'http://www.culture.gouv.fr/public/mistral/joconde_fr?ACTION=CHERCHER&FIELD_1=REF&VALUE_1=')]
    local_inst = load(RESEARCH / 'local-institutions.json')
    mapped = [i for i in local_inst if set(i['museofile_codes']) & set(source['museum_codes'])]
    result = {'at': core.now(), 'input_sha256': core.sha(path.read_bytes()), 'targets': {}}
    for target in ('local', 'cloud'):
        with connect(target) as db:
            inst = db.execute('SELECT id::text,slug,name,status,website_url,wikidata_id FROM institutions WHERE slug=ANY(%s)', ([i['slug'] for i in mapped],)).fetchall()
            bycode = {code: [i for i in inst if any(i['slug']==m['slug'] and code in m['museofile_codes'] for m in mapped)] for code in source['museum_codes']}
            ids = [i['id'] for i in inst]
            existing = db.execute('''WITH chosen AS MATERIALIZED (
               SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
               UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND superseded_by IS NULL
               UNION SELECT entity_id FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)
               UNION SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)
               UNION SELECT id FROM artworks WHERE title=ANY(%s) OR normalized_title=ANY(%s)
             ) SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.current_institution_id::text,a.status,a.revision,
               a.creation_year_start,a.creation_year_end,a.primary_media_id::text,
               ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id) urls,
               ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme LIKE '%%joconde%%') refs,
               ARRAY(SELECT l.institution_id::text FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.superseded_by IS NULL) institution_ids
               FROM chosen s JOIN artworks a ON a.id=s.id''', (ids, ids, urls, urls, [r['Titre'] for r in source['rows']], [norm(r['Titre']) for r in source['rows']])).fetchall()
            # Source-identifier lookup catches records without a canonical URL.
            schemes = [r['scheme'] for r in db.execute("SELECT DISTINCT scheme FROM external_identifiers WHERE scheme LIKE '%joconde%'").fetchall()]
            source_ids = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme=ANY(%s) AND external_id=ANY(%s)", (schemes, refs)).fetchall()
            artists = db.execute('''SELECT a.id::text,a.display_name,a.birth_year,a.death_year,a.status,
              ARRAY(SELECT alias FROM artist_aliases x WHERE x.artist_id=a.id) aliases FROM artists a WHERE a.status<>'archived' ''').fetchall()
            approved, held, present = [], [], []
            for row in source['rows']:
                ref = row['Reference']; code = row['Code_Museofile']
                exact = {x['entity_id'] for x in source_ids if x['external_id']==ref}
                exact.update(w['id'] for w in existing if ref in w['refs'] or any(u.rstrip('/').endswith('/joconde/'+ref) for u in w['urls']))
                if exact:
                    present.append({'ref': ref, 'artwork_ids': sorted(exact), 'reason': 'Exact source identity already exists; existing metadata preserved'})
                    continue
                try:
                    f = facts(row)
                    peers = bycode[code]
                    assert peers and all(i['status']!='archived' for i in peers), 'Museum identity not established'
                    canonical = next((i for i in peers if i['slug']=='joconde-'+code.lower()), None) or (peers[0] if len(peers)==1 else None)
                    assert canonical, 'Multiple museum identities without canonical code'
                    related = {i['id'] for i in peers}
                    leads = [w for w in existing if (
                        (related & (set(w['institution_ids']) | {w['current_institution_id']})) and
                        (acckeys(f['accession']) & acckeys(w['accession_number']) or norm(f['title']) in {norm(w['title']),norm(w['alternate_title'] or '')})
                    ) or norm(f['title'])==norm(w['title'])]
                    assert not leads, 'Possible existing accession/title: '+','.join(w['id'] for w in leads[:8])
                    # No automatic person creation or nationality/lifespan inference.
                    # Require exact name-token identity AND two matching source life dates.
                    life = re.search(r'\((\d{4})-(\d{4})\)', f['creator_label'])
                    creator_key = tokenkey(re.sub(r'\([^)]*\)', '', f['creator_label']))
                    matches = [a for a in artists if life and (a['birth_year'],a['death_year'])==(int(life[1]),int(life[2])) and creator_key in {tokenkey(n) for n in [a['display_name']]+a['aliases']}]
                    artist = matches[0] if len(matches)==1 else None
                    approved.append({'ref': ref, 'artwork_id': uid('joconde/'+ref), 'slug': 'france-joconde-'+ref.lower(),
                        'institution': canonical, 'artist': artist, 'facts': f, 'source_row_sha256': core.sha(core.encode(row))})
                except AssertionError as error:
                    held.append({'ref': ref, 'title': row['Titre'], 'reason': str(error)})
            # Do not import two selected source notices sharing an inventory/title
            # without a human decision about studies, components, and versions.
            original = approved[:]
            for item in original:
                peers = [x for x in original if x['ref']!=item['ref'] and x['institution']['id']==item['institution']['id'] and (acckeys(x['facts']['accession']) & acckeys(item['facts']['accession']))]
                if peers:
                    held.append({'ref': item['ref'], 'title': item['facts']['title'], 'reason': 'Selected notices share accession; component identity needs review'})
                    approved.remove(item)
            save(BACKUP / batch / (target+'-scoped-preimages.json'), {'at':core.now(),'institutions':inst,'artworks':existing})
            result['targets'][target] = {'ready': approved, 'held': held, 'existing': present}
            print(target, 'new review records', len(approved), 'held', len(held), 'existing', len(present), flush=True)
    save(run / 'plan.json', result)
    save(run / 'plan-manifest.json', {'sha256': core.sha((run/'plan.json').read_bytes())})


def apply_metadata(batch, target):
    run = RUN / batch
    backup = load(RUN / 'backups.json')
    assert backup['cloud']['status']=='SUCCESSFUL' and backup['local']['archive_directory_validated']
    assert Path(backup['local']['path']).stat().st_size == backup['local']['bytes']
    plan_raw = (run/'plan.json').read_bytes()
    assert core.sha(plan_raw) == load(run/'plan-manifest.json')['sha256']
    plan = json.loads(plan_raw)
    assert core.sha((run/'selected-source-rows.json').read_bytes()) == plan['input_sha256']
    review = load(run/'review.json')
    assert review['plan_sha256'] == core.sha(plan_raw) and review['approved'] is True
    ready = {r['ref']:r for r in plan['targets'][target]['ready']}
    assert set(review['source_references']) <= set(ready)
    raw_rows = {r['Reference']:r for r in load(run/'selected-source-rows.json')['rows']}
    sid = uid('source/'+SOURCE)
    stats = collections.Counter()
    with connect(target, False) as db:
        for ref in review['source_references']:
            item = ready[ref]; row = raw_rows[ref]; f = item['facts']; aid = item['artwork_id']
            assert core.sha(core.encode(row)) == item['source_row_sha256']
            assert facts(row) == f, 'Source parsing changed; re-review plan'
            source_url = 'https://pop.culture.gouv.fr/notice/joconde/'+ref
            scheme = 'european-joconde-'+row['Code_Museofile'].lower()+'-object'
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='5s'")
                db.execute('SELECT pg_advisory_xact_lock(559320260916)')
                db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'France — selected Joconde source records, review only','authority_data','https://pop.culture.gouv.fr/','https://www.etalab.gouv.fr/licence-ouverte-open-licence/') ON CONFLICT(slug) DO NOTHING", (sid,SOURCE))
                assert str(db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']) == sid
                old = db.execute('SELECT id::text,status,research_candidate FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone()
                if old:
                    citation = db.execute("SELECT evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='france_selected_joconde_source'",(aid,sid)).fetchone()
                    assert citation and json.loads(citation['evidence_note'])['source_row_sha256']==item['source_row_sha256'], 'Unexpected existing artwork; no overwrite'
                    assert old['status']=='review' and old['research_candidate']
                    stats['already_applied'] += 1
                    continue
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE scheme=%s AND external_id=%s",(scheme,ref)).fetchone(), 'Concurrent source identity'
                assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",([source_url,source_url.replace('https://pop.','https://www.pop.')],)).fetchone(), 'Concurrent source citation'
                inst = db.execute('SELECT id::text,slug,status FROM institutions WHERE id=%s FOR SHARE',(item['institution']['id'],)).fetchone()
                assert inst and inst['slug']==item['institution']['slug'] and inst['status']!='archived'
                assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(inst['id'],f['accession'])).fetchone(), 'Concurrent accession'
                db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,description_md,status,research_candidate,created_by,updated_by)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)''',
                  (aid,item['slug'],f['title'],norm(f['title']),f['date_display'],f['first'],f['last'],f['precision'],f['work_type'],f['medium'],f['dimensions'],f['accession'],
                   'Joconde source creator label: '+f['creator_label']+'. Source metadata retained for review; museum association is not an accepted current holding or on-view claim.',core.ACTOR,core.ACTOR))
                if item['artist']:
                    artist = item['artist']
                    current = db.execute('SELECT display_name,birth_year,death_year,status FROM artists WHERE id=%s FOR SHARE',(artist['id'],)).fetchone()
                    assert current and all(current[k]==artist[k] for k in ('display_name','birth_year','death_year','status')), 'Artist changed since exact name/lifespan review'
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(aid,artist['id'],'Unqualified Joconde creator: exact name tokens and both supplied life dates match existing authority. Source label: '+f['creator_label']))
                evidence = {'snapshot_sha256':SNAPSHOT_SHA,'source_snapshot_date':'2026-09-10','source_row_sha256':item['source_row_sha256'],
                    'raw_source_record':row,'interpreted_facts':f,'plan_sha256':core.sha(plan_raw),
                    'policy':'Review-only metadata. No image permission, current display, accepted museum holding, masterpiece designation, nationality or invented creator biography.'}
                db.execute('''INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                  VALUES('artwork',%s,'france_selected_joconde_source',%s,%s,%s,%s,'2026-09-10'::timestamptz,%s)''',
                  (aid,sid,ref,source_url,json.dumps(evidence,ensure_ascii=False),core.ACTOR))
                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,'2026-09-10'::timestamptz)",(aid,scheme,ref,source_url,sid))
                db.execute('''INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                  VALUES(%s,'holding',%s,'unknown',%s,%s,%s,'2026-09-10'::timestamptz,'review')''',
                  (aid,inst['id'],sid,source_url,'Documented source museum association, not accepted holding or current display. Legal status: '+row['Statut_juridique']+'. Deposit: '+row['Lieu_de_depot']))
                check = db.execute('SELECT status,research_candidate,published_at,current_institution_id,primary_media_id FROM artworks WHERE id=%s',(aid,)).fetchone()
                assert check['status']=='review' and check['research_candidate'] and all(check[k] is None for k in ('published_at','current_institution_id','primary_media_id'))
            receipt = {'at':core.now(),'target':target,'source_reference':ref,'artwork_id':aid,'status':'review','creator_linked':bool(item['artist']),'holding_state':'review','image_added':False,'plan_sha256':core.sha(plan_raw)}
            save(run/'applied'/target/(ref+'.json'),receipt)
            stats['created_review_artworks'] += 1
            print(target,ref,'created review',flush=True)
    print(target,dict(stats),flush=True)
    save(run/(target+'-result.json'),{'at':core.now(),'counts':dict(stats)})


def verify_campaign():
    review=load(RUN/'metadata-001/review.json')
    plan=load(RUN/'metadata-001/plan.json')
    images=load(RUN/'images-pilot001/go-selection.json')
    out={'at':core.now(),'targets':{},'campaign_new_artworks':len(review['source_references']),'campaign_images':len(images),
        'limits':'No publication or UI visibility claim. Holdings remain review; no on-view assertions. No exhaustive collection import.'}
    for target in ('local','cloud'):
        ids=[x['artwork_id'] for x in plan['targets'][target]['ready'] if x['ref'] in review['source_references']]
        image_ids=[x['targets'][target]['id'] for x in images]
        with connect(target) as db:
            new=db.execute('''SELECT a.id::text,a.slug,a.title,a.status,a.research_candidate,a.published_at,a.current_institution_id::text,a.work_type,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='holding' AND l.review_state='review') review_holdings,
              (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND (l.claim_type='display' OR l.review_state='accepted')) accepted_or_display_claims
              FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(ids,)).fetchall()
            assert len(new)==8 and all(r['status']=='review' and r['research_candidate'] and r['published_at'] is None and r['current_institution_id'] is None and r['review_holdings']==1 and r['accepted_or_display_claims']==0 for r in new)
            media=db.execute('''SELECT a.id::text,a.title,a.status,a.research_candidate,ma.storage_path,ma.checksum_sha256,ma.byte_size,ma.rights_status,ma.license_url,ma.creator_credit,
              (SELECT count(*) FROM media_rights_evidence e WHERE e.media_id=ma.id) rights_evidence
              FROM artworks a JOIN media_assets ma ON ma.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id''',(image_ids,)).fetchall()
            assert len(media)==2 and all(r['status']=='review' and r['research_candidate'] and r['byte_size']<=100000 and r['rights_evidence']==1 and r['creator_credit'] for r in media)
            totals=db.execute("SELECT (SELECT count(*) FROM artworks WHERE status<>'archived') active_artworks,(SELECT count(*) FROM artists WHERE status<>'archived') active_artists,(SELECT count(*) FROM artworks WHERE status<>'archived' AND primary_media_id IS NOT NULL) artworks_with_media").fetchone()
            out['targets'][target]={'new_records':new,'images':media,'live_totals_including_unrelated_work':totals}
            print(target,totals,'verified new review works',len(new),'verified image attachments',len(media),flush=True)
    assert {x['checksum_sha256'] for x in out['targets']['local']['images']}=={x['checksum_sha256'] for x in out['targets']['cloud']['images']}
    save(RUN/'verification-final.json',out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['backups', 'select', 'image-plan', 'image-targets', 'plan', 'apply', 'verify'])
    parser.add_argument('--batch', default='metadata-001')
    parser.add_argument('--codes', default=','.join(PRIORITY))
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--target', choices=['local','cloud'])
    args = parser.parse_args()
    assert re.fullmatch(r'[a-z0-9-]+', args.batch)
    if args.phase == 'backups':
        backups()
    elif args.phase == 'select':
        select(args.batch, args.codes.split(','))
    elif args.phase == 'image-plan':
        image_plan(args.batch, args.limit)
    elif args.phase == 'image-targets':
        image_targets(args.batch)
    elif args.phase == 'plan':
        metadata_plan(args.batch)
    elif args.phase == 'verify':
        verify_campaign()
    else:
        assert args.target, '--target required'
        apply_metadata(args.batch,args.target)


if __name__ == '__main__':
    main()
