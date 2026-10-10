"""Show every supplemental identity lead with preserved primary physical fields."""
import gzip,json,sys
from pathlib import Path
RUN=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-fifteenth-minimum-20261008'
def load(n):return json.load(gzip.open(RUN/n,'rt'))
def main():
 lo,hi=map(int,sys.argv[1:3]);mode=sys.argv[3] if len(sys.argv)>3 else 'delta'
 fs=load('native-candidates-001.json.gz')['rows'];old=load('native-identity-001.json.gz')['comparisons'];new=load('native-identity-002.json.gz')['comparisons'];ctx={}
 for p in load('physical-comparison-context-002.json.gz')['rows']:ctx.setdefault(p['existing_artwork_id'],[]).append(p['literal_primary_record'])
 for r,a,b in zip(fs,old,new):
  if not lo<=r['number']<=hi:continue
  f=r['facts'];seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in a[k]};leads={}
  for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits']:
   for v in b[k]:
    if mode=='all' or v['id'] not in seen or k in ['object_alias_hits','related_inventory_hits']:leads.setdefault(v['id'],[v,[]])[1].append(k)
  if not leads:continue
  print('\n#',r['number'],f['title'],'|',f['creator_label'],'|',f['date_display'],'|',f['inventory'],'|',f['medium'],'|',f['dimensions_text'])
  for aid,(v,kinds) in sorted(leads.items()):
   print('MATCH',aid,','.join(kinds),'|',v['title'],'|',','.join(v['creators']) or v.get('unlinked_creator_label'),'|',v['date_display'],'|',v['accession_number'],'|',v['medium_text'],'|',v['dimensions_text'])
   for p in ctx.get(aid,[]):print(' PRIMARY',' | '.join(str(p.get(k) or '') for k in ['Reference','Titre','Auteur','Numero_inventaire','Materiaux_techniques','Mesures','Millesime_de_creation','Periode_de_creation','Localisation']))
   if v.get('evidence'):print(' INVENTORY EVIDENCE',json.dumps(v['evidence'],ensure_ascii=False))
if __name__=='__main__':main()
