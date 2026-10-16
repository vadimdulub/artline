import importlib.util,json,re,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('b','ops/continuous-mnac-batch-000099.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;b.PHASE='mnac-medieval-v3'
lock=(b.R/'worker.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
parsed=h.load(b.E/'parsed-native-objects.json');records=[];checks=[];artistchecks=[]
def acc(s):return re.sub(r'^0+','',str(s or '').upper().replace(' ','').replace('-000',''))
dates={'Últim quart del segle XIV':(1376,1400),'Segle XIV':(1301,1400),'Finals del segle XIV':(1301,1400),'Primera meitat del segle XIV':(1301,1350),'Segon quart del segle XIV':(1326,1350),'Tercer quart del segle XIV':(1351,1375),'Segona meitat del segle XIV':(1351,1400)}
with h.connect() as db:
 existing=[r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artworks a WHERE current_institution_id=%s ORDER BY id LIMIT 2001',(b.MID,))];assert len(existing)<=2000
 b.save('institution-scope-before.json.gz',existing)
 ids=[a['id'] for a in existing];idents=[dict(r) for r in db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,))];b.save('institution-identifiers-before.json',idents)
 aliases=[dict(r) for r in db.execute("SELECT id::text,display_name name FROM artists WHERE status<>'archived' UNION SELECT a.id::text,al.alias name FROM artist_aliases al JOIN artists a ON a.id=al.artist_id WHERE a.status<>'archived'")]
 for x in parsed:
  ft=x['features'];inv=next(f.split(': ',1)[1] for f in ft if f.startswith('Inventory number:'));date=ft[1];label='; '.join(x['creators']);reason=None;matched=[]
  for a in existing:
   if acc(a['accession_number'])==acc(inv) or inv.split('-')[0] in a['title'] or h.norm(a['title'])==h.norm(x['title']):matched.append(a['id'])
  matched+= [r['entity_id'] for r in idents if acc(r['external_id'])==acc(inv) or inv.lower() in (r['canonical_url'] or '').lower()]
  globalmatch=[dict(r) for r in db.execute("SELECT id::text,title,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s)",([inv,inv.split('-')[0]],))]
  sourcematch=[dict(r) for r in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=%s UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=%s",(x['url'],x['url']))]
  matched=sorted(set(matched+[r['id'] for r in globalmatch]+[r['entity_id'] for r in sourcematch]))
  if matched:reason='Existing or unresolved physical object identity; do not duplicate'
  elif 'loan' in ft[3].lower() and inv!='035677-000':reason='Source explicitly identifies long-term loan/custody; not an ownership holding'
  elif inv=='024059-000':reason='Painted structural baldachin with separate construction/polychromy periods; object/component review needed'
  years=[int(y) for y in re.findall(r'(?<!\d)1\d{3}(?!\d)',date)]
  if date in dates:lo,hi=dates[date];basis='Conservative closed source-century bounds using established 1301–1400 convention; half and quarter wording bounded literally. Finals (late) retains whole century without invented narrower years.'
  elif years and len(years)<=2:lo,hi=min(years),max(years);basis='Explicit source creation year/range; circa qualifier preserved.'
  else:lo=hi=None;reason=reason or 'Source date requires separate review';basis='Unknown; no numeric date invented'
  names={a['id']:a['name'] for a in aliases if h.norm(a['name'])==h.norm(label)}
  artistid=next(iter(names)) if len(names)==1 and not re.search('Anonymous|workshop',label,re.I) else None
  if len(names)>1:reason=reason or 'Ambiguous global creator authorities'
  artistchecks.append(dict(creator_label=label,candidates=names,linked_id=artistid,no_new_painter=True))
  if artistid:
   others=[dict(r) for r in db.execute('SELECT a.id::text,a.title,a.accession_number,a.current_institution_id::text,a.date_display,a.dimensions_text FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s ORDER BY a.id LIMIT 1001',(artistid,))];assert len(others)<=1000
   if any(h.norm(a['title'])==h.norm(x['title']) for a in others):reason=reason or 'Same creator/title requires version reconciliation'
   b.save('creator-scope-'+artistid+'.json',others)
  checks.append(dict(source_id=inv,title=x['title'],creator=label,date=date,existing_ids=matched,global_accession_matches=globalmatch,source_url_matches=sourcematch,outcome=reason or 'selected'))
  print(inv,x['title'],reason or 'SELECTED',flush=True)
  if reason:continue
  assert lo and hi<=1970 and 'Painting' in x['tags']
  medium=next(t for t in x['tags'] if t not in ['Medieval Gothic Art','Gallardo Collection',label,'Religion','Painting'])
  raw=Path(x['receipt']['body_path']).read_bytes();sp=BeautifulSoup(raw,'html.parser');main=sp.select_one('.ds-details') or sp
  records.append(dict(provider='mnac',source_id=inv,museum=b.MUSEUM,title=x['title'],date_display=date,year_start=lo,year_end=hi,date_decision='eligible',date_basis=basis,source_type='painting',creator_label=label,verified_artist_id=artistid,creator_link_hold=not artistid,accession_number=inv,medium=medium,dimensions=ft[2],credit=ft[3],documented_gift_after_former_loan=(inv=='035677-000' and ft[3]=='Long-term loan from the former Bosch i Catarineu Collection, 1934; given by Julio Muñoz Ramonet, 1950'),source_url=x['url'],evidence=x['receipt'],evidence_file=x['receipt']['body_path'],raw=dict(original_title=None,features=ft,tags=x['tags'],source_creators=x['creators'],full_object_text=main.get_text(' ',strip=True)),identity_review='One native inventory unit. Whole altarpieces, triptychs, frontals and surviving fragments are not multiplied into depicted scenes. Exact accession globally and museum title/source identities reconciled. Source attribution retained; no current-display assertion.'))
 inst=db.execute('SELECT slug,website_url FROM institutions WHERE id=%s',(b.MID,)).fetchone();h.museums=lambda:{b.MUSEUM:(inst['slug'],inst['website_url'])}
b.save('global-identity-reconciliation-final.json',dict(at=h.now(),scope_count=len(existing),checks=checks));b.save('global-creator-reconciliation-final.json',dict(at=h.now(),records=artistchecks));h.save(b.E/b.PHASE/'source-records.json.gz',records)
h.plan(b.PHASE)
