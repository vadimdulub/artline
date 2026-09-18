#!/usr/bin/env python3
"""Read-only verification of exact planned identities, images and publication."""
import importlib.util,json,collections,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;r=b.r;OUT=s.RUN/('verification-final' if '--final' in sys.argv else '')
plan=json.loads((s.RUN/'batches/batch-001.json').read_bytes());expected={x['record']['qid']:x for x in plan['entries']};targets={}
for target in ['local','production']:
 with s.connect(target) as db:
  db.execute('SET TRANSACTION READ ONLY')
  rows=db.execute('''SELECT e.external_id qid,a.id::text,a.slug,a.title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.status,a.primary_media_id::text,a.unlinked_creator_label,i.slug institution,m.checksum_sha256 image_sha,m.byte_size,m.rights_status,m.creator_credit,m.license_url,m.storage_path,me.source_checksum rights_source_checksum,
   (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.review_state='review' AND l.claim_type='holding') review_holdings,
   (SELECT count(*) FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND l.claim_type='display') display_claims,
   (SELECT count(*) FROM citations c WHERE c.entity_id=a.id AND c.entity_type='artwork') citations,
   artline_has_selection_evidence(a.id) selected,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope
   FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id AND e.entity_type='artwork'
   LEFT JOIN institutions i ON i.id=a.current_institution_id LEFT JOIN media_assets m ON m.id=a.primary_media_id LEFT JOIN media_rights_evidence me ON me.media_id=m.id
   WHERE e.scheme='wikidata' AND e.external_id=ANY(%s) ORDER BY e.external_id''',(list(expected),)).fetchall()
  assert len(rows)==len(expected)
  for row in rows:
   rec=expected[row['qid']]['record'];im=expected[row['qid']]['image'];d=rec['date'];assert row['title']==rec['title'] and row['status']=='review';assert (row['creation_year_start'],row['creation_year_end'],row['date_precision'])==(d['first'],d['last'],d['precision']);assert row['review_holdings']==1 and not row['display_claims'] and row['citations']>0 and row['selected']
   assert bool(im)==bool(row['primary_media_id'])
   if im:assert row['image_sha'].strip()==im['sha256'] and row['byte_size']<=100000 and row['rights_source_checksum'] and row['creator_credit'] and row['license_url'] and row['scope']=='eligible'
  gender=db.execute('SELECT count(*) n FROM artist_gender_evidence WHERE is_woman').fetchone()['n'];women_scope=db.execute("SELECT count(*) n FROM artists a JOIN artist_gender_evidence g ON g.artist_id=a.id AND g.is_woman WHERE a.status<>'archived' AND a.timeline_start_year<=2000 AND a.timeline_end_year>=1100").fetchone()['n']
  source=db.execute("SELECT count(DISTINCT a.id) n FROM artists a WHERE a.status='review' AND EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=ANY(%s))",(list({x['record']['creator_qid'] for x in plan['entries']}),)).fetchone()['n']
 targets[target]={'at':s.core.now(),'artworks':len(rows),'images':sum(bool(x['primary_media_id']) for x in rows),'unknown_dates':sum(x['date_precision']=='unknown' for x in rows),'unlinked_creator_labels':sum(bool(x['unlinked_creator_label']) for x in rows),'review_creator_profiles_in_selected_set':source,'women_evidence_total':gender,'women_timeline_total':women_scope,'rows':rows}
 s.save(OUT/('verification-'+target+'.json'),targets[target]);print(target,{k:v for k,v in targets[target].items() if k!='rows'},flush=True)
compare=lambda target:[{k:v for k,v in x.items() if k not in ('id',)} for x in targets[target]['rows']]
assert compare('local')==compare('production')
s.save(OUT/'final-verification.json',{'at':s.core.now(),'targets':{k:{a:b for a,b in v.items() if a!='rows'} for k,v in targets.items()},'exact_target_parity':True})
