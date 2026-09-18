#!/usr/bin/env python3
"""Review scoped source IDs, accessions, artist authorities and title collisions."""
import argparse,pathlib,json,re,collections,importlib.util
import psycopg
from psycopg.rows import dict_row
p=argparse.ArgumentParser();p.add_argument('--run',type=pathlib.Path,required=True);a=p.parse_args();root=pathlib.Path(__file__).resolve().parents[1];run=a.run.resolve();s=importlib.util.spec_from_file_location('nga',root/'ops/overnight-nga-commons.py');nga=importlib.util.module_from_spec(s);s.loader.exec_module(nga);rows=json.loads((run/'source-candidates.json').read_text());aids=sorted({c['artist']['id'] for c in rows});held=[];out=[]
with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
 iid=db.execute("SELECT id::text FROM institutions WHERE slug='national-gallery-of-art'").fetchone()['id']
 prior=db.execute("""SELECT a.id::text,a.title,a.alternate_title,a.accession_number,a.current_institution_id::text,
    (SELECT jsonb_agg(aa.artist_id::text) FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids,
    (SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='european-nga-object') nga_id,
    (SELECT external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qid
    FROM artworks a WHERE a.current_institution_id=%s OR a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[]))
    OR a.id IN (SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s)""",(iid,aids,iid)).fetchall()
 qids={c['object']['wikidataid'] for c in rows if c['object']['wikidataid']};existing_qids={r['external_id']:r['entity_id'] for r in db.execute("SELECT external_id,entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s)",(list(qids),)).fetchall()}
 artist_titles=collections.defaultdict(list);accessions=collections.defaultdict(list)
 for old in prior:
  if old['current_institution_id']==iid or old['nga_id']:accessions[nga.norm(old['accession_number'] or '')].append(old)
  for a in old['artist_ids'] or []:
   for t in [old['title'],old['alternate_title']]:
    if t:artist_titles[(a,nga.norm(t))].append(old)
 aliases=collections.defaultdict(set)
 for x in db.execute('SELECT artist_id::text,alias FROM artist_aliases WHERE artist_id=ANY(%s::uuid[])',(aids,)).fetchall():aliases[x['artist_id']].add(nga.norm(x['alias']))
 artist_qids={x['entity_id']:x['external_id'] for x in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artist' AND scheme='wikidata' AND entity_id=ANY(%s::uuid[])",(aids,)).fetchall()}
 for c in rows:
  o=c['object'];ar=c['artist'];person=c['creator'];reasons=[]
  if o['wikidataid'] in existing_qids:reasons.append('Existing artwork Wikidata identifier')
  if accessions.get(nga.norm(o['accessionnum'])):reasons.append('Existing NGA accession')
  conflicts=[x for x in artist_titles.get((ar['id'],nga.norm(o['title'])),[]) if not x['nga_id']]
  if conflicts:reasons.append('Same artist/title without distinct authoritative object identity')
  name_ok=nga.norm(person['forwarddisplayname']) in aliases[ar['id']]|{nga.norm(ar['display_name'])}
  qid_ok=person['wikidataid'] and person['wikidataid']==artist_qids.get(ar['id'])
  if not name_ok and not qid_ok:reasons.append('Artist name/authority needs review')
  if person['wikidataid'] and artist_qids.get(ar['id']) and person['wikidataid']!=artist_qids[ar['id']]:reasons.append('Museum and existing artist Wikidata conflict')
  if reasons:held.append({'object_id':o['objectid'],'reasons':reasons,'possible_duplicate_ids':[x['id'] for x in conflicts]});continue
  out.append(c)
nga.core.save_new(run/'after-duplicate-review.json',out);nga.core.save_new(run/'duplicate-held.json',held);nga.core.save_new(run/'duplicate-review-report.json',{'at':nga.core.now(),'existing_scoped_objects':len(prior),'artist_ids':len(aids),'accepted':len(out),'popular':sum(x['artist']['popular'] for x in out),'types':dict(collections.Counter(x['object']['classification'] for x in out)),'held_reasons':dict(collections.Counter(reason for x in held for reason in x['reasons']))})
print('NGA accepted',len(out),'popular',sum(x['artist']['popular'] for x in out),'types',dict(collections.Counter(x['object']['classification'] for x in out)),'held',len(held),flush=True)
