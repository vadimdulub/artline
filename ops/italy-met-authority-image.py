#!/usr/bin/env python3
"""One existing Italian artwork: exact Wikidata-to-Met object crosswalk.

The database's existing Wikidata identifier remains the attachment key. The
actual authority's unique Met ID and accession must agree with the fresh API.
"""
import argparse
import importlib.util
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'ops'/filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
c = module('campaign', 'italy-image-campaign.py')
w = module('commons', 'overnight-commons-images.py')
PROVIDER = 'italy-met-authority'
LABEL = 'round-39-met-authority'
QID = 'Q126118762'
MET_ID = '872016'

def validate(image):
    entity, raw = image['raw']['wikidata'], image['raw']['met']
    if image['scheme'] != 'wikidata' or image['external_id'] != QID or entity['id'] != QID:
        raise ValueError('Existing exact authority identity differs')
    w.entity_match(image, entity, require_primary_image=False)
    if w.values(entity, 'P3634') != [MET_ID] or str(raw.get('objectID')) != MET_ID:
        raise ValueError('Actual authority/native object crosswalk differs')
    if raw.get('accessionNumber') not in w.values(entity, 'P217'):
        raise ValueError('Actual museum accession differs')
    if w.norm(raw.get('title','')) != w.norm(image['title']):
        raise ValueError('Native title differs')
    if w.norm(raw.get('artistDisplayName','')) != w.norm(image['artist']):
        raise ValueError('Native artist differs')
    if raw.get('classification') != 'Paintings' or raw.get('isPublicDomain') is not True or raw.get('rightsAndReproduction'):
        raise ValueError('Native object type or rights not explicitly cleared')
    if not 0 < raw.get('objectBeginDate',0) <= raw.get('objectEndDate',9999) <= 1970:
        raise ValueError('Native date is not eligible')
    if not (raw['objectBeginDate'] <= image['creation_year_start'] <= image['creation_year_end'] <= raw['objectEndDate']):
        raise ValueError('Existing creation interval not corroborated')
    if image['source_image_url'] != raw.get('primaryImageSmall') or urlparse(image['source_image_url']).hostname != 'images.metmuseum.org':
        raise ValueError('Exact native primary image differs')
    if image['rights_status'] != 'cc0' or image['policy_url'] != c.core.POLICIES['met'] or image['license_label'] != 'CC0 1.0':
        raise ValueError('Native Open Access rights differ')
    if image['page'] != 'https://www.metmuseum.org/art/collection/search/'+MET_ID:
        raise ValueError('Native source page differs')

def research():
    run = c.RUN/LABEL
    source = c.load(c.RUN/'round-37-italian-abroad-authorities/candidates.json')['candidates']
    row = next(r for r in source if r['external_id'] == QID)
    row = dict(row, provider=PROVIDER)
    if not (run/'candidates.json').exists():
        for target, dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
            rows = c.snapshot([row], dsn)
            if len(rows)!=1 or rows[0]['primary_media_id'] or rows[0]['date_scope']!='eligible' or not rows[0]['selected']:
                raise ValueError('Current eligible image gap differs')
            old = next(r for r in c.load(c.RUN/'round-37-italian-abroad-authorities'/(target+'-before.json')) if r['local_id']==row['artwork_id'])
            if rows[0]['metadata']!=old['metadata'] or rows[0]['creators']!=old['creators']:
                raise ValueError('Current metadata changed')
            c.save(run/(target+'-before.json'), rows)
        c.save(run/'candidates.json', {'selected_at':c.core.now(),'candidates':[row],
            'selection':'Existing Italian painter artwork; actual unique authority Met ID and fresh Open Access native evidence'})
    if row['artwork_id'] in c.core.latest_events(run): return
    fetcher = c.core.Fetcher(run/'metadata/native-evidence')
    entity = w.api(fetcher,'www.wikidata.org',{'action':'wbgetentities','ids':QID})['entities'][QID]
    im = c.core.image_record(dict(row,provider='met',external_id=MET_ID),fetcher,{}, {})
    if not im: raise ValueError('No explicitly reusable native primary image')
    raw = im['raw']
    im.update(provider=PROVIDER,external_id=QID,page='https://www.metmuseum.org/art/collection/search/'+MET_ID,
        raw={'wikidata':entity,'met':raw},creator_credit='The Metropolitan Museum of Art',
        attribution_text=row['artist']+'. '+row['title']+'. The Metropolitan Museum of Art, '+raw['accessionNumber']+'. CC0 1.0. Full-frame proportional JPEG reproduction.')
    validate(im)
    c.save(run/'selected'/PROVIDER/(row['artwork_id']+'.json'),im)
    c.core.event(run,{'provider':PROVIDER,'artwork_id':row['artwork_id'],'external_id':QID,'outcome':'rights_selected'})
    print('Exact Met Open Access image selected',flush=True)

if __name__=='__main__': research()
