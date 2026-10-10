"""Display all new comparison leads, grouped by existing artwork to avoid repeated output."""
import gzip,json,runpy,sys
from pathlib import Path
RUN=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-fourteenth-minimum-20261008'
def load(n):return json.load(gzip.open(RUN/n,'rt'))
def main():
    lo,hi=map(int,sys.argv[1:3]);rows=load('native-candidates-001.json.gz')['rows'];old=load('native-identity-001.json.gz')['comparisons'];new=load('native-identity-002.json.gz')['comparisons'];notes=runpy.run_path(str(RUN/'working-notes-through-605-003.py'));arts={}
    for r,o,c in zip(rows,old,new):
        n=r['number']
        if not lo<=n<=hi or n not in notes['NOTES']:continue
        seen={v['id'] for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits'] for v in o[k]};delta={}
        for k in ['leads','exact_title_hits','inventory_hits','untitled_creator_hits','lexical_hits']:
            for v in c[k]:
                if v['id'] not in seen:
                    delta.setdefault(v['id'],[]).append(k)
                    arts[v['id']]=v
        if delta:print('CANDIDATE',n,r['facts']['title'],'|',r['facts']['creator_label'],'|',r['facts']['medium'],'|',json.dumps(delta,ensure_ascii=False))
    for aid,a in sorted(arts.items()):print('ART',json.dumps({k:a.get(k) for k in ['id','title','alternate_title','creators','unlinked_creator_label','medium_text','dimensions_text','date_display','accession_number']},ensure_ascii=False))
if __name__=='__main__':main()
