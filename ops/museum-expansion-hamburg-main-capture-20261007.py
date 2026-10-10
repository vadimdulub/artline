import importlib.util,json
s=importlib.util.spec_from_file_location('d','ops/museum-expansion-hamburg-discovery-20261007.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
pages=[]
for path in ['/de/sammlung-online','/de/alte-meister','/de/19-jahrhundert','/de/moderne']:
 url=d.BASE+path
 try:
  raw,cap=d.n.capture('hamburg',url);soup=d.BeautifulSoup(raw,'html.parser')
  links=[dict(text=a.get_text(' ',strip=True),url=d.urljoin(url,a['href'])) for a in soup.select('a[href]')]
  pages.append(dict(url=url,capture=cap,heading=[h.get_text(' ',strip=True) for h in soup.select('h1')],full_text=soup.get_text(' ',strip=True),links=links))
  print('PAGE',path,'bytes',len(raw),'links',len(links),flush=True)
  for h in soup.select('h3'):
   if h.get_text(' ',strip=True) in ['Jean-Honoré Fragonard','Philipp Otto Runge']:
    print('SAMPLE',str(h.parent.parent)[:8000],flush=True)
 except Exception as ex:
  pages.append(dict(url=url,error=type(ex).__name__+': '+str(ex)));print('ERROR',url,str(ex),flush=True)
d.m.save(d.RUN/'main-site-discovery-001.json.gz',dict(at=d.m.now(),pages=pages,policy='Four selected public department/index pages only. Separate online catalogue returned Anubis access denial through web tool; no challenge bypass, images, approvals or DB writes.'))
