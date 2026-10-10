"""Selected official collection narratives and an acquisition-funder object."""
import importlib.util,json
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-city-art-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
n.HOSTS.update(edinburgh={'www.edinburgh.gov.uk','edinburgh.gov.uk','cultureedinburgh.com','www.edinburghmuseums.org.uk'},artfund={'www.artfund.org','artfund.org'})
SOURCES=[
('artfund','https://www.artfund.org/our-purpose/art-funded-by-you/portrait-of-naomi-mitchison'),
('edinburgh','https://cultureedinburgh.com/news/new-exhibition-explores-story-of-the-woman-who-shaped-edinburghs-fine-art-collection')]

def main():
 dest=RUN/'supplements-001.json.gz';assert not dest.exists();rows=[];stopped=set();fails={}
 for provider,url in SOURCES:
  if provider in stopped:rows.append(dict(provider=provider,url=url,state='unrequested_after_access_hold'));continue
  try:
   body,cap=n.capture(provider,url);parsed=n.parsed(body);soup=n.BeautifulSoup(body,'html.parser');parsed['images']=[dict(alt=v.get('alt',''),src=v.get('src',''),title=v.get('title','')) for v in soup.select('img')];rows.append(dict(provider=provider,url=url,capture=cap,parsed=parsed));fails[provider]=0;print(json.dumps(dict(provider=provider,url=url,bytes=len(body))),flush=True)
  except Exception as e:
   rows.append(dict(provider=provider,url=url,error=type(e).__name__+': '+str(e)));fails[provider]=fails.get(provider,0)+1;print(json.dumps(rows[-1]),flush=True)
   if fails[provider]>=3 or any(t in str(e) for t in ['403','429','robots']):stopped.add(provider)
 m.save(dest,dict(at=m.now(),rows=rows,stopped_providers=sorted(stopped),script_reference=s.ref(Path(__file__).resolve()),policy='Two selected public metadata pages only. Historical 404 endpoints are not retried; current culture article is a separate legitimate public resource. No image bytes,private endpoints,held-provider requests or database writes. Collection-wide counts and unnamed artists do not create artwork records. Loans and post1970 works excluded from selected holdings.'))
if __name__=='__main__':main()
