"""Read-only duplicate audit; no event identity inferred from title alone."""
import difflib,json
import historical_exhibitions_fitzwilliam_london_early_discovery_20261012 as d
c=d.c;n=d.m.f.n
leads=c.load(d.OUT/'discovery.json.gz')['records'];years=sorted({int(v[:4])for r in leads for v in r['lead']['dates']})
with c.connect()as db:
 candidates=n.normal(db.execute("SELECT e.id,e.title,e.start_year,e.end_year,o.city_label,o.venue_label FROM exhibitions e LEFT JOIN exhibition_occurrences o ON o.exhibition_id=e.id WHERE e.start_year=ANY(%s) AND e.status<>'archived'",(years,)).fetchall())
 nids=sorted({o['nativeID']for r in leads for o in r['objects']})
 works=n.normal(db.execute("SELECT x.external_id,a.id,a.title,a.accession_number,a.primary_media_id FROM external_identifiers x JOIN artworks a ON a.id=x.entity_id WHERE x.scheme='fitzwilliam-native-object' AND x.external_id=ANY(%s)",(nids,)).fetchall())
reviews=[]
for row in leads:
 r=row['lead'];year=int(r['dates'][0][:4]);matches=[]
 for x in candidates:
  if x['start_year']!=year:continue
  ratio=difflib.SequenceMatcher(None,c.norm(r['title']),c.norm(x['title'])).ratio()
  if ratio>=.42:matches.append(dict(record=x,similarity=round(ratio,3)))
 matches=sorted(matches,key=lambda x:-x['similarity'])[:5];reviews.append(dict(lead=r,matches=matches))
 print(r['nativeID'],r['title'],[(x['record']['title'],x['record']['city_label'],x['similarity'])for x in matches])
result=dict(at=c.now(),candidates=candidates,reviews=reviews,existingNativeObjects=works,newProductionEvents=0)
c.save(d.OUT/'production-duplicate-audit.json.gz',result);print('Existing native objects',len(works))
