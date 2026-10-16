import importlib.util,json,concurrent.futures
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-auckland-images-000101.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
slugs={'edmund-blair-leighton':['peril'],'william-hodges':['dusky'],'wilhelm-trubner':['violet','violett'],'robert-bevan':['mydlow'],'edward-william-cooke':['pink'],'edward-armitage':['easter']}
def run(slug):
 url='https://www.wikiart.org/en/'+slug+'/all-works/text-list'
 try:
  raw,rc=b.capture(url);rows=[dict(title=a.get_text(' ',strip=True),url='https://www.wikiart.org'+a['href']) for a in BeautifulSoup(raw,'html.parser').select('li a[href]') if a['href'].startswith('/en/'+slug+'/') and 'all-works' not in a['href']]
  b.save('indexes/'+slug+'.json',dict(receipt=rc,entries=rows));leads=[r for r in rows if any(t in r['title'].lower() for t in slugs[slug])];print(slug,len(rows),json.dumps(leads),flush=True)
 except Exception as e: print(slug,type(e).__name__,str(e)[:200],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,slugs))
