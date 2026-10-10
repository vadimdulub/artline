#!/usr/bin/env python3
import argparse,importlib.util
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museums-exactly-one-deep-links-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
d=a.d;RUN=a.RUN
def prepare():
 before=d.load(RUN/'existing-wikidata-links/baseline.json.gz');review=d.load(RUN/'existing-wikidata-links/review.json.gz');official=d.load(RUN/'existing-wikidata-links/manessier-official.json')
 aid='105b8263-a924-59b4-b653-e3d7c1477122';old=before[aid];r=next(x for x in review['records']if x['artwork_id']==aid)
 source=next(x for x in d.load(RUN/'waves/missing-authorities-reviewed/source-verified.json.gz')['records']if x['source_record_id']=='Q141442953')
 a.m.m.configure('wikidata-reviewed').check_body(source,{})
 assert not old['artwork']['current_institution_id'] and not old['assertions']
 assert r['title']==old['artwork']['title'] and r['creator']=='Alfred Manessier' and r['fields']['Date']==old['artwork']['date_display']=='1952'
 assert r['native_ids']==[old['identifiers'][0]['external_id']] and r['canonical']==old['identifiers'][0]['canonical_url'] and r['canonical']in source['alternate_native_urls']
 a.a.checked(r['receipt']);text=BeautifulSoup(a.a.checked(official['receipt']),'html.parser').get_text(' ',strip=True)
 phrase='La Chaux-de-Fonds , musée des beaux-arts : La Passion de Notre Seigneur Jésus-Christ , 1952, huile sur toile, 200 × 150 cm'
 normalized=' '.join(text.replace('\xa0',' ').split());assert phrase in normalized
 basis='Exact existing WikiArt native ID, creator, French title and 1952 date verified. Wikidata explicitly cross-references that exact WikiArt page and has one referenced collection statement for La Chaux-de-Fonds. Its underlying official Alfred Manessier public-collections catalogue was opened and independently confirms the exact French title, date and museum. Editorial confidence 0.95, not calibrated probability. Preserve existing unknown dimensions and all artwork metadata.'
 claim=dict(artwork_id=aid,title=old['artwork']['title'],scheme='wikidata',external_id=source['source_record_id'],institution=source['museum'],source_url=source['facts']['source_url'],checked_at=source['source_receipt']['retrieved_at'],location_text=source['museum']['name'],identity_basis=basis,source_class='referenced_wikidata_with_official_creator_catalogue_confirmation',source_receipt=source['source_receipt'],duplicate_source_urls=[r['canonical']],object_evidence=dict(editorial_confidence=.95,confidence_basis=basis,wikiart=r,wikidata=source,official_artist_catalogue=official),claim_type='holding',review_state='accepted',limitation='Collection relationship only; no current display inference. Original artwork dates, source labels, images and publication state preserved.')
 dest=RUN/'links/extra-existing';d.save(dest/'claims.json.gz',dict(at=d.now(),provider='reviewed-wikidata-and-official-artist-catalogue',claims=[claim],held=[dict(artwork_id='f7ae8061-875b-5b59-8536-ad5974ecca34',reason='WikiArt Private Collection conflicts with referenced museum holding; official Smithsonian catalogue visible in web search but direct source capture returned 403. Retain for independently captured primary-source comparison.')]));d.save(dest/'baseline.json.gz',{aid:old});d.save(dest/'backups.json',d.load(RUN/'backups.json'));print('Prepared Manessier existing-artwork museum link',flush=True)
def phase(name):a.a.campaign().link_delivery(name,'extra-existing')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();phase(x.phase)if x.phase.startswith('link_')else globals()[x.phase]()
