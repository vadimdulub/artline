#!/usr/bin/env python3
"""Deliver one visually reviewed catalogue object, preserving its period label."""
import argparse,gzip,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('nicosia-artwork-delivery-20261007.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
n,h=v.n,v.h
PARENT=v.R
v.R=n.ROOT=PARENT/'nicosia-cyprus-museum-followup-20261007'
v.B=n.BACKUP=v.B/v.R.name
h.RUN=v.R;h.BACKUP=v.B

def prepare():
    source=n.load(PARENT/'cyprus-museum-artwork-candidates.json')
    raw=next(x['raw_fields']for x in source['held']if x['raw_fields']['catalogue_number']==133)
    assert raw['header']==['Decorated valve of the shell Pinctada','margaritifera','Seashell','H. 14 cm; W. 16 cm','Hellenistic/Roman period','Cyprus, archaeological context unknown','Cyprus Museum, H19-1935']
    rc=source['source_receipt']
    f=dict(source='cyprus-museum-cultures-in-dialogue-2012',scheme='cyprus-museum-cultures-in-dialogue-2012',source_id='133',source_url=rc['url'],receipt=rc,museum_slug='cyprus-museum-nicosia',raw_fields=raw,
        title='Decorated valve of the shell Pinctada margaritifera',creator_label=None,medium='Seashell',dimensions='H. 14 cm; W. 16 cm',accession='H19-1935',work_type='unknown',image_url=None,
        date_display='Hellenistic/Roman period',first=None,last=None,precision='unknown',shared_source_url=True,source_publication_year=2012,
        holding_note='Cyprus Museum lender credit and inventory H19-1935 in the Department of Antiquities official 2012 catalogue, printed page 180, catalogue 133. The Brussels temporary exhibition is not a present-display claim.',
        editorial_confidence=.96,confidence_basis='Primary museum lender and unique inventory, caption and description visually checked on printed page 180; illustration 133 checked on page 181. The source describes carved decoration of the shell; this is an art object, not an unmodified natural specimen. Editorial assessment, not calibrated probability.',
        remaining_uncertainty='The source gives a historical period without numeric creation bounds. Preserve it literally, with null numeric dates and review status. Maker is unnamed. Subsequent transfers and present display are not independently verified; no image use inferred.',
        review_reason='Historical period retained without invented numeric bounds. Not automatically classified as date-eligible. Anonymous ancient Greek/Cypriot art is included under the explicit collection priority.')
    n.save(v.R/'artwork-candidates.json.gz',dict(records=[f],decision='Resolve prior date-parser hold by preserving the literal period and unknown numeric bounds, not by inventing a year.',visual_review_pages=[180,181]))
    n.save(v.R/'editorial-identity-resolutions.json',{})
    n.save(v.R/'production-backup.json',n.load(PARENT/'production-backup.json'))

def inputs():
    facts=n.load(v.R/'artwork-candidates.json.gz')['records'];assert len(facts)==1
    f=facts[0];assert f['source_id']=='133'and f['accession']=='H19-1935'
    assert f['first']is None and f['last']is None and f['precision']=='unknown'and f['date_display']=='Hellenistic/Roman period'
    assert f['image_url']is None
    rc=f['receipt'];assert rc['status']==200 and h.sha(gzip.decompress((n.REPO/rc['body_path']).read_bytes()))==rc['sha256']
    return facts

v.inputs=inputs
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['prepare','plan','apply','verify']);args=parser.parse_args()
    if args.phase=='prepare':prepare();inputs();print('Prepared one visually reviewed Cyprus Museum object; numeric dates remain unknown.')
    elif args.phase=='plan':v.make_plan()
    else:getattr(v,args.phase)()
