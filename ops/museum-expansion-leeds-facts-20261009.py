"""Exact Leeds object facts; source collection qualifiers are never creation dates."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-leeds-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
one=s.one;val=s.val;qual=s.qual;statements=s.statements
def inventory(value):
 return value if re.fullmatch(r'LEEAG\.PA\.[A-Za-z0-9.]+',value or '') else None
def titlekey(value):return re.sub(r'[^\w]','',m.norm(re.sub(r'\s*\(\d{4}\s*[–-]\s*\d{4}\)','',value or '')))
def namekey(value):return sorted(m.norm(re.sub(r'\b(Sir|Dame|Lord|Lady)\b','',value or '',flags=re.I)).split())
def facts(r,initial):
 e=r['entity'];a=r['artwork'];issues=[];assert e['id']==r['source_id'];links=[v for v in initial['snapshot']['artists'] if v['artwork_id']==a['id']];painters={v['id']:v for v in initial['painters']};creator='; '.join(painters[v['artist_id']]['display_name'] for v in links) or a['unlinked_creator_label'] or '';creatorqid=val(e,'P170')['id'];authors={v['entity_id'] for v in initial['creator_authorities'] if v['scheme']=='wikidata' and v['external_id']==creatorqid}
 if len(links)!=1 or links[0]['attribution_role']!='primary' or authors!={links[0]['artist_id']}:issues.append('creator_authority_requires_reconciliation')
 if one(e,'P170').get('qualifiers'):issues.append('qualified_creator')
 assert a['current_institution_id'] is None and a['status']=='review' and a['published_at'] is None;assert val(e,'P31')['id']=='Q3305213' and not one(e,'P31').get('qualifiers');titles=sorted({v['value'] for v in e.get('labels',{}).values()}|{v['value'] for vs in e.get('aliases',{}).values() for v in vs})
 if m.norm(a['title']) not in {m.norm(v) for v in titles}:issues.append('literal_title_mismatch')
 related={p:statements(e,p) for p in ['P518','P361','P1877','P527','P144','P4969','P1639'] if statements(e,p)}
 if related:issues.append('related_version_component_or_pendant_requires_review')
 collections=statements(e,'P195');assert collections and {s.value(v)['id'] for v in collections}=={s.QID};collection=next((v for v in collections if s.references(v,'P1679')),collections[0]);sourceqid=s.QID
 for c in collections:
  if set(c.get('qualifiers',{}))-{'P580'}:issues.append('collection_qualification_requires_review')
  if 'P580' in c.get('qualifiers',{}):assert s.year(qual(c,'P580'))<=2026
 inv=one(e,'P217');invtext=s.value(inv);number=inventory(invtext);assert invtext==a['accession_number'] and number;assert set(inv.get('qualifiers',{}))=={'P195'} and qual(inv,'P195')['id'] in s.QIDS.values();artuk=val(e,'P1679');assert isinstance(artuk,str) and artuk
 if set(one(e,'P1679').get('qualifiers',{}))-{'P407'}:issues.append('artuk_id_qualification')
 matchedrefs=[v for v in collection.get('references',[]) if artuk in [n.get('datavalue',{}).get('value') for n in v['snaks'].get('P1679',[])] and 'Q105003187' in [n.get('datavalue',{}).get('value',{}).get('id') for n in v['snaks'].get('P248',[])]]
 if not matchedrefs:issues.append('missing_exact_artuk_collection_reference')
 dates=statements(e,'P571');source_dates=None
 if dates:
  try:source_dates=s.creation(one(e,'P571'))
  except AssertionError:issues.append('creation_qualifier_requires_review')
  if source_dates is not None and source_dates!=(a['creation_year_start'],a['creation_year_end'],a['date_precision']):issues.append('source_catalogue_date_mismatch')
 elif a['date_precision']!='unknown':issues.append('missing_source_date')
 filenames=[s.value(v) for v in statements(e,'P18')]
 if any(re.search(r'\b(?:after|attributed|circle|workshop|school|manner|copy|replica|follower|panels|triptych|study)\b',v,re.I) for v in filenames+[a['title']]):issues.append('filename_or_title_qualification')
 ids=[v for v in initial['snapshot']['identifiers'] if v['entity_id']==a['id'] and v['scheme']=='wikidata'];assert len(ids)==1 and ids[0]['external_id']==e['id'];native=r.get('native_object');nativeurls=[]
 if native:
  fields=native['fields'];assert fields['Category']==['Art'];assert len(fields['Catalogue number'])==1 and inventory(fields['Catalogue number'][0])==number
  if titlekey(a['title'])!=titlekey(native['title']):issues.append('native_title_difference')
  if len(fields.get('Creator',[]))!=1 or namekey(fields['Creator'][0])!=namekey(creator):issues.append('native_creator_name_difference')
  if fields.get('Production date',[])!=[a['date_display']]:issues.append('native_date_wording_difference')
  nativeurls=[native['url']]
 return dict(source_id=e['id'],source_url='https://www.wikidata.org/wiki/'+e['id'],title=a['title'],titles=titles,creator_label=creator,creator_qid=creatorqid,artist_links=links,inventory=invtext,normalized_inventory=number,date_display=a['date_display'],first=a['creation_year_start'],last=a['creation_year_end'],date_precision=a['date_precision'],source_creation_statements=dates,source_fields={'ATTRIBUZIONI':creator},native_page_urls=nativeurls,native_metadata_urls=[],artuk_id=artuk,artuk_url='https://artuk.org/discover/artworks/'+artuk,commons_filenames=filenames,source_collection_statements=collections,source_collection_qid=sourceqid,source_related_statements=related,museum_qid=s.QIDS[s.NETWORK],native_object=native,native_id=r.get('native_id'),issues=issues)
def rows():
 initial=m.load(RUN/'initial-scope-001.json.gz');out=[];errors=[]
 for r in m.load(RUN/'source-context-001.json.gz')['rows']:
  try:f=facts(r,initial);out.append(dict(number=r['number'],source_id=r['source_id'],source_institution_id=r['institution_id'],institution_id=s.NETWORK,existing_artwork_id=r['artwork']['id'],facts=f,issues=f['issues']))
  except Exception as e:errors.append(dict(number=r['number'],title=r['artwork']['title'],error=type(e).__name__+': '+str(e)))
 return out,errors
def main():
 dest=RUN/'candidate-facts-001.json.gz';assert not dest.exists();rs,errors=rows();m.save(dest,dict(at=m.now(),rows=rs,source_fact_holds=errors,source_reference=ref(RUN/'source-context-001.json.gz'),parser_reference=ref(Path(__file__).resolve()),read_only=True));print(json.dumps(dict(rows=len(rs),source_fact_holds=errors,issues=dict(collections.Counter(v for r in rs for v in r['issues'])))),flush=True)
if __name__=='__main__':main()
