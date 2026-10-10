"""Selected further MBP object details; bounded types and no image download."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-mbp-more-national-source-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);s=n.s;m=n.m;RUN=n.RUN
def main():
 discovery=m.load(RUN/'national-discovery-001.json.gz');first=[];prints=[];other=[]
 preferred={'Portable icon','Bilateral icon','Triptych','Altarscreen door','Labarum (liturgical textile)','Wallpainting','Wall mosaic','Floor mosaic','Mosaic','Painting','Double-sided panel','Corinthian capital','Capital','Colonette'}
 printtypes={'Etching','Engraving','Lithograph','Xylography','Chromolithograph','Overpainted etching','Overpainted lithograph','Colour etching'}
 for number,v in enumerate(discovery['rows'],201):
  types={t.get('en')for t in v.get('types')or[]};pair=(number,v)
  (first if types&preferred else prints if types&printtypes else other).append(pair)
 chosen=first+prints[:max(0,120-len(first))];chosen.sort();assert len(chosen)<=120;ids={v['recordId']for _,v in chosen}
 selection=dict(source_reference=s.s.ref(RUN/'national-discovery-001.json.gz'),selected_ids=[v['recordId']for _,v in chosen],discovery_numbers={str(v['recordId']):number for number,v in chosen},deferred_ids=[v['recordId']for v in discovery['rows']if v['recordId']not in ids],policy='At most120 further metadata objects. Prioritize portable icons and inventoried wall art, then a bounded print selection. Individual date,group,edition and duplicate review required; modern works are source leads,not automatic additions.')
 dest=RUN/'national-selection-001.json'
 if dest.exists():assert m.load(dest)==selection
 else:m.save(dest,selection)
 out=[]
 for number,v in chosen:
  raw,rc=s.src.capture('national-object-'+str(v['recordId'])+'-001',n.NA+'/portal-api/exhibits/'+str(v['recordId']));r=json.loads(raw);assert r['recordId']==v['recordId']and r['storeLocation']['name']['gr']==n.LABEL
  out.append(dict(number=number,raw=r,receipt=rc));print(json.dumps(dict(number=number,progress=len(out),total=len(chosen),id=r['recordId'],title=r['title'].get('en'),first=r.get('start'),last=r.get('end'))),flush=True)
 m.save(RUN/'national-details-001.json.gz',dict(at=m.now(),rows=out,selection_reference=s.s.ref(dest),policy='Selected individual Ministry metadata; original titles,descriptions,dates,identifiers and rights retained. No images downloaded.'))
if __name__=='__main__':main()
