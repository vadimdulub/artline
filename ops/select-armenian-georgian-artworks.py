#!/usr/bin/env python3
"""Select named-creator painting records; preserve unknown dates in review."""
import importlib.util,json,re,collections,uuid
from pathlib import Path
from urllib.parse import urlparse
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;r=b.r

def main():
 ids=json.loads((s.RUN/'bounded-work-selection.json').read_bytes())['selected_work_ids']
 ids=list(dict.fromkeys(ids+json.loads((s.RUN/'priority-selection.json').read_bytes())['work_ids']))
 es,receipts=r.entities(ids);aqids={v['id'] for e in es.values() for v in r.values(e,'P170') if isinstance(v,dict)};artists,ar=r.entities(sorted(aqids));iqids={v['id'] for e in es.values() for v in r.values(e,'P195') if isinstance(v,dict)};institutions,ir=r.entities(sorted(iqids))
 baseline=json.loads((s.RUN/'local-before.json').read_bytes());byqid={v:k for k,v in r.MAPPING.items()};known={i['slug']:i for i in baseline['institutions']};mapping={};excluded=[]
 explicit={'Q2087788':('national-gallery-armenia','National Gallery of Armenia','https://www.gallery.am/'),'Q2028327':('shalva-amiranashvili-museum','Shalva Amiranashvili Museum of Fine Arts','https://museum.ge/'),'Q13054028':('martiros-saryan-museum','Martiros Saryan House-Museum','https://sarian.am/'),'Q5548057':('art-palace-georgia','Art Palace of Georgia','https://artpalace.ge/'),'Q12130481':('gevorg-grigoryan-museum','Gevorg Grigoryan Studio-Museum','https://www.gallery.am/en/'),'Q13052114':('sargsyan-kojoyan-museum','Ara Sargsyan and Hakob Kojoyan House-Museum','https://sargsyan-kojoyan-foundation.am/')}
 for q,e in institutions.items():
  existing=next((i for i in baseline['institutions'] if i['wikidata_id']==q),None) or known.get(byqid.get(q))
  if not existing:
   urls=r.values(e,'P856');hosts={urlparse(u).hostname.removeprefix('www.') for u in urls if isinstance(u,str) and urlparse(u).hostname};matches=[i for i in baseline['institutions'] if i['website_url'] and urlparse(i['website_url']).hostname and urlparse(i['website_url']).hostname.removeprefix('www.') in hosts]
   if len(matches)==1:existing=matches[0]
  if existing:inst=existing
  elif q in explicit:
   slug,name,url=explicit[q];inst={'id':str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/institution/'+q)),'slug':slug,'name':name,'website_url':url,'wikidata_id':q,'new_institution':True}
  else:continue
  mapping[q]={'qid':q,'institution':inst,'institution_entity':e,'institution_receipt':ir[q]}
 selected=[];deferred=[]
 with s.connect('local') as db:
  db.execute('SET TRANSACTION READ ONLY')
  for q in ids:
   e=es[q];reason=None;date=r.date(e);cs=r.claims(e,'P170');cols=r.claims(e,'P195');types={v.get('id') for v in r.values(e,'P31') if isinstance(v,dict)}
   if e.get('id')!=q:reason='redirect_or_missing_identity'
   elif 'Q3305213' not in types:reason='nonpainting_type_needs_separate_mapping'
   elif len(cs)!=1 or cs[0].get('qualifiers'):reason='qualified_or_multiple_creators_need_review'
   elif len(cols)!=1 or cols[0].get('qualifiers'):reason='ambiguous_or_qualified_collection'
   elif r.value(cols[0]).get('id') not in mapping:reason='institution_requires_identity_review'
   elif date['first'] is not None and not date['eligible']:reason='outside_creation_scope'
   if reason:deferred.append({'qid':q,'title':r.label(e),'reason':reason});continue
   aq=r.value(cs[0])['id'];artist=artists[aq];iq=r.value(cols[0])['id'];inst=mapping[iq];existing=db.execute("SELECT a.id::text,a.slug,a.primary_media_id::text,a.current_institution_id::text,a.status FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id AND e.entity_type='artwork' WHERE e.scheme='wikidata' AND e.external_id=%s",(q,)).fetchone()
   if existing:deferred.append({'qid':q,'title':r.label(e),'reason':'existing_global_identity_preserved','existing':existing});continue
   accession=list(dict.fromkeys(v for v in r.values(e,'P217') if isinstance(v,str)));record={'qid':q,'title':r.label(e),'titles':r.labels(e),'date':date,'entity':e,'entity_receipt':receipts[q],'creator_qid':aq,'creator_label':r.label(artist),'creator_entity':artist,'creator_receipt':ar[aq],'collection':inst,'holding_statement':cols[0],'accession':accession[0] if len(accession)==1 else None,'images':r.values(e,'P18'),'existing_local':None,'selection_note':'Selected for Armenian/Georgian research through a documented collection statement. Museum identity checked independently; collection attribution remains in review, and no present display or museum masterpiece designation is asserted.'}
   selected.append(record)
 s.save(s.RUN/'selected/catalogue.json',{'selected':selected,'deferred':deferred,'metadata_inspected':len(ids),'at':s.core.now()});print('Selected',len(selected),'named painting records, deferred',len(deferred));print('Creators',collections.Counter(x['creator_label'] for x in selected));print('Institutions',collections.Counter(x['collection']['institution']['name'] for x in selected))
if __name__=='__main__':main()
