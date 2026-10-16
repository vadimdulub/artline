#!/usr/bin/env python3
"""Audit every eligible Getty checklist expansion object and venue connection."""
import requests
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST

def main():
 scope=c.load(DEST/'scope-review.json.gz');discovery=c.load(DEST/'discovery.json.gz');eligible={o['id']:o for o in scope['eligibleObjects']};expected={(r['objectID'],r['eventID'],r['occurrenceID'])for r in discovery['connections']if r['objectID']in eligible};assert len(eligible)==38 and len(expected)==146
 plans=[c.load(DEST/(folder+'/plan.json.gz'))for folder in ['existing-five-release','bartholomew-release','thirtyone-connections-release','poussin-connection-release']];entries=[e for p in plans for e in p['entries']];assert len(entries)==146;ids=[e['id']for e in entries]
 with c.connect()as db:
  rows=n.normal(db.execute('SELECT e.*,a.primary_media_id,a.work_type,a.creation_year_start,a.creation_year_end,a.unlinked_creator_label FROM exhibition_entries e JOIN artworks a ON a.id=e.artwork_id WHERE e.id=ANY(%s::uuid[])',(ids,)).fetchall());assert len(rows)==146
  actual={(r['source_artwork_id'],r['exhibition_id'],r['occurrence_id'])for r in rows};assert actual==expected
  assert all(r['primary_media_id']and r['participation']=='exhibited'and r['work_type']in ['painting','drawing','print','icon']for r in rows)
  events=n.normal(db.execute('SELECT id,title,start_year,end_year,status FROM exhibitions WHERE id=ANY(%s::uuid[])',(list({r['exhibition_id']for r in rows}),)).fetchall());assert all(1600<=e['start_year']<=e['end_year']<=1989 and e['status']!='archived'for e in events)
  works=list({r['artwork_id']for r in rows});links=n.normal(db.execute("SELECT artwork_id,artist_id FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])AND attribution_role='primary'",(works,)).fetchall());totals=n.normal(db.execute("SELECT count(*)active,count(*)FILTER(WHERE event_state='held')held,count(*)FILTER(WHERE start_year IS NULL)undated FROM exhibitions WHERE status<>'archived'").fetchone())
 checked=[]
 for e in events:
  url='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+e['id'];res=requests.get(url,timeout=40);res.raise_for_status();detail=res.json();assert detail['startYear']==e['start_year']and detail['endYear']==e['end_year'];expectedArtists={a['artist_id']for a in links if any(r['exhibition_id']==e['id']and r['artwork_id']==a['artwork_id']for r in rows)};assert expectedArtists<={p['artist_id']for p in detail['participants']}
  items=[];after=None
  while True:
   params=dict(limit=100)
   if after:params['after']=after
   res=requests.get(url+'/entries',params=params,timeout=40);res.raise_for_status();page=res.json();items+=page['items'];after=page.get('nextCursor')
   if not after:break
  wanted={r['id']:r['artwork_id']for r in rows if r['exhibition_id']==e['id']};selected=[x for x in items if x['id']in wanted];assert {x['id']:x['artworkId']for x in selected}==wanted and all(x.get('image')for x in selected);checked.append(dict(id=e['id'],title=e['title'],entries=len(selected)))
 result=dict(at=c.now(),batchComplete=True,scope='38 eligible painting/drawing objects in the Getty checklist expansion; complete for 146 captured reciprocal historical venue references, not complete exhibition checklists or worldwide coverage.',counts=dict(eligibleObjects=38,newArtworks=32,reusedArtworks=6,newImages=32,illustratedVenueEntries=146,affectedExhibitions=len(events),newExhibitions=0,worksWithPrimaryArtistLinks=len({a['artwork_id']for a in links}),explicitUnlinkedCreatorWorks=len({r['artwork_id']for r in rows if r['unlinked_creator_label']})),events=checked,totals=totals,remaining=['Seven object creator labels remain explicit pending missing/duplicate artist-profile reconciliation or multi-creator attribution review.','Two decorative cabinets excluded and one whole illuminated manuscript held for item-scope review; no entries added for these three.'],realLocalWrites=False)
 c.save(DEST/'batch-verified.json',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-checklist-expansion-delivery.json',result);print(result)
if __name__=='__main__':main()
