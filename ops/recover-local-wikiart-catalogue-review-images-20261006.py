#!/usr/bin/env python3
"""Individual local image review preserving unknown dates and creator records."""
import argparse
import collections
import gzip
import importlib.util
import json
from pathlib import Path
from psycopg.types.json import Jsonb

s = importlib.util.spec_from_file_location('reuse', Path(__file__).with_name('recover-local-wikiart-reused-images-20261006.py'))
reuse = importlib.util.module_from_spec(s)
s.loader.exec_module(reuse)
wiki, base, core = reuse.wiki, reuse.base, reuse.core
RUN = core.ROOT / 'docs/research/local-wikiart-catalogue-review-images-20261006'
reuse.RUN = wiki.RUN = base.RUN = wiki.chicago.RUN = RUN
core.VERSION = 'local-wikiart-individual-catalogue-review-v1'
original_facts = reuse.page_facts
BASIS = 'Existing local artwork Wikidata identity and unchanged primary creator authority, current WikiArt object/image evidence and individual visual/version/scope review. Source creation dates retained separately; unknown catalogue dates and review status preserved. Actual source rights assertions and user approval recorded separately; no independent copyright-holder permission asserted.'


def snapshot():
    if (RUN / 'candidates.json').exists(): return
    audit = json.loads((reuse.AUDIT / 'discovery.json').read_bytes())
    leads = {x['artwork_id']: x for x in audit['leads'] if x['category'] != 'matching_local_identity' or x['current_local_state']['creation_scope'] != 'eligible'}
    if len(leads) != 10: raise ValueError('Expected bounded ten-record follow-up differs')
    packets = {}
    for pin in audit['source_pins']:
        data = (reuse.AUDIT / pin['path']).read_bytes()
        if core.sha(data) != pin['sha256']: raise ValueError('Prior research capture changed')
        plan = json.loads(gzip.decompress(data))
        correction = json.loads((reuse.AUDIT / 'prior-plan-captures' / pin['operation'] / 'impression-correction.json').read_bytes())
        for claim in plan['claims']:
            aid = claim['work']['id']
            if aid not in leads: continue
            if core.sha(core.encode(claim)) != leads[aid]['prior_claim_sha256']: raise ValueError('Prior individual claim changed')
            captures = {}
            reuse.capture_receipts(claim, captures)
            reuse.capture_receipts(plan['prepared'][aid], captures)
            packet = dict(claim=claim, prepared=plan['prepared'][aid], prior_preimage=plan['preimages'][aid], prior_plan_pin=pin,
                captures=list(captures.values()), retractions=[x for x in correction['retracted'] if x['artwork_id'] == aid])
            core.save_new(RUN / 'prior-research' / (aid + '.json'), packet)
            packets[aid] = packet
    with base.connect() as db:
        rows = db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,
          a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
          to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,i.wikidata_id institution_qid,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) catalogue_scope,
          ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
          (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
          (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers,
          COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
          FROM artworks a JOIN institutions i ON i.id=a.current_institution_id
          WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review'
            AND artline_has_selection_evidence(a.id) ORDER BY a.id''', (list(packets),)).fetchall()
        if len(rows) != 10: raise ValueError('Selected current local gaps differ')
        artists = sorted({c['creator_links'][0]['artist_id'] for c in rows})
        records = {x['record']['id']: x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])', (artists,))}
        aliases, identifiers = collections.defaultdict(list), collections.defaultdict(list)
        for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY id', (artists,)):
            aliases[x['record']['artist_id']].append(x['record'])
        for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id", (artists,)):
            identifiers[x['record']['entity_id']].append(x['record'])
        baseline = db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
    for c in rows:
        packet = packets[c['artwork_id']]
        old = packet['claim']['work']
        if any(c[k] != old[k] for k in ('title','creation_year_start','creation_year_end','date_precision','accession_number','institution_id')):
            raise ValueError('Local object metadata differs from audited prior claim')
        qids = [x for x in c['identifiers'] if x['scheme'] == 'wikidata']
        if len(qids) != 1 or c['roles'] != ['primary'] or len(c['creator_links']) != 1:
            raise ValueError('Unique existing artwork/creator authority absent')
        identity = qids[0]
        artist_id = c['creator_links'][0]['artist_id']
        c.update(scheme=identity['scheme'], external_id=identity['external_id'], source_id=identity['source_id'],
            page=packet['claim']['page']['url'], provider=wiki.PROVIDER, artist=records[artist_id]['display_name'], target_ids={'local':c['artwork_id']},
            creator_authorities=[dict(artist_record=records[artist_id],artist_aliases=aliases[artist_id],artist_identifiers=identifiers[artist_id])],
            prior_research_sha256=core.sha(core.encode(packet)), prior_creator_links_differ=not leads[c['artwork_id']]['same_creator_links'])
    core.save_new(RUN / 'candidates.json', dict(at=core.now(),baseline=baseline,candidates=rows,
        selection='Ten existing local WikiArt research leads requiring individual unknown-date or creator-record review. No automatic eligibility or source matching; existing metadata and publication holds remain intact.'))
    docs = []
    for source in ('AGENTS.md','docs/ARTLINE_IMAGE_USE.md'):
        data = (core.ROOT / source).read_bytes(); capture = 'metadata/authorization/' + Path(source).name
        core.save_new(RUN / capture, data); docs.append(dict(source_path=source,capture=capture,sha256=core.sha(data)))
    core.save_new(RUN / 'source-authorization.json',dict(at=core.now(),source='WikiArt',target='local',record_actual_rights_separately=True,
        documents=docs,user_instruction='see new md file - wiki art is fully approved',scope='Individual image-only review; preserve unknown dates, existing creator records, holdings and review/publication status.'))
    print('Snapshotted ten current local gaps',flush=True)


def artwork_authority(c):
    url = 'https://www.wikidata.org/wiki/Special:EntityData/' + c['external_id'] + '.json'
    p = RUN / 'metadata/artwork-authorities' / (core.sha(url.encode()) + '.json')
    data = p.read_bytes(); rc = json.loads(p.with_suffix('.receipt.json').read_bytes())
    if rc['url'] != url or core.sha(data) != rc['sha256'] or len(data) != rc['bytes']: raise ValueError('Current artwork authority capture changed')
    entity = json.loads(data)['entities'][c['external_id']]
    if entity['id'] != c['external_id']: raise ValueError('Wrong artwork authority')
    qids = {x['external_id'] for x in c['creator_authorities'][0]['artist_identifiers'] if x['scheme'] == 'wikidata'}
    if len(qids) != 1 or {x['id'] for x in base.m.values(entity,'P170')} != qids:
        raise ValueError('Current artwork authority does not identify the existing local creator')
    claims = [x for x in entity.get('claims',{}).get('P170',[]) if x.get('rank') != 'deprecated']
    if any(set(x.get('qualifiers',{})) - {'P7452'} for x in claims): raise ValueError('Qualified creator authority requires separate attribution review')
    names = {wiki.norm(x['value']) for x in entity.get('labels',{}).values()}
    names.update(wiki.norm(x['value']) for rows in entity.get('aliases',{}).values() for x in rows)
    if wiki.norm(c['title']) not in names: raise ValueError('Existing title does not identify the exact artwork authority')
    institution_crosswalk = None
    if c['institution_qid'] not in {x['id'] for x in base.m.values(entity,'P195')}:
        if c['artwork_id'] != '53649ace-517d-5b25-bda4-164208228772' or c['institution_qid'] is not None:
            raise ValueError('Current artwork holding authority differs')
        institution_crosswalk = json.loads((RUN/'institution-identity-review.json').read_bytes())
        institution = institution_crosswalk['local_record']
        if (institution['id'],institution['name'],institution['slug'],institution['wikidata_id']) != (c['institution_id'],c['museum'],c['institution_slug'],None):
            raise ValueError('Individually reviewed existing Cardiff identity differs')
        url = 'https://www.wikidata.org/wiki/Special:EntityData/Q1321874.json'
        p = RUN/'metadata/artwork-authorities'/(core.sha(url.encode())+'.json')
        raw = p.read_bytes(); capture = json.loads(p.with_suffix('.receipt.json').read_bytes())
        if capture != institution_crosswalk['capture'] or capture['url'] != url or core.sha(raw) != capture['sha256']:
            raise ValueError('Pinned Cardiff authority changed')
        museum = json.loads(raw)['entities']['Q1321874']
        labels = {wiki.norm(x['value']) for x in museum['labels'].values()}
        if wiki.norm(institution['name']) not in labels or institution['website_url'] not in base.m.values(museum,'P856') or 'Q1321874' not in {x['id'] for x in base.m.values(entity,'P195')}:
            raise ValueError('Existing museum name and official website do not establish this Cardiff holding identity')
    inventories = base.m.values(entity,'P217')
    if inventories and c['accession_number'] not in inventories: raise ValueError('Existing inventory conflicts with artwork authority')
    result = dict(entity=entity,receipt=rc,existing_creator_qid=next(iter(qids)),authority_inventory_present=bool(inventories))
    if institution_crosswalk: result['institution_crosswalk'] = institution_crosswalk
    return result


def page_facts(c,data,rc):
    authority = artwork_authority(c)
    facts = original_facts(c,data,rc)
    facts['local_artwork_authority'] = authority
    if c['catalogue_scope'] == 'review':
        if c['date_precision'] != 'unknown' or c['creation_year_start'] is not None or c['creation_year_end'] is not None:
            raise ValueError('This individually reviewed scope only covers fully unknown catalogue dates')
        facts['date_note'] += ' Catalogue dates remain unknown and PostgreSQL creation scope remains review. The separately recorded WikiArt date is evidence for individual image-only scope review, not a catalogue date replacement or publication approval.'
    elif c['catalogue_scope'] != 'eligible': raise ValueError('Unexpected catalogue date scope')
    if c['prior_creator_links_differ']:
        facts['date_note'] += ' The prior research uses a different painter UUID. This operation independently verifies the existing local primary creator through the current artwork Wikidata creator claim and its WikiArt profile; no creator record or link is changed.'
    return facts


wiki.page_facts = page_facts


def scope_review(im):
    reuse.verify_version(im,require_approved=True)
    if im['artwork_id'] == 'c6f6265e-ee56-5c73-89a4-b4f8051292af' and (im.get('view_label') != 'Three interior panels' or not im['raw'].get('view_scope_review')):
        raise ValueError('Reviewed triptych must retain its explicit interior-panel view')
    review = im['raw']['object_version_review']
    expected = dict(decision='approved_image_only',catalogue_scope_retained=im['catalogue_scope'],
        unknown_catalogue_dates_preserved=im['catalogue_scope']=='review',publication_status_retained='review',
        source_year_start=im['raw']['wikiart_facts']['source_year_start'],source_year_end=im['raw']['wikiart_facts']['source_year_end'])
    if review.get('scope_review') != expected or not 1 <= expected['source_year_start'] <= expected['source_year_end'] < 1970:
        raise ValueError('Individual source-date and preserved catalogue-scope approval absent')


def attach(db,im,target):
    if target != 'local': raise ValueError('Only local attachment authorized')
    wiki.verify_image(im); wiki.chicago.verify_view(im); reuse.verify_original(im); scope_review(im)
    wiki.chicago.authority_unchanged(db,im,True)
    institution = im['raw']['wikiart_facts']['local_artwork_authority'].get('institution_crosswalk')
    if institution and db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE id=%s FOR SHARE',(im['institution_id'],)).fetchone()['record'] != institution['local_record']:
        raise ValueError('Individually reviewed Cardiff institution changed')
    if im['catalogue_scope'] == 'eligible':
        result = reuse.original_attach(db,im,target)
        if result == 'attached': db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(BASIS,im['media_id']))
        return result
    row = db.execute('''SELECT to_jsonb(a) record,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,
        artline_has_selection_evidence(a.id) selected FROM artworks a WHERE a.id=%s FOR UPDATE''',(im['artwork_id'],)).fetchone()
    if row['record'] != im['before_record'] or row['scope'] != 'review' or not row['selected'] or row['record']['status'] != 'review':
        raise ValueError('Individually reviewed local state changed')
    verified = im['rights_status'] == 'public_domain'
    db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,
        alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
        VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (im['media_id'],im['path'],im['page'],core.PROVIDERS[wiki.PROVIDER],im['width'],im['height'],im['bytes'],im['sha256'],
         im.get('alt_text',im['artist']+' — '+im['title']),im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],
         im['attribution_text'],im['downloaded_at'],im['checked_at'] if verified else None,core.ACTOR if verified else None))
    db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,
        adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (im['media_id'],im['source_id'],im['external_id'],core.sha(core.encode(im['raw'])),im['source_image_url'],im['policy_url'],BASIS,core.VERSION,
         im['checked_at'],Jsonb({k:v for k,v in im.items() if k not in ('artist','title')})))
    db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',
        (im['artwork_id'],im['media_id'],im.get('view_label','Full composition')))
    db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',
        (im['media_id'],core.ACTOR,im['artwork_id']))
    return 'attached'


base.m.attach = attach


def verify():
    approved = {x['artwork_id'] for x in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts'] if x['result']=='attached'}
    for im in base.prepared():
        reuse.verify_original(im); reuse.verify_version(im)
        if im['artwork_id'] in approved: scope_review(im)
    wiki.verify()
    checks = []
    with base.connect() as db:
        for im in base.prepared():
            if im['artwork_id'] not in approved: continue
            institution = im['raw']['wikiart_facts']['local_artwork_authority'].get('institution_crosswalk')
            if institution and db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE id=%s',(im['institution_id'],)).fetchone()['record'] != institution['local_record']:
                raise ValueError('Existing Cardiff institution fields changed')
            row = db.execute('''SELECT a.status,a.date_precision,a.creation_year_start,a.creation_year_end,
              artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,e.rights_basis,e.source_record_id
              FROM artworks a JOIN media_rights_evidence e ON e.media_id=a.primary_media_id WHERE a.id=%s''',(im['artwork_id'],)).fetchone()
            if row['rights_basis'] != BASIS or row['source_record_id'] != im['external_id'] or row['scope'] != im['catalogue_scope'] or row['status'] != 'review':
                raise ValueError('Stored authority, date scope or review status differs')
            for k in ('date_precision','creation_year_start','creation_year_end'):
                if row[k] != im[k]: raise ValueError('Catalogue date was modified')
            checks.append(dict(artwork_id=im['artwork_id'],catalogue_scope=row['scope'],unknown_dates_preserved=row['date_precision']=='unknown'))
    core.save_new(RUN/'catalogue-review-database-verification.json',dict(at=core.now(),passed=True,checks=checks,
        unknown_dates_and_review_scopes_preserved=True,existing_creator_links_and_identifiers_preserved=True))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['snapshot','research','prepare','apply','verify']);a=p.parse_args()
    if a.phase=='snapshot': snapshot()
    elif a.phase=='research': wiki.research(10)
    elif a.phase=='prepare': reuse.prepare()
    elif a.phase=='apply': base.apply()
    else: verify()
