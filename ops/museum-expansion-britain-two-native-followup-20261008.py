"""Selected native object follow-up for copies, a study and missing Art UK reference."""
import importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-two-native-20261008.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN

def main():
 dest=RUN/'native-probes-002.json';assert not dest.exists();selected=[(212,'1975-05-7-1'),(116,'1953-03-22-1'),(194,'1962-12-37-1'),(218,'1956-02-194-1'),(71,'1991-02-64-1')];out=[]
 for number,acc in selected:
  url='https://collection.nam.ac.uk/detail.php?acc='+acc
  try:
   raw,cap=n.n.capture('nam',url);soup=n.n.BeautifulSoup(raw,'html.parser');out.append(dict(number=number,url=url,capture=cap,text=soup.get_text(' ',strip=True),headings=[v.get_text(' ',strip=True) for v in soup.select('h1,h2,h3')]))
  except Exception as error:out.append(dict(number=number,url=url,error=type(error).__name__+': '+str(error)));break
 m.save(dest,dict(at=m.now(),rows=out,script_reference=n.f.ref(Path(__file__).resolve()),policy='Bounded follow-up of already selected artwork inventories, with the native suffix convention checked against returned object identity. A missing page does not validate an inventory. No images or display assertion.'));print(json.dumps([dict(number=v['number'],headings=v.get('headings'),error=v.get('error')) for v in out]),flush=True)
if __name__=='__main__':main()
