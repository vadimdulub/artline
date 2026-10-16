#!/usr/bin/env python3
"""Independent read-only verification of the frozen exhibition linking delivery."""
import collections,json
import exhibition_catalogue_links_20261013 as m
c=m.c

def main():
 p=c.load(m.OUT/m.PLAN);plan_sha=c.sha((m.OUT/m.PLAN).read_bytes());baseline=c.load(m.OUT/'baseline.json.gz');receipts=[c.load(m.OUT/'iterations'/f"{b['iteration']:04d}.json")for b in p['batches']]
 assert all(r['verified']and r['committed']and r['planSHA256']==plan_sha for r in receipts)
 assert sum(r['events']==10 for r in receipts)>=1000
 seen=[eid for r in receipts for eid in r['eventIDs']];assert len(seen)==len(set(seen))==10406
 with c.connect()as db:
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY')
  entries=m.normal(db.execute('SELECT e.* FROM exhibition_entries e WHERE exhibition_id=ANY(%s::uuid[])',(seen,)).fetchall());people=m.normal(db.execute('SELECT * FROM exhibition_participants WHERE exhibition_id=ANY(%s::uuid[])',(seen,)).fetchall())
  works=m.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',(list(p['newWorks']),)).fetchall());artists=m.normal(db.execute('SELECT * FROM artists WHERE id=ANY(%s::uuid[])',(list(p['newArtists']),)).fetchall())
  authors=m.normal(db.execute('SELECT * FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(list(p['newWorks']),)).fetchall())
  holdings=m.normal(db.execute("SELECT artwork_id,institution_id FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(list(p['newWorks']),)).fetchall())
  oldworks=c.load(m.OUT/'works-before.json.gz')['works'];afterold=m.normal(db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])',([w['id']for w in oldworks],)).fetchall())
  events=m.normal(db.execute('SELECT * FROM exhibitions WHERE id=ANY(%s::uuid[])',(seen,)).fetchall())
  c.save(m.OUT/'after-delivery.json.gz',dict(at=c.now(),entries=entries,participants=people,newWorks=works,newArtists=artists,authors=authors,holdings=holdings,existingWorks=afterold,events=events))
 entrymap={e['id']:e for e in entries};personmap={x['id']:x for x in people};pairs={(x['exhibition_id'],x['artist_id'])for x in people if x['artist_id']};expectedentries={l['before']['id']:l for b in p['batches']for l in b['entryLinks']};expectedpeople={l['before']['id']:l for b in p['batches']for l in b['participantLinks']}
 for old in baseline['entries']:
  now=entrymap[old['id']];change=expectedentries.get(old['id'])
  for key in now:
   if change and key in ('artwork_id','evidence','match_basis'):continue
   assert now[key]==old[key],('Unexpected entry change',old['id'],key)
  if change:
   assert now['artwork_id']==change['artworkID']and now['match_basis']==change['basis']
   assert {k:v for k,v in now['evidence'].items()if k!='catalogue_link_20261013'}==old['evidence']
   assert now['evidence']['catalogue_link_20261013']['operation']==m.OP
 for old in baseline['participants']:
  now=personmap[old['id']];change=expectedpeople.get(old['id'])
  for key in now:
   if change and key in ('artist_id','evidence'):continue
   assert now[key]==old[key],('Unexpected participant change',old['id'],key)
  if change:
   assert now['artist_id']==change['artistID'];assert {k:v for k,v in now['evidence'].items()if k!='catalogue_link_20261013'}==old['evidence']
 for b in p['batches']:
  assert all((x['exhibitionID'],x['artistID'])in pairs for x in b['newParticipants'])
 assert len(works)==len(p['newWorks'])and len(artists)==len(p['newArtists'])
 ah=collections.defaultdict(set)
 for x in authors:assert x['attribution_role']=='primary';ah[x['artwork_id']].add(x['artist_id'])
 loc={(x['artwork_id'],x['institution_id'])for x in holdings}
 for w in works:
  exp=p['newWorks'][w['id']]
  for field,key in [('slug','slug'),('title','title'),('date_display','date'),('creation_year_start','first'),('creation_year_end','last'),('date_precision','precision'),('work_type','type'),('accession_number','accession'),('current_institution_id','institutionID'),('unlinked_creator_label','creatorLabel')]:assert w[field]==exp[key],(w['id'],field)
  assert w['status']=='published'and w['published_at']and w['research_candidate']is False
  assert ah[w['id']]==set(exp['creators']);assert(w['id'],exp['institutionID'])in loc
 for a in artists:
  exp=p['newArtists'][a['id']];assert a['display_name']==exp['display_name']and a['birth_year']==exp['birth_year']and a['death_year']==exp['death_year']and a['status']=='published'and a['published_at']
 assert sorted(oldworks,key=lambda x:x['id'])==sorted(afterold,key=lambda x:x['id']),'Unrelated existing artwork changed since snapshot; identify concurrent work before reporting'
 assert sorted(baseline['events'],key=lambda x:x['id'])==sorted(events,key=lambda x:x['id']),'Exhibition metadata changed'
 result=dict(verifiedAt=c.now(),operation=m.OP,fullIterations=sum(r['events']==10 for r in receipts),tailExhibitions=sum(r['events']for r in receipts if r['events']<10),distinctExhibitions=len(seen),newPublishedArtworks=len(works),newPublishedCreators=len(artists),existingEntryLinks=len(expectedentries),existingArtistReferencesLinked=len(expectedpeople),newArtistConnections=sum(x['evidence'].get('operation')==m.OP for x in people),newArtworkCreatorLinks=len(authors),newHoldings=len(holdings),unknownCreationDates=sum(x['date_precision']=='unknown'for x in works),sourceOnlyCreatorLabels=sum(not ah[x['id']]for x in works),newImages=0,unresolvedEntryReasons=dict(collections.Counter(h['reason']for b in p['batches']for h in b['holds']if h['kind']=='entry')),unresolvedArtistReferences=sum(h['kind']=='participant'for b in p['batches']for h in b['holds']),exhibitionsWithoutCapturedEntries=p['counts']['eventsWithoutEntries'],oldArtworkRowsPreserved=len(oldworks),allOriginalExhibitionFieldsPreserved=True,allOriginalEntryLabelsAndParticipationPreserved=True,realLocalDatabaseWrites=False,verification='Production SQL snapshot and exact ID/field assertions; separately authorized API release verification recorded in deployment.json')
 c.save(m.OUT/'verified.json',result);c.save(m.DOC/'delivery.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
