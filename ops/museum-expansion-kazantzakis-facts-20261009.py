"""Literal object facts; source attribution and date uncertainty are preserved."""
import collections,gzip,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'));q=importlib.util.module_from_spec(z);z.loader.exec_module(q);s=q.s;m=q.m;RUN=q.RUN

def date(value):
 if not value:return None,None,'unknown'
 if re.fullmatch(r'\d{4}',value):return int(value),int(value),'exact'
 match=re.fullmatch(r'(\d{4})\s*[-–]\s*(\d{4})',value)
 if match:
  first,last=map(int,match.groups());assert first<=last;return first,last,'range'
 raise ValueError('Unreviewed date '+value)
def invkey(v):return m.norm(v)if v else None
def one(fields,key):
 vs=fields.get(key,[]);assert len(vs)<=1,(key,vs);return vs[0]if vs else None
def rows():
 out=[]
 for r in m.load(RUN/'native-selection-001.json.gz')['rows']:
  fs=r['fields'];title=one(fs,'Τίτλος');creator=one(fs,'Δημιουργός');ds=one(fs,'Ημερομηνία');first,last,precision=date(ds);types=fs.get('Τύπος',[]);description=fs.get('Περιγραφή',[]);typ='drawing'if any('μακέτα κοστουμιού'in v for v in types)else 'unknown';nonart=any('αλληλογραφία'in v for v in types)
  if nonart:state='not_an_artwork'
  elif first is None:state='unknown_date_review_deferred'
  elif first>1970:state='outside_creation_scope'
  elif last>1970:state='cutoff_date_review_hold'
  else:state='eligible_metadata_candidate'
  soup=BeautifulSoup(gzip.decompress((m.ROOT/r['receipt']['body_path']).read_bytes()),'html.parser');rights=list({a['href']:dict(url=a['href'],label=q.clean(a.get_text(' ',strip=True)))for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']}.values());image=soup.find('img',src=lambda v:v and '/thumbnails/edm-record/'+r['source_id'] in v);native=[v['url']for v in r['links']if '/records/'in v['url']];f=dict(source_id=r['source_id'],native_id=r['source_id'],source_url=r['source_url'],native_page_urls=sorted(set([r['source_url']]+native)),title=title,titles=[title],creator_label=creator,date_display=ds or 'Creation date unknown',first=first,last=last,date_precision=precision,work_type=typ,object_form=None,medium=None,dimensions_text=None,inventory=None,description_md=None,source_narrative='\n'.join(description),source_fields=fs,semantic_enrichment=r['enrichment'],rights=rights,rights_label='; '.join(v['label']or v['url']for v in rights),source_links=r['links'],thumbnail_url=q.BASE+image['src']if image and image['src'].startswith('/')else image['src']if image else None,image_downloaded=False,date_policy='Dedicated Date field on the individually catalogued physical design/artwork,reviewed alongside its description. Enriched historical periods,artist lifespans,publication/performance contexts and repository timestamps do not independently date creation. Unknown and crossing dates are held; no inferred years.',creator_policy='Literal source creator retained. EKT-enriched creator and related-person labels are separate evidence; no silent resolution of unknown original creators or artist-authority linking.')
  out.append(dict(number=r['number'],source_id=r['source_id'],retrieved_at=r['receipt']['retrieved_at'],facts=f,receipt=r['receipt'],metadata_state=state))
 return out
if __name__=='__main__':
 out=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,source_reference=s.ref(RUN/'native-selection-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='No source IDs masquerade as accession numbers. Materials/dimensions unknown unless separately supported. Original unknown creator labels preserved despite enrichment.'));print(json.dumps(dict(rows=len(out),states=dict(collections.Counter(v['metadata_state']for v in out)))),flush=True)
