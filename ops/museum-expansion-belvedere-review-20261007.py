#!/usr/bin/env python3
"""Review a bounded Belvedere selection toward200 eligible records; no DB writes."""
import importlib.util,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-belvedere-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;m=w.m;RUN=w.RUN
HOLDS={
'58':'Daumier Sancho variants include4227cad0-0700-4495-8c32-621e03a443d7 and330f9444-5a17-5209-9b4b-960a45081652. Overlapping subject and chronology require version resolution; date differences alone do not justify another record.',
'73':'Existing1a4c0db0-af64-5a9f-b413-1438c4857711 Dordrecht by Gilbert von Canal has the same1071 accession and unknown creation date. Keep source before1910 for separate reconciliation; no duplicate or metadata rewrite.',
'471':'Existing8d94a658-3a8e-53e8-b3a3-4adf7f2b7911 Female organ player by Klimt1885 may be the native1884 Allegory of Sacred Music. Preserve title/date discrepancy and resolve existing identity.',
'509':'Existing863e5853-205b-5520-9126-23616253ea22 Leibl portrait of Rosine Fischler1878 likely overlaps native1877. Date discrepancy alone does not establish another version.',
'540':'Existing19be9637-c50b-4bc0-b841-d05915030003 has the same native Belvedere object identity. Preserve its current relationships and reconcile separately.',
'656':'Existingf3c12404-2770-5764-9779-38e053ed71e0 Barbara Krafft portrait of Clemens von Raglovich1813 is a likely duplicate. Resolve existing record rather than insert.',
'657':'Regional-maker Crucifixion title/date leads include Cranach and the KHM GG6905 record. Resolve physical version and possible historical attribution/collection transfer before approving an addition.'}
SPECIAL={
'8':'Ferdinand Georg Waldmuller is the Artist; Emperor Ferdinand is a depicted person, not a second creator. Preserve separate source roles. The133x105cm canvas has accession4357 and1909 transfer evidence.',
'97':'Source Portfolio1093a-p groups16 Czech landscape paintings on cardboard. Add one native portfolio record with unknown normalized type, not16 invented artworks or individual inventories.',
'133':'Gideon Ernst von Laudon is the depicted person. Sigmund L Allemand remains the sole source artist; role labels govern over shared peopleField markup.',
'193':'The oil-on-paper mounted on canvas is explicitly an Entwurf/study,37x25cm. Emperor Franz is a depicted person; preserve Amerling as the sole creator and the study qualifier.',
'134':'This Sigmund L Allemand oil-on-canvas mounted on cardboard study differs from Wenceslaus Hollar etchings returned by alias/name discovery. Source before1870 retains an unknown lower bound.',
'167':'Gastein Valley I, native1162 accession, describes a different named location and composition from the existing Greillenstein Castle LM736 lead; retain the numbered valley identity.',
'178':'In the Fog1882 is a different documented subject from the existing In the Studio1881. Same painter and adjacent dates do not identify the same composition.',
'240':'Arthur Oskar Alexander and Hans Alexander Mueller are different named creators; common Alexander token and rural subject are not same-object evidence.',
'260':'Native Large Prater Landscape1849,70x93cm wood panel, differs physically from existing Cleveland Prater Landscape c1831,25x31cm panel1983.155. Retain full1912 Eissler acquisition history without making a legal-title claim.',
'287':'Native Pissarro oil-on-canvas street scene38.5x46.2cm differs from View/Market at Pontoise prints and Lucien Pissarro church lead. Keep Camille Jacob Pissarro source name and the specific Rue de Gisors title.',
'412':'Current role is Attribution to Slowakischer Maler. Preserve Attributed to qualification and regional unknown-maker label; no invented artist. Painting on spruce92x56cm is one native1402a object; source type Blackboard remains unknown in normalized type.',
'7981':'Native Object type Blackboard is retained as source evidence; oil-on-wood23.5x21.7cm does not authorize silently translating the source type. Normalized type remains unknown.'}
def main():
 rows=m.load(RUN/'native-candidates-002.json.gz')['rows'];cm={r['source_id']:r for r in m.load(RUN/'native-comparisons-002.json.gz')['records']};fm={r['source_id']:r for r in m.load(RUN/'native-filtered-comparisons-002.json.gz')['records']};decisions=[];queue=[]
 for row in rows:
  sid=row['source_id'];f=row['facts'];x,p=w.checked_record(m.ROOT/row['source_reference']['path']);assert f==w.facts(x,p)
  if row['state']!='candidate':queue.append(dict(**row,review_state='source_hold'));continue
  cmp=cm[sid]
  if sid in HOLDS:queue.append(dict(**row,comparison=cmp,review_state='identity_hold',editorial_reason=HOLDS[sid]));continue
  if len(decisions)>=112:queue.append(dict(**row,review_state='unselected_candidate',editorial_reason='Outside this112addition selection toward200eligible records; source eligibility is not import approval. Individual identity and provenance review still required.'));continue
  assert not cmp['source_hits'] and not cmp['native_url_hits'] and not [v for v in cmp['inventory_hits'] if v['relevant']]
  basis=f"Official Belvedere Painting index and native object agree on {f['title']}, creation {f['date_display']}, artist identity and native object {sid}; accession {f['inventory']} agrees with the museum caption. Current qualification governs over abbreviated index or older caption attributions. Creator/alias, translated-caption title, inventory and native-ID/URL comparisons reviewed. "
  basis+=SPECIAL.get(sid,'Other named subjects and unrelated same-title creators do not establish the same physical object. Preserve this separately inventoried source work and all literal qualifiers.')
  basis+=' Full source acquisition/provenance evidence retained: '+f['provenance_text']
  limitation='Editorial confidence0.90 is not a calibrated probability. Documented museum connection does not establish current display, custody or legal title. Original source rights and display text remain evidence only; no image permission inferred. No artist profile or link created.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.9,basis=basis,limitation=limitation,facts=f,index=row['index'],source_reference=row['source_reference'],comparison=cmp,filtered_comparison=fm[sid]))
 assert len(decisions)==112 and len(queue)==91 and len({r['facts']['inventory'] for r in decisions})==112
 m.save(RUN/'native-editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,supplements=[w.ref(RUN/'native-filtered-comparisons-002.json.gz')],candidate_reference=w.ref(RUN/'native-candidates-002.json.gz'),comparison_reference=w.ref(RUN/'native-comparisons-002.json.gz'),selection_policy='First112 individually reviewed supported candidates in retained native index order after source and identity holds, to bring88existing eligible records to200. Later candidates are not approved merely by this source pass.'))
 m.save(RUN/'native-followup-queue-001.json.gz',dict(at=m.now(),rows=queue,counts=dict(collections.Counter(r['review_state'] for r in queue)),index_unselected=m.load(RUN/'discovered-001.json.gz')['unselected'],policy='91captured objects and37index leads retained outside the applied selection. No database changes from this queue.'))
 print('Approved',len(decisions),'object follow-up',len(queue),'index unselected37',flush=True)
if __name__=='__main__':main()
