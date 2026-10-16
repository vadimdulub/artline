from pathlib import Path
import sys,json,collections,re
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'
ALLOWED={'Painting','Drawing','Print','Portrait Miniature','Monotype','Calligraphy'}
# Manuscripts/portfolios can contain eligible works. Uncertain classifications
# require object review, so this deletion only uses explicit excluded media.
EXCLUDED={'Sculpture','Ceramic','Textile','Metalwork','Photograph','Jewelry','Silver','Enamel','Furniture and woodwork','Lace','Embroidery','Spindle Whorl','Coins','Glass','Jade','Ivory','Arms and Armor','Velvet','Lacquer','Mask','Garment','Plate','Funerary Equipment','Tapestry','Wood','Stone','Musical Instrument','Carpet','Tools and Equipment','Vessels','Glyptic','Cosmetic Objects','Amulets','Basketry','Timepiece','Seals','Netsuke','Leather','Lithographic Stone','Scarabs','Time-based Media','Book Binding','Plaque','Sampler'}
CANON_EXCLUDED={'photograph','photography','sculpture','ceramic','metalwork','textile'}
TABLES=['exhibition_entries','exhibition_publications','exhibition_participants','exhibition_occurrences','exhibition_source_records']
def plan():
 es=c.load(OUT/'historical-entries-for-review.json.gz');ts=c.load(OUT/'cma-selected-classifications.json');candidates=c.load(OUT/'historical-title-medium-review.json')['selected']
 by=collections.defaultdict(list);excluded=[];held=[]
 for e in es:
  native=str(e['evidence'].get('id',''));source=ts.get(native);typ=source.get('type')if source else None
  excluded_type=typ in EXCLUDED or (typ is None and e['work_type']in CANON_EXCLUDED)
  by[e['exhibition_id']].append((e,typ,excluded_type))
  if excluded_type:excluded.append(dict(id=e['id'],exhibition_id=e['exhibition_id'],artwork_id=e['artwork_id'],title=e['title_label'],sourceNativeID=native,sourceType=typ,canonicalType=e['work_type'],sourceEvidence=source))
 selected=[]
 for e in candidates:
  items=by[e['id']]
  reason=None
  if any(t in ALLOWED or (t is None and r['work_type']in ['painting','drawing','print','icon','manuscript_illumination','calligraphy'])for r,t,x in items):reason='Known eligible two-dimensional works; retain mixed exhibition'
  elif any(not x for r,t,x in items):reason='Unclassified entries need object review'
  elif re.search(r'design|original objects|European and American Art|ornamental arts|decorative arts|wade memorial|art of the dance',e['title'],re.I):reason='Potentially mixed exhibition or drawn designs; title insufficient'
  if reason:held.append(dict(**e,reason=reason))
  else:selected.append(e)
 ids=[e['id']for e in selected];entryids=[e['id']for e in excluded if e['exhibition_id']not in set(ids)]
 with c.connect()as db:
  rows=db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall();assert len(rows)==len(ids)
  assert not db.execute('SELECT id FROM exhibitions WHERE parent_exhibition_id=ANY(%s::uuid[]) AND NOT(id=ANY(%s::uuid[]))',(ids,ids)).fetchall()
  counts={t:db.execute('SELECT count(*) n FROM '+t+' WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']for t in TABLES}
  pinned=db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id',(entryids,)).fetchall();assert len(pinned)==len(entryids)
 c.save(OUT/'medium-removal-plan.json',dict(at=c.now(),events=rows,dependentCounts=counts,entries=pinned,decisions=excluded,heldEvents=held,sourceIndexSHA256=c.sha((OUT/'cma-selected-classifications.json').read_bytes()),rule='Remove source-confirmed excluded media from exhibitions only; retain mixed events and uncertain objects. Main catalogue deletion uses a separate 546-work reviewed scope.'))
 print(json.dumps(dict(events=len(rows),additionalEntries=len(pinned),dependentCounts=counts,heldEvents=len(held),entryTypes=dict(collections.Counter(e['sourceType']or e['canonicalType']for e in excluded))),indent=2),flush=True)
def apply():
 p=c.load(OUT/'medium-removal-plan.json');ids=[e['id']for e in p['events']];entryids=[e['id']for e in p['entries']]
 with c.connect(write=True)as db:
  db.execute('SELECT pg_advisory_xact_lock(2026101201)')
  now=db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();assert json.loads(json.dumps(now,default=str))==p['events']
  now=db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(entryids,)).fetchall();assert json.loads(json.dumps(now,default=str))==p['entries']
  counts={}
  counts['excludedEntriesInRetainedEvents']=db.execute('DELETE FROM exhibition_entries WHERE id=ANY(%s::uuid[])',(entryids,)).rowcount;assert counts['excludedEntriesInRetainedEvents']==len(entryids)
  for t in TABLES:
   counts[t]=db.execute('DELETE FROM '+t+' WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).rowcount;assert counts[t]==p['dependentCounts'][t]
  counts['exhibitions']=db.execute('DELETE FROM exhibitions WHERE id=ANY(%s::uuid[])',(ids,)).rowcount;assert counts['exhibitions']==len(ids)
  counts['remainingActiveExhibitions']=db.execute("SELECT count(*) n FROM exhibitions WHERE status<>'archived'").fetchone()['n']
 c.save(OUT/'medium-removal-delivered.json',dict(at=c.now(),counts=counts,planSHA256=c.sha((OUT/'medium-removal-plan.json').read_bytes()),realLocalDatabaseWrites=False));print(json.dumps(counts),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
