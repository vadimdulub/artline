"""Select eighty further Vicenza drawings after bound-album holds; no writes."""
import copy,csv,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-italy-fourth-discovery-20261008.py'));d=importlib.util.module_from_spec(z);z.loader.exec_module(d)
def main():
 src=d.RUN/'five-museum-discovery-001.json.gz';x=copy.deepcopy(d.m.load(src));known={v['index_record']['source_record_id'] for v in x['rows']};t=next(v for v in x['targets'] if v['slug']=='arco-museum-d8786290e15dec21891a');pool=[]
 for v in csv.DictReader(open(d.checked(x['source_reference']))):
  dt=d.arco.numeric_date(v['source_creation_range'])
  if v['museum_slug']==t['slug'] and v['source_record_id'] not in known and re.fullmatch(r'HistoricOrArtisticProperty/\d+',v['source_record_id']) and dt and 1800<=dt[0]<=dt[1]<=1970:pool.append((dt,v))
 chosen=sorted(pool,key=lambda v:(v[0][1]-v[0][0],v[1]['source_record_id']))[:80];assert len(chosen)==80
 for dt,v in chosen:x['rows'].append(dict(number=len(x['rows'])+1,institution_id=t['institution_id'],museum={k:t[k] for k in ['institution_id','name','slug']},index_record=v,authority_candidates=t['authorities'],state='selected_for_source_research_only'))
 x.update(at=d.m.now(),prior_reference=d.ref(src),selector_reference=d.ref(Path(__file__).resolve()),supplement_reason='Initial Vicenza notices mostly represent bound albums/series and are held pending physical-leaf identity. Select80 additional explicitly1800–1970 numeric-ID drawings, shortest source date ranges first. Numeric IDs and narrow dates do not prove distinct physical sheets; fresh object/category/identity review still required.',supplement_numbers=list(range(619,699)))
 d.m.save(d.RUN/'five-museum-discovery-002.json.gz',x);print(json.dumps(dict(selected=len(x['rows']),supplement=80,pool=len(pool))))
if __name__=='__main__':main()
