import sys,json,re
sys.path.insert(0,'ops')
import historical_exhibitions_fitzwilliam_discovery_20261012 as f
ls=[l for l in f.c.load(f.OUT/'index-discovery.json.gz')['leads']if re.search('Byzant|Russian|Greek|Icon|Rembrandt|Uccello|Cesi',l['title'],re.I)]
def get(l):
 raw,rc=f.c.capture(l['url']+'?format=json');d=json.loads(raw);result=dict(lead=l,data=d,receipt=rc);f.c.save(f.OUT/'selected-details'/(d['admin']['id']+'.json'),result);return result
with f.ThreadPoolExecutor(max_workers=2)as pool:rs=list(pool.map(get,ls))
report=[]
for r in rs:
 d=r['data'];vs=d.get('venues',[]);dates=[x.get('@link',{}).get('date',[])for x in vs];report.append(dict(id=d['admin']['id'],title=d['summary_title'],venues=[x.get('summary_title')for x in vs],dates=dates))
f.c.save(f.OUT/'selected-details-discovery.json',dict(at=f.c.now(),records=report,reviewState='Discovery only; dates, object medium, tour identity and canonical event/object matching require review.'))
for r in report:print(json.dumps(r))
