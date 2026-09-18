#!/usr/bin/env python3
"""Exact existing Italian print, using current Mia object-level PDM evidence."""
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
c=module('campaign','italy-image-campaign.py')
m=module('mia_source','overnight-mia-images.py')
p=module('primary_capture','italy-catalogue-pdf-evidence.py')
LABEL='round-44-mia-print';PROVIDER='italy-mia'
ARTWORK='bcc9a763-3612-5960-8262-8b9811805223';OBJECT='120878'

def validate(im):
    if im['artwork_id']!=ARTWORK or im['scheme']!='mia-object' or im['external_id']!=OBJECT:
        raise ValueError('Only the exact existing selected print is authorized')
    if len(im['creators'])!=1 or im['creators'][0]['qid']!='Q921242' or im['creators'][0]['role']!='primary':
        raise ValueError('Exact existing primary creator differs')
    url,facts=m.source_match(im,im['raw']['object'])
    if im['source_image_url']!=url or im['page']!='https://collections.artsmia.org/art/'+OBJECT:
        raise ValueError('Current native primary image/page differs')
    if im['rights_status']!='public_domain' or im['policy_url']!=m.PDM or im['license_label']!='Public Domain Mark 1.0':
        raise ValueError('Exact native image licence differs')
    receipt=im['raw']['current_policy_review']
    if receipt['url']!=m.POLICY or receipt['method']!='Current primary policy read with web tool':
        raise ValueError('Current museum rights policy source differs')
    data=(ROOT/receipt['path']).read_bytes()
    if c.core.sha(data)!=receipt['sha256']:
        raise ValueError('Current policy capture checksum differs')
    facts=c.load(ROOT/receipt['path'])
    if facts['licence_uri']!=m.PDM or facts['scope']!='Images explicitly identified as Public Domain' or facts['commercial_reuse'] is not True or facts['permission_required'] is not False:
        raise ValueError('Museum public-domain image permission is absent')
    client=im['raw']['image_mapping_evidence']
    if client['official_client_url']!='https://collections.artsmia.org/bundle.js' or 'https://img.artsmia.org/web_objects_cache/' not in client['public_image_url_construction']:
        raise ValueError('Official client image resource mapping absent')
    return facts

def research():
    run=c.RUN/LABEL
    row=next(r for r in c.load(c.RUN/'eligible-image-gaps.json') if r['artwork_id']==ARTWORK)
    row=dict(row,provider=PROVIDER,scheme='mia-object',external_id=OBJECT,
        page='https://collections.artsmia.org/art/'+OBJECT,
        artist=row['creators'][0]['name'],aliases=[],roles=['primary'])
    if not (run/'candidates.json').exists():
        for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]:
            before=c.snapshot([row],dsn)
            if len(before)!=1 or before[0]['primary_media_id'] or before[0]['date_scope']!='eligible' or not before[0]['selected']:
                raise ValueError('Current eligible image gap differs')
            if any(before[0][k]!=row[k] for k in ('title','slug','creation_year_start','creation_year_end','work_type')):
                raise ValueError('Current object metadata differs')
            row.setdefault('target_ids',{})[target]=before[0]['target_id']
            c.save(run/(target+'-before.json'),before)
        c.save(run/'candidates.json',{'selected_at':c.core.now(),'candidates':[row],
            'selection':'One existing Italian print; exact native accession, creator, dates and current Public Domain full-image flag required'})
    else:row=c.load(run/'candidates.json')['candidates'][0]
    if row['artwork_id'] in c.core.latest_events(run):return
    c.core.HOSTS.add('search.artsmia.org')
    fetcher=c.core.Fetcher(run/'metadata/native-evidence')
    obj=fetcher.metadata('https://search.artsmia.org/id/'+OBJECT)
    url,facts=m.source_match(row,obj)
    policy=c.RUN/'mia-followup/current-policy-review.json'
    facts=c.load(policy)
    receipt={'url':m.POLICY,'method':'Current primary policy read with web tool',
        'reviewed_at':facts['reviewed_at'],'path':str(policy.relative_to(ROOT)),
        'sha256':c.core.sha(policy.read_bytes())}
    prior=ROOT/'docs/research/overnight-images-20260915/mia/client-resource-evidence.json'
    im=dict(row,source_image_url=url,rights_status='public_domain',policy_url=m.PDM,
        license_label='Public Domain Mark 1.0',checked_at=c.core.now(),scope_evidence=facts,
        raw={'object':obj,'current_policy_review':receipt,'image_mapping_evidence':c.load(prior),
             'image_mapping_evidence_path':str(prior.relative_to(ROOT)),
             'image_mapping_evidence_sha256':c.core.sha(prior.read_bytes())},
        creator_credit='Minneapolis Institute of Art; '+obj['creditline'],
        attribution_text=row['artist']+'. '+row['title']+'. Minneapolis Institute of Art, '+obj['accession_number']+'. '+obj['creditline']+'. Public Domain Mark 1.0 ('+m.PDM+'). Full-frame proportional JPEG reproduction.')
    validate(im)
    c.save(run/'selected'/PROVIDER/(ARTWORK+'.json'),im)
    c.core.event(run,{'provider':PROVIDER,'artwork_id':ARTWORK,'external_id':OBJECT,'outcome':'rights_selected'})
    print('Exact current Mia public-domain primary image selected',flush=True)

if __name__=='__main__':research()
