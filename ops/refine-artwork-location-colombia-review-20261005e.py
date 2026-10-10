#!/usr/bin/env python3
"""Separate Colombia's technical-metadata review from an explicit collection link."""
import copy
import gzip
import importlib.util
from pathlib import Path
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('p',Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);r=p.r


def main():
    index=p.Index();ids={v['id']for v in r.load(r.RUN/'museum-guides-baseline-20261005e.json.gz')['missing']}
    policy=r.load(r.RUN/'colombia-review-policy-20261005e.json');rc=policy['receipt']
    raw=gzip.decompress((r.ROOT/rc['body_path']).read_bytes());assert rc['status']==200 and r.sha(raw)==rc['sha256']
    text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
    assert 'sincronizados en tiempo real' in text and 'inventarios históricos' in text
    claims=[]
    for old in r.load(r.RUN/'primary-plans/colombia-20261005b.json.gz')['claims']:
        if old['artwork_id']not in ids:continue
        evidence=old['object_evidence'];obj=evidence['current_object'];row=index.by_id[old['artwork_id']]
        if evidence['qualifications']!=['museum_marks_record_under_research'] or row['artwork']['status']!='review':continue
        assert obj['en_investigacion'] is True and obj['ubicacion_actual']=='Museo Nacional de Colombia'
        assert obj['ubicacion_estado'] in ['En reserva','En exhibición']
        assert old['source_receipt']['status']==200 and old['external_id']==obj['id_objeto']
        basis=index.match(row,'colombia-object',obj['id_objeto'],[obj['titulo']],[obj['autor']],obj['numero_registro'],[obj['fecha']])
        assert basis.startswith(('existing_','unique_'))
        c=copy.deepcopy(old);c['review_state']='accepted'
        c['object_evidence']['collection_identity_with_metadata_review']={
            'catalogue_policy':policy,'museum_object_id':obj['id_objeto'],'museum_inventory':obj['numero_registro'],
            'explicit_current_institution':obj['ubicacion_actual'],'source_technical_metadata_remains_under_research':True,
            'artwork_publication_remains_review':True,
            'interpretation':'The museum publishes its current collection-management inventory while flagging historical technical metadata for ongoing normalization and documentary review. The unique exact supplied creator/title/date match and explicit current museum field identify the catalogue association. Technical metadata and curator attributions remain subject to review; no metadata is overwritten.'}
        c['identity_basis']+='; explicit current museum field and published catalogue review policy; technical metadata review retained'
        c['limitation']='Museum catalogue holding association only. The museum labels the source technical metadata En investigación; that qualification and the artwork editorial review remain intact. No authentication of attribution, replacement dates, publication, ownership transfer, dated on-view assertion or independent physical observation.'
        claims.append(c)
    p.output('colombia-metadata-review-holdings-20261005e',claims,[])


if __name__=='__main__':main()
