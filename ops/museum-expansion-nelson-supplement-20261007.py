#!/usr/bin/env python3
"""Read-only historical-creator, anonymous-subject and selected version evidence."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-nelson-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);f=i.f;m=i.m;RUN=i.RUN
PATTERNS=['%john%patmos%','%john%prochor%','%john%dictat%','%jean%patmos%','%ioann%','%иоан%патм%','%hospitality%abraham%','%abraham%angel%','%abraham%feast%','%trinity%','%троиц%','%bow%boy%','%boy%bow%','%marscha%','%marsha%','%benedictine%abbot%','%abbe%benedict%']
def queries(db):
 ids=[x['id'] for x in db.execute('SELECT id::text FROM artworks WHERE lower(title) LIKE ANY(%s) OR lower(alternate_title) LIKE ANY(%s) ORDER BY id LIMIT 2001',(PATTERNS,PATTERNS))];assert len(ids)<=2000
 arts=db.execute('SELECT '+i.i.ARTCOLS+' FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
 links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(ids,)).fetchall()
 return dict(artworks=arts,links=links)
def main():
 rs=i.rows();extra=[r for r in rs if r['number'] in [69,91]]
 for r in extra:r['facts']['identity_creator_labels']+=['Arthur Devis'] if r['number']==69 else ['Anthony van Dyck']
 p=i.parameters(extra)
 comparisons=m.load(RUN/'identity-comparisons-002.json.gz')['records'];nums=[48,49,50,52,54,55,57,58,64,65,67,80,93,108,112,113,115,116,120,121,127,138,141,148,149,156,158,159,166,168,171,177,178,183]
 selected={r['source_id'] for r in rs if r['number'] in nums};ids=set()
 for c in comparisons:
  if c['source_id'] in selected:ids|={a['id'] for a in c['focused_top'][:4]+c['leads'][:5]}
 with m.connect() as db:
  anonymous=queries(db);state=i.queries(db,p)
  citations=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(sorted(ids),)).fetchall()
  identifiers=db.execute("SELECT to_jsonb(c) row FROM external_identifiers c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(sorted(ids),)).fetchall()
 m.save(RUN/'supplemental-identity-001.json.gz',dict(at=m.now(),anonymous_patterns=PATTERNS,anonymous_state=anonymous,params=p,state=state,rows=extra,comparisons=i.comparisons(extra,state),version_artwork_ids=sorted(ids),citations=[x['row'] for x in citations],identifiers=[x['row'] for x in identifiers],identity_reference=f.ref(RUN/'identity-scope-002.json.gz'),script_reference=f.ref(Path(__file__).resolve()),policy='Read-only bounded subject scope includes Russian/English/French labels for icons and anonymous portraits; Devis and van Dyck historical narrative attributions are search leads only. Existing physical metadata and citations preserved for selected version review. No identity approvals from string similarity.'))
 print(json.dumps(dict(anonymous=len(anonymous['artworks']),historical=len(state['artworks']),version_artworks=len(ids),citations=len(citations))),flush=True)
if __name__=='__main__':main()
