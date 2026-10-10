"""Parse exact saved source statements without rewriting existing catalogue fields."""
import collections,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-britain-eight-source-20261009.py');w=module('w','museum-expansion-walker-holdings-20261007.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
one=w.one;val=w.val;qual=w.qualifier_value

def statements(e,p):return [v for v in e['claims'].get(p,[]) if v['rank']!='deprecated']
def references(v,p):return [snak['datavalue']['value'] for r in v.get('references',[]) for snak in r.get('snaks',{}).get(p,[]) if snak.get('snaktype')=='value']
def facts(r,initial):
 e=r['entity'];a=r['artwork'];iid=r['institution_id'];qid=r['museum_qid'];issues=[];links=[v for v in initial['snapshot']['artists'] if v['artwork_id']==a['id']];painters={v['id']:v for v in initial['painters']};creator='; '.join(painters[v['artist_id']]['display_name'] for v in links) or a['unlinked_creator_label'] or '';creatorqid=val(e,'P170')['id'];authors=[v for v in initial['creator_authorities'] if v['scheme']=='wikidata' and v['external_id']==creatorqid];authorids={v['entity_id'] for v in authors}
 if len(links)!=1 or links[0]['attribution_role']!='primary' or authorids!={links[0]['artist_id']}:issues.append('creator_authority_requires_reconciliation')
 if one(e,'P170').get('qualifiers'):issues.append('qualified_creator')
 assert e['id']==r['source_id']
 if a['current_institution_id'] is not None:issues.append('existing_institution_requires_review')
 if a['status']=='archived':issues.append('archived_record_excluded')
 elif a['status']!='review':issues.append('existing_nonreview_status_requires_review')
 titles=sorted({v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs})
 if m.norm(a['title']) not in {m.norm(v) for v in titles}:issues.append('literal_title_mismatch')
 assert val(e,'P31')['id']=='Q3305213' and not one(e,'P31').get('qualifiers')
 if any(statements(e,p) for p in ['P518','P361','P1877','P527']):issues.append('component_copy_or_aggregate')
 collections=statements(e,'P195');assert collections and {w.h.value(v)['id'] for v in collections}=={qid}
 for c in collections:
  assert not set(c.get('qualifiers',{}))-{'P580'}
  if c.get('qualifiers'):assert 100<=w.year(qual(c,'P580'))<=2026
 assert val(e,'P276')['id']==qid and not one(e,'P276').get('qualifiers');assert not statements(e,'P127')
 inv=one(e,'P217');assert set(inv.get('qualifiers',{}))=={'P195'} and qual(inv,'P195')['id']==qid;inventory=w.h.value(inv)
 if a['accession_number'] is None:issues.append('missing_catalogue_inventory')
 else:assert inventory==a['accession_number']
 assert re.fullmatch(r'\d+(?:/\d+)*',inventory) if qid=='Q7569107' else re.fullmatch(r'(?:CAC|HH)[A-Za-z0-9./-]+',inventory)
 artuk=val(e,'P1679') if statements(e,'P1679') else None
 if artuk:
  assert re.fullmatch(r'[a-z0-9-]+-\d+',artuk) and not one(e,'P1679').get('qualifiers');refs={v for c in collections for v in references(c,'P1679')};urls={v.split('#',1)[0] for c in collections for v in references(c,'P854')};assert refs=={artuk} or (not refs and urls=={'https://artuk.org/discover/artworks/'+artuk})
 else:issues.append('missing_exact_artuk_reference')
 date_statement=statements(e,'P571');source_dates=None
 if date_statement:
  try:source_dates=w.creation(one(e,'P571'))
  except AssertionError as err:
   if a['date_precision']!='unknown':issues.append('unreviewed_creation_qualifier:'+str(err))
  if source_dates is not None and source_dates!=(a['creation_year_start'],a['creation_year_end'],a['date_precision']):issues.append('source_catalogue_date_mismatch')
 elif a['date_precision']!='unknown':issues.append('missing_source_date')
 if a['creation_year_end'] is not None and a['creation_year_end']>1970:issues.append('post1970_catalogue_date')
 filenames=[w.h.value(v) for v in statements(e,'P18')];qualification=re.compile(r'\b(?:after|attributed|circle|workshop|school|manner|copy|replica|follower)\b',re.I)
 if any(qualification.search(v) for v in filenames+[a['title']]):issues.append('filename_or_title_qualification')
 ids=[v for v in initial['snapshot']['identifiers'] if v['entity_id']==a['id'] and v['scheme']=='wikidata'];assert len(ids)==1 and ids[0]['external_id']==e['id']
 return dict(source_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'],title=a['title'],titles=titles,creator_label=creator,creator_qid=creatorqid,artist_links=links,inventory=inventory,date_display=a['date_display'],first=a['creation_year_start'],last=a['creation_year_end'],date_precision=a['date_precision'],source_creation_statements=date_statement,source_fields={'ATTRIBUZIONI':creator},native_page_urls=['https://artuk.org/discover/artworks/'+artuk] if artuk else [],native_metadata_urls=[],artuk_id=artuk,commons_filenames=filenames,source_collection_statements=collections,museum_qid=qid,issues=issues)
def rows():
 initial=m.load(RUN/'initial-scope-001.json.gz');out=[]
 errors=[]
 for r in m.load(RUN/'source-context-001.json.gz')['rows']:
  try:
   f=facts(r,initial);out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=r['institution_id'],existing_artwork_id=r['artwork']['id'],facts=f,issues=f['issues']))
  except Exception as err:errors.append(dict(number=r['number'],title=r['artwork']['title'],error=type(err).__name__+': '+str(err)))
 if errors:raise AssertionError(json.dumps(errors,ensure_ascii=False))
 return out
def main():
 dest=RUN/'candidate-facts-001.json.gz';assert not dest.exists();rs=rows();m.save(dest,dict(at=m.now(),rows=rs,source_reference=ref(RUN/'source-context-001.json.gz'),parser_reference=ref(Path(__file__).resolve()),read_only=True));print(json.dumps(dict(rows=len(rs),issues=dict(collections.Counter(i for r in rs for i in r['issues'])))),flush=True)
if __name__=='__main__':main()
