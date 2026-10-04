import sys,importlib.util,json,time
from pathlib import Path
import psycopg
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'ops'))
s=importlib.util.spec_from_file_location('research',R/'ops/research-early-books-20260923.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
r.OUT=R/'docs/research/period-connections-20261002'
assert not (r.OUT/'plan.json').exists(), 'Preserve completed campaign evidence; use a new campaign for new research.'
titles=['Tarikh al-Sudan']
with psycopg.connect('postgres://localhost/artline',options='-c default_transaction_read_only=on') as db: existing={a:b for a,b in db.execute('select source_id,id from book_records')}
candidates=[]
for offset in range(0,len(titles),12):
 data,proof=r.capture('en.wikipedia.org',{'action':'query','titles':'|'.join(titles[offset:offset+12]),'redirects':1,'prop':'pageprops|extracts|revisions','ppprop':'wikibase_item','exintro':1,'explaintext':1,'exlimit':20,'rvprop':'ids|timestamp'})
 for p in data['query']['pages']:
  q=p.get('pageprops',{}).get('wikibase_item')
  if q and not p.get('missing'): candidates.append({'title':p['title'],'qid':q,'extract':p.get('extract',''),'revision':p.get('revisions',[{}])[0].get('revid'),'source':proof,'existing':existing.get(q)})
 time.sleep(5)
wanted=sorted({i['qid'] for i in candidates if not i['existing']});entities={}
for offset in range(0,len(wanted),40):
 data,proof=r.capture('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(wanted[offset:offset+40]),'props':'info|labels|descriptions|claims','languages':'en'})
 entities.update({q:{'entity':e,'source':proof} for q,e in data['entities'].items()});time.sleep(5)
for i in candidates: i['wikidata']=entities.get(i['qid'])
r.OUT.mkdir(parents=True,exist_ok=True);(r.OUT/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2))
print(json.dumps({'candidates':len(candidates),'missing':[(i['title'],i['qid']) for i in candidates if not i['existing']]},indent=2))
