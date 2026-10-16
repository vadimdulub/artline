"""Exhibition artist navigation from verified native drawing identities."""
import json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_oldmaster_drawing_catalogue_20261012 as q
c=q.c;n=q.n;OP='historical-exhibitions-fitzwilliam-drawing-participants-20261012'
p=c.load(q.OUT/'plan.json.gz');audit=c.load(q.BACKUP/'creator-links-preimage.json.gz');byname={a['display_name']:a['id']for a in audit['artists']};records={r['nativeID']:r for r in p['records']};groups={}
for e in p['entriesBefore']:
 r=records[e['source_artwork_id'].split('/')[-1]]
 if r['creator']not in audit['mapping']:continue
 aid=byname[audit['mapping'][r['creator']]];groups.setdefault((e['exhibition_id'],aid),[]).append(dict(entryID=e['id'],artworkID=r['id'],sourceID=e['source_record_id'],nativeID=r['nativeID']))
ids=sorted({k[0]for k in groups});workids=sorted({e['artworkID']for es in groups.values()for e in es});entryids=sorted({e['entryID']for es in groups.values()for e in es});assert len(workids)==68
with c.connect()as db:
 before=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchall());assert not before
 people=n.normal(db.execute('SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id',(workids,)).fetchall());assert len(people)==68
 entries=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id',(entryids,)).fetchall());assert len(entries)==len(entryids)
 for (eid,aid),es in groups.items():
  for e in es:
   assert any(x['artwork_id']==e['artworkID']and x['artist_id']==aid and x['attribution_role']=='primary'for x in people)
   assert any(x['id']==e['entryID']and x['artwork_id']==e['artworkID']and x['exhibition_id']==eid and x['participation']=='exhibited'for x in entries)
c.save(q.BACKUP/'drawing-participants-preimage.json.gz',dict(at=c.now(),before=before,people=people,entries=entries))
with c.connect(write=True)as db:
 db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
 assert not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(ids,)).fetchone()
 assert n.normal(db.execute('SELECT aa.*,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id',(workids,)).fetchall())==people
 assert n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(entryids,)).fetchall())==entries
 with db.pipeline():
  for (eid,aid),es in groups.items():
   name=next(x['display_name']for x in people if x['artist_id']==aid);evidence=dict(operation=OP,basis='Verified unqualified source creator and exact native object participation. Qualified or unresolved creators are excluded from this primary participant mapping.',entries=es,currentDisplayClaim=False)
   db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP+'/'+eid+'/'+aid),eid,es[0]['sourceID'],aid,name,Jsonb(evidence)))
verified=[]
for eid in ids:
 response=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid,timeout=40);response.raise_for_status();data=response.json();expected={aid for event,aid in groups if event==eid};assert {x['artist_id']for x in data['participants']}==expected;verified.append(dict(eventID=eid,artistCount=len(expected)))
result=dict(at=c.now(),newArtistParticipants=len(groups),exhibitions=len(ids),supportingArtworks=len(workids),supportingEntries=len(entryids),verified=verified,newArtworks=0,newImages=0,realLocalWrites=False)
c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-drawing-participants-delivery.json',result);print(json.dumps(result))
