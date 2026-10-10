"""Reuse fresh4097-row snapshot; remove empty-title false positives, with no new SQL."""
import difflib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('base',Path(__file__).with_name('museum-expansion-rhodes-identity-20261009.py'));base=importlib.util.module_from_spec(z);z.loader.exec_module(base)
f=base.f;q=base.q;prod=base.prod;s=base.s;m=base.m;RUN=base.RUN

def comparisons(rows,state):
 cached=[(a,{v for v in [m.norm(a['title']),m.norm(a['alternate_title'])]if v})for a in state['artworks']];out=[]
 for row in rows:
  v=row['facts'];tt={m.norm(t)for t in v['titles']}|{m.norm(v['title'].split('[')[0])}|{m.norm(t)for t in re.findall(r'\[([^\]]+)\]',v['title'])};tt.discard('');assert tt;hits=[];urls=set(v['native_page_urls'])
  for a,at in cached:
   reasons=[];sim=0
   if tt&at:reasons.append('exact_title');sim=1
   if f.invkey(a['accession_number'])==f.invkey(v['inventory']):reasons.append('inventory')
   for t in tt:
    for u in at:
     matcher=difflib.SequenceMatcher(None,t,u)
     if matcher.real_quick_ratio()>=.8 and matcher.quick_ratio()>=.8:sim=max(sim,matcher.ratio())
   if sim>=.8:reasons.append('similar_title')
   if reasons:hits.append(dict(a,hit_types=reasons,same_museum=a['id']in state['scoped_ids'],title_similarity=round(sim,4)))
  sources=[c for c in state['source_hits']+state['external_hits']+state['native_id_hits']if(c.get('source_url')or c.get('canonical_url')or'').rstrip('/')in{u.rstrip('/')for u in urls}or c.get('external_id')in[row['source_id'],'TehnisRodou/000188-'+row['source_id']]]
  out.append(dict(number=row['number'],source_id=row['source_id'],hits=hits,source_hits=sources))
 return out
if __name__=='__main__':
 prior=m.load(RUN/'production-identity-001.json.gz');s.checked(prior['script_reference']);result=dict(prior);result.update(at=m.now(),comparisons=comparisons(prior['rows'],prior['state']),script_reference=s.ref(Path(__file__).resolve()),prior_identity_reference=s.ref(RUN/'production-identity-001.json.gz'),correction='Empty translated-title candidates and null alternate titles must never match. Fresh read-only SQL snapshot inherited unchanged. No production writes occurred.');m.save(RUN/'production-identity-002.json.gz',result);print(json.dumps(dict(artworks=len(result['state']['artworks']),comparisons=len(result['comparisons']),title_hits=sum(len(v['hits'])for v in result['comparisons']))),flush=True)
