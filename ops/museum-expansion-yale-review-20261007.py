#!/usr/bin/env python3
"""Recorded editorial decisions on a bounded Yale LUX selection; no DB writes."""
import importlib.util,collections,re
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-yale-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;m=w.m;RUN=w.RUN
HOLDS={
'25989':'Pissarro Peasant Woman at NGA,36cf6a3a-a7cf-48bd-8657-03241ae76830, has nearly identical dimensions. Resolve composition/version rather than rely on1880 versus1885.',
'25517':'Boudin Trouville low-tide/harbor versions include3ed50c58-c4ea-5275-8aca-460098482413 and5815d291-186e-41f4-9d7d-f671949ea19d; incomplete physical metadata prevents secure separation.',
'309':'Botticelli Virgin/Madonna and Child legacy lead1a339575-c528-49fb-92c5-3efd89e90ee4 lacks a physical identifier. Resolve version before adding.',
'9303':'Renoir Bather leadc6df95c5-5a7b-4eab-a564-3281eafbe108 has incomplete physical metadata; source dating differences alone are insufficient.',
'54470':'Unknown-maker Virgin and Child with Saints overlaps generic legacy subjects and potentially revised attributions. Sourceca1900 is retained; resolve version before adding.',
'3029':'Matteo di Giovanni Virgin/Child with Saints and Angels lead8114e2c9-b73f-4dce-a0db-43f61e8206d4 has an unresolved version and no physical metadata.',
'200752':'Credit explicitly names the separate Yale Center for British Art and accessionB1981.25.57. GalleryILE2021.2.1 and LUX owner field do not authorize transferring this holding.',
'160':'Existing8d4074b5-b6d3-5791-8517-61770547d29a has the sameQ49178494 and accession1835.12. Preserve new early19th-century evidence for separate reconciliation; no duplicate or date rewrite.',
'196':'Creation1881, accession1850.4 and Salisbury Estate credit need a chronology check. Accession prefix is not itself an acquisition date; preserve the discrepancy without correction.',
'195':'Creation1851, accession1850.3 and Salisbury Estate credit require chronology review. Do not infer an acquisition date or rewrite the supplied creation year.',
'183944':'Bourdon Salomon sacrifiant aux idoles54bc9640-ad4a-40e3-ab47-5f5ff4101aa9 is a translated-title lead with incomplete physical metadata.',
'2460':'Creation range1568–1625 matches the attributed Brueghel lifespan, while multiple flower-basket versions exist. Verify an object creation basis before counting as eligible.',
'44860':'Couder Washington/Rochambeau/Yorktown leadc628455a-6b45-475b-897b-ac92f3f70f6a includes the same subject with unresolved physical version;1836 versusc1837 alone does not separate it.',
'25722':'The Mary Magdalen subject has an Italian-title forgery/reattribution leadd5cbbb87-b5ce-467c-85d7-9d4429ac6f65. Resolve physical object and attribution history.',
'359547':'Source records former Fine Arts Museums of San Francisco accession55.18, deaccession and another version retained there. Compare historical physical identity before a new record; preserve2026Yale acquisition evidence.',
'17268':'Source medium is Copper plate despite aggregated Paintings classification. Resolve whether this is a printing matrix or painted object before assigning a normalized type.',
'57246':'Van der Helst generic female portrait has unresolved anonymous-sitter variants, including071a4c26-582a-4fab-867c-1a5876289093, with missing physical metadata.',
'25509':'Boudin Trouville beach variants include7a640bad-8c80-4524-a52d-0e2476d1c73a with missing physical metadata. Retain attribution and source dimensions for version review.',
'9366':'Tintoretto generic portrait overlaps several incompletely identified male-portrait versions. Keep native1959.15.19 separate pending sitter/version checks.',
'45457':'Anonymous Virgin and Child c1500 has broad same-subject legacy matches. No artist is invented; physical version and prior attribution need review.',
'251':'Anonymous Nativity c1420 has broad same-subject legacy matches. Resolve prior attribution and physical version; anonymity alone is not exclusion.',
'43506':'Albertinelli Creation and Fall of Mane3ae6f17-d99f-5439-83f1-a33d26ddc6db may overlap Temptation of Adam and Eve. Different creation wording alone does not settle the version.',
'318':'Source explicitly discusses the disputed Sano di Pietro/Master of the Osservanza relationship and an eight-panel series. Resolve aliases/components before another Saint Anthony scene.',
'43268':'Source provenance gives an earlier sitter titleFrancesco Maria della Rovere, while current title namesGuidobaldoII. Extend the legacy title/version comparison before an addition.'}
SPECIAL={
'103786':'This source explicitly describes a copy after Caravaggio,136.5x188cm. It differs physically and in attribution from the133.5x169.5cm Irish originalL.14702. Preserve the copy qualification and full17th-century envelope.',
'52114':'The117.5x165.4cm Yale panel differs in format and dimensions from the82.6x54cm Metropolitan panel1974.1. Same Vanitas title does not merge them.',
'8914':'Yale Interior is oil on panel42x52.5cm with an explicit1966Wetmore bequest; comparison interiors have different supports/dimensions. Full provenance qualifications retained.',
'191510':'Yale horizontal canvas83.82x125.73cm differs physically from the National Gallery vertical97.2x74cm canvasNG6277. Preserve merged narrative attribution wording in evidence.',
'8614':'The Yale object is oil on panel32.4x24.1cm; same-title database leads are1833lithographs. No painting/print conflation.',
'248':'The literal titlePotrait and copy-after qualification remain. The66.7x53.3cm copy differs from the77.5x61.6cm Metropolitan2017.422portrait.',
'49021':'Anonymous Russian19th-century icon1951.19.3 is one native object despite several subjects in its title. Keep its Soviet-era acquisition narrative and1951museum gift; no invented maker.',
'51376':'Anonymous Greek icon1951.53.1 retains ca1720,31.1x24.1cm tempera panel and Whitridge gift. Regional unknown maker is supported explicitly.',
'254':'Circle of George Klontzas remains a qualified Cretan object label, not an artist link. The27x19.1cm panel differs from the18.5x13.25inch1704Anagnostou comparison.',
'110696':'Source records1936forced sale,1984Berlin bequest,2003restitution to heirs and2007partial gift/purchase by Yale. Preserve every event; current museum connection is not a legal-title judgment.',
'43503':'Source explicitly distinguishes a1953loan from a1959deed of gift. Current gift credit supports the collection connection.',
'309423':'The1984–2008Stuttgart loan is historical; the source records a2021Yale purchase. Nazi-era documentation-gap language remains evidence.',
'354451':'The source records the2025sale and2026Yale purchase and explicitly notes Nazi-era provenance documentation gaps. Creation1861 is independent of acquisition.',
'52945':'The source describes Millet retouching his own work about15years later. Preserve the suppliedca1850–65creation envelope and distinguish Van Gogh, mentioned as a comparison.',
'165655':'The porcelain portrait has no current maker supplied. Keep makerNULL and the literalca1850date, museum credit and dimensions.',
'75029':'One24.4x18.4cm separately inventoried panel1959.15.13b. The former Basaiti sale attribution is retained in provenance; no reconstruction of a complete ensemble.',
'128321':'One tabernacle frame with its own2008.186.1inventory. Preserve1472(?) as uncertain circa, physical frame dimensions and title; do not count decorative figures separately.'}
def main():
 rows=m.load(RUN/'native-candidates-001.json.gz')['rows'];cm={r['source_id']:r for r in m.load(RUN/'native-comparisons-001.json.gz')['records']};decisions=[];queue=[]
 for row in rows:
  f=row['facts'];sid=row['source_id'];oid=f['native_object_id'];x,p=w.checked_record(m.ROOT/row['source_reference']['path']);assert f==w.facts(x,p)
  if row['state']!='candidate':queue.append(dict(**row,review_state='source_hold'));continue
  cmp=cm[sid]
  if oid in HOLDS:queue.append(dict(**row,comparison=cmp,review_state='editorial_hold',editorial_reason=HOLDS[oid]));continue
  assert not w.source_holds(f,p);assert not cmp['source_hits'] and not cmp['native_url_hits'] and not [v for v in cmp['inventory_hits'] if v['relevant']]
  assert not f['inventory'].startswith('ILE') and 'Yale Center for British Art' not in f['credit_line']
  basis=f"Public Yale LUX physical object {sid} agrees with native museum object {oid}, accession {f['inventory']}, primary title {f['title']}, creation label {f['date_display']}, Gallery collection and credit. Creator/alias, all literal-title, accession, native URL/ID and equivalent Wikidata comparisons reviewed. "
  basis+=SPECIAL.get(oid,'Preserve the individually inventoried source object, physical medium/dimensions and every creator qualification. Other named subjects, unrelated creators and different physical media do not identify this object.')
  if re.search(r'\b(?:leaf|fragment|panel|predella)\b',f['title'],re.I):basis+=' One native accession counts once; no inferred complete manuscript, altarpiece or extra components.'
  basis+=' Source collection credit: '+f['credit_line']+'. Full source provenance: '+(f['provenance_text'] or 'No provenance narrative supplied.')
  limit='Editorial confidence0.90 is not calibrated. Museum connection does not establish current display, custody or legal title. Original LUX aggregation, unknowns, provenance gaps and rights labels remain evidence. No image permission or artist authority is inferred.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.9,basis=basis,limitation=limit,facts=f,index=row['index'],source_reference=row['source_reference'],comparison=cmp))
 assert len(decisions)==99 and len(queue)==141 and len({r['facts']['inventory'] for r in decisions})==99
 assert {'49021','51376','254'}.issubset({r['facts']['native_object_id'] for r in decisions})
 m.save(RUN/'native-editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,supplements=[],candidate_reference=w.ref(RUN/'native-candidates-001.json.gz'),comparison_reference=w.ref(RUN/'native-comparisons-001.json.gz'),selection_policy='99supported additions from240bounded painting objects. Reaches129eligible records from30; further research required toward200. Anonymous, Greek, Cretan and Russian works retained where source/identity evidence supports them.'))
 m.save(RUN/'native-followup-queue-001.json.gz',dict(at=m.now(),rows=queue,counts=dict(collections.Counter(r['review_state'] for r in queue)),policy='117source holds and24editorial holds. Evidence retained, no database mutation.'))
 print('Approved',len(decisions),'held',len(queue),flush=True)
if __name__=='__main__':main()
