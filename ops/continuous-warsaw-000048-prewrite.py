#!/usr/bin/env python3
"""Reparse official captures and reconcile live object/creator identities before writes."""
import gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('b','ops/continuous-warsaw-batch-000048.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E
p,pin=h.pinned(b.PHASE);ids=[r['artwork_id'] for r in p['records']];checks=[];creators=[]
periods={'XIX w.':(1801,1900),'1. poł. XIX w.':(1801,1850),'1. poł. XVIII w.':(1701,1750),'4. ćw. XIX w.':(1876,1900),'XVII w.':(1601,1700)}
with h.connect() as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
 assert not h.snapshot(db,ids)
 b.no_collision(db,p['records'])
 for r in p['records']:
  rc=r['api_receipt'];raw=gzip.decompress(Path(rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256'] and rc['status']==200
  o=json.loads(raw)['data'];assert o==r['raw'];assert str(o['id'])==r['source_id'] and o['title']==r['title'] and o['noEvidence']==r['accession_number']
  assert o['dimensionText']==r['dimensions'];assert r['creator_label']==b.attribution(o) and not r['artist_id'] and r['creator_link_hold']
  assert len(o['createDates'])==1 and not o['createDates'][0]['comment'] and o['createDates'][0]['name']==r['date_display']
  assert periods[r['date_display']]==(r['first'],r['last']) and r['last']<=1900 and r['precision']=='range'
  assert r['medium']=='; '.join(x['name']+(' ('+x['comment']+')' if x.get('comment') else '') for x in o['techniques']+o['materials'])
  assert 'tempera' in [x['name'] for x in o['techniques']] and 'ikona' in [x['name'] for x in o['types']] and 'okład' not in [x['name'] for x in o['types']]
  assert o['owner']=={'id':107515,'name':'Muzeum Narodowe w Warszawie'} and o['image']['position']==1 and not o['connections']
  assert o['copyrights'] and all(x['name']=='DOMENA PUBLICZNA' and not x['restricted'] for x in o['copyrights'])
  titles=[dict(x) for x in db.execute('SELECT id::text,title,accession_number,dimensions_text,current_institution_id::text FROM artworks WHERE normalized_title=%s LIMIT 25',(h.norm(r['title']),))];assert not titles,'Same title needs manual comparison'
  authors=[]
  for a in o['authors']:
   assert re.search(r'warsztat|szkoła',a['name'],re.I)
   matches=[dict(x) for x in db.execute("SELECT id::text,display_name name FROM artists WHERE normalized_name=%s UNION SELECT a.id::text,a.display_name name FROM artist_aliases al JOIN artists a ON a.id=al.artist_id WHERE lower(al.alias)=lower(%s)",(h.norm(a['name']),a['name']))]
   authors.append(dict(native_author_id=a['id'],name=a['name'],role=a['role'],comment=a['comment'],global_exact_matches=matches,decision='Workshop/school label is not an identified individual; retain object label and native authority ID without inventing painter'))
  creators.append(dict(source_id=r['source_id'],authors=authors))
  checks.append(dict(source_id=r['source_id'],artwork_id=r['artwork_id'],title=r['title'],inventory=r['accession_number'],source_sha256=rc['sha256'],selected_evidence_sha256=r['evidence']['sha256'],date_display=r['date_display'],date_bounds=[r['first'],r['last']],creator_label=r['creator_label'],dimensions=r['dimensions'],global_title_matches=titles,ownership=o['owner'],historical_numbers=o['extraNumPatterns'],source_provenance=o['historicalProvenance'],history=o['history'],whole_inventory_object=True,scene_count_not_artwork_count=True))
policy=h.load(E/'policy-project.receipt.json');raw=gzip.decompress(Path(policy['body_path']).read_bytes());assert h.sha(raw)==policy['sha256'] and 'komercyjnym' in raw.decode()
b.save('creator-global-reconciliation.json',dict(at=h.now(),records=creators,new_painters=0))
b.save('independent-source-verification.json',dict(at=h.now(),plan_sha256=pin,records=checks,new_artwork_preimages={},policy_receipt=policy,source_descriptions_checked_for_object_identity=True,modern_acquisition_and_back_inscription_dates_not_used_for_creation=True))
selected={r['source_id'] for r in p['records']};outcomes=[];page=h.load(E/'warsaw-icons-page2.json')['data'];assert len(page['items'])==24
for row in page['items']:
 oid=str(row['id']);o=h.load(E/f'object-{oid}.json')['data'];date='; '.join(x['name'] for x in o['createDates']);tech=[x['name'] for x in o['techniques']]
 if oid in selected:reason='selected_new_whole_painted_icon'
 elif oid=='455220':reason='Existing exact Greek proskynetarion IK 103 MNW; prior campaign object excluded from batch increments'
 elif 'odlew' in tech:reason='Cast metalwork requires separate casting/version and complete-object review; not selected for painted-board batch'
 elif 'XIX/XX' in date:reason='Turn-of-century wording retained; exact date-boundary editorial treatment pending, no arbitrary year invented'
 elif oid=='498332':reason='Painted icon plus metal cover under IK 111/a-b; component/ensemble and reproduction-state review required'
 elif oid=='498541':reason='Tempera with embossed metal and multipart museum description; review cover/support and complete reproduced state'
 elif oid=='498621':reason='Physical fragment of iconostasis; parent/component overlap and complete supplied fragment review required'
 elif oid=='498692':reason='Questioned XVIII-century dating and same-title Saint George versions require individual date/composition review'
 elif oid=='498616':reason='Generic Resurrection title requires comparison to existing museum versions; museum notes extensive repainting and paint loss'
 else:raise AssertionError((oid,date,tech))
 outcomes.append(dict(source_id=oid,title=o['title'],inventory=o['noEvidence'],date_display=date,outcome=reason,evidence=f'object-{oid}.receipt.json',retry='Use saved exact source capture; do not repeat unchanged searches'))
b.save('research-outcomes.json',dict(at=h.now(),captured=24,selected=len(selected),records=outcomes))
b.save('research-holds.json',dict(at=h.now(),records=[r for r in outcomes if r['source_id'] not in selected and r['source_id']!='455220'],existing_excluded=['455220'],prior_unchanged_holds=h.load(E/'source-access-holds.json')['warsaw_prior_holds']))
print('Verified source/preimages:',len(checks),'excluded:',24-len(checks))
