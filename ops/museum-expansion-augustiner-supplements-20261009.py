"""Two selected annual reports linked by the accessible official press page."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-augustiner-discovery-20261009.py'));d=importlib.util.module_from_spec(z);z.loader.exec_module(d);m=d.m;RUN=d.RUN
def main():
 src=m.load(RUN/'native-discovery-001.json.gz');p=next(x for x in src['rows'] if x['key']=='press');rows=[]
 for key,term in [('report2022current','STM_Jahresbericht_2022_barrierefrei.pdf'),('report2024','MF_Jahresbericht_2024.pdf')]:
  links={a['href'] for a in p['parsed']['links'] if a['href'].endswith(term)};assert len(links)==1;url='https://museen.freiburg.de'+links.pop()
  try:row=d.capture(key,url);rows.append(row);print(json.dumps(dict(key=key,bytes=row['capture']['receipt']['bytes'])),flush=True)
  except Exception as e:
   rows.append(dict(key=key,url=url,error=type(e).__name__+': '+str(e)))
   if any(t in str(e) for t in ['403','429','access_denied']):break
 m.save(RUN/'supplements-001.json.gz',dict(at=m.now(),rows=rows,script_reference=d.s.ref(Path(__file__).resolve()),discovery_reference=d.s.ref(RUN/'native-discovery-001.json.gz'),policy='Current public museum press links only. Legacy2022 URL404 retained. No held portal requests or database writes.'))
if __name__=='__main__':main()
