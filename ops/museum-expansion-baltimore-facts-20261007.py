#!/usr/bin/env python3
"""Literal Baltimore native object fields with explicit unresolved source warnings."""
import argparse,importlib.util,json,re,types
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-baltimore-native-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;RUN=c.RUN;IID=c.IID;ref=c.ref;checked=c.checked
def text(node):return node.get_text(' ',strip=True) if node else None
def physical(raw):
 if not raw:return None,None
 # Preserve units and full frame/object distinctions. Split only at a visible
 # native separator before a dimension field, never infer a missing unit.
 match=re.search(r',\s*(?=(?:Unframed|Framed|Overall|Image|Sheet|Sight|Height|Diameter|Panel|Support|Frame|Platemark|Plate|Mat|Object|Canvas|Dimensions)(?:\s*\([^)]*\))?\s*:|\d)',raw,re.I)
 if match:return raw[:match.start()].strip() or None,raw[match.end():].strip() or None
 return raw,None
def work_type(medium):
 t=(medium or '').casefold()
 if re.match(r'(?:oil|acrylic|alkyd|tempera|egg tempera|distemper)\b',t):return 'painting'
 if re.match(r'watercolou?r\b',t):return 'watercolor'
 if re.match(r'(?:etching|engraving|lithograph|crayon lithograph|drypoint|woodcut|wood engraving|linocut|mezzotint|aquatint)\b',t):return 'print'
 if re.match(r'(?:pen|pencil|graphite|charcoal|pastel|chalk|black chalk|red chalk|gouache|ink)\b',t):return 'drawing'
 return 'unknown'
def extract(raw):
 soup=BeautifulSoup(raw,'html.parser');nodes=soup.select('flynt-component[name="BMAArtworkDetail"]');assert len(nodes)==1
 detail=nodes[0];header=detail.select_one('.titleSection');hero=soup.select_one('flynt-component[name="BMAArtworkHero"] .artworkMeta');assert header and hero
 fields=[]
 for node in detail.select('.objectInfo .infoRow'):
  label=text(node.select_one('.label'));value=text(node.select_one('.value'));assert label;fields.append(dict(label=label,value=value))
 assert len({x['label'] for x in fields})==len(fields)
 sections=[]
 for node in detail.select('.accordionItem'):
  label=text(node.select_one('.accordionHeader > span'));value=text(node.select_one('.accordionBody'));assert label
  sections.append(dict(label=label,text=value))
 makers=[]
 for node in detail.select('#artists .artistBio'):
  name=text(node.select_one('.artistName'));role=text(node.select_one('.bioHeading'));dates=text(node.select_one('.artistDates'));link=node.select_one('.artistNameLink[href]')
  makers.append(dict(name=name,role=role,biography=dates,url=link['href'] if link else None))
 canonical=soup.select('link[rel="canonical"]');og=soup.select('meta[property="og:url"]');assert len(canonical)<=1 and len(og)==1
 declared=canonical[0]['href'] if canonical else og[0]['content'];assert declared.rstrip('/')==og[0]['content'].rstrip('/')
 return dict(title=text(header.select_one('.artworkTitle')),creator_label=text(header.select_one('.artistName')),date_display=text(header.select_one('.dateLocation')),hero_title=text(hero.select_one('.artworkTitle')),hero_creator=text(hero.select_one('.artistName')),hero_date=text(hero.select_one('.dateLocation')),canonical=declared,declared_url_basis='canonical link' if canonical else 'OpenGraph URL',fields=fields,sections=sections,makers=makers,wall_text=text(detail.select_one('.wallText')),display_label=text(detail.select_one('.onViewBadge')),rights_labels=[text(x) for x in soup.select('[class*="imageCredit"],[class*="copyrightNotice"],[class*="rightsStatement"]')])
def parse(path):
 x=m.load(path);checked(x['queue_reference']);queue=m.load(c.QUEUE);row=next(r for r in queue['selected'] if r['number']==x['number']);assert x['index']==row
 for lead in row['index_references']:
  ix=m.load(checked(lead['index_reference']));assert lead['source_record'] in c.validate_index(ix)['results']
 z=extract(c.body(x['capture']));assert z['canonical'].rstrip('/')==row['url'].rstrip('/')==x['capture']['receipt']['final_url'].rstrip('/')
 assert (z['title'],z['date_display'])==(z['hero_title'],z['hero_date'])
 ff={f['label']:f['value'] for f in z['fields']};flags=[]
 for k in ['title','creator_label','date_display']:
  if m.norm(z[k])!=m.norm(row[k]):flags.append('index_detail_'+k+'_difference')
 assert z['title'];dates=c.dates.creation(z['date_display']);medium,dims=physical(ff.get('Physical Qualities'));kind=work_type(medium)
 if dates['date_issue']:flags.append('creation_date_requires_review')
 if kind=='unknown':flags.append('object_type_requires_review')
 if not ff.get('Object Number') or not ff.get('Credit Line'):flags.append('inventory_or_credit_requires_review')
 if not dims:flags.append('dimensions_not_separated')
 creator=z['creator_label'];artist_names=[p['name'] for p in z['makers'] if p['role']=='Artist' and p['name']]
 additional=[name for name in artist_names if m.norm(name) not in m.norm(creator or '')]
 if additional:creator='; '.join(([creator] if creator else [])+additional)
 labels=sorted({v for v in [z['creator_label']]+[p['name'] for p in z['makers']] if v})
 if z['creator_label']!=z['hero_creator']:flags.append('hero_detail_creator_difference')
 if not creator:flags.append('unnamed_creator')
 if len(z['makers'])>1 or re.search(r'and others|\bet al\b',creator or '',re.I):flags.append('multiple_creators_or_truncated_heading')
 if any(v['role']!='Artist' for v in z['makers']):flags.append('creator_role_requires_review')
 for maker in z['makers']:
  years=[int(y) for y in re.findall(r'(?<!\d)\d{3,4}(?!\d)',maker['biography'] or '')]
  if 2<=len(years)<=4 and max(years)-min(years)>=10 and (dates['first'],dates['last'])==(min(years),max(years)):flags.append('creation_matches_creator_life_or_activity')
 provenance=' '.join(v['text'] or '' for v in z['sections'] if v['label']=='Provenance')
 if re.search(r'\b(?:deaccession\w*|restitu\w*|repatriat\w*|lost|missing|location[^;.]*unknown|loan|lent|borrow\w*|promised gift)\b',provenance+' '+(ff.get('Credit Line') or ''),re.I):flags.append('holding_or_custody_requires_review')
 if re.search(r'\b(?:pair|diptych|triptych|polyptych|verso|reverse|fragment|part of|pendant|copy|after|workshop|attributed|circle|school|cast|edition|portfolio|album|studies)\b',z['title']+' '+(creator or ''),re.I):flags.append('physical_version_or_qualified_creator_review')
 titles={z['title']}
 for section in z['sections']:
  for title in re.findall(r'(?:Exhibited|Published) as ["“]([^"”]+)["”]',section['text'] or '',re.I):titles.add(title)
 facts=dict(source_id=row['source_id'],native_object_id=row['source_id'],source_url=z['canonical'],native_page_urls=sorted({z['canonical'],row['url'],row['url'].replace('://artbma.org/','://collection.artbma.org/')}),native_metadata_urls=[],wikidata_ids=[],title=z['title'],titles=sorted(titles),creator_label=creator,detail_creator_label=creator,identity_creator_labels=labels,creator_label_kind='source_object_heading',date_display=z['date_display'],**dates,inventory=ff.get('Object Number'),medium=medium,dimensions_text=dims,work_type=kind,object_form=None,credit_line=ff.get('Credit Line'),source_fields=z['fields'],source_sections=z['sections'],source_makers=z['makers'],source_wall_text=z['wall_text'],source_rights=z['rights_labels'],source_display_label=z['display_label'],source_note='Literal official object HTML, native physical-qualities string, credits, dates, creator roles, biography, provenance and qualifications preserved. Search index numeric IDs remain discovery IDs, not invented accessions. Historic translated titles are discovery aliases only. Unknown rights remain unknown. No image, display, custody or ownership claim.')
 facts.update(source_detail_creator_heading=z['creator_label'],source_hero_creator_heading=z['hero_creator'],source_declared_url_basis=z['declared_url_basis'],creator_label_basis='Qualified main detail heading, with separately named additional Artist-role contributors appended. Printer/publisher roles remain evidence and discovery labels, not promoted to artists.')
 return dict(provider='baltimore',institution_id=IID,number=x['number'],source_id=row['source_id'],facts=facts,index=row,source_reference=ref(path),retrieved_at=x['capture']['receipt']['retrieved_at'],state='source_candidate',review_flags=sorted(set(flags)))
def dependencies():
 files={Path(__file__).resolve()};seen=set()
 def visit(mod):
  if id(mod) in seen:return
  seen.add(id(mod));file=getattr(mod,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  files.add(Path(file).resolve())
  for v in vars(mod).values():
   if isinstance(v,types.ModuleType):visit(v)
 visit(c);return [ref(p) for p in sorted(files)]
def main(suffix,partial):
 paths=sorted((RUN/'objects-001').glob('*.json.gz'));expected=len(m.load(c.QUEUE)['selected']);assert partial or len(paths)==expected
 rows=[parse(p) for p in paths];out=RUN/('native-candidates-'+suffix+'.json.gz');assert not out.exists()
 m.save(out,dict(at=m.now(),rows=rows,parser_reference=ref(Path(__file__).resolve()),dependencies=dependencies(),queue_reference=ref(c.QUEUE),capture_count=len(paths),expected_capture_count=expected,partial=partial,policy='Literal source facts only, not editorial approval. Verify source dates, physical versions, complete creators, holding evidence and existing catalogue identities before any selected addition.'))
 print(json.dumps(dict(rows=len(rows),partial=partial,flags=[dict(number=r['number'],title=r['facts']['title'],flags=r['review_flags']) for r in rows if r['review_flags']])),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);p.add_argument('--partial',action='store_true');a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix,a.partial)
