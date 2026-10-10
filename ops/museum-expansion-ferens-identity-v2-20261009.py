"""Fresh bounded Ferens identity scope, including native accession aliases."""
import importlib.util,json,re
from pathlib import Path
def module(name,file):
 s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
f=module('f','museum-expansion-ferens-facts-20261009.py');i=module('i','museum-expansion-italy-fourth-identity-v2-20261008.py');m=f.m;RUN=f.RUN;ref=f.ref;IID=f.IID;i.RUN=RUN;i.q.RUN=RUN;i.IIDS=[IID];i.terms=i.q.search_terms
def creator_terms(facts):
 raw='; '.join(facts['native_fields'].get('Artist / Maker:',[])) or facts['creator_label'] or ''
 special={2:['beccafumi'],3:['stevens'],5:['stevens'],6:[],8:[],9:[],17:['helst'],25:['gysbrechts','gijsbrechts'],28:['canaletto'],29:[],30:[],38:['reynolds'],48:['wright'],50:['wilson'],57:['sartorius'],58:[],59:[],61:['romeyn','romyn'],66:[],67:['meyer'],68:[],69:[],70:[],72:[],73:[],74:[],75:[],76:['chinnery'],85:['sartorius'],125:['roberts'],193:[]}
 number=NUMBER_BY_SOURCE[facts['source_id']]
 if number in special:return special[number]
 surname=raw.split(',')[0] if ',' in raw else raw
 surname=re.sub(r'\([^)]*\)|\b(?:the|elder|younger|senior|junior|unknown|artist|sir|attributed|follower|of|school)\b',' ',surname,flags=re.I)
 out={t for t in m.norm(surname).split() if len(t)>=3}
 aliases={'gheeraerdts':['gheeraerts'],'le':['leprince'],'prince':['leprince'],'l':['laubiniere'],'aubiniere':['laubiniere'],'mccallum':['maccallum'],'santa':['santacroce'],'croce':['santacroce'],'bakhuizen':['backhuysen','backhuyzen']}
 for t in list(out):out.update(aliases.get(t,[]))
 return sorted(out)
NUMBER_BY_SOURCE={r['source_id']:r['number'] for r in m.load(RUN/'native-candidates-001.json.gz')['rows']}
i.terms=creator_terms
def params_for(rows):
 p=i.params_for(rows);invs=set(p['inventories'])
 for r in rows:
  for inv in [r['facts']['inventory']]+r['facts']['inventory_aliases']:
   invs.add(inv);invs.add(inv.removeprefix('KINCM:'))
 p['inventories']=sorted(invs);return p
queries=i.queries
def main():
 dest=RUN/'native-identity-001.json.gz';assert not dest.exists();candidate=RUN/'native-candidates-001.json.gz';rows=m.load(candidate)['rows'];p=params_for(rows)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on';state=queries(db,p)
  citations=[r['row'] for r in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 print(json.dumps(dict(query_counts={k:len(v) for k,v in state.items()},citations=len(citations))),flush=True)
 comps=i.comparisons(rows,state)
 # Prefix normalization is comparison-only. Native accession suffixes and old numbers remain intact.
 for r,c in zip(rows,comps):
  invs={i.q.compact(v.removeprefix('KINCM:')) for v in [r['facts']['inventory']]+r['facts']['inventory_aliases']}
  c['accession_alias_hits']=[a for a in state['artworks'] if a['accession_number'] and i.q.compact(a['accession_number'].removeprefix('KINCM:')) in invs]
 m.save(dest,dict(at=m.now(),candidate_reference=ref(candidate),params=p,state=state,comparisons=comps,within_batch=i.within_batch(rows),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='All180 source records including holds compared. Full current museum scope plus bounded maker/alias/title/inventory/native-source queries. Old accession numbers and KINCM prefix forms included. Scores are leads; physical identity needs editorial review.'))
 m.save(RUN/'identity-citations-001.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=citations,read_only=True));print(json.dumps(dict(comparisons=len(comps),hit_pairs=sum(len(c['hits']) for c in comps),alias_hits=sum(len(c['accession_alias_hits']) for c in comps))),flush=True)
if __name__=='__main__':main()
