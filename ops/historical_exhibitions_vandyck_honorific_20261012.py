import sys,json,requests
sys.path.insert(0,'ops')
from psycopg.types.json import Jsonb
import historical_exhibitions_nineteenth_wave3_20261012 as m
c=m.c;n=m.n
OP='historical-exhibitions-vandyck-honorific-20261012';eid='ba3616e0-cdd9-5ab2-85d5-b4827988d898';aid='1703ba8b-2115-4dc5-b82b-9ae5a97e2705'
p=c.load(m.OUT/'plan.json.gz');entries=[e for e in p['entries']if e['eventID']==eid and e['history']['object']['attribution']=='Sir Anthony van Dyck'];assert len(entries)==3
with c.connect()as db:
 before=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s',(eid,)).fetchall());assert not before
 people=n.normal(db.execute('SELECT aa.*,a.display_name,a.status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',([e['workBefore']['id']for e in entries],)).fetchall());assert len(people)==3 and all(x['artist_id']==aid and x['attribution_role']=='primary'and x['display_name']=='Anthony van Dyck'for x in people)
evidence=dict(operation=OP,basis='Exact native object identities and current primary attribution agree; source Sir is an honorific, not a creator identity difference.',sourceCreator='Sir Anthony van Dyck',catalogueCreator='Anthony van Dyck',entryIDs=[e['id']for e in entries],nativeObjectIDs=[e['history']['objectID']for e in entries],excluded='Native object 52251 remains attributed to Jan Boeckhorst, not Van Dyck.',currentDisplayClaim=False)
c.save(m.BACKUP/'vandyck-participant-preimage.json',dict(before=before,people=people,evidence=evidence))
with c.connect(write=True)as db:
 db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
 assert not db.execute('SELECT 1 FROM exhibition_participants WHERE exhibition_id=%s',(eid,)).fetchone()
 current=n.normal(db.execute('SELECT aa.*,a.display_name,a.status FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',([e['workBefore']['id']for e in entries],)).fetchall());assert current==people
 db.execute("INSERT INTO exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) VALUES(%s,%s,%s,%s,%s,'artist',%s)",(c.uid(OP),eid,entries[0]['sourceID'],aid,'Anthony van Dyck',Jsonb(evidence)))
with c.connect()as db:
 result=n.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=%s',(eid,)).fetchall());assert len(result)==1 and result[0]['artist_id']==aid
r=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+eid,timeout=40);r.raise_for_status();d=r.json();print(json.dumps(d)[:2500])
c.save(m.OUT/'vandyck-participant-delivery.json',dict(at=c.now(),rows=result,api=d))
c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/vandyck-participant-delivery.json',dict(at=c.now(),eventID=eid,artistID=aid,newArtistConnections=1,newEvents=0,newArtworks=0,newImages=0,evidence=evidence,verified=True))
