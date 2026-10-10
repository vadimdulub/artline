"""Exact saved Royal Collection statements; retain reference age and unknowns."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-royal-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
one=s.one;val=s.val;qual=s.qual;statements=s.statements
def rcin(value):
 hit=re.fullmatch(r'(?:RCIN\s+)?(\d{1,8})',value or '',re.I);return hit[1] if hit else None
def facts(r,initial):
 e=r['entity'];a=r['artwork'];issues=[];assert e['id']==r['source_id'];links=[v for v in initial['snapshot']['artists'] if v['artwork_id']==a['id']];painters={v['id']:v for v in initial['painters']};creator='; '.join(painters[v['artist_id']]['display_name'] for v in links) or a['unlinked_creator_label'] or '';creatorqid=val(e,'P170')['id'];authors={v['entity_id'] for v in initial['creator_authorities'] if v['scheme']=='wikidata' and v['external_id']==creatorqid}
 if len(links)!=1 or links[0]['attribution_role']!='primary' or authors!={links[0]['artist_id']}:issues.append('creator_authority_requires_reconciliation')
 if one(e,'P170').get('qualifiers'):issues.append('qualified_creator')
 assert a['current_institution_id'] is None and a['status']=='review' and a['published_at'] is None;assert val(e,'P31')['id']=='Q3305213' and not one(e,'P31').get('qualifiers');titles=sorted({v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs})
 if m.norm(a['title']) not in {m.norm(v) for v in titles}:issues.append('literal_title_mismatch')
 related={p:statements(e,p) for p in ['P518','P361','P1877','P527','P144','P4969','P1639'] if statements(e,p)}
 if related:issues.append('related_version_component_or_pendant_requires_review')
 collection=one(e,'P195');assert s.value(collection)['id']==s.QID and not collection.get('qualifiers');assert val(e,'P276')['id']==s.QID and not one(e,'P276').get('qualifiers')
 inventory=val(e,'P217') if statements(e,'P217') else None;number=rcin(inventory)
 if inventory:
  inv=one(e,'P217');assert set(inv.get('qualifiers',{}))=={'P195'} and qual(inv,'P195')['id']==s.QID;assert inventory==a['accession_number'] and number
 else:assert a['accession_number'] is None;issues.append('missing_inventory')
 native=val(e,'P11057') if statements(e,'P11057') else None
 if native:
  assert re.fullmatch(r'\d{1,8}',native);assert not set(one(e,'P11057').get('qualifiers',{}))-{'P407'}
  if native!=number:issues.append('native_id_inventory_conflict')
 else:issues.append('missing_nondeprecated_native_id')
 refs=s.references(collection,'P854');nativeurls=[u for u in refs if re.fullmatch(r'https?://(?:www\.)?(?:royalcollection\.org\.uk|rct\.uk)/collection/'+re.escape(number or 'MISSING')+r'(?:/[^?#]*)?/?',u)]
 if not nativeurls:issues.append('missing_exact_native_object_collection_reference')
 dates=statements(e,'P571');source_dates=None
 if dates:
  try:source_dates=s.creation(one(e,'P571'))
  except AssertionError:issues.append('creation_qualifier_requires_review')
  if source_dates is not None and source_dates!=(a['creation_year_start'],a['creation_year_end'],a['date_precision']):issues.append('source_catalogue_date_mismatch')
 elif a['date_precision']!='unknown':issues.append('missing_source_date')
 filenames=[s.value(v) for v in statements(e,'P18')]
 if any(re.search(r'\b(?:after|attributed|circle|workshop|school|manner|copy|replica|follower|panels|triptych)\b',v,re.I) for v in filenames+[a['title']]):issues.append('filename_or_title_qualification')
 ids=[v for v in initial['snapshot']['identifiers'] if v['entity_id']==a['id'] and v['scheme']=='wikidata'];assert len(ids)==1 and ids[0]['external_id']==e['id']
 return dict(source_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'],title=a['title'],titles=titles,creator_label=creator,creator_qid=creatorqid,artist_links=links,inventory=inventory,rcin=number,native_object_id=native,date_display=a['date_display'],first=a['creation_year_start'],last=a['creation_year_end'],date_precision=a['date_precision'],source_creation_statements=dates,source_fields={'ATTRIBUZIONI':creator},native_page_urls=sorted(set(nativeurls)),native_metadata_urls=[],commons_filenames=filenames,source_collection_statements=[collection],source_owner_statements=statements(e,'P127'),source_related_statements=related,museum_qid=s.QID,issues=issues)
def rows():
 initial=m.load(RUN/'initial-scope-001.json.gz');out=[];errors=[]
 for r in m.load(RUN/'source-context-001.json.gz')['rows']:
  try:f=facts(r,initial);out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=s.IID,existing_artwork_id=r['artwork']['id'],facts=f,issues=f['issues']))
  except Exception as e:errors.append(dict(number=r['number'],title=r['artwork']['title'],error=type(e).__name__+': '+str(e)))
 return out,errors
def main():
 dest=RUN/'candidate-facts-001.json.gz';assert not dest.exists();rs,errors=rows();m.save(dest,dict(at=m.now(),rows=rs,source_fact_holds=errors,source_reference=ref(RUN/'source-context-001.json.gz'),parser_reference=ref(Path(__file__).resolve()),read_only=True));print(json.dumps(dict(rows=len(rs),source_fact_holds=errors,issues=dict(collections.Counter(v for r in rs for v in r['issues'])))),flush=True)
if __name__=='__main__':main()
