"""Exact participant links supported by four delivered native object sets."""
import json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_romney_catalogue_20261012 as r
import historical_exhibitions_fitzwilliam_print_catalogue_two_20261012 as p
c=r.c;n=r.n;OP='historical-exhibitions-fitzwilliam-four-participants-20261012'
plans=[c.load(x.OUT/'plan.json.gz')for x in [r,p]];groups={}
for plan in plans:
 bynative={x['nativeID']:x for x in plan['records']}
 for e in plan['entriesBefore']:
  record=bynative[e['source_artwork_id'].split('/')[-1]];key=(e['exhibition_id'],record['artistID']);groups.setdefault(key,[]).append(dict(entryID=e['id'],artworkID=record['id'],sourceID=e['source_record_id'],nativeID=record['nativeID']))
assert len(groups)==4 and sum(map(len,groups.values()))==217
ids=sorted({k[0]for k in groups});workids=[e['artworkID']for es in groups.values()for e in es]
with c.connect()as db:
 before=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchall());assert not before
 people=n.normal(db.execute('SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id',(workids,)).fetchall());assert len(people)==217
 for (eid,aid),entries in groups.items():
  for e in entries:assert any(x['artwork_id']==e['artworkID']and x['artist_id']==aid and x['attribution_role']=='primary'for x in people)
c.save(r.BACKUP/'four-participants-preimage.json',dict(at=c.now(),before=before,people=people))
with c.connect(write=True)as db:
 db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
 assert not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()
 assert n.normal(db.execute('SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id',(workids,)).fetchall())==people
 for (eid,aid),entries in groups.items():
  name=next(x['display_name']for x in people if x['artist_id']==aid);evidence=dict(operation=OP,basis='Exact source native object IDs and verified primary creator links for exhibited objects.',entries=entries,currentDisplayClaim=False)
  db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/'+eid),eid,entries[0]['sourceID'],aid,name,Jsonb(evidence)))
verified=[]
for eid,aid in groups:
 response=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid,timeout=40);response.raise_for_status();data=response.json();assert any(x['artist_id']==aid for x in data['participants']);verified.append(dict(eventID=eid,artistID=aid,entries=len(groups[eid,aid])))
result=dict(at=c.now(),newArtistParticipants=4,verified=verified,newArtworks=0,newImages=0,realLocalWrites=False)
c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-four-participants-delivery.json',result);print(json.dumps(result))
