"""Read-only display of frozen source facts and physical-object comparison leads."""
import gzip,json,sys
from pathlib import Path
RUN=Path(__file__).resolve().parent.parent/'docs/research/museum-expansion-20261006/native/france-sixth-minimum-20261008'
def load(p):return json.load(gzip.open(p,'rt'))
fs=load(RUN/'native-candidates-001.json.gz')['rows'];ix=load(RUN/'native-identity-001.json.gz')
def short(a):return {k:a.get(k) for k in ['id','title','creators','unlinked_creator_label','medium_text','dimensions_text','date_display','accession_number']}
def main():
    lo,hi=map(int,sys.argv[1:3])
    for r,c in zip(fs,ix['comparisons']):
        if not lo<=r['number']<=hi:continue
        f=r['facts'];d=f['source_fields'];print('\n#',r['number'],f['source_id'],f['title'],'|',f['creator_label'],'|',f['date_display'],'|',f['inventory'],'|',f['work_type'],'|',f['medium'],'|',f['dimensions_text'])
        for k in ['Denomination','Description','Precisions_sujets_representes','Genese','Historique','Precisions_inscriptions','Commentaires','Ancienne_attribution','Periode_de_l_original_copie']:
            if d.get(k):print(k+':',d[k])
        print('POOL',len(c['creator_pool_ids']),'EXACT',len(c['exact_title_hits']),'INV',len(c['inventory_hits']))
        for a in c['leads'][:4]:
            if a['title_similarity']>=.48:print('LEAD',json.dumps(short(a),ensure_ascii=False))
        for a in c['exact_title_hits']:
            if a['id'] in c['creator_pool_ids']:continue
            if len(c['exact_title_hits'])>8 and (a['creators'] or a['unlinked_creator_label']) and 'anonyme' not in (a['unlinked_creator_label'] or '').lower():continue
            print('EXACT',json.dumps(short(a),ensure_ascii=False))
        for a in c['inventory_hits']:
            if a['relevant']:print('INV',json.dumps(short(a),ensure_ascii=False))
if __name__=='__main__':main()
