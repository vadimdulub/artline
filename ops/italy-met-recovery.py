#!/usr/bin/env python3
"""Exact single-object Met donation recovery after a confirmed API 404."""
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'ops'/filename)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
c=module('campaign','italy-image-campaign.py')
recovery=module('met_recovery','recover-met-commons-images.py')
LABEL='round-27-met-donation'

def validate(image):
    checked=recovery.identity_and_rights(image,image['raw'])
    if (checked['donor_creation_start'],checked['donor_creation_end'])!=(image['creation_year_start'],image['creation_year_end']):
        raise ValueError('Original museum donation dates differ from exact selected object')
    for key in ('source_image_url','rights_status','policy_url','commons_original_sha1','donor_object_id'):
        if image[key]!=checked[key]:raise ValueError('Donated image identity/rights evidence differs')
    if image.get('recovery_basis',{}).get('source_reason','').find('404 Client Error')<0:
        raise ValueError('Recovery is limited to a confirmed absent API record')
    source=image['recovery_basis']['commons_metadata_capture'];path=ROOT/source['path']
    if c.core.sha(path.read_bytes())!=source['sha256']:raise ValueError('Exact donated metadata capture checksum mismatch')
    original=c.load(path)['response']['query']['pages']
    if any(original.get(key)!=page for key,page in image['raw']['query']['pages'].items()):
        raise ValueError('Selected file differs from preserved Commons response')

def select():
    run=c.RUN/LABEL
    if (run/'candidates.json').exists():return
    evidence=c.RUN/'met-retired-source-followup/397347.json';saved=c.load(evidence)
    image=c.load(evidence.with_name('397347-exact-recovery.json'))
    original=saved['candidate']
    event=c.core.latest_events(c.RUN/'round-12-met-prints')[original['artwork_id']]
    image['recovery_basis']={'source_reason':event['reason'],
        'source_event':event,'no_external_identifier_remapping':True,
        'commons_metadata_capture':{'path':str(evidence.relative_to(ROOT)),'sha256':c.core.sha(evidence.read_bytes())}}
    candidate=dict(original,provider='met-commons')
    before={target:c.snapshot([candidate],dsn) for target,dsn in [('local','postgres://127.0.0.1/artline'),('cloud',c.core.cloud_dsn())]}
    for target,rows in before.items():
        if len(rows)!=1 or rows[0]['primary_media_id'] or rows[0]['date_scope']!='eligible' or not rows[0]['selected']:
            raise ValueError('Current exact object eligibility/media changed')
        if any(rows[0][k]!=candidate[k] for k in ('slug','title','creation_year_start','creation_year_end','work_type')):
            raise ValueError('Current object metadata changed')
        candidate.setdefault('target_ids',{})[target]=rows[0]['target_id']
    image['target_ids']=candidate['target_ids']
    validate(image)
    c.save(run/'candidates.json',{'selected_at':c.core.now(),'candidates':[candidate],
        'selection':'One confirmed Met API 404 with exact original museum-donated object XML and current Commons CC0; no remapping or replacement of current restrictive rights'})
    for target,rows in before.items():c.save(run/(target+'-before.json'),rows)
    c.save(run/'selected/met-commons'/(candidate['artwork_id']+'.json'),image)
    c.core.event(run,{'provider':'met-commons','artwork_id':candidate['artwork_id'],'external_id':candidate['external_id'],'outcome':'rights_selected'})
    print(LABEL,'selected one exact retired-source recovery',flush=True)

if __name__=='__main__':select()
