"""Compact complete comparison display; repeated leads retain explicit references."""
import gzip,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-fifteenth-minimum-20261008'
def load(n):return json.load(gzip.open(R/n,'rt'))
def main():
 lo,hi=map(int,sys.argv[1:3]);mode=sys.argv[3] if len(sys.argv)>3 else 'delta'
 fs=load('native-candidates-001.json.gz')['rows'];old=load('native-identity-001.json.gz')['comparisons'];new=load('native-identity-002.json.gz')['comparisons'];ctx={};seenout={}
 for p in load('physical-comparison-context-002.json.gz')['rows']:ctx.setdefault(p['existing_artwork_id'],[]).append(p['literal_primary_record'])
 for r,a,b in zip(fs,old,new):
  if not lo<=r['number']<=hi:continue
  f=r['facts'];seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in a[k]};leads={}
  for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits','object_alias_hits','related_inventory_hits']:
   for v in b[k]:
    if mode=='all' or v['id'] not in seen or k in ['object_alias_hits','related_inventory_hits']:leads[v['id']]=v
  if not leads:continue
  print('\n#',r['number'],f['title'],'|',f['creator_label'],'|',f['inventory'],'|',f['medium'],'|',f['dimensions_text'])
  repeated=[]
  for aid,v in sorted(leads.items()):
   if aid in seenout:repeated.append(seenout[aid]);continue
   ix=len(seenout)+1;seenout[aid]=ix
   if ctx.get(aid):
    for p in ctx[aid]:print(ix,aid,'|',' | '.join(str(p.get(k) or '') for k in ['Titre','Auteur','Numero_inventaire','Materiaux_techniques','Mesures','Millesime_de_creation','Periode_de_creation']))
   else:print(ix,aid,'|',' | '.join(str(v.get(k) or '') for k in ['title','unlinked_creator_label','creators','accession_number','medium_text','dimensions_text','date_display']))
  if repeated:print('Previously displayed comparator numbers:',','.join(map(str,repeated)))
if __name__=='__main__':main()
