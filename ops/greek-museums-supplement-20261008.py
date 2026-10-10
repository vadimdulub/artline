#!/usr/bin/env python3
"""Museum-supplied EKT records remain authoritative when the old native URL is absent."""
import argparse, importlib.util, re
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
d.PLAN='supplement-delivery-plan.json.gz';d.FACTS='supplement-facts.json'
d.APPLIED='supplement-catalogue-applied.json';d.AFTER='supplement-catalogue-transaction-after.json.gz'


def facts():
    used={f['source_id']for f in d.load(d.RUN/'delivery-plan-v4.json.gz')['records']if f['source']=='searchculture'}
    collections={'DigWAR','EIM','PLI','ZoggopoulosF','pinakothiki_agrinio'};records=[];held=[];museums={}
    for file in ['searchculture-object-facts.json','searchculture-ordered-object-facts.json']:
        for x in d.load(d.RUN/file)['records']:
            key=x['collection'];fs=x['fields'];index=x['index'];url=index['source_url'].split('?')[0];sid=url.split('/aggregator/edm/',1)[1]
            if key not in collections or sid in used:continue
            native=d.preferred(fs.get('Created'))
            # This provider emits repository timestamps as Created. Its separate
            # Date is a physical object date, and is never the semantic Year.
            if native and re.search(r'T\d\d:\d\d',native):native=None
            dt=d.date(native or d.preferred(fs.get('Date')))
            if dt['last'] is not None and dt['last']>1970:held.append(dict(source_url=url,reason='creation_after_cutoff',date=dt));continue
            name,city=d.SC_MUSEUMS[key];mk='sc-'+d.norm(name).replace(' ','-');col=d.load(d.RUN/'collections'/(key+'.json'))
            museums[mk]=dict(key=mk,name=name,city=city,source_url=col['receipt']['url'],receipt=col['receipt'],collection_keys=[key],source_context=col['text'].split(' Search More search options')[0])
            creator=d.untag((fs.get('Creator')or[''])[0])or None
            if d.norm(creator)in ['αγνωστος δημιουργος','αγνωστος','unknown']:creator=None
            inv=re.findall(r'Inventory number ([A-Za-zΑ-Ωα-ω0-9.\-/]+)',str(fs.get('Description')))
            accession=inv[0]if len(set(inv))==1 else None
            # Some legacy catalogue strings repeat the inventory value without
            # a separator (335335); retain it in evidence, not as a guessed ID.
            if accession and len(accession)%2==0 and accession[:len(accession)//2]==accession[len(accession)//2:]:accession=None
            kinds=d.sc_kind(index)
            if kinds=='photograph'and dt['last']is not None and dt['last']<1826:held.append(dict(source_url=url,reason='photograph_subject_date'));continue
            records.append(dict(source='searchculture',scheme='searchculture-edm',source_id=sid,source_url=url,native_url=None,receipt=x['receipt'],museum_key=mk,
                title=d.preferred(fs.get('Title'))or index['title'],alternate_title=None,creator_label=creator,creator_values=fs.get('Creator')or[],**dt,
                work_type=kinds,medium=d.preferred(fs.get('Medium')),dimensions=d.preferred(fs.get('Extent')),accession=accession,raw=x,
                original_title=d.preferred(fs.get('Title'))or index['title'],holding_confidence=.93,
                holding_basis='Museum-supplied record preserved by the Greek National Documentation Centre in the exact named institution collection. The stable EKT object identifier, title, original provider metadata and collection synopsis identify the work. The former native object URL is unavailable; this is explicitly retained as an evidence limitation, not substituted with an invented link. No current-display claim.'))
    d.save(d.RUN/d.FACTS,dict(at=d.now(),records=records,held=held,museums=list(museums.values())))
    print('Supplement facts',len(records),'records',len(museums),'museums',len(held),'holds',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['facts','plan','apply']);a=p.parse_args()
    {'facts':facts,'plan':d.plan,'apply':d.apply}[a.action]()
