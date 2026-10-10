"""Read-only compact supplemental comparison display; no decisions inferred."""
import gzip,json,runpy,sys
from pathlib import Path
RUN=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-fourteenth-minimum-20261008'
def load(n):return json.load(gzip.open(RUN/n,'rt'))
def main():
    lo,hi=map(int,sys.argv[1:3]);rows=load('native-candidates-001.json.gz')['rows'];old=load('native-identity-001.json.gz')['comparisons'];new=load('native-identity-002.json.gz')['comparisons'];notes=runpy.run_path(str(RUN/'working-notes-through-605-003.py'));arts={}
    primary={r['existing_artwork_id']:r for r in load('physical-comparison-context-002.json.gz')['rows']}
    for r,o,c in zip(rows,old,new):
        n=r['number']
        if not lo<=n<=hi or n not in notes['NOTES']:continue
        seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in o[k]};delta={}
        for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits']:
            for v in c[k]:
                if v['id'] not in seen:delta.setdefault(v['id'],[]).append(k);arts[v['id']]=v
        if delta:print('C',n,r['facts']['title'],'|',r['facts']['creator_label'],'|',r['facts']['medium'],'|',','.join(x[:8] for x in delta))
    for aid,a in sorted(arts.items()):
        p=primary.get(aid,{}).get('literal_primary_record',{})
        print('A',aid[:8],a['title'],'|',';'.join(a.get('creators') or []) or a.get('unlinked_creator_label'),'|',a.get('medium_text') or p.get('Materiaux_techniques'),'|',a.get('dimensions_text') or p.get('Mesures'),'|',a.get('date_display'),'|',a.get('accession_number') or p.get('Numero_inventaire'))
if __name__=='__main__':main()
