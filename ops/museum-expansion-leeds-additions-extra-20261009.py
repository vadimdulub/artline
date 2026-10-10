"""Ten selected dated drawing leads from the already captured public discovery page."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('o',Path(__file__).with_name('museum-expansion-leeds-additions-objects-20261009.py'));o=importlib.util.module_from_spec(z);z.loader.exec_module(o);n=o.n;m=o.m;RUN=o.RUN;ref=o.ref
IDS=['43755','43781','43659','210035','43442','209675','43372','42713','43397','43924']
def main():
 src=m.load(RUN/'cotmania-discovery-001.json.gz');by={v['objectID'].split('/')[-1]:v for v in src['data']['hits']};selected=[]
 for id in IDS:
  r=by[id];assert r['type']=='Works of Art' and r['objectname']=='Drawing';date=o.date(r['date']);assert date;selected.append(dict(source_id=id,index=r,date=date))
 m.save(RUN/'cotmania-extra-selection-001.json.gz',dict(at=m.now(),rows=selected,index_reference=ref(RUN/'cotmania-discovery-001.json.gz'),policy='Ten source-dated drawing metadata leads selected from already captured discovery page. No new global search or image requests. Copies,uncertain titles and version relationships reviewed as such.'))
 out=[]
 for number,r in enumerate(selected,41):
  raw,c=n.n.capture('cotmania',r['index']['url']);row=dict(number=number,**r,capture=c,parsed=o.parsed(raw));out.append(row);m.save(RUN/'selected-objects-001'/('%03d.json'%number),row);print(json.dumps(dict(number=number,fields=row['parsed']['fields'])),flush=True)
 m.save(RUN/'cotmania-extra-objects-001.json.gz',dict(at=m.now(),rows=out,selection_reference=ref(RUN/'cotmania-extra-selection-001.json.gz'),script_reference=ref(Path(__file__).resolve())))
if __name__=='__main__':main()
