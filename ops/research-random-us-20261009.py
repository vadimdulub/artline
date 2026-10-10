#!/usr/bin/env python3
"""Bounded official US collection selection, metadata before any downloads."""
import importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import quote
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-random-country-collections-20261009.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
r.phase('US');b=r.b;CC0=b.CC0

def cleveland():
 s=b.Source();out=[];held=[];totals={}
 fields='id,accession_number,title,creation_date,creation_date_earliest,creation_date_latest,culture,technique,type,measurements,creators,legal_status,record_type,cover_accession_number,creditline,url,share_license_status,copyright,images,department,external_resources'
 for kind,cap in [('Painting',500),('Drawing',100),('Print',100)]:
  for skip in range(0,cap,100):
   d,rc=s.get('https://openaccess-api.clevelandart.org/api/artworks/',dict(type=kind,limit=100,skip=skip,fields=fields));totals[kind]=d['info']['total']
   for w in d['data']:
    if w.get('legal_status')!='accessioned' or w.get('cover_accession_number') or w.get('record_type')!='object':continue
    creators=w.get('creators',[]);label='; '.join(r.clean_name(x.get('description') or x.get('name') or '') for x in creators) or None
    row=b.candidate('cleveland',w,rc,source_id=str(w['id']),title=w['title'],museum='Cleveland Museum of Art',source_url=w['url'].replace('http:','https:'),accession_number=w['accession_number'],creator_label=label,date_display=w.get('creation_date'),year_start=w.get('creation_date_earliest'),year_end=w.get('creation_date_latest'),medium=w.get('technique'),source_type=w.get('type'),image_url=(w.get('images') or {}).get('web',{}).get('url'),image_license_url=CC0 if w.get('share_license_status')=='CC0' and not w.get('copyright') else None,image_rights_label=w.get('share_license_status'),credit=w.get('creditline'),selection_basis='Bounded native accessioned museum records: first 500 paintings, 100 drawings and 100 prints')
    if r.accept(row,held) and row['date_decision']=='within_cutoff_source_bounds':out.append(row)
   print('Cleveland',kind,skip+len(d['data']),flush=True)
   if len(d['data'])<100:break
 b.save('cleveland-records.json.gz',dict(records=out,held=held,totals=totals))
def chicago():
 s=b.Source();out=[];held=[]
 fields='id,title,main_reference_number,date_start,date_end,date_display,artist_display,artist_id,artist_ids,place_of_origin,dimensions,medium_display,credit_line,fiscal_year_deaccession,artwork_type_title,department_title,is_public_domain,copyright_notice,image_id'
 query={'bool':{'filter':[{'terms':{'artwork_type_title.keyword':['Painting','Drawing and Watercolor']}},{'range':{'date_end':{'lte':1970}}}]}}
 for pg in range(1,5):
  d,rc=s.get('https://api.artic.edu/api/v1/artworks/search',{'params':json.dumps(dict(query=query,fields=fields.split(','),limit=100,page=pg))})
  for w in d['data']:
   if w.get('fiscal_year_deaccession'):continue
   iid=w.get('image_id');label=r.clean_name((w.get('artist_display') or '').split('\n')[0])
   row=b.candidate('chicago',w,rc,source_id=str(w['id']),title=w['title'],museum='Art Institute of Chicago',accession_number=w.get('main_reference_number'),source_url='https://www.artic.edu/artworks/'+str(w['id']),creator_label=label,date_display=w.get('date_display'),year_start=w.get('date_start'),year_end=w.get('date_end'),medium=w.get('medium_display'),dimensions=w.get('dimensions'),source_type=w.get('artwork_type_title'),image_url=f'https://www.artic.edu/iiif/2/{iid}/full/843,/0/default.jpg' if iid else None,image_license_url=CC0 if w.get('is_public_domain') else None,image_rights_label='Public domain' if w.get('is_public_domain') else w.get('copyright_notice') or 'Not public domain',credit=w.get('credit_line'),selection_basis='First four official API painting/drawing pages with native end date through 1970')
   if len(w.get('artist_ids') or [])>1:row['creator_link_hold']=True
   if r.accept(row,held) and row['date_decision']=='within_cutoff_source_bounds':out.append(row)
  print('Chicago',pg,len(out),flush=True)
 b.save('chicago-records.json.gz',dict(records=out,held=held,source_total=d['pagination']['total']))
if __name__=='__main__':globals()[sys.argv[1]]()
