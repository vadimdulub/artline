#!/usr/bin/env python3
import argparse,importlib.util,os,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('deep',Path(__file__).with_name('museums-exactly-one-deep-20261008.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
m=x.m;d=x.d;m.AUTHORITY_NAMES=['Brigham Young University Museum of Art','Broad Art Museum','Frances Lehman Loeb Art Center','Fukuoka Art Museum','Hammer Museum','Herbert F. Johnson Museum of Art','Hirshhorn Museum and Sculpture Garden','Kasama Nichido Museum of Art','Louisiana Museum of Modern Art','Magritte Museum','Musée Angladon','Musée Maillol','Musée Zervos','Musée des beaux-arts de La Chaux-de-Fonds','Museo Botero','Museo Luigi Bailo','Museum of Fine Arts of Uzbekistan','Museum of Deinze and the Leie region','Museum of Modern and Contemporary Art of Trento and Rovereto','National Museum in Gdańsk','National Museum of African Art','Phoenix Art Museum','Philbrook Museum of Art','Rose Art Museum','Royal Pavilion','Sree Chitra Art Gallery','Teylers Museum','Wawel Castle','Residenzgalerie']

CROSSWALK={
'Q4967319':'Brigham Young University','Q5360357':'Broad MSU','Q5478803':'Frances Lehman','Q3073273':'Fukuoka Art','Q677561':'Hammer Museum','Q5734055':'Herbert F. Johnson','Q1620553':'Hirshhorn','Q11599987':'Kasama Nichido','Q1410617':'Louisiana','Q943581':'Magritte','Q3329052':'Musée Angladon','Q946883':'Musee Maillol','Q3329394':'Musée Zervos','Q3330204':'Musée des Beaux-Arts de La Chaux','Q3329100':'Museo Botero','Q642603':'Museum of Modern and Contemporary Art of Trento','Q1968661':'National Museum, Gdańsk','Q46812':'National Museum of African','Q977015':'Phoenix Art','Q7367636':'Rose Art','Q62364':'Royal Pavilion','Q7585629':'Sree Chitra','Q474563':'Teylers','Q18820':'Wawel','Q1248553':'Residenzgalerie'}
# Philbrook was already exhaustively indexed in round 3 (no additional referenced
# eligible collection claims). Keep that result; don't repeat its requests.
def prepare():
 n=m.r.wd_module();search=d.load(x.RUN/'museum-authority-search.json');base=d.load(x.RUN/'baseline.json.gz')['selected'];allinst=d.load(x.RUN/'all-institution-authorities.json.gz');full=n.entities(list(CROSSWALK));selected=[];held=[]
 for q,prefix in CROSSWALK.items():
  matches=[b['institution'] for b in base if b['institution']['name'].startswith(prefix)];assert len(matches)==1,(q,prefix)
  museum=matches[0];result=next(v for v in search if v['results'] and v['results'][0]['id']==q)
  conflict=[r['institution']for r in allinst if r['institution']['wikidata_id']==q and r['institution']['id']!=museum['id']]
  if conflict:held.append(dict(qid=q,museum=museum,reason='duplicate_authority_requires_review',conflicts=conflict));continue
  assert museum['wikidata_id']in [None,q]
  entity=full[q]['entity'];assert result['results'][0]['label']in {v['value']for v in entity['labels'].values()}
  selected.append(dict(museum=dict(museum,wikidata_id=q),catalogue_institution=museum,authority=full[q],search=result,projected_count=1,cursor='',page_number=1,confidence_basis='Individually reviewed full museum name, city/country context and Wikidata institution description/official website. Research-only authority reconciliation; catalogue institution metadata is preserved.'))
  print(museum['name'],q,[n.w.value(v) for v in n.w.active(entity,'P856')],flush=True)
 d.save(x.RUN/'reviewed-museum-authorities.json.gz',selected);d.save(x.RUN/'museum-authority-holds.json',held)
def research():m.authority_research()
def resume_research():
 n=m.r.wd_module();wave='missing-authorities-resumed';selected=d.load(x.RUN/'reviewed-museum-authorities.json.gz');d.save(n.ROOT/wave/'selected-museums.json',selected)
 n.research(wave,len(selected),target_count=25)
 source=d.load(x.RUN/'waves'/wave/'source-verified.json.gz');byid={r['museum']['id']:r for r in selected}
 rows=[dict(r,museum=byid[r['museum']['id']]['catalogue_institution'],raw_source_record=dict(r['raw_source_record'],museum_authority=byid[r['museum']['id']]))for r in source['records']]
 n.c.prepare_wave('missing-authorities-reviewed',rows,source['held'])

def saved_index_metadata():
 # The SPARQL host returned 429 again after its documented backoff. Stop that
 # host. Review only already-captured successful museum indexes through the
 # independent public entity API; no replacement index endpoint is used.
 n=m.r.wd_module();saved=d.load(n.ROOT/'missing-authorities/index-evidence.json.gz');candidates=[];held=list(saved['held'])
 authorities={r['museum']['id']:r for r in d.load(x.RUN/'reviewed-museum-authorities.json.gz')}
 for ev in saved['evidence']:
  raw,rc=n.checked_capture(ev['receipt']);assert rc['status']==200
  for q in ev['selected_ids']:candidates.append(dict(qid=q,museum=ev['museum'],index_receipt=rc))
 with d.connect()as db:
  known=set()
  for part in d.chunks([r['qid']for r in candidates],400):known.update(r['external_id']for r in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(part,)))
 selected=[r for r in candidates if r['qid']not in known];d.save(n.ROOT/'saved-index-metadata/selected-new-object-ids.json',selected)
 entities=n.entities([r['qid']for r in selected]);creatorids={n.w.value(claim)['id']for r in entities.values()for claim in n.w.active(r['entity'],'P170')if isinstance(n.w.value(claim),dict)}
 artists=n.entities(creatorids);creators={q:r['entity']for q,r in artists.items()};d.save(n.ROOT/'saved-index-metadata/creator-evidence.json.gz',artists);ready=[]
 for c in selected:
  q=c['qid'];source=entities[q];facts,reason=n.fields(source['entity'],c['museum'],creators,source['receipt'])
  if reason:held.append(dict(qid=q,museum_id=c['museum']['id'],reason=reason));continue
  artistids=[n.w.value(v)['id']for v in n.w.active(source['entity'],'P170')];auth=authorities[c['museum']['id']]
  ready.append(dict(artwork_id=d.uid('wikidata-new/'+q),slug=x.OP+'-wikidata-'+q.lower(),source_record_id=q,provider='wikidata-catalogue',origin='verified_native_entity',museum=auth['catalogue_institution'],facts=facts,alternate_native_urls=n.native_urls(source['entity']),source_receipt=source['receipt'],body_path=source['receipt']['body_path'],raw_source_record=dict(entity=source['entity'],creators={i:artists[i]for i in artistids},index_receipt=c['index_receipt'],museum_authority=auth)))
 n.c.prepare_wave('missing-authorities-reviewed',ready,held)
def plan():m.plan()
def identity():m.identity_review()
def apply():m.configure('wikidata-reviewed').apply()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args();(getattr(m,a.phase)if a.phase=='authority_search'else globals()[a.phase])()
