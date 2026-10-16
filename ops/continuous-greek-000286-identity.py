import importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-greek-batch-000286.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h
rs=h.load(b.E/b.PHASE/'source-records.json.gz');chosen=[r for r in rs if 'Koutlidis' not in r['credit']]
for r in chosen:b.capture(r['raw']['creator_url'])
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 names=[dict(x) for x in db.execute('SELECT id::text,display_name name,birth_year,death_year,status FROM artists UNION SELECT a.id::text,al.alias name,a.birth_year,a.death_year,a.status FROM artist_aliases al JOIN artists a ON a.id=al.artist_id')]
 terms=['bonheur','bonnat','bores','μπόρες','μπορες'];artists=[x for x in names if any(t in h.norm(x['name']) for t in terms)]
 b.save('creator-authority-global-review.json',dict(at=h.now(),terms=terms,candidates=artists,all_names_and_aliases_inspected=len(names)))
 print('ARTISTS',json.dumps(artists,ensure_ascii=False))
 acc=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,current_institution_id::text,status FROM artworks WHERE accession_number=ANY(%s)',([r['accession_number'] for r in chosen],))]
 urls=[r['source_url'] for r in chosen];native=[dict(x) for x in db.execute("SELECT entity_id::text,canonical_url,scheme,external_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=ANY(%s) AND external_id=ANY(%s)))",(urls,h.SCHEMES['athens'],[r['source_id'] for r in chosen]))]
 citations=[dict(x) for x in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)",(urls,))]
 aids=sorted({r['id'] for r in artists});works=[dict(x) for x in db.execute('SELECT a.id::text,a.title,a.alternate_title,a.accession_number,a.dimensions_text,a.date_display,a.current_institution_id::text,aa.artist_id::text,a.primary_media_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) ORDER BY aa.artist_id,a.id LIMIT 1000',(aids,))]
 assert len(works)<1000
 labels=[dict(x) for x in db.execute("SELECT id::text,title,accession_number,unlinked_creator_label,current_institution_id::text FROM artworks WHERE unlinked_creator_label ~* 'bonheur|bonnat|bores' LIMIT 500")];assert len(labels)<500
 titles=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,unlinked_creator_label,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s)',([h.norm(r['title']) for r in chosen],))]
 b.save('global-artwork-version-reconciliation.json',dict(at=h.now(),global_accession_matches=acc,native_matches=native,source_citation_matches=citations,linked_creator_works=works,unlinked_maker_works=labels,exact_normalized_titles=titles))
 preserved=h.snapshot(db,sorted({r['id'] for r in works+labels+titles}));h.save(b.E/'other-identity-candidates-before.json.gz',dict(at=h.now(),artworks=preserved))
 print('COUNTS',len(works),len(labels),len(titles),'ACCESSIONS',acc,'NATIVE',native,'CITES',citations)
 for x in works:
  if re.search('horse|cheva|salv|palette|fruit',x['title']+' '+str(x['alternate_title']),re.I):print('TITLE CANDIDATE',json.dumps(x,ensure_ascii=False))
 print('LABELS',json.dumps(labels,ensure_ascii=False));print('TITLES',json.dumps(titles,ensure_ascii=False))
