#!/usr/bin/env python3
"""Recheck both wave50 records unchanged; account explicitly for five later DIA additions."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-next-samples-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
snapshot=a.snapshot;counts=a.counts;expected_art=a.expected_art;SID=a.SID;citation_note=a.citation_note;holding_note=a.holding_note
def verify(db,p,digest):
 output={}
 for v in p['records']:
  iid=v['institution_id'];key=v['provider'];fv=v['facts'];aid=v['artwork_id'];initial=p['before'][key];snap=snapshot(db,[aid],iid)
  assert snapshot(db,initial['scoped_ids'],iid)==initial['snapshot'];assert counts(db,iid)==dict(linked=(6 if key=='detroit' else 1),eligible=(6 if key=='detroit' else 1))
  assert all(len(snap[k])==1 for k in ['artworks','identifiers','citations','assertions']);assert not snap['artists'] and not snap['media'];art=snap['artworks'][0];assert all(art[k]==value for k,value in expected_art(v).items())
  for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
  ident=snap['identifiers'][0];assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(v['scheme'],fv['source_id'],fv['source_url'],SID)
  c=snap['citations'][0];assert (c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_reviewed_metadata',fv['source_id'],fv['source_url'],citation_note(v,digest))
  a=snap['assertions'][0];assert a['claim_type']=='holding' and a['institution_id']==iid and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_id']==SID and a['source_url']==fv['source_url'] and a['evidence_note']==holding_note(v,digest)
  assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
  assert db.execute("SELECT artline_has_selection_evidence(%s) ok",(aid,)).fetchone()['ok']
  output[key]=dict(added=1,current_counts=counts(db,iid),old_artworks_unchanged=len(initial['snapshot']['artworks']),old_citations_unchanged=len(initial['snapshot']['citations']))
 return dict(verified_new_records=2,museums=output,new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
