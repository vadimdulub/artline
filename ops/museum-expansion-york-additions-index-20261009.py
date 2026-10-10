"""Three bounded native York index pages; discovery only, no object/image or database writes."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;PRIOR=n.RUN;RUN=m.RUN/'native/york-additions-20261009';n.RUN=RUN;IID='87750cb4-a118-5588-876c-999695cbe14b';CP=PRIOR/'delivery-checkpoint-001.json'
def main():
 dest=RUN/'native-index-001.json.gz';assert not dest.exists();assert n.ref(CP)['sha256']=='b18514150f7dd97550b6bb1309177f695764a55c6f1f81b0cf3544d556b4a11c';context=m.load(PRIOR/'native-extra-001.json.gz');first=next(v for v in context['rows'] if v.get('provider')=='york');captures=[];rows=[];failures=[];url=first['url']
 for page in range(1,4):
  try:
   if page==1:
    c=first['capture'];raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256']
   else:raw,c=n.capture('york',url)
   soup=n.BeautifulSoup(raw,'html.parser');hits=[]
   for a in soup.select('a[href]'):
    obj=a.select_one('.object_number')
    if not obj:continue
    fields={k:(a.select_one('.'+k).get_text(' ',strip=True) if a.select_one('.'+k) else None) for k in ['object_number','title','creator','dates']};assert fields['object_number'].startswith('YORAG : ');link=urljoin(url,a['href']);oid=parse_qs(urlparse(link).query).get('id');assert oid and len(oid)==1 and oid[0].isdigit();entry=dict(number=len(rows)+1,page=page,institution_id=IID,fields=fields,url=link,native_id=oid[0],index_url=url,capture_reference=n.ref(m.ROOT/c['body_path']));rows.append(entry);hits.append(entry)
   assert len(hits)<=16 and hits;captures.append(dict(page=page,url=url,capture=c,objects=len(hits)));print(json.dumps(dict(page=page,objects=len(hits))),flush=True)
   if page<3:
    nxt=next((a for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Next page'),None);assert nxt;url=urljoin(url,nxt['href']);assert parse_qs(urlparse(url).query)['collections_page']==[str(page+1)]
  except Exception as e:
   failures.append(dict(page=page,url=url,error=type(e).__name__+': '+str(e)));print(json.dumps(failures[-1]),flush=True);break
 assert len({v['native_id'] for v in rows})==len(rows)
 with m.connect() as db:
  invs=[v['fields']['object_number'] for v in rows];existing=db.execute('SELECT id::text,title,accession_number,current_institution_id::text,status FROM artworks WHERE accession_number=ANY(%s) ORDER BY accession_number,id',(invs,)).fetchall();counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
 m.save(dest,dict(at=m.now(),rows=rows,captures=captures,failed_selected_requests=failures,exact_inventory_existing_discovery=existing,before_counts=counts,previous_checkpoint_reference=n.ref(CP),first_page_reference=n.ref(PRIOR/'native-extra-001.json.gz'),script_reference=n.ref(Path(__file__).resolve()),policy='Maximum3pages/48 museum-scoped FineArt index entries. First page reuses verified fresh prior capture; follow only observed next-page links. Exact string inventory lookup is discovery,not complete normalized/source/creator/version identity review. Index dates are unreviewed source strings; no creation classifications or publication. No object pages,images or database mutations.'))
 print(json.dumps(dict(leads=len(rows),existing_exact_inventory_hits=len(existing),before=counts,failed=len(failures))),flush=True)
if __name__=='__main__':main()
