"""Bounded source leads for Brest; discovery only, with no database writes."""
import importlib.util,json,collections
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-beziers-source-20261009.py'));src=importlib.util.module_from_spec(z);z.loader.exec_module(src);m=src.m;src.RUN=m.RUN/'native/beziers-more-20261009'
def main():
 RUN=src.RUN;context=[]
 for key,url in [('brest-collection','https://musee.brest.fr/les-collections'),('brest-works','https://musee.brest.fr/les-collections/oeuvres')]:
  raw,rc=src.capture('next-'+key+'-001',url)
  if rc['status']!=200:
   context.append(dict(receipt=rc,text=None,links=[],state='Saved HTTP '+str(rc['status'])+' response; no retry. Web reader exposed a cached index; object-source work continues independently through the national API.'));continue
  soup=BeautifulSoup(raw,'html.parser');main=soup.select_one('main') or soup;context.append(dict(receipt=rc,text=main.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),url=a['href']) for a in main.select('a[href]')]))
 url='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/?Code_Museofile__exact=M0197&Domaine__contains=beaux-arts&page_size=100'
 raw,rc=src.capture('next-brest-joconde-001',url);data=json.loads(raw);rows=data['data'];assert len(rows)<=100 and all(v['Code_Museofile']=='M0197' for v in rows)
 m.save(RUN/'next-brest-source-leads-001.json.gz',dict(at=m.now(),museum_id='258b8c79-fe6f-41e9-90c0-988eec2165b4',museofile='M0197',context=context,receipt=rc,rows=rows,total=data['meta']['total'],next_page=data['links']['next'],policy='Selected next-museum research leads only. No identity or date decisions yet; no artworks added to Brest. Fresh scoped production count79/79. Use musee.brest.fr; old musee-brest.com search results appear unrelated and are not an authority. No current-display claim.'))
 print(json.dumps(dict(brest_source_total=data['meta']['total'],bounded_leads=len(rows),domains=dict(collections.Counter(v['Domaine'] for v in rows)))),flush=True)
if __name__=='__main__':main()
