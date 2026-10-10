#!/usr/bin/env python3
"""Source facts from selected official Thyssen object pages; no import decisions."""
import argparse,collections,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-thyssen-native-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m;d=n.d;RUN=n.RUN;ref=n.ref
def facts(x,p):
 j=p['jsonld'];creators=j.get('creator',[]);date=n.creation(p['date_display']);native_id=str(j.get('identifier','')).strip();url=p['canonical'];title=p['title']
 assert isinstance(creators,list) and all(isinstance(a,dict) for a in creators)
 soup=d.d.BeautifulSoup(n.body(x['capture']),'html.parser');native_urls=list(dict.fromkeys([url]+[el['href'] for el in soup.select('link[rel="alternate"][href]') if el['href'].startswith(d.BASE+'/')]))
 labels=[a.get('name') for a in creators if a.get('name')];forms={'Painting':'painting','Drawing':'drawing','Print':'print','Sculpture':'sculpture'}
 return dict(source_id=native_id,source_url=url,native_object_id=native_id,native_metadata_urls=[],native_page_urls=native_urls,wikidata_ids=[],title=title,titles=[title],creator_label=p['creator_label'],detail_creator_label='; '.join(labels) or None,identity_creator_labels=labels,creator_fields=creators,date_display=p['date_display'],**date,inventory=p['inventory_display'] or None,inventory_fields=p['inventory_fields'],medium=p['medium'],dimensions_text=p['dimensions_text'],work_type=forms.get(j.get('artform'),'unknown'),object_form=j.get('artform') if j.get('artform') in ['Work on paper','Relief'] else None,credit_line=p['credit_line'],source_artform=j.get('artform'),source_medium=j.get('artMedium'),source_surface=j.get('artworkSurface'),source_description=p['description_text'],source_description_html=p['description_html'],source_rights=p['rights_text'],source_location_text=p['source_location_text'],source_location_label=n.text(soup.select_one('.js-zoom-map-info a[data-splash-id="splash-artwork-location"]')),index_title=x['index']['title'],index_creator=x['index']['creator_label'],index_date=x['index']['date_display'],source_note='Official public artwork HTML and VisualArtwork JSON-LD, linked by independently accessible museum pages. Original inventory,creator qualifications,date,physical facts,narrative,credit and rights retained. Display text remains source evidence,never a current-display assertion; documented collection connection does not establish custody or legal title.')
def source_holds(v,x,p):
 out=[];j=p['jsonld'];rc=x['capture']['receipt'];url=v['source_url']
 if v['date_issue']:out.append(v['date_issue'])
 if not v['source_id'] or v['source_id'] not in v['inventory_fields']:out.append('JSON-LD accession absent from literal inventory fields')
 if not v['inventory'] or len(v['inventory_fields']) not in [1,2]:out.append('Unresolved native inventory structure')
 if not(url==j.get('url')==rc['url']==rc['final_url']==x['index']['source_url']):out.append('Canonical,requested,final or JSON-LD URLs disagree')
 if m.norm(v['title'])!=m.norm(j.get('name')) or m.norm(v['title'])!=m.norm(v['index_title']):out.append('Index,heading or JSON-LD titles disagree')
 if n.text(d.d.BeautifulSoup(j.get('dateCreated',''),'html.parser'))!=v['date_display']:out.append('Heading and JSON-LD creation labels disagree')
 if n.creation(v['index_date'])!=n.creation(v['date_display']):out.append('Related/masterpiece card and object dates disagree')
 # JSON-LD names are commonly surname-first or Spanish; the shared explicit
 # native creator URL binds that label to the unchanged qualified heading.
 if not v['creator_label'] or len(v['creator_fields'])!=1 or v['creator_fields'][0].get('url')!=p['creator_url'] or m.norm(v['creator_label'])!=m.norm(v['index_creator']):out.append('Creator labels or role structure require review')
 if v['work_type']=='unknown' and v['source_artform'] not in ['Work on paper','Relief']:out.append('Unmapped source artwork type')
 if v['credit_line']!='Museo Nacional Thyssen-Bornemisza, Madrid':out.append('Qualified collection/deposit/holding credit requires explicit review')
 return out
def candidates(suffix,sources):
 rows=[];seen=set()
 for source_suffix in sources:
  source=RUN/('selected-capture-'+source_suffix+'.json.gz')
  for reference in m.load(source)['records']:
   path=m.ROOT/reference['path'];assert ref(path)==reference;x=m.load(path)
   if 'error' in x:rows.append(dict(state='capture_hold',source_url=x['index']['source_url'],source_reference=reference,reasons=[x['error']]));continue
   x,p=n.checked_record(path);v=facts(x,p);holds=source_holds(v,x,p)
   if v['source_id'] in seen:holds.append('Native accession repeats within selected pages')
   seen.add(v['source_id']);rows.append(dict(source_id=v['source_id'],facts=v,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/('native-candidates-'+suffix+'.json.gz'),dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['state'] for r in rows)),parser_references=[ref(Path(__file__).resolve()),ref(Path(n.__file__).resolve())],policy='Source triage only. Qualified credits,unknown dates,index conflicts and duplicate native identities retained. Physical version and broader database identity review remain required.'))
 print('COUNTS',dict(collections.Counter(r['state'] for r in rows)),flush=True)
 for row in rows:
  if row['state']!='candidate':print('HOLD',row.get('source_id'),row.get('facts',{}).get('title'),row['reasons'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);p.add_argument('--sources',nargs='+',required=True);a=p.parse_args();candidates(a.suffix,a.sources)
