"""Source and physical-unit decisions, still pending production reconciliation."""
import collections
import csv
import importlib.util
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

HOLDS={35:'Restaurant-menu lithograph is inscribed Paris14December72. The century and physical printing date require reconciliation; likely1972 must not be assumed pre1971.',94:'Description explicitly identifies November2018; excluded post1970 even though the date field is empty.',108:'Artist-supervised digital printing on vinyl after a smaller original. This physical reproduction is not interchangeable with the original; creation date of this version is unresolved.'}
NOTES={
1:'The1835 in the description concerns the represented residence/context, not an explicit printing date.',
2:'Byzantine6th-century subject, not an ancient creation date. Different figures and photographed inventory23517 distinguish source3.',
3:'Byzantine6th-century subject, not an ancient creation date. Different figures and photographed inventory23520 distinguish source2.',
4:'Candia composition and visible inventory10114 differ from source5 inventory10113; distinct physical framed prints.',
5:'Candia composition and visible inventory10113 differ from source4 inventory10114; distinct physical framed prints.',
7:'The547 in the title dates the depicted subject, not manufacture of this paper print.',
8:'Justinian/Theodora lifespans in the title are subjects, not creation years.',
10:'Repeated Dunkerque title differs visually from existing source11: built harbour/foreground workers versus open water and a red-sailed ship; photographed inventories10100 versus10101. Preserve literal title pending title-specific correction.',
15:'Brest composition and inventory10105 differ from source16 inventory10104; not duplicate merely because title is repeated.',
16:'Brest composition and inventory10104 differ from source15 inventory10105; not duplicate merely because title is repeated.',
27:'The New York Public LibraryDigital collections. is a source/institution label, not a human creator. The museum photograph shows a distinct framed physical print with inventory23521; retain the literal credit in evidence without inventing a maker.',
31:'Observed thumbnail is the reverse of a framed object, not the front composition. The handwritten1758-1836 accompanies C.Vernet and is a lifespan, not artwork creation. Source describes hand-coloured aquatint, despite broad painting category. No primary front-image claim.',
37:'Source credits Eastman Kodak Co.; this manufacturer label does not establish the drawing maker. Photograph shows a framed coloured drawing on card with inventory10154. Keep source date1948 and unresolved creator; do not assign it to Malamos by resemblance.',
42:'Detailed physical lion-on-shield description supports this metadata proposal; thumbnail failed decoding and was not retried. No visual identity review claimed for42.',
44:'Distinct street view from source45: view toward different buildings; same title and date are not identity.',
45:'Initial contact-sheet suspicion versus128 cleared by full thumbnail comparison:45 depicts a hill/skyline;128 a square and substantial buildings. Also different from44. No alias or merge.',
49:'Reverse family annotation24May1946 and old number1177 are not silently converted into a creation year or canonical museum accession.',
50:'Source transcribes1863 in an inscription; keep as inscription evidence. No explicit creation-date field; numeric creation remains unknown pending review.',
56:'Two joined pieces form one icon, not two artworks. Slavic inscriptions are explicit; a Russian origin is not inferred solely from the script.',
61:'One Russian icon with metal covering and its small icon case; no separate artwork counts for the covering/frame/case. Possible gilded silver remains qualified.',
62:'Two registers of saints are one wooden icon. Dedication includes1871 and initials; retain inscription as evidence without inventing a creator or exact manufacture date.',
63:'The physical object is a decorated wooden frame with a postcard photograph of the Tinos icon; it is not ownership of the original Tinos icon. Classify the composite decorative object, not a painted icon.',
84:'Source creator is Takis Kalmouchos but description gives a questioned signature. Preserve qualified attribution; no secure artist link yet.',
87:'Source creator fieldFOLTZ PHILIPPE BORMERG conflicts with reportedT.Foye signature. Keep attribution unresolved; no forced reconciliation.',
88:'Source supplies a named modern portrait and gift inscription but no creation date. Date-scope review remains required; telephone/contact details are retained only in source evidence, not intended public prose.',
90:'Source says around1850, not exact1850. Named designer/printmaker roles await reconciliation.',
103:'Source explicitly identifies the depicted KonstantinosChristomanos and Karavia signature; sitter is not a second creator.',
105:'Lithographic processing after an earlier photograph with altered background. The battle/event date does not date this lithographic version.',
106:'Source distinguishes Paulide as designer andDeye as lithographer; retain roles as source evidence, not undifferentiated invented painter authorities.',
109:'Source1900 date checked against the exact KontopoulosVyron authority; no modern-name confusion or inferred lifespan date.',
111:'Source datearound1850 conflicts with description of prototype painting1853-1854. Preserve both in evidence; proposed numeric creation years remain null, not an invented correction.',
112:'1900 is part of the represented scene title, not an explicit manufacture date for this oil-on-aluminium painting.',
117:'Full-length Thon portrait differs from the oval watercolour133. Fresh global same-work reconciliation still required.',
120:'This1841 coloured lithograph depicts Stademann drawing in1835; the scene/preparatory-work date does not replace the1841 source print date.',
128:'Different composition from45 verified at full thumbnail size; square/buildings versus hill/skyline. Both independent source objects remain proposals.',
133:'Oval watercolour1899 differs from full-length painting117; one framed physical support.',
138:'Wax Byron bust differs from139 painted metal bust on square foot; source materials retained.',
139:'Painted metal Byron bust differs in form and material from138 wax bust.',
159:'Different coastal composition from160 despite the same generic print title andGudin credit; inventories10110 versus10109.',
160:'Different storm/boat composition from159; inventories10109 versus10110.',
162:'Pinx R.A. in the creator list is an inscription/role fragment, not an additional human artist. Keep literal source list; Brandard/Turner roles require reconciliation.'}

def clean(value):return re.sub(r'\\+"','"',value).strip()

def dates(row):
    n=row['number'];values=row['fields'].get('Ημερομηνία',[]);literal='; '.join(values)
    if n==111:return None,None,'unknown','Creation date unresolved; source says around1850 and describes an1853–1854 prototype',literal
    if not literal:return None,None,'unknown','Creation date unknown',None
    if re.fullmatch(r'\d{4}',literal):return int(literal),int(literal),'year',literal,literal
    if re.fullmatch(r'\d{4}-\d{4}',literal):first,last=map(int,literal.split('-'));return first,last,'range',literal,literal
    if re.fullmatch(r'\d{2}/\d{2}/\d{4}',literal):year=int(literal[-4:]);return year,year,'year',literal,literal
    if literal=='Γύρω στο 1850':return 1850,1850,'circa',literal,literal
    raise ValueError((n,literal))

def main():
    assert not(RUN/'editorial-source-decisions-001.json.gz').exists()
    source=m.load(RUN/'selected-source-records-001.json.gz');visual=m.load(RUN/'visual-references-001.json');assert len(source['rows'])==145 and len(visual['rows'])==142 and visual['unavailable_numbers']==[42]
    frames={x['number']:x for x in visual['rows']};out=[]
    for row in source['rows']:
        n=row['number'];f=row['fields'];first,last,precision,display,literal=dates(row)
        title=clean(f['Τίτλος'][0]);creators=f.get('Δημιουργός',[]);anonymous=not creators or all(x in ['Άγνωστος Δημιουργός','Αγνώστου'] for x in creators)
        creator=None if anonymous or n in {27,37} else '; '.join(creators)
        if n==84:creator='Attributed to Καλμούχος Τάκης (signature questioned in source)'
        if n==87:creator='Unresolved attribution: source lists FOLTZ PHILIPPE BORMERG; reported signature T.Foye'
        if n==162:creator='Brandard Edward; TURNER JOSEPH MALLORD WILLIAM (source roles unresolved)'
        kind='unknown';form=None
        cats=row['index']['selected_categories'];medium='; '.join(f.get('Υλικό',[])) or None
        if 'Icon' in cats and n!=63:kind='painting';form='icon'
        elif 'Sculpture' in cats:kind='sculpture'
        elif 'Engraving' in cats or 'Lithography' in cats or n==31:kind='print'
        elif 'Drawing' in cats or n in {37,44,45,47,65,67,68,69,70,71,72,73,74,75,76,78,80,81,82,83,102,115,128}:kind='drawing'
        elif n in {33,101,133}:kind='watercolor'
        elif 'Painting' in cats:kind='painting'
        if n==108:kind='print'
        notes=[NOTES[n]] if n in NOTES else []
        if n in {65,69,70,75,80}:notes.append('Two drawings are documented and visibly placed on one sheet/support. Count this source unit once, not as two additions.')
        if 140<=n<=152:notes.append('Museum identifies a study by VasileiosMarkezinis during adolescence. Several copy well-known compositions; these are the student studies, not originals by the depicted-model artists. No numeric dates inferred from birth/adolescence or signatures copied in an exercise.')
        decision='existing_comparator' if row['index']['historical_source_match'] else 'hold_scope' if n in HOLDS else 'proposed_review_artwork'
        if n in HOLDS:notes.append(HOLDS[n])
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=title,original_title=f['Τίτλος'][0],creator_label=creator,creator_source_literals=creators,artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=literal,work_type=kind,object_form=form,cultural_context='Russian' if n==61 else None,medium_text=medium,dimensions_text=None,inventory=None,description_source=f.get('Περιγραφή',[]),decision=decision,review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],source_receipt=row['receipt'],visual_reference=frames.get(n),source_image_reviewed=n in frames,date_scope_review_required=first is None,proposed_status='review',museum_connection='Documented museum catalogue object, not a current-display assertion.',ready_to_apply=False,applied=False))
    candidates=[x for x in out if x['decision']=='proposed_review_artwork'];assert len(candidates)==135
    assert sum(x['decision']=='existing_comparator' for x in out)==7 and sum(x['decision']=='hold_scope' for x in out)==3
    assert sum(x['object_form']=='icon' for x in candidates)==14
    deps=[c.ref(RUN/name) for name in ['selected-source-records-001.json.gz','metadata-selection-001.json','visual-references-001.json','creator-source-corroboration-001.json']]
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=out,dependencies=deps,script_reference=c.ref(Path(__file__).resolve()),visual_review=dict(sheets_viewed=6,thumbnails_viewed=142,individual_detail_numbers=[45,128,31,37,35,87,84,149],exact_duplicate_hash_groups=0,unavailable_number42=True),policy='Proposals pending fresh global duplicate/artist/physical identity reconciliation. Unknown dates explicitly require scope review and do not count as numerically eligible. Exact source labels and qualified attributions retained; no new authority records, publish/display claims or DB writes.'))
    table=RUN/'candidate-review-001.csv'
    with table.open('x',encoding='utf-8-sig',newline='') as f:
        columns=['number','source_id','title','creator_label','first','last','date_precision','work_type','object_form','decision','source_url'];w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(out)
    summary=dict(at=m.now(),proposed_new_records=len(candidates),numeric_dated_candidates=sum(x['first'] is not None for x in candidates),unknown_date_candidates=sum(x['first'] is None for x in candidates),types=dict(collections.Counter(x['work_type'] for x in candidates)),icons=14,existing_comparators=7,scope_holds=3,index_post1970_excluded=17,new_production_records=0,ready_to_apply=False,source_decisions_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'))
    m.save(RUN/'source-review-summary-001.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
