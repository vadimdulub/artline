#!/usr/bin/env python3
"""Add seven source-required country codes from the UN M49 reference table."""
import importlib.util,json,requests
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.x.BASE/'country-taxonomy';URL='https://unstats.un.org/unsd/methodology/m49/overview/'
EXPECTED={'VE':('Venezuela (Bolivarian Republic of)','South America'),'UY':('Uruguay','South America'),'PE':('Peru','South America'),'IS':('Iceland','Northern Europe'),'NI':('Nicaragua','Central America'),'HT':('Haiti','Caribbean'),'NA':('Namibia','Southern Africa')}

def main():
 p=RUN/'un-m49-overview.html';receipt=p.with_suffix('.receipt.json')
 if not p.exists():
  r=requests.get(URL,timeout=45);r.raise_for_status();assert len(r.content)<3_000_000
  m.m.core.save_new(p,r.content);m.m.core.save_new(receipt,{'url':URL,'retrieved_at':m.m.core.now(),'sha256':m.m.core.sha(r.content),'bytes':len(r.content)})
 evidence=json.loads(receipt.read_text());assert m.m.core.sha(p.read_bytes())==evidence['sha256']
 soup=BeautifulSoup(p.read_bytes(),'html.parser');table=soup.find('table',id='downloadTableEN');headers=[c.get_text(' ',strip=True) for c in table.select('thead td, thead th')]
 assert 'ISO-alpha2 Code' in headers and 'Country or Area' in headers
 selected={}
 for tr in table.select('tbody tr'):
  vals=[c.get_text(' ',strip=True) for c in tr.find_all('td')];row=dict(zip(headers,vals));code=row.get('ISO-alpha2 Code')
  if code not in EXPECTED:continue
  name,region=EXPECTED[code];assert row['Country or Area']==name and (row['Intermediate Region Name'] or row['Sub-region Name'])==region
  selected[code]={'code':code,'name':name,'region_code':region.lower().replace(' ','-'),'historical_note':None,'source_row':row}
 assert selected.keys()==EXPECTED.keys();m.m.core.save_new(RUN/'selected-countries.json',{'countries':selected,'receipt':evidence})
 for target in ['local','production']:
  done=RUN/(target+'-added.json')
  if done.exists():continue
  with m.m.r.base.connect(target=='production') as db:
   with db.transaction():
    db.execute('SELECT pg_advisory_xact_lock(559220260914)')
    existing=db.execute('SELECT * FROM countries WHERE code=ANY(%s) ORDER BY code',(sorted(selected),)).fetchall();assert not existing
    m.m.core.save_new(m.BACKUPS/('taxonomy-'+target+'-preimages.json'),{'at':m.m.core.now(),'codes':sorted(selected),'rows':existing})
    for c in selected.values():db.execute('INSERT INTO countries(code,name,region_code,historical_note) VALUES(%s,%s,%s,%s)',(c['code'],c['name'],c['region_code'],c['historical_note']))
   rows=db.execute('SELECT * FROM countries WHERE code=ANY(%s) ORDER BY code',(sorted(selected),)).fetchall()
   assert rows==[{k:selected[code][k] for k in ['code','name','region_code','historical_note']} for code in sorted(selected)]
  m.m.core.save_new(done,{'at':m.m.core.now(),'countries':rows,'source_receipt':evidence});print(target,'seven country codes verified',flush=True)
if __name__=='__main__':main()
