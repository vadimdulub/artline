#!/usr/bin/env python3
import argparse,collections,gzip,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museums-exactly-one-artefact-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
m=a.m;d=a.d;RUN=a.RUN;ROOT=a.ROOT
h=m.module('links_capture','research-havre-rouen-cyprus-20261006.py');h.RUN=RUN/'existing-wikiart'
loc=m.module('link_snapshots','apply-artwork-locations-20261004.py')

def research():
 identity=d.load(RUN/'identity/artefact-corrected/discovery.json.gz');leads=d.load(RUN/'identity/artefact-corrected/title-leads.json');byid={x['artwork']['id']:x['artwork']for x in identity['comparisons']};byurl=collections.defaultdict(set)
 for row in identity['identifiers']:
  if(row['canonical_url']or'').startswith('https://www.wikiart.org/en/'):byurl[row['entity_id']].add(row['canonical_url'])
 selected={x['existing_id']for x in leads if x['similarity']>=.82 and not x['existing_museum'] and len(byurl[x['existing_id']])==1}
 # These are discovery leads only. Every proposed link must independently pass
 # exact existing WikiArt native identity and an explicit museum Location.
 with d.connect()as db:before=loc.snapshots(db,sorted(selected))
 d.save(RUN/'existing-wikiart/baseline.json.gz',before)
 rows=[];held=[]
 for aid in sorted(selected):
  url=next(iter(byurl[aid]));raw,rc=h.capture(url);assert rc['status']==200
  soup=BeautifulSoup(raw,'html.parser');info=soup.select_one('.wiki-layout-artwork-info');assert info
  fields={}
  for li in info.select('article > ul > li'):
   node=li.find('s')
   if node:key=node.get_text(' ',strip=True).rstrip(':');node.extract();fields[key]=li.get_text(' ',strip=True)
  title=info.select_one('h1').get_text(' ',strip=True);creator=info.select_one('h2').get_text(' ',strip=True)
  native=sorted(set(re.findall(r"trackPageView\('painting',\s*'([a-f0-9]{24})'",raw.decode('utf8','replace'))));canonical=soup.find('link',rel='canonical')['href']
  old=before[aid];identifiers=[x for x in old['identifiers']if x['external_id']in native and (x.get('canonical_url')or'').rstrip('/')==canonical.rstrip('/')]
  reasons=[]
  if len(native)!=1 or len(identifiers)!=1:reasons.append('native_identity_conflict')
  if d.norm(title)!=d.norm(old['artwork']['title']):reasons.append('title_requires_review')
  if d.norm(creator)not in {d.norm(x['name'])for x in old['creator_keys']}:reasons.append('creator_requires_review')
  if not fields.get('Location'):reasons.append('no_source_location')
  matches=[i for i in a.BASE.values() if d.norm(i['name'])==d.norm(fields.get('Location'))]
  if len(matches)!=1:reasons.append('museum_label_requires_review')
  row=dict(artwork_id=aid,receipt=rc,title=title,creator=creator,fields=fields,native_ids=native,identifiers=identifiers,canonical=canonical,museum=matches[0]if len(matches)==1 else None,discovery=[x for x in leads if x['existing_id']==aid],issues=reasons)
  rows.append(row);print(title,fields.get('Location'),reasons,flush=True)
 d.save(RUN/'existing-wikiart/review.json.gz',dict(at=d.now(),records=rows))

def prepare():
 proof=d.load(RUN/'existing-wikiart/review.json.gz');before=d.load(RUN/'existing-wikiart/baseline.json.gz');claims=[];held=[]
 native={r['source_record_id']:r for r in d.load(RUN/'waves/artefact-corrected/source-verified.json.gz')['records']}
 reviewed={
 '1624fd58-d68f-55f7-b118-a263e726484d':('6749c74063ac0611596f60a9','59 x 42.5 cm','1889'),
 '02a18728-2e90-5d5b-8d0f-3c849db25818':('595343a05a93481c74b379f7','59 x 67 cm','1913'),
 '7af76e6b-b3b1-54ca-93d3-7ab1c26f7c9b':('6749bcc0bbcf22117581186a','66.5 x 88.5 cm','1904'),
 }
 for r in proof['records']:
  if r['issues'] and r['artwork_id']not in reviewed:held.append(r);continue
  aid=r['artwork_id'];old=before[aid];assert not old['artwork']['current_institution_id'];assert not any(x['claim_type']=='holding' and x['review_state']=='accepted' and not x['superseded_by'] for x in old['assertions'])
  raw=a.checked(r['receipt']);assert r['canonical'].rstrip('/')==r['receipt']['url'].rstrip('/')
  assert not set(r['issues'])-{'no_source_location','museum_label_requires_review'}
  identifier=r['identifiers'][0];museum=r['museum'];url=r['canonical'];rc=r['receipt'];scheme=identifier['scheme'];external=identifier['external_id'];confidence=.95;source_class='user_approved_wikiart_catalogue';source=None
  basis='Exact existing WikiArt native artwork ID, canonical URL, title and creator independently verified. Explicit current source Location matches the full existing museum name. Source discovery through official Artefact catalogue title variants; actual holding evidence is WikiArt. Editorial confidence 0.95, not a calibrated probability.'
  if aid in reviewed:
   key,dimensions,year=reviewed[aid];source=native[key];a.check_body(source,{})
   assert r['fields']['Dimensions']==dimensions and r['fields']['Date'].startswith(year)
   assert source['facts']['first']==source['facts']['last']==int(year)
   museum=source['museum']
   if aid=='1624fd58-d68f-55f7-b118-a263e726484d':
    assert r['fields']['Location']=='Chuvash State Museum of Fine Arts, Cheboksary, Russia' and museum['id']=='abbaec64-5854-56a4-9c5c-02866b87ff2d'
    basis='Exact existing WikiArt object identity, Levitan creator, 1889 date and 59 x 42.5 cm dimensions agree with official Artefact Dandelions / Одуванчики. WikiArt explicitly names Chuvash State Museum of Fine Arts, Cheboksary: individually reconciled with Chuvashian State Arts Museum and its official native catalogue authority. Holding source is WikiArt; confidence 0.95 editorial assessment, not calibrated probability.'
   else:
    assert not r['fields'].get('Location')
    url=source['facts']['source_url'];rc=source['source_receipt'];scheme='artefact-object';external=key;confidence=.9;source_class='official_artefact_holding_with_exact_wikiart_identity'
    basis='Individually reviewed translated title, exact creator, creation year and distinctive dimensions ('+dimensions+') agree across the existing WikiArt object and official museum Artefact catalogue. Existing WikiArt native ID and canonical page verified. Actual holding evidence is the official Artefact Collection field and museum-scoped catalogue; WikiArt has no Location field. Editorial confidence 0.90, not a calibrated probability.'
  claims.append(dict(artwork_id=aid,title=old['artwork']['title'],scheme=scheme,external_id=external,institution=museum,source_url=url,checked_at=rc['retrieved_at'],location_text=r['fields'].get('Location')or museum['name'],identity_basis=basis,source_class=source_class,source_receipt=rc,duplicate_source_urls=[r['canonical']],object_evidence=dict(editorial_confidence=confidence,confidence_basis=basis,source_review=r,official_artefact=source),claim_type='holding',review_state='accepted',limitation='Documented collection relationship, no current display inference. Original artwork metadata, dates, source credits, images and publication states remain unchanged.'))
 dest=RUN/'links/deep-existing';d.save(dest/'claims.json.gz',dict(at=d.now(),provider='reviewed-wikiart-and-artefact',claims=claims,held=held));d.save(dest/'baseline.json.gz',{x['artwork_id']:before[x['artwork_id']]for x in claims});d.save(dest/'backups.json',d.load(RUN/'backups.json'));print('Prepared',len(claims),'verified existing artwork links',flush=True)

def phase(name):
 c=a.campaign();c.link_delivery(name,'deep-existing')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();phase(x.phase)if x.phase.startswith('link_')else globals()[x.phase]()
