#!/usr/bin/env python3
"""Read-only Thyssen title,creator,accession and native-source identity comparisons."""
import argparse,collections,difflib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-thyssen-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;IID=f.d.IID
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-yale-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);i.RUN=RUN;i.IID=IID
def inventory_parts(raw):
 return {i.compact(v) for v in re.split(r'[();]',raw or '') if v.strip()}
def params(rows):
 p=i.params_for(rows);p['inventories']=sorted(set(p['inventories'])|{x for row in rows for x in row['facts']['inventory_fields'] if x})
 heads={name.split(',',1)[0].strip() for row in rows for name in row['facts']['identity_creator_labels'] if name}
 terms={term for name in heads for term in i.search_terms(dict(creator_label=name))}
 full={row['facts']['creator_label'] for row in rows if row['facts']['creator_label']}
 p['patterns']=sorted({'%'+term+'%' for term in terms}|{'%'+m.norm(name)+'%' for name in heads|full})
 p['raw_patterns']=sorted({'%'+name.lower()+'%' for name in heads|full})
 p['native_identifiers']=sorted({x for row in rows for x in [row['facts']['inventory'],row['source_id']]+row['facts']['inventory_fields'] if x})
 return p
def queries(db,p):
 # Reuse the reviewed artist/alias-scoped ID query. Supplemental native IDs
 # are queried only against institution-specific identifier namespaces.
 state=i.queries(db,p)
 extra=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND scheme IN ('european-thyssen-object','thyssen-object','museum-expansion-thyssen-object') AND external_id=ANY(%s) ORDER BY entity_id,scheme,external_id",(p['native_identifiers'],)).fetchall()
 extraids=sorted({x['entity_id'] for x in extra}-set(state['artwork_ids']))
 if extraids:
  arts=db.execute('SELECT '+i.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(extraids,)).fetchall()
  links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(extraids,)).fetchall()
  state['artworks']=sorted(state['artworks']+arts,key=lambda r:r['id']);state['links']=sorted(state['links']+links,key=lambda r:(r['artwork_id'],r['artist_id']));state['artwork_ids']=sorted(set(state['artwork_ids'])|set(extraids))
 for row in extra:
  if row not in state['external_hits']:state['external_hits'].append(row)
 state['external_hits']=sorted(state['external_hits'],key=lambda r:(r['entity_id'],r['scheme'],r['external_id']))
 return state
def comparisons(rows,state):
 broad=i.comparisons(rows,state);links=collections.defaultdict(list)
 for a in state['links']:links[a['artwork_id']].append(a)
 out=[]
 for row,cmp in zip(rows,broad):
  v=row['facts'];names={m.norm(x) for x in [v['creator_label']]+v['identity_creator_labels'] if x}
  # Reversed surname-first labels are explicit source forms, not invented
  # authorities. Parenthetical aliases stay available in the broad review.
  names|={m.norm(' '.join(reversed(x.split(', ',1)))) for x in v['identity_creator_labels'] if ', ' in x}
  names|={m.norm(x.split(' (',1)[0]) for x in [v['creator_label']]+v['identity_creator_labels'] if x}
  if 'rembrandt' in i.tokens(v['creator_label']):names|={'rembrandt','rembrandt van rijn'}
  ids={a['id'] for a in state['artists'] if m.norm(a['display_name']) in names}|{a['artist_id'] for a in state['aliases'] if m.norm(a['alias']) in names}
  pool=[];inventory_leads=[];source_parts=inventory_parts(v['inventory'])|{i.compact(x) for x in v['inventory_fields']}
  for art in state['artworks']:
   exact_creator=bool(ids&{a['artist_id'] for a in links[art['id']]}) or m.norm(art['unlinked_creator_label']) in names
   if exact_creator:
    score=max((difflib.SequenceMatcher(None,m.norm(t),m.norm(art[k])).ratio() for t in v['titles'] for k in ['title','alternate_title'] if art.get(k)),default=0)
    pool.append(dict(art,artist_links=links[art['id']],title_similarity=score))
   if source_parts&inventory_parts(art['accession_number']):
    inventory_leads.append(dict(art,artist_links=links[art['id']],matching_inventory_parts=sorted(source_parts&inventory_parts(art['accession_number'])),relevant=exact_creator or art['current_institution_id']==IID))
  native=[a for a in state['external_hits'] if a['scheme'] in ['european-thyssen-object','thyssen-object','museum-expansion-thyssen-object'] and a['external_id'] in [v['inventory'],row['source_id']]+v['inventory_fields']]
  out.append(dict(cmp,focused_creator_ids=sorted(ids),focused_pool_ids=[a['id'] for a in pool],focused_top=sorted(pool,key=lambda a:a['title_similarity'],reverse=True)[:20],inventory_component_hits=inventory_leads,institution_native_id_hits=native))
 return out
def main(suffix,candidate_suffix):
 source=RUN/('native-candidates-'+candidate_suffix+'.json.gz');rows=[r for r in m.load(source)['rows'] if r['state']!='capture_hold'];p=params(rows)
 with m.connect() as db:state=queries(db,p)
 dest=RUN/('identity-scope-'+suffix+'.json.gz');m.save(dest,dict(at=m.now(),params=p,state=state,rows=rows,candidate_reference=f.ref(source),policy='Read-only bounded creator/alias,exact-title,inventory and native-identifier discovery. Similarity/shared inventory numbers are leads,not identity approval.'))
 cm=comparisons(rows,state);m.save(RUN/('identity-comparisons-'+suffix+'.json.gz'),dict(at=m.now(),records=cm,scope_reference=f.ref(dest),policy='Both broad surname and focused full-name scopes retained. Language-specific source URLs and native identifier namespaces included.'))
 print(json.dumps(dict(rows=len(rows),counts={k:len(v) for k,v in state.items()})),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);p.add_argument('--candidates',required=True);a=p.parse_args();main(a.suffix,a.candidates)
