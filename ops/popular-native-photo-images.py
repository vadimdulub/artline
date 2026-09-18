#!/usr/bin/env python3
"""Find photographs for selected native museum records without adding authority IDs.

Discovery reads a scoped catalogue snapshot. Accession, creator, current holding
and dates must agree independently before exact Commons photo/rights checks.
Preparation never writes a database. The existing reviewed-image writers deliver.
"""
import argparse
import collections
import datetime
import fcntl
import importlib.util
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs

import psycopg
from psycopg.rows import dict_row

spec = importlib.util.spec_from_file_location('photo', Path(__file__).with_name('research-popular-painting-photos.py'))
photo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(photo)
common = photo.m
core = common.core
PROVIDER = 'popular-native-photo'
core.PROVIDERS[PROVIDER] = 'Museum inventory / independently licensed Wikimedia Commons photograph'
core.VERSION = 'popular-native-photo-v1'
MUSEUMS = {'state-russian-museum': 'Q211043', 'pushkin-state-museum-fine-arts': 'Q4872',
           'tate': 'Q430682', 'national-gallery-london': 'Q180788', 'musee-marmottan-monet': 'Q1327886'}
SOURCE_HOSTS = {'state-russian-museum': {'rusmuseumvrm.ru'},
                'pushkin-state-museum-fine-arts': {'pushkinmuseum.art', 'collection.pushkinmuseum.art'},
                'tate': {'tate.org.uk'}, 'national-gallery-london': {'nationalgallery.org.uk'},
                'musee-marmottan-monet': {'marmottan.fr'}}


def host(url):
    return (urlsplit(url or '').hostname or '').removeprefix('www.')


def verify_inventory(c, entity, institution):
    common.entity_match(c, entity, require_primary_image=False)
    if common.ids(entity, 'P195') != {c['institution_qid']}:
        raise ValueError('Multiple holding claims need review')
    if not c.get('accession_number') or common.norm(c['accession_number']) not in {
            common.norm(v) for v in common.values(entity, 'P217') if isinstance(v, str)}:
        raise ValueError('Exact museum inventory absent or different')
    if institution.get('id') != c['institution_qid'] or host(c['website_url']) not in {
            host(u) for u in common.values(institution, 'P856') if isinstance(u, str)}:
        raise ValueError('Institution authority does not corroborate official website')
    years = [int(match[1]) for date in common.values(entity, 'P571')
             if isinstance(date, dict) and date.get('precision', 0) >= 9
             and (match := re.match(r'^\+(\d+)-', date.get('time', '')))]
    if not years or any(not c['creation_year_start'] <= y <= c['creation_year_end'] for y in years):
        raise ValueError('Exact creation interval needs independent review')
    if host(c['source_record_url']) not in SOURCE_HOSTS[c['institution_slug']]:
        raise ValueError('Unapproved native collection identifier')


def verify(im):
    raw = im['raw']
    verify_inventory(im, raw['wikidata'], raw['institution'])
    photo.exact_photo(im, raw['commons'], raw['structured_data'])
    photo.verify_original_photograph(im, raw['commons'])
    common.rights_and_identity(im, raw['wikidata'], raw['commons'], raw['structured_data'],
                              im.get('rendered_licence_evidence'))


def attach(db, im, target):
    verify(im)
    with db.transaction():
        rows = db.execute("""SELECT a.id::text,a.slug,a.title,a.accession_number,a.creation_year_start,
          a.creation_year_end,a.work_type,a.status,a.published_at,i.slug institution_slug FROM external_identifiers e
          JOIN artworks a ON a.id=e.entity_id JOIN institutions i ON i.id=a.current_institution_id
          WHERE e.entity_type='artwork' AND e.scheme=%s AND e.external_id=%s FOR UPDATE OF a""",
          (im['scheme'], im['external_id'])).fetchall()
        keys = ('slug','title','accession_number','creation_year_start','creation_year_end','work_type','institution_slug')
        if len(rows) != 1 or rows[0]['id'] != im['target_ids'][target] or any(rows[0][k] != im[k] for k in keys):
            raise ValueError('Native target catalogue identity changed')
        if rows[0]['status'] != 'review' or rows[0]['published_at'] is not None:
            raise ValueError('Native target editorial state changed')
        creators = db.execute("""SELECT e.external_id qid,aa.attribution_role role FROM artwork_artists aa
          LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata'
          WHERE aa.artwork_id=%s""", (rows[0]['id'],)).fetchall()
        if creators != [{'qid': im['creators'][0]['qid'], 'role': 'primary'}]:
            raise ValueError('Target creator changed')
        owners = db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=%s", (im['qid'],)).fetchall()
        if any(r['entity_id'] != rows[0]['id'] for r in owners):
            raise ValueError('Another physical record owns this authority; review duplicate')
        result = common.original_attach(db, im, target)
        if result == 'attached':
            db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s WHERE id=%s',
                       (im['creator_credit'], im['attribution_text'], im['media_id']))
        return result


core.attach = attach


def discover(args):
    rows = json.loads(args.gaps.read_text())['records']
    groups = collections.defaultdict(list)
    for c in rows:
        if c['institution_slug'] not in MUSEUMS or not c.get('accession_number') or c['roles'] != ['primary']:
            continue
        if len(c['creators'] or []) != 1 or not c['creators'][0].get('qid'):
            continue
        native = [e for e in c['identifiers'] or [] if e['scheme'] != 'wikidata' and host(e['url']) in SOURCE_HOSTS[c['institution_slug']]]
        if not native:
            continue
        e = native[0]
        c = dict(c, institution_qid=MUSEUMS[c['institution_slug']], scheme=e['scheme'], external_id=e['external_id'],
                 source_record_url=e['url'], native_identifiers=native, provider=PROVIDER, popular=True,
                 artist=c['creators'][0]['name'], target_ids={'local': c['artwork_id']})
        groups[(c['institution_qid'], c['creators'][0]['qid'])].append(c)
    fetch = core.Fetcher(args.run / 'metadata')
    museums = common.api(fetch, 'www.wikidata.org', {'action':'wbgetentities', 'ids':'|'.join(sorted({k[0] for k in groups})),
                         'props':'claims|labels', 'languages':'en|ru'})['entities']
    selected, held, searched = [], [], []
    order = sorted(groups.items(), key=lambda item: (item[1][0]['institution_slug'] != 'state-russian-museum', -len(item[1])))
    for (museum, artist), group in order[:args.groups]:
        if time.time() >= args.deadline:
            break
        checkpoint = args.run / 'groups' / (museum + '-' + artist + '.json')
        if checkpoint.exists():
            result = json.loads(checkpoint.read_text())
            selected.extend(result['selected']); held.extend(result['held']); searched.append(result['summary'])
            continue
        query = f'haswbstatement:P170={artist} haswbstatement:P195={museum}'
        qids, offset, total = [], 0, 0
        while offset < 500:
            d = common.api(fetch, 'www.wikidata.org', {'action':'query','list':'search','srsearch':query,
                           'srnamespace':0,'srlimit':50,'srprop':'','sroffset':offset})
            total = d.get('query', {}).get('searchinfo', {}).get('totalhits', 0)
            qids.extend(r['title'] for r in d.get('query', {}).get('search', []) if re.fullmatch(r'Q\d+', r['title']))
            if 'continue' not in d:
                break
            offset = d['continue']['sroffset']
        entities = {}
        for start in range(0, len(qids), 50):
            entities.update(common.api(fetch, 'www.wikidata.org', {'action':'wbgetentities','ids':'|'.join(qids[start:start+50]),
                            'props':'claims|labels|aliases','languages':'en|mul|ru|fr|de|nl|it'})['entities'])
        index = collections.defaultdict(list)
        for entity in entities.values():
            for inv in common.values(entity, 'P217'):
                if isinstance(inv, str):
                    index[common.norm(inv)].append(entity)
        found, failures = [], []
        for c in group:
            hits = {e['id']:e for e in index[common.norm(c['accession_number'])]}
            try:
                if len(hits) != 1:
                    raise ValueError('Exact inventory missing or ambiguous')
                entity = next(iter(hits.values()))
                c = dict(c, qid=entity['id'])
                verify_inventory(c, entity, museums[museum])
                c.update(discovery_entity=entity, institution_entity=museums[museum])
                found.append(c)
            except ValueError as exc:
                failures.append({'artwork_id':c['artwork_id'],'reason':str(exc)})
        summary = {'institution_qid':museum,'artist_qid':artist,'gaps':len(group),'entities':len(entities),
                   'truncated':total>len(entities),'exact_inventory_leads':len(found)}
        core.save_new(checkpoint, {'selected':found,'held':failures,'summary':summary})
        selected.extend(found); held.extend(failures); searched.append(summary)
        print(core.now(), 'Native inventory groups',len(searched),'leads',len(selected),flush=True)
    core.save_new(args.run/'discovery-report.json', {'at':core.now(),'groups':searched,'held':held,'leads':len(selected)})
    persist_selection(args, selected)


def persist_selection(args, selected):
    # Preserve every physical record; ambiguous cross-record matches stay held.
    counts = collections.Counter(c['qid'] for c in selected)
    chosen = [c for c in selected if counts[c['qid']] == 1][:args.limit]
    with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        owners = db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",([c['qid'] for c in chosen],)).fetchall()
        owned = {r['external_id']:r['entity_id'] for r in owners}
        chosen = [c for c in chosen if owned.get(c['qid'],c['artwork_id']) == c['artwork_id']]
        preimage = db.execute("""SELECT to_jsonb(a) artwork,
          (SELECT jsonb_agg(to_jsonb(aa)) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creators,
          (SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",([c['artwork_id'] for c in chosen],)).fetchall()
    backup = Path.home()/'Library/Application Support/Artline/backups'/args.run.name/'local-selected-before.json'
    core.save_new(backup, preimage)
    core.save_new(args.run/'backups.json', {'targets':{'local':{'path':str(backup),'rows':len(preimage),'sha256':core.sha(backup.read_bytes())}},
                                          'production':'pending authentication, identity revalidation and preimages'})
    core.save_new(args.run/'candidates.json', {'at':core.now(),'candidates':chosen})
    print('Selected local-only native photo candidates',len(chosen),flush=True)


def verified_cached_entities(folder, needed):
    """Intact recent public API responses only; image rights are fetched afresh."""
    found = {}
    for path in sorted((folder/'metadata').glob('*.receipt.json')):
        receipt = json.loads(path.read_text())
        url = urlsplit(receipt['url']); params = parse_qs(url.query)
        if (url.scheme,url.hostname,url.path) != ('https','www.wikidata.org','/w/api.php') or params.get('action') != ['wbgetentities']:
            continue
        requested = set(params.get('ids',[''])[0].split('|')) & needed
        if not requested:
            continue
        age = datetime.datetime.now(datetime.timezone.utc).timestamp()-datetime.datetime.fromisoformat(receipt['retrieved_at'].replace('Z','+00:00')).timestamp()
        if not 0 <= age <= 48*3600:
            continue
        original = path.with_name(path.name.replace('.receipt.json','.json'))
        content = original.read_bytes()
        if core.sha(content) != receipt['sha256'] or len(content) != receipt['bytes'] or original.stem != core.sha(receipt['url'].encode()):
            raise ValueError('Cached source checksum, size or URL key differs')
        for qid, entity in json.loads(content).get('entities',{}).items():
            if qid in requested and entity.get('id') == qid:
                found[qid] = (entity,receipt)
    return found


def cached_discover(args):
    gaps = {c['artwork_id']:c for c in json.loads(args.gaps.read_text())['records']}
    selected, held = [], []
    for folder in args.cached_leads:
        leads = [c for c in json.loads((folder/'native-match-leads.json').read_text())
                 if c['artwork_id'] in gaps and c['institution_slug'] in MUSEUMS]
        needed = {c['qid'] for c in leads} | {c['institution_qid'] for c in leads}
        cache = verified_cached_entities(folder,needed)
        for lead in leads:
            c = gaps[lead['artwork_id']]
            try:
                if c['roles'] != ['primary'] or len(c['creators'] or []) != 1:
                    raise ValueError('Current creator selection differs')
                entity, receipt = cache[lead['qid']]
                institution, institution_receipt = cache[lead['institution_qid']]
                native = [e for e in c['identifiers'] or [] if e['scheme'] != 'wikidata' and host(e['url']) in SOURCE_HOSTS[c['institution_slug']]]
                if not native:
                    raise ValueError('Current exact museum identifier absent')
                e = native[0]
                c = dict(c,qid=lead['qid'],institution_qid=lead['institution_qid'],native_identifiers=native,
                         scheme=e['scheme'],external_id=e['external_id'],source_record_url=e['url'],
                         provider=PROVIDER,popular=True,artist=c['creators'][0]['name'],target_ids={'local':c['artwork_id']})
                verify_inventory(c,entity,institution)
                c.update(discovery_entity=entity,institution_entity=institution,
                         cached_authority_receipts={'artwork':receipt,'institution':institution_receipt})
                selected.append(c)
            except (KeyError,ValueError) as exc:
                held.append({'artwork_id':c['artwork_id'],'reason':str(exc)})
    unique = {c['artwork_id']:c for c in selected}
    selected = sorted(unique.values(),key=lambda c:(c['artist']!='Claude Monet',c['artist'],c['title']))
    core.save_new(args.run/'cached-discovery-report.json',{'at':core.now(),'selected':len(selected),'held':held,
                    'policy':'Current local eligible gaps; intact public metadata captures under 48 hours old; fresh exact Commons identity and image licence checks required.'})
    persist_selection(args,selected)


def prepare(args):
    assert (args.run/'backups.json').exists()
    rows = json.loads((args.run/'candidates.json').read_text())['candidates']
    done = core.latest_events(args.run)
    fetch = core.Fetcher(args.run/'photo-metadata')
    for c in rows[:args.limit]:
        if time.time() >= args.deadline:
            break
        if done.get(c['artwork_id'],{}).get('outcome') in ('prepared','manual_review','complete'):
            continue
        try:
            im = photo.research(c,c['discovery_entity'],fetch,args.run,
                                independent_photographers_only=True,extended_search=True)
            im.update(provider=PROVIDER,source_name=core.PROVIDERS[PROVIDER],source_record_url=c['source_record_url'],
                      source_object_id=c['external_id'])
            im['raw']['institution'] = c['institution_entity']
            verify(im)
            core.save_new(args.run/'selected'/PROVIDER/(c['artwork_id']+'.json'),im)
            core.worker(PROVIDER,[c],SimpleNamespace(run=args.run,prepare_only=True),None)
        except (ValueError,KeyError) as exc:
            core.event(args.run,{'provider':PROVIDER,'artwork_id':c['artwork_id'],'outcome':'manual_review','reason':str(exc)})
        print(core.now(),'Native photo outcomes',dict(collections.Counter(e['outcome'] for e in core.latest_events(args.run).values())),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase',choices=['discover','cached-discover','prepare'])
    p.add_argument('--run',required=True,type=Path)
    p.add_argument('--gaps',type=Path)
    p.add_argument('--cached-leads',type=Path,action='append',default=[])
    p.add_argument('--groups',type=int,default=20)
    p.add_argument('--limit',type=int,default=120)
    p.add_argument('--deadline',type=float,required=True)
    args=p.parse_args(); args.run.mkdir(parents=True,exist_ok=True)
    lock=(args.run/'worker.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    {'discover':discover,'cached-discover':cached_discover,'prepare':prepare}[args.phase](args)
