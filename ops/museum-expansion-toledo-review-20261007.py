#!/usr/bin/env python3
"""Record object-level Toledo editorial decisions after reading source narratives and identity leads."""
import importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-toledo-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w;m=w.m;RUN=w.RUN
HOLDS={
 '55283':'Existing Anton Mauve A Dutch Road, 1880, a7b47f1a-4320-5082-b5b1-db7ca6487ce5 requires reconciliation, not another record.',
 '55161':'Several Diaz Fontainebleau identities, including an unlocated exact-title entry and untranslated variants, remain unresolved.',
 '55257':'A-B grouped triptych wings combine paintings and sculpture; narrative assigns production to Lendenstreich workshop while authority heading names the artist. Preserve this grouping and qualification for follow-up.',
 '54740':'An existing Lorenzo Monaco Madonna of Humility without inventory could overlap this workshop panel; different imported date alone does not resolve it.',
 '55353':'Existing Steen peasants outside an inn requires physical-version comparison.',
 '55065':'Existing Fantin-Latour flowers-and-fruit still life dated1866 requires physical-version comparison.',
 '55131':'Multiple Boudin Trouville versions, including overlapping1864/1865 dates and incompletely described records, require physical comparison.',
 '54797':'Multiple Utrillo Montmartre street identities in several languages require further version comparison.',
 '55170':'Generic Derain Landscape identities require a physical comparison beyond titles and differing dates.',
 '54794':'One of four Guillaume portraits; compare the existing Novo Pilota entry before adding this library portrait.',
 '54985':'The Boston1899 Isles of Shoals canvas has nearly identical dimensions. Preserve both identities for direct source-version review.',
 '55152':'The existing Corot Pond in Picardy has a close date and size; compare native physical identities before addition.',
 '55218':'An incompletely described Goodhart master Madonna and Child enthroned needs further comparison against this anonymous panel; different imported century alone is insufficient.'}
NOTES={
 '55698':'The Date field says about1911 while the label proposes1894-1911. Both are retained; the catalogue uses the explicit circa Date without treating the narrower wording as a certain year.',
 '57077':'The explicit circa1905 Date is retained beside the1904 exhibition/reference evidence. No exact creation year or artist biography is inferred.',
 '54987':'Toledo1922.36 has an entire frame76.8x104.8cm, smaller than the existing NGA1973.16.1 painted canvas98x161.5cm; these are distinct Tiber compositions.',
 '55201':'The Toledo115.6x96.2cm oil canvas is distinct from the anonymous Cleveland2013.312 gum-tempera/gold-on-paper work. The label explicitly identifies Guardi copying an Andrea Pozzo composition; no Pozzo creator link is added.',
 '57056':'The museum explicitly says After Jean-François Millet. This60.9x37.5cm oil panel is distinct from the small Gleaners etchings and unrelated Bather/Sewer/Lovers works in the identity scope.',
 '55073':'The native narrative distinguishes this right-hand-scene version from the Amiens mural and the Metropolitan version. Toledo1951.313 measures94x125.1cm, unlike the Walters113.5x197cm canvas and Met33.3x134.3cm canvas. One separately inventoried version, not the parent mural, is counted.',
 '55216':'The source explicitly calls this a cut fragment from an Annunciation polyptych. Count only inventory1951.341, the surviving Head of the Virgin; no reconstructed altarpiece or lost companion is created.',
 '57076':'The museum classifies the object as Paintings but supplies metal and stones as medium and describes the covered background. Preserve both literal facts and unknown creator, without inventing a paint support or splitting off its cover.',
 '56983':'Unknown creator and Cretan origin remain source evidence. Probably mid-17th century is retained literally with uncertain full-century1601-1700 bounds; no precise midpoint is invented.',
 '57075':'School of Andrey Rublyov is retained as an object-level qualification, not a definite artist link. The source circa1420 date belongs to the icon, not Rublyov biography.',
 '55359':'The octagonal portrait is distinct from the existing1906 Mary portrait; native title/date and dimensions remain literal. The label says Mary was about16, while Date says about1910; neither approximation becomes an exact inferred birth-based year.',
 '55136':'Toledo1951.404 is a47x63.2cm oil painting from the small Venetian-view series; the existing1925.1239.18 Prison view is a14.4x21.1cm etching, not this object.',
 '55180':'Unknown maker remains unknown. Native research revises the former Henry VI marriage interpretation to an unidentified male saint; the complete source title and late15th-century date survive.',
 '54965':'Anonymous French late15th-century panel, not the similarly titled prints, later paintings, or small Raphael/Rogier panels in the comparison scope.',
 '76788':'The museum supplies no medium. Keep it null; use only the explicit Meiji Era1868-1912 range, not an artist lifespan.'}
def main():
 source=RUN/'native-candidates-003.json.gz';candidate=m.load(source);comparisons=m.load(RUN/'native-comparisons-001.json.gz');cm={x['source_id']:x for x in comparisons['records']};decisions=[];follow=[]
 for row in candidate['rows']:
  sid=row['source_id'];f=row['facts']
  if row['state']!='candidate' or sid in HOLDS:
   follow.append(dict(row,state='editorial_hold' if sid in HOLDS else 'source_hold',editorial_reason=HOLDS.get(sid)));continue
  cmp=cm[sid];assert not cmp['source_hits'] and not [h for h in cmp['inventory_hits'] if h['relevant']]
  basis=f"Official Toledo object{sid}, inventory{f['inventory']}, links its title, literal creation Date, medium/dimensions and acquisition credit ({f['acquisition']}) to this museum's collection. The preserved collection index agrees. Creator-scoped, exact-title, inventory and source-URL comparisons found no unresolved same-object lead after editorial review. "
  basis+=NOTES.get(sid,'Source narrative and references were reviewed. Generic title matches with different documented makers or media are not assumed to be the same object; no source history, sitter event or artist lifespan replaces the creation Date.')
  if sid in ['57059','58860','58861','58862']:basis+=' Each study has its own native object ID and accession. Shared frame dimensions are retained as frame dimensions, not invented individual supports or four separate frames; the completed painting1906.255 has a different identity.'
  if 'On Loan' in ' '.join(f['core_text']):basis+=' The source marks an external address/On Loan while retaining its accession and acquisition credit. This supports the documented collection connection only, never current physical presence at Toledo.'
  decisions.append(dict(source_id=sid,state='approved_review_only_addition',confidence=.9,basis=basis,limitation='Editorial confidence, not a calibrated probability. Museum connection does not establish legal title, physical custody or current display. Web-tool extracts include their crawl metadata; they are not live raw HTTP responses. Qualified and unknown creators, source approximations, omitted fields and original narrative remain evidence.',facts=f,index=row['index'],source_reference=row['source_reference'],comparison=cmp))
 assert len(decisions)==105 and len(follow)==24
 m.save(RUN/'native-editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=decisions,candidate_reference=w.ref(source),comparison_reference=w.ref(RUN/'native-comparisons-001.json.gz'),policy='Individual source narrative, collection, qualification, grouping and version review.105 eligible review-only records;13 editorial holds plus11 source holds and15 failed object requests retained.'))
 m.save(RUN/'native-followup-queue-001.json.gz',dict(at=m.now(),rows=follow,capture_errors=candidate['errors'],policy='All39 unadded index leads remain traceable. Refresh database identity comparisons before follow-up writes.'))
 print(json.dumps(dict(approved=len(decisions),held=len(follow),failed=len(candidate['errors']))))
if __name__=='__main__':main()
