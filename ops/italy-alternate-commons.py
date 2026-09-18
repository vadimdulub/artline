#!/usr/bin/env python3
"""Research alternative licensed files for selected exact Italian artworks.

No downloads here. A different Commons photograph must independently establish
the same physical object and its own original provenance and licence.
"""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'ops/italy-image-campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
spec = importlib.util.spec_from_file_location('commons', ROOT / 'ops/overnight-commons-images.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def select(label, limit, source_rounds=None, only_visual_holds=False):
    run = c.RUN / label
    run.mkdir(parents=True, exist_ok=True)
    if (run / 'candidates.json').exists():
        return
    found = {}
    all_rejected_files = collections.defaultdict(set)
    for review_path in c.RUN.glob('*/visual-review.json'):
        for review in c.load(review_path)['images']:
            if review['outcome'] != 'held': continue
            for image_path in (review_path.parent/'images').glob('*/'+review['artwork_id']+'.json'):
                previous_image = c.load(image_path)
                if previous_image['sha256'] == review['sha256'] and previous_image.get('raw',{}).get('commons'):
                    all_rejected_files[review['artwork_id']].add(previous_image['raw']['commons']['title'])
    for name in source_rounds or ['round-06-brera','round-07-venice','round-08-borghese','round-09-carrara','round-10-ambrosiana','round-01-commons']:
        source = c.RUN / name
        path = source / 'candidates.json'
        if not path.exists(): continue
        latest = c.core.latest_events(source)
        visual_path = source / 'visual-review.json'
        visual_holds = {r['artwork_id']:r for r in c.load(visual_path)['images'] if r['outcome']=='held'} if visual_path.exists() else {}
        for candidate in c.load(path)['candidates']:
            event = latest.get(candidate['artwork_id'], {})
            visual_hold = visual_holds.get(candidate['artwork_id'])
            if only_visual_holds and not visual_hold: continue
            if event.get('outcome') != 'manual_review' and not visual_hold: continue
            if not candidate.get('qid'): continue
            rejected_files = sorted(all_rejected_files[candidate['artwork_id']])
            if visual_hold:
                image = c.load(source / 'images' / candidate['provider'] / (candidate['artwork_id']+'.json'))
                if image['raw']['commons']['title'] not in rejected_files:
                    rejected_files.append(image['raw']['commons']['title'])
            found.setdefault(candidate['artwork_id'], dict(candidate, prior_round=name,
                prior_reason=visual_hold.get('note') if visual_hold else event.get('reason'),
                visually_rejected_files=rejected_files))
    candidates = list(found.values())[:limit]
    local = c.snapshot(candidates, 'postgres://127.0.0.1/artline') if candidates else []
    remote = c.snapshot(candidates, c.core.cloud_dsn()) if candidates else []
    indexes = []
    for rows in (local, remote):
        idx = collections.defaultdict(list)
        for r in rows: idx[r['local_id']].append(r)
        indexes.append(idx)
    approved = []
    held = []
    for r in candidates:
        groups = [idx[r['artwork_id']] for idx in indexes]
        if any(len(g) != 1 for g in groups):
            held.append(dict(r, reason='Current exact local/production object missing or ambiguous'))
            continue
        l, remote_row = groups[0][0], groups[1][0]
        if any(x['primary_media_id'] or x['status']=='archived' or x['date_scope']!='eligible' or not x['selected'] for x in (l, remote_row)):
            held.append(dict(r, reason='Existing image or eligibility changed'))
            continue
        if any(x[k] != r[k] for x in (l, remote_row) for k in ('slug','title','creation_year_start','creation_year_end','work_type')):
            held.append(dict(r, reason='Catalogue identity metadata differs'))
            continue
        r['target_ids'] = {'local':l['target_id'],'cloud':remote_row['target_id']}
        approved.append(r)
    c.save(run / 'candidates.json', {'selected_at':c.core.now(),'candidates':approved,
         'selection':'Existing exact artwork identities; seek independent alternate file where first source lacks acceptable provenance/rights'})
    c.save(run / 'local-before.json', local)
    c.save(run / 'cloud-before.json', remote)
    c.save(run / 'selection-held.json', held)
    print(label, 'alternate targets', len(approved), 'held', len(held), flush=True)


def research(label, limit):
    run = c.RUN / label
    latest = c.core.latest_events(run)
    rows = [r for r in c.load(run / 'candidates.json')['candidates'] if r['artwork_id'] not in latest][:limit]
    fetcher = w.core.Fetcher(run / 'metadata/alternate-commons')
    entities = {}
    for start in range(0,len(rows),20):
        entities.update(w.api(fetcher,'www.wikidata.org',{'action':'wbgetentities',
            'ids':'|'.join(r['qid'] for r in rows[start:start+20]),'props':'labels|aliases|claims','languages':'en|it|fr|de|mul'})['entities'])
    for number, record in enumerate(rows, 1):
        qid = record['qid']
        entity = entities[qid]
        failures = []
        try:
            w.entity_match(record, entity, require_primary_image=False)
            params = {'action':'query','generator':'search','gsrsearch':'haswbstatement:P6243='+qid,
                      'gsrnamespace':6,'gsrlimit':20,'prop':'imageinfo|revisions',
                      'iiprop':'url|extmetadata|sha1|size|mime','iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'}
            result = w.api(fetcher,'commons.wikimedia.org',params)
            pages = list(result.get('query',{}).get('pages',{}).values())
            structured_pages_found = bool(pages)
            discovery_queries = [dict(params)]
            # Some correct file pages identify the physical object in their
            # Artwork template but have no Structured Data P6243 statement.
            # Retain the actual primary filenames as additional metadata leads.
            primary_files = [f for f in w.values(entity,'P18') if isinstance(f,str)]
            if len(primary_files) > 5:
                raise ValueError('Too many authority image leads for bounded independent review')
            if primary_files:
                primary_params = {'action':'query','titles':'|'.join('File:'+f for f in primary_files),
                    'prop':'imageinfo|revisions','iiprop':'url|extmetadata|sha1|size|mime',
                    'iiurlwidth':960,'rvprop':'ids|content','rvslots':'main'}
                primary_result = w.api(fetcher,'commons.wikimedia.org',primary_params)
                pages += list(primary_result.get('query',{}).get('pages',{}).values())
                discovery_queries.append(primary_params)
            if not structured_pages_found:
                categories = w.values(entity,'P373')
                if len(categories)==1 and isinstance(categories[0],str):
                    params = {k:v for k,v in params.items() if not k.startswith('gsr')}
                    params.update(generator='categorymembers',gcmtitle='Category:'+categories[0],gcmtype='file',gcmlimit=20)
                    result = w.api(fetcher,'commons.wikimedia.org',params)
                    pages += list(result.get('query',{}).get('pages',{}).values())
                    discovery_queries.append(dict(params))
            pages = list({p['pageid']:p for p in pages if p.get('imageinfo') and p.get('ns')==6 and p.get('pageid',0)>0}.values())
            pages.sort(key=lambda p: (-min(p['imageinfo'][0].get('width',0),p['imageinfo'][0].get('height',0)),p['title']))
            media_ids = ['M'+str(p['pageid']) for p in pages]
            structured = w.api(fetcher,'commons.wikimedia.org',{'action':'wbgetentities','ids':'|'.join(media_ids),'props':'claims'})['entities'] if media_ids else {}
            selected = None
            for page in pages:
                try:
                    if page['title'] in record.get('visually_rejected_files', []):
                        raise ValueError('Previously rejected at visual inspection; different image required')
                    if re.search(r'\b(detail|particolare|dettaglio|verso|reverse|collage|montage)\b',page['title'],re.I):
                        raise ValueError('Detail/reverse/composite excluded from primary-image choice')
                    sdc = structured.get('M'+str(page['pageid']),{})
                    rendered = w.rendered_rights_uri(fetcher,page)
                    info,credit,licence,uri,status,url,original = w.rights_and_identity(record,entity,page,sdc,rendered)
                    selected = dict(record,page=info['descriptionurl'],source_image_url=url,policy_url=uri,
                        rights_status=status,license_label=licence,checked_at=c.core.now(),
                        image_selection_basis='independent_exact_commons_file',
                        raw={'wikidata':entity,'commons':page,'structured_data':sdc,
                             'alternate_search':params,'discovery_queries':discovery_queries,
                             'prior_source_hold':record['prior_reason']},
                        creator_credit=credit,
                        attribution_text=f"{record['artist']}. {record['title']}. Image credit: {credit}. {info['descriptionurl']}. {licence} ({uri}). Full-frame proportional resize and JPEG compression; applicable ShareAlike terms retained.")
                    if rendered: selected['rendered_licence_evidence']=rendered
                    if original: selected['commons_original_sha1']=info['sha1']
                    break
                except (ValueError,KeyError) as error:
                    failures.append({'file':page['title'],'reason':str(error)})
            if selected:
                c.save(run / 'selected/night-commons' / (record['artwork_id']+'.json'),selected)
                c.core.event(run,{'provider':'night-commons','artwork_id':record['artwork_id'],
                    'external_id':record['external_id'],'outcome':'rights_selected','alternate':True})
            else:
                c.core.event(run,{'provider':'night-commons','artwork_id':record['artwork_id'],
                    'external_id':record['external_id'],'outcome':'manual_review',
                    'reason':'No independently licensed exact full-work alternate in bounded search','files_inspected':len(pages)})
            c.save(run / 'alternate-outcomes' / (record['artwork_id']+'.json'),
                   {'qid':qid,'files_inspected':len(pages),'search_capped':bool(result.get('continue')),
                    'selected_file':selected['page'] if selected else None,'file_holds':failures})
        except Exception as error:
            c.core.event(run,{'provider':'night-commons','artwork_id':record['artwork_id'],
                'external_id':record['external_id'],'outcome':'manual_review','reason':str(error)[:350]})
        print(label, number, '/',len(rows),record['title'][:60],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('phase',choices=['select','research'])
    p.add_argument('--label',default='round-11-alternate-commons')
    p.add_argument('--limit',type=int,default=60)
    p.add_argument('--source-round', action='append')
    p.add_argument('--only-visual-holds', action='store_true')
    args=p.parse_args()
    if args.phase=='select':select(args.label,args.limit,args.source_round,args.only_visual_holds)
    else:research(args.label,args.limit)
