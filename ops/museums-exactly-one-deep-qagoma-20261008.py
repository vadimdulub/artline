#!/usr/bin/env python3
import argparse,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('ar',Path(__file__).with_name('museums-exactly-one-artefact-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
d=a.d;RUN=a.RUN;ROOT=a.ROOT;h=a.h;h.RUN=RUN/'qagoma'
IDS=[12117,3267,33304,7980,5929,7690,1241,20694,3959,105649,5218,118651,9193,1441,21777,5818,12099]
MUSEUM=next(i for i in a.BASE.values() if i['name'].startswith('Queensland Art Gallery'))
def parse(raw,key):
 soup=BeautifulSoup(raw,'html.parser');title=soup.select_one('h1 em');dl=soup.find('dl')
 assert title and dl
 fields={x.get_text(' ',strip=True):x.find_next_sibling('dd').get_text(' ',strip=True) for x in dl.find_all('dt')}
 date=fields['Date Created'];years=a.dates(date)
 if not years:
  x=date.replace('–','-');r=re.fullmatch(r'(c\.)?([12]\d{3})-([0-9]{2})',x)
  if r:
   first=int(r[2]);last=int(r[2][:2]+r[3]);years=(first,last,'range')if first<=last else None
 if not years or years[1]>1970:return None,'creation_date_requires_review'
 kind={'Painting':'painting','Drawing':'drawing','Print':'print'}.get(fields.get('Media Category'))
 if not kind:return None,'work_type_requires_review'
 if fields.get('Secondary Media Category')=='watercolour':kind='watercolor'
 object_node=soup.select_one('article.node--type-object')
 assert object_node
 creator_list=object_node.select_one('.node__content > div > .artist-list')
 assert creator_list
 people=[]
 for node in creator_list.select('li'):
  value=node.get_text(' ',strip=True)
  if not re.fullmatch(r'.+ - (?:Creator|Artist)',value):return None,'qualified_creator_role_requires_review'
  people.append(value.rsplit(' - ',1)[0])
 citation=soup.select_one('#clipboardjs')['value']
 assert 'Collection: Queensland Art Gallery | Gallery of Modern Art' in citation
 assert '/objects/'+str(key)+' 'in citation
 assert people,(key,'creator selector')
 if any(p.upper()=='UNKNOWN' for p in people):return None,'unknown_creator_requires_review'
 assert fields.get('Accession No.') and fields.get('Credit Line')
 assert not re.search(r'loan|lent|deaccession',fields['Credit Line'],re.I)
 assert 'Queensland Art Gallery Board of Trustees'in soup.get_text(' ',strip=True)
 # Only the explicit source creation field determines eligibility; acquisition
 # and credit years are retained as evidence and never treated as creation.
 f=dict(title=title.get_text(' ',strip=True),creator_label='; '.join(dict.fromkeys(people)),first=years[0],last=years[1],date_precision=years[2],date_display=date,work_type=kind,medium=fields.get('Medium'),dimensions=fields.get('Dimensions A'),accession=fields['Accession No.'],source_url='https://collection.qagoma.qld.gov.au/objects/'+str(key),holding_basis='Official Queensland Art Gallery Board of Trustees collection catalogue, exact object number and accession with collection credit. QAGOMA is the collection publisher; this records the museum collection relationship, not a claim that the object is displayed in the QAG building.')
 return dict(facts=f,fields=fields,creators=list(dict.fromkeys(people))),None

def research():
 rows=[];held=[]
 for key in IDS:
  url='https://collection.qagoma.qld.gov.au/objects/'+str(key)
  raw,rc=h.capture(url);assert rc['status']==200
  parsed,reason=parse(raw,key)
  if reason:held.append(dict(source_url=url,reason=reason));continue
  rows.append(dict(artwork_id=d.uid('qagoma/'+str(key)),slug=a.m.OP+'-qagoma-'+str(key),source_record_id=str(key),provider='qagoma-native',origin='selected_official_collection',museum=MUSEUM,facts=parsed['facts'],source_receipt=rc,body_path=rc['body_path'],alternate_native_urls=[url.replace('/objects/','/index.php/objects/')],raw_source_record=parsed))
  print(key,parsed['facts']['title'],parsed['facts']['creator_label'],flush=True)
 a.campaign().prepare_wave('qagoma-corrected',rows,held)

def check(row,cache):
 raw=a.checked(row['source_receipt']);parsed,reason=parse(raw,row['source_record_id']);assert not reason and parsed==row['raw_source_record'] and parsed['facts']==row['facts'];assert row['museum']['id']==MUSEUM['id']
def configure(wave='qagoma-corrected'):
 out=a.configure(wave);out.check_body=check;out.scheme=lambda row:'qagoma-object';out.SOURCE_NAME='Selected official Queensland Art Gallery catalogue records, 8 October 2026';out.SOURCE_BASE_URL='https://collection.qagoma.qld.gov.au/';out.CONFIDENCE_BASIS='Exact official collection native object ID, inventory, source creator, explicit creation date, medium and collection credit. Editorial confidence; no current display claim.';return out
def plan():configure().plan()
def apply():configure('qagoma-reviewed').apply()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();globals()[x.phase]()
