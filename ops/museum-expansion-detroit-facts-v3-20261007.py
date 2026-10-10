#!/usr/bin/env python3
"""Detroit original metadata with single, anonymous and multiple source creators."""
import argparse,copy,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-detroit-resume-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);m=c.m;d=c.d;RUN=c.RUN;IID=c.IID;ref=c.ref
def checked(r):
 p=m.ROOT/r['path'];assert ref(p)==r;return p
def known(value):return None if not value or re.fullmatch(r'[-\s]+',value) else value
def object_id(url):
 p=urlparse(url);assert p.hostname=='dia.org';x=re.fullmatch(r'/collection/.*?(?:-|/)(\d+)/?',p.path);assert x,url;return x[1]
def extract(raw):
 soup=BeautifulSoup(raw,'html.parser');fields=[];sections=[]
 for node in soup.select('.artwork_details > p'):
  label=node.select_one('label');assert label
  for tip in label.select('.tooltip'):tip.decompose()
  key=label.get_text(' ',strip=True);label.decompose();fields.append(dict(label=key,value=node.get_text(' ',strip=True)))
 ff={v['label']:v['value'] for v in fields};assert len(ff)==len(fields)
 for h in soup.select('h2.section-title'):
  node=copy.copy(h.parent)
  for tip in node.select('.tooltip'):tip.decompose()
  sections.append(dict(heading=h.get_text(' ',strip=True),classes=h.parent.get('class'),disabled=h.parent.has_attr('disabled'),text=node.get_text(' ',strip=True)))
 canonical=soup.select('link[rel=canonical]');assert len(canonical)==1
 metadata=[a['href'] for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Metadata']
 hero=soup.select_one('.hero_content');assert soup.h1 and hero
 makers=[]
 for node in soup.select('.artwork_details .makers > span'):
  label=node.get_text(' ',strip=True);match=re.fullmatch(r'(.+?)\s*\(([^()]*)\)',label);bio=node.find_next_sibling('i')
  makers.append(dict(label=label,name=match[1].strip() if match else label,role=match[2].strip() if match else None,biography=bio.get_text(' ',strip=True) if bio else None))
 return dict(makers=makers,title=soup.h1.get_text(' ',strip=True),canonical=canonical[0]['href'],fields=fields,field_map=ff,sections=sections,hero=hero.get_text(' ',strip=True),metadata_links=metadata)
def parse(path):
 x=m.load(path);checked(x['queue_reference']);queue=m.load(c.QUEUE);q=next(v for v in queue['selected'] if v['number']==x['number']);assert q==x['index']
 for lead in q['index_references']:
  index=m.load(checked(lead['index_reference']));parsed=d.index(d.body(index['capture']),index['capture']['receipt']['url']);assert parsed==index['parsed'];assert {k:lead[k] for k in parsed['rows'][0]} in parsed['rows']
 z=extract(d.body(x['capture']));ff=z['field_map'];assert all(k in ff for k in ['Title','Artwork Date','Medium','Dimensions','Classification','Department','Credit','Accession Number','Copyright'])
 sid=q['source_id'];assert object_id(z['canonical'])==object_id(x['capture']['receipt']['final_url'])==sid
 assert set(z['metadata_links'])=={'/download/metadata/'+sid}
 assert z['title']==ff['Title'];flags=[]
 for key,field in [('title','Title'),('date_display','Artwork Date')]:
  if m.norm(q[key])!=m.norm(ff[field]):flags.append('index_detail_'+key+'_difference')
 makers=z['makers'];multiple=bool(makers)
 if multiple:
  assert 'Makers' in ff and 'Artist' not in ff and len(makers)>=2
  artist='; '.join(v['name'] if v['role']=='Artist' else v['label'] for v in makers);cultural=None;flags.append('multiple_source_creators_review')
  if any(v['role']!='Artist' for v in makers):flags.append('creator_roles_require_review')
 else:
  assert all(k in ff for k in ['Artist','Life Dates','Nationality','Culture']);artist=known(ff['Artist']);cultural=known(ff['Culture']) or known(ff['Nationality'])
 creator=artist or cultural
 if not creator:flags.append('unknown_creator_label')
 if not (multiple and q['creator_label']=='Multiple makers') and m.norm(q['creator_label'] or '')!=m.norm(creator or ''):flags.append('index_detail_creator_difference')
 dates=d.creation(ff['Artwork Date'])
 if dates['date_issue']:flags.append('creation_date_requires_review')
 if ff['Classification']!='Paintings':flags.append('classification_requires_review')
 if not known(ff['Accession Number']) or not known(ff['Credit']):flags.append('accession_or_credit_missing')
 provenance=' '.join(v['text'] for v in z['sections'] if v['heading']=='Provenance')
 if re.search(r'\b(?:deaccession\w*|restitu\w*|repatriat\w*|lost|missing|location[^;.]*unknown|on loan|loan from|lent by|promised gift)\b',provenance+' '+ff['Credit'],re.I):flags.append('holding_or_custody_requires_review')
 if re.search(r'\b(?:pair|diptych|triptych|polyptych|verso|reverse|fragment|part of|pendant|copy|after|workshop|attributed|circle|school)\b',ff['Title']+' '+(creator or ''),re.I):flags.append('version_or_qualified_creator_review')
 life=known(ff.get('Life Dates'))
 if life and m.norm(ff['Artwork Date'])==m.norm(life):flags.append('creation_equals_creator_life_dates')
 facts=dict(source_id=sid,native_object_id=sid,source_url=z['canonical'],native_page_urls=sorted({z['canonical'],q['url'],x['capture']['receipt']['final_url'],'https://dia.org/collection/'+sid}),native_metadata_urls=['https://dia.org/download/metadata/'+sid],wikidata_ids=[],title=ff['Title'],titles=[ff['Title']],creator_label=creator,detail_creator_label=artist,identity_creator_labels=[v['name'] for v in makers] if multiple else ([creator] if creator else []),creator_label_kind='multiple_source_artists' if multiple else ('source_artist_or_school' if artist else 'source_cultural_label'),date_display=ff['Artwork Date'],**dates,inventory=known(ff['Accession Number']),medium=known(ff['Medium']),dimensions_text=known(ff['Dimensions']),work_type='painting' if ff['Classification']=='Paintings' else None,object_form=None,credit_line=known(ff['Credit']),source_fields=z['fields'],source_makers=makers,source_sections=z['sections'],source_hero=z['hero'],source_rights=known(ff['Copyright']),source_note='Complete original official object HTML retained. Literal creator or cultural label, creation date, inventory, credit, biography, provenance and unknown copyright placeholder are preserved. Linked JSON was discovered but not fetched for these records. No current-display, physical-custody or image claim.')
 return dict(provider='detroit',institution_id=IID,number=q['number'],source_id=sid,facts=facts,source_reference=ref(path),source_references=[ref(path)]+[v['index_reference'] for v in q['index_references']],retrieved_at=x['capture']['receipt']['retrieved_at'],state='source_candidate',review_flags=flags)
def main(suffix):
 paths=sorted((RUN/'objects-001').glob('*.json.gz'));rows=[parse(p) for p in paths];assert len(rows)==len({v['source_id'] for v in rows})
 dest=RUN/('native-candidates-'+suffix+'.json.gz');assert not dest.exists()
 m.save(dest,dict(at=m.now(),rows=rows,parser_reference=ref(Path(__file__).resolve()),complete_capture_count=len(rows),queue_reference=ref(c.QUEUE),policy='Complete captures only. Every object still needs identity and editorial review, including all source warnings. Unknown or missing custody never establishes current collection presence. Cultural and school labels remain object labels; no new artist authority.'))
 print(json.dumps([dict(number=v['number'],title=v['facts']['title'],creator=v['facts']['creator_label'],date=v['facts']['date_display'],inventory=v['facts']['inventory'],flags=v['review_flags']) for v in rows],ensure_ascii=False),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix)
