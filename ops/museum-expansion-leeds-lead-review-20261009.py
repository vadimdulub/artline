"""Record exact source gaps for the22 selected GAC leads without treating them as additions."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-leeds-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN
SPECIAL={
'A Dead Linnet':('existing_match','Known wave92 candidate77. Source1862 versus existingcirca1862–1863; preserve range unless a separate date-enrichment review approves a change. Do not duplicate.'),
'Natural History Museum of the Child':('existing_match','Known wave92 candidate1 by John Melville1937. Do not duplicate. Rights wording remains indeterminate; no image attached.'),
'Italian Landscape':('source_conflict','Source names John Skelton1758/1759 but gives Digital projections,paraffin wax and metal structure as medium. Do not import this internally inconsistent medium or resolve the historical creator by guesswork.'),
'Women and Bird Women and Bird':('incoming_private_loan','Exact object page names Women and Bird-front,with a second angle of the same sculpture. Explicitly on loan from a private collection; do not assert permanent Leeds holding or count image angles as separate objects.'),
'The Foot of Mount St. Gotthard':('holding_source_gap','Exhibition object has a date and Turner creator but no provenance field. Museum-published exhibition inclusion alone does not establish permanent holding.'),
'Adam and Eve in the Garden of Eden':('venue_creator_version_review','Gift from Sir Alvary Gascoigne1968 in city-wide Leeds service. Confirm Lotherton versus ArtGallery and which JanBrueghel/workshop/version before assigning. No gallery assignment from temporary exhibition.')}
def main():
 x=m.load(RUN/'additional-object-metadata-001.json.gz');assert len(x['rows'])==22;rows=[]
 for r in x['rows']:
  c=r['capture'];raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256'];lead=r['lead'];state,note=SPECIAL.get(lead['title'],('selected_further_review','Museum-published provenance and pre1971-labelled creation retained. Reconcile exact gallery allocation,ownership versus ArtFund relationship,physical version and existing catalogue before any addition. Wide date ranges remain literal source uncertainty; no inferred exact year.'))
  rows.append(dict(lead=lead,state=state,reason=note,body_reference=s.ref(m.ROOT/c['body_path']),raw_sha256=c['receipt']['sha256']))
 m.save(RUN/'additional-lead-review-001.json.gz',dict(at=m.now(),rows=rows,source_reference=s.ref(RUN/'additional-object-metadata-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='22selected metadata pages,2known existing matches,4specific unresolved/excluded leads,and16further identity/venue reviews. None counted as new artworks. No images or database writes.'))
 print(json.dumps(dict(selected_metadata_pages=22,known_existing=2,specific_gaps=4,further_reviews=16)),flush=True)
if __name__=='__main__':main()
