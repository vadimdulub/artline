#!/usr/bin/env python3
"""Resume the finite public Brazil registry with two paced metadata requests."""
import concurrent.futures,importlib.util,math,threading,time
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('south-america-1000-20261011.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d
base='https://www.rmiberoamericanos.org/Busqueda/IndexFilterTree?searchString=&searchStringTree=-55&page='
raw,rc=c.capture(base+'1');total=int(BeautifulSoup(raw,'html.parser').select_one('#hdNumRegistros')['value']);assert total==3012
missing=[]
for page in range(1,math.ceil(total/10)+1):
 u=base+str(page)
 if (c.RUN/'captures'/(d.sha(u.encode())+'.json.gz')).exists():c.capture(u)
 else:missing.append(u)
print('Resume Brazil registry:',len(missing),'metadata pages; two workers, starts at least one second apart',flush=True)
pace=threading.Lock();last=[0.0]
def one(url):
 with pace:
  time.sleep(max(0,last[0]+1-time.monotonic()));last[0]=time.monotonic()
  assert not (c.RUN/'access-holds/www.rmiberoamericanos.org.json').exists(),'Provider held; no retry'
 raw,rc=c.c.r.b.capture(url);assert rc['status']==200
 assert int(BeautifulSoup(raw,'html.parser').select_one('#hdNumRegistros')['value'])==total
 return rc
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for n,rc in enumerate(pool.map(one,missing),1):
  if n%10==0:print('Remaining Brazil pages captured',n,'/',len(missing),flush=True)
c.directory('BR')
