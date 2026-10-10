import importlib.util,copy,collections,re,json
from pathlib import Path
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
rows=m.base.load(m.RUN/'gap-final-plan-v2.json.gz');qids=[r['artist_qid'] for r in rows]
with m.base.connect('production') as db:
 artists=db.execute("SELECT a.id,a.slug,a.display_name,e.external_id FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=ANY(%s) AND a.status<>'archived'",(qids,)).fetchall();byartist={r['external_id']:r for r in artists}
 ids=[r['id'] for r in artists]
 works=db.execute('''SELECT w.id,w.slug,w.title,w.creation_year_start,w.creation_year_end,w.date_precision,w.status,w.primary_media_id,w.accession_number,w.unlinked_creator_label,aa.artist_id,aa.attribution_role,e.external_id wikidata,i.external_id institution_wikidata
 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id LEFT JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=w.id AND e.scheme='wikidata'
 LEFT JOIN external_identifiers i ON i.entity_type='institution' AND i.entity_id=w.current_institution_id AND i.scheme='wikidata'
 WHERE aa.artist_id=ANY(%s::uuid[]) AND w.status<>'archived' ''',(ids,)).fetchall()
 globalworks=db.execute('''SELECT e.external_id wikidata,w.id,w.slug,w.title,w.creation_year_start,w.creation_year_end,w.date_precision,w.status,w.primary_media_id,w.unlinked_creator_label,
 ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=w.id) creator_ids FROM external_identifiers e JOIN artworks w ON w.id=e.entity_id
 WHERE e.entity_type='artwork' AND e.scheme='wikidata' AND e.external_id=ANY(%s)''',([r['work_qid'] for r in rows],)).fetchall()
 m.base.save(m.BACKUP/'production-gap-reconciled-preflight.json.gz',dict(artists=artists,works=works,globalworks=globalworks))
 globalbyqid={r['wikidata']:r for r in globalworks};grouped=collections.defaultdict(list)
 for r in works:grouped[str(r['artist_id'])].append(r)
 ready=[];held=[];norm=lambda x:re.sub(r'\W','',x.casefold())
 for original in rows:
  r=copy.deepcopy(original);artist=byartist.get(r['artist_qid'])
  if not artist:held.append(dict(work=r['work_qid'],reason='no_existing_production_artist_authority'));continue
  r.update(artist_id=str(artist['id']),artist_slug=artist['slug']);candidate=globalbyqid.get(r['work_qid']);link=False
  if candidate:
   if candidate['status']=='archived':held.append(dict(work=r['work_qid'],reason='archived_source_object'));continue
   if r['artist_id'] not in candidate['creator_ids']:
    if candidate['creator_ids'] or norm(candidate['unlinked_creator_label'] or '')!=norm(r['artist_name']):held.append(dict(work=r['work_qid'],reason='creator_link_requires_reconciliation'));continue
    link=True
  else:
   matches={str(w['id']):w for w in grouped[r['artist_id']] if w['institution_wikidata'] in r['collections'] and w['accession_number'] and norm(w['accession_number']) in {norm(x) for x in r['inventory'] if isinstance(x,str)}}
   if len(matches)>1:held.append(dict(work=r['work_qid'],reason='ambiguous_inventory'));continue
   candidate=next(iter(matches.values()),None)
   if not candidate and any(norm(w['title'])==norm(r['title']) for w in grouped[r['artist_id']]):held.append(dict(work=r['work_qid'],reason='possible_duplicate_title'));continue
  if candidate:
   if candidate['creation_year_start']!=r['year'] or candidate['creation_year_end'] not in [None,r['year']] or candidate['date_precision'] not in ['exact','circa']:held.append(dict(work=r['work_qid'],reason='existing_source_date_difference'));continue
   r['targets']['production']=dict(artwork_id=str(candidate['id']),slug=candidate['slug'],new=False,primary_media_id=str(candidate['primary_media_id']) if candidate['primary_media_id'] else None,status=candidate['status'],link_creator=link,original_creator_label=candidate.get('unlinked_creator_label'))
  ready.append(r)
 m.save('gap-production-plan-v3.json.gz',ready);m.save('gap-production-held-v3.json.gz',held)
 review=m.base.load(m.RUN/'visual-review.json');review.update(plan_sha256=m.base.digest(m.RUN/'gap-production-plan-v3.json.gz'),parent_plan_sha256=m.base.digest(m.RUN/'gap-final-plan-v2.json.gz'),production_identity_reconciliation='Exact existing artist Wikidata authority, global artwork authority, and preserved original creator labels; no duplicate artwork creation')
 m.save('visual-review-production.json',review)
 print('production',len(ready),'held',held,'new',sum(r['targets']['production']['new'] for r in ready),'creator_links',sum(r['targets']['production'].get('link_creator',False) for r in ready))
