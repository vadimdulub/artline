#!/usr/bin/env python3
"""Explicit editorial review of the bounded NGA partner selection; no writes to DB."""
import importlib.util,re,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-ngaustralia-gac-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;m=w.m;RUN=w.RUN
HOLDS={
'mwFCyYb483WWlQ':'Blue poles (Number 11), Pollock 1952, already exists as 9409a1a2-9a96-574c-85b2-93653c585f0d. Reconcile existing identity rather than insert a duplicate.',
'cQHo-H9AASYwOg':'Captain John Piper, Earle 1826, already exists as eb603c2f-8b2c-51a1-9e15-c078c76e1d99. Existing accession 71248 equals native IRN, not an independently supplied accession. Preserve and reconcile separately.',
'mgER0Hhlc5yuXA':'The bath of Diana, Van Diemen\'s Land, Glover 1837, already exists as fe461c59-a6ab-5614-b1c2-9b9a24bd0241. Existing identity requires reconciliation.',
'rAH3wSjx2kymbw':'Ned Kelly, Nolan 1946, already exists as 712ff2f4-c7dd-57ef-8678-7b40375e30d6. Keep series qualifier and reconcile existing record.',
'aQG3GaDaMaLVVA':'Boat on Beach, Queenscliff already exists as 8c072c49-8018-5edb-ab54-211b0d29f32a with 1886 versus source c.1887. Preserve discrepancy and resolve same-work identity without new duplicate.',
'3QEEe4iqSDAetQ':'Victory girls, Tucker 1943, already exists as 46289be2-56ac-511e-8a76-a6e1e7a3bca2. Reconcile existing identity separately.',
'nQGkS__SGYPWyA':'Joint Rex Nan Kivell collection credit names National Library of Australia and NGA. Preserve both institutions; do not choose one accepted current institution without resolving the shared arrangement.',
'2gG0dr7EIeS9aw':'Joint acquisition credit explicitly names Tasmanian Museum and Art Gallery and NGA. Resolve shared collection representation before any single-institution projection.',
'0gEk3X6Bn40QKg':'Many Monet Nympheas variants overlap the circa1914-17 date. Source unit formatting is unreliable for dimension comparison. Resolve exact version before insertion.',
'VAE3AsfK8q8M6A':'1951 dates the photographed Battersea event; retained object page does not independently establish the date of this gelatin-silver print. Keep physical print chronology unresolved.',
'UwEazE_oCEFJQA':'Museum provenance research and independent review record unresolved export/origin history for The Bronze Weaver. Keep historical collection evidence and provenance uncertainty; defer current holding treatment.'}
SPECIAL={
'4AEs9yO8JlsLhw':'Native IRN8610 coincides with an unrelated legacy accession on St. Benedict Destroying Idols (1653). It is not an accession match; creator, title and date distinguish the objects. Narrative Louvre reference concerns Sisley drawings, not this Sara Lee gifted painting.',
'awGdV5KaneoocQ':'Museum narrative expressly distinguishes this small1885 oil-on-panel study from the finished Tate canvas. Existing Tate N06067 and National Gallery London L728 leads are the same finished canvas: retained official NG metadata names Tate lender number N06067, oil on canvas,64.8x81.6cm. Retain the separate NGA panel study.',
'ywE-_izp3iBJoQ':'Official NGA Ocean to Outback object page, IRN131114, identifies The Bridge in building1929-30, NGA2005.239, and separately names The Bridge in-curve c.1930 at NGV. The existing Bridge in Curve record is not this work. Supplemental accession/dimensions remain evidence; partner-only fields stay unknown.',
'8gHLdQFhJ6lQ0A':'Source narrative identifies this1914 variation separately from Long\'s1897 Queensland painting and later etchings. Retain1914 source object and literal rights credit.',
'cAH5v2Pqbdb2GQ':'Source creation field1915-16 is supported by the narrative; the inscribed1914 is discussed as retrospective Suprematist dating. Retain both in source evidence without copying depicted or inscribed history into creation fields.',
'AQG1Xb_t-T_aEw':'Mrs John Piper is a separate portrait from the existing Captain John Piper. Museum narrative also distinguishes the two smaller NGA portraits from full-length State Library versions.',
'IQELfZqgC8es6g':'Four panels are one museum object and one native IRN115741. Add one grouped screen record, never four invented artworks or accessions.',
'VQF2ju2o6lZDnw':'This1912 painted plaster is distinguished in the narrative from the original bronze and later bronze casts. Preserve the narrative\'s almost-certain identification of the Hare plaster; do not assert another surviving cast.',
'ogHWSUGgNtT2xQ':'13th-century Nepalese Malla-period copper figure, purchased1984. Exact-title Cleveland600s work differs in date and cultural identity. Preserve cultural creator label and the museum\'s ongoing Asian provenance-research context; no legal-title claim.',
'6QF_yOceObMRag':'Museum narrative reports a base inscription stating September1807. Retain source year1807 and Shan people attribution as an object label; not an invented artist.',
'hwE1HrPXhMbYgw':'Museum describes the c.1870 collaborative Schomburgk/Wendt inkwell. Preserve source Schomburgk label and full workshop narrative, without inventing a linked artist or type.',
'7QFRQegI7i332w':'The1857 oil painting is explicitly distinguished from later drawings, reduced canvas variants and the1866-68 published lithograph in the narrative.',
'CgFen0FqYEONKg':'Existing Winter morning near Heidelberg1866 by Buvelot has a different specific title and NGV accession p.300.4-1; this NGA native IRN47067 is the purchased1959 View near Heidelberg. Preserve separate documented objects.'}

def main():
 rows=m.load(RUN/'gac-candidates-002.json.gz')['rows'];cm={r['source_id']:r for r in m.load(RUN/'gac-comparisons-003.json.gz')['records']};decisions=[];queue=[];subtitles={}
 for row in rows:
  sid=row['source_id'];f=row['facts'];x,p=w.checked_record(m.ROOT/row['source_reference']['path']);assert f==w.facts(x,p)
  if row['state']!='candidate':queue.append(dict(**row,review_state='source_hold'));continue
  cmp=cm[sid]
  if sid in HOLDS:queue.append(dict(**row,comparison=cmp,review_state='editorial_hold',editorial_reason=HOLDS[sid]));continue
  assert not cmp['source_hits'] and not cmp['native_url_hits']
  if cmp['legacy_irn_accession_leads']:assert sid=='4AEs9yO8JlsLhw'
  basis=f"Museum-partner index and object page agree on {f['title']}, {f['creator_label']}, creation {f['date_display']}, and native NGA object IRN{f['native_object_id']}. Creator, alias, title and native-URL identity scope reviewed; no unresolved same-object lead remains in this selection. "
  basis+=SPECIAL.get(sid,'Different titled works and unrelated same-title creators in the saved comparisons do not establish identity with this source object. Literal medium, period and grouping retained.')
  if not f['acquisition_text']:basis+=' Acquisition/rights credit is absent. Museum publisher heading, partner index, official NGA external object link and consistent creator/title/date establish the documented collection connection; acquisition and image rights remain unknown.'
  else:basis+=' Literal source acquisition/rights credit retained: '+f['acquisition_text']
  if f['creator_label']=='Sidney NOLAN':basis+=' This separately identified1946-47 first-series painting differs from existing1955-57 later-series Glenrowan/Cave versions; the1946 Ned Kelly duplicate itself is held.'
  if m.norm(p['subtitle'])!=m.norm(f['creator_label']+' '+f['date_display']):
   subtitles[sid]=dict(subtitle=p['subtitle'],detail_creator=f['creator_label'],detail_date=f['date_display'],decision='Heading uses an abbreviated, expanded or transliterated identity for the same named creator. Literal detailed creator governs; cultural people qualifiers are retained. No artist link created.')
  limitation='Editorial confidence0.90 is not a calibrated probability. Historical museum-published metadata establishes a collection connection, not current display, custody or legal ownership. No image permission inferred. Native modern catalogue returned403; old collection site supplied navigation. Native IRN is never substituted for accession. Unreliable legacy dimension units remain evidence only.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.9,basis=basis,limitation=limitation,facts=f,index=row['index'],source_reference=row['source_reference'],comparison=cmp))
 assert len(decisions)==103 and len(queue)==34 and len({x['facts']['native_object_id'] for x in decisions})==103
 m.save(RUN/'gac-subtitle-review-002.json',dict(at=m.now(),records=subtitles))
 m.save(RUN/'gac-editorial-reviewed-002.json.gz',dict(at=m.now(),decisions=decisions,supplements=[w.ref(RUN/f'web-discovery-00{n}.json.gz') for n in [4,5,6]]+[w.ref(RUN/'seurat-comparison-supplement-002.json.gz')],supersedes='Editorial001: corrected mistaken Sainsbury institution name to National Gallery London, verified actual lender identity and material against retained official source. No database writes used001.',candidate_reference=w.ref(RUN/'gac-candidates-002.json.gz'),comparison_reference=w.ref(RUN/'gac-comparisons-003.json.gz')))
 m.save(RUN/'gac-followup-queue-002.json.gz',dict(at=m.now(),rows=queue,counts=dict(collections.Counter(r['review_state'] for r in queue)),policy='Retained unresolved leads; no new database record or holding from this queue. Reconcile existing identities, shared collections, version/cast/print dates and source uncertainties individually.'))
 print('Approved',len(decisions),'Follow-up',len(queue),'subtitle variants',len(subtitles),flush=True)
if __name__=='__main__':main()
