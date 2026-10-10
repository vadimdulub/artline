"""Capture only22 pre1971-labelled story objects; no collection crawl or image downloads."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-leeds-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref

def main():
 src=m.load(RUN/'additional-object-leads-001.json.gz');selected=[v for v in src['rows'] if v['state']=='selected_metadata_lead'];assert len(selected)==22;out=[];failures=0
 for v in selected:
  try:
   raw,c=n.n.capture('gac',v['url']);p=n.parsed(raw);out.append(dict(lead=v,capture=c,parsed=p));print(json.dumps(dict(title=v['title'],text=p['text'])),flush=True);failures=0
  except Exception as e:
   out.append(dict(lead=v,error=type(e).__name__+': '+str(e)));failures+=1
   if failures>=3 or any(x in str(e) for x in ['403','429']):break
 m.save(RUN/'additional-object-metadata-001.json.gz',dict(at=m.now(),rows=out,selection_reference=ref(RUN/'additional-object-leads-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Museum-published selected metadata only. Leads,not approved additions. Reconcile venue,ownership/loans,creator and physical versions; preserve exact source date wording. Existing Natural History Museum of the Child and Dead Linnet are known matching leads and must not be duplicated. No images.'))
if __name__=='__main__':main()
