#!/usr/bin/env python3
"""Read-only creator, source-ID, native-reference, title and inventory comparisons for Hamburg."""
import importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-hamburg-facts2-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;IID=f.d.IID
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-yale-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);i.RUN=RUN;i.IID=IID

def rows():
 labels={**f.f.sources('wikidata-creator-capture-001.json.gz'),**f.f.sources('wikidata-extra-label-capture-002.json.gz')};out=[]
 for r in m.load(RUN/'wikidata-candidates-002.json.gz')['rows']:
  if r['state']!='candidate':continue
  v=dict(r['facts']);cr=labels[v['creator_qid']]['entity'];v['identity_creator_labels']=[x['value'] for k,x in cr.get('labels',{}).items() if k in ['en','de','mul','fr','it','nl']]
  v.update(native_object_id='',wikidata_ids=[r['source_id']],native_metadata_urls=[])
  out.append(dict(source_id=r['source_id'],facts=v,source_reference=r['source_reference'],kind='wikidata_candidate'))
 for r in m.load(RUN/'main-site-leads-001.json.gz')['rows']:
  sid='caption-%03d'%r['lead_number']
  v=dict(source_id=sid,title=r['title'],titles=[r['title']],creator_label=r['creator_label'],identity_creator_labels=[],inventory=None,source_url=r['source_url'],native_page_urls=[],native_metadata_urls=[],native_object_id='',wikidata_ids=[],date_display=r['date_display'])
  out.append(dict(source_id=sid,facts=v,source_reference=r['source_reference'],kind='official_caption'))
 assert len(out)==166;return out

def main():
 rs=rows();params=i.params_for(rs);qids=sorted({r['facts']['creator_qid'] for r in rs if r['kind']=='wikidata_candidate'})
 with m.connect() as db:
  authorities=db.execute("SELECT ei.entity_id::text,ei.external_id,a.display_name FROM external_identifiers ei JOIN artists a ON a.id=ei.entity_id WHERE ei.entity_type='artist' AND ei.scheme='wikidata' AND ei.external_id=ANY(%s) ORDER BY ei.external_id,ei.entity_id",(qids,)).fetchall()
  # Include known database authority spellings in the scoped surname search.
  extra={t for a in authorities for t in i.search_terms(dict(creator_label=a['display_name']))}
  params['patterns']=sorted(set(params['patterns'])|{'%'+t+'%' for t in extra})
  params['raw_patterns']=sorted(set(params['patterns'])|{'%'+a['display_name'].lower()+'%' for a in authorities})
  state=i.queries(db,params)
  assert {a['entity_id'] for a in authorities}<=set(state['artist_ids'])
 m.save(RUN/'identity-scope-001.json.gz',dict(at=m.now(),params=params,state=state,creator_authorities=authorities,rows=rs,policy='Read-only identity discovery. Existing creators mapped through authorities and bounded names; artworks then scoped by returned artist IDs, explicit source IDs, titles, inventories and URLs. Shared official caption-page URLs are contextual leads, never proof of one artwork identity.'))
 print(json.dumps({k:len(v) for k,v in state.items()}),flush=True)
 comparisons=i.comparisons(rs,state)
 m.save(RUN/'identity-comparisons-001.json.gz',dict(at=m.now(),records=comparisons,scope_reference=f.ref(RUN/'identity-scope-001.json.gz'),policy='Similarity and shared caption pages are leads requiring object/version review. No inferred artist links or import decisions.'))
 print('comparisons',len(comparisons),flush=True)

if __name__=='__main__':main()
