"""Retain contradictory Clausen source relationship as uncertain."""
import json,requests
from psycopg.types.json import Jsonb
import historical_exhibitions_fitzwilliam_london_early_release_20261012 as q
c=q.c;n=q.n;ID='5c3b9b1b-560f-5093-96a0-b20670b77c26';OP='fitzwilliam-clausen-chronology-20261012'
audit=c.load(q.r.OUT/'delivered-chronology-audit.json');issue=next(x for x in audit['conflicts']if x['entryID']==ID)
with c.connect()as db:
 before=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s',(ID,)).fetchone());assert before['participation']=='exhibited' and before['source_artwork_id']=='fitzwilliam/210190'
c.save(q.BACKUP/'clausen-chronology-preimage.json',dict(at=c.now(),entry=before,issue=issue))
with c.connect(write=True)as db:
 db.execute("SELECT set_config('artline.actor_user_id','local-european-research',true)");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(2026101201)')
 assert n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s FOR UPDATE',(ID,)).fetchone())==before
 db.execute("UPDATE exhibition_entries SET participation='uncertain',evidence=%s WHERE id=%s",(Jsonb(before['evidence']|dict(chronologyReview=issue,previousParticipation='exhibited',reviewOperation=OP)),ID))
with c.connect()as db:
 after=n.normal(db.execute('SELECT * FROM exhibition_entries WHERE id=%s',(ID,)).fetchone());assert after['participation']=='uncertain'
 for k,v in before.items():
  if k not in ['participation','evidence','updated_at']:assert after[k]==v
res=requests.get('https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+before['exhibition_id']+'/entries',timeout=40);res.raise_for_status();entry=next(x for x in res.json()['items']if x['id']==ID);assert entry['participation']=='uncertain'
result=dict(at=c.now(),entryID=ID,issue=issue,participation='uncertain',sourceMetadataPreserved=True,apiVerified=True,newEvents=0,newImages=0,realLocalWrites=False)
c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/fitzwilliam-clausen-chronology.json',result);print(json.dumps(result))
