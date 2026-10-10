"""Selected earlier art articles expose historical collection highlights."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-harris-box-additions-supplements-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN
def main():
 dest=RUN/'historic-articles-001.json.gz';assert not dest.exists();rows=[]
 for term in ['painting','Cottonian','Reynolds']:
  url='https://theboxplymouth.com/wp-json/wp/v2/posts?'+urlencode(dict(search=term,per_page=20,orderby='id',order='asc',_fields='id,link,slug,title,excerpt,content'))
  try:
   b,c=p.n.capture('box',url);data=json.loads(b);assert len(data)<=20;rows.append(dict(provider='box',url=url,capture=c,data=data));print(json.dumps(dict(term=term,objects=[dict(id=v['id'],title=v['title']['rendered']) for v in data])),flush=True)
  except Exception as e:
   rows.append(dict(provider='box',url=url,error=str(e)));print(str(e),flush=True)
   if any(t in str(e) for t in ['403','429','robots']):break
 m.save(dest,dict(at=m.now(),rows=rows,script_reference=p.s.ref(Path(__file__).resolve()),policy='Three bounded museum-authored historical art article searches. Repeated articles deduplicated by native ID. Loans and modern works excluded; no exhaustive catalogue or image requests.'))
if __name__=='__main__':main()
