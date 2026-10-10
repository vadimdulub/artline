"""Select distinct photographic works with explicit digital-collection and date limits."""
import collections,csv,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-photographs-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN

def clean(value):return re.sub(r'\\+"','"',value).strip()

def dates(row):
    literal='; '.join(row['fields']['Ημερομηνία']);n=row['number']
    if n<=7:
        assert literal=='1960'
        return None,None,'unknown','Photograph date unresolved: source field1960; series title1965–1970',literal
    if re.fullmatch(r'\d{4}',literal):return int(literal),int(literal),'exact',literal,literal
    if literal=='1965-70':return 1965,1970,'range',literal,literal
    if literal=='1965 - 1968':return 1965,1968,'range',literal,literal
    raise ValueError((n,literal))

def main():
    assert not(RUN/'editorial-source-decisions-001.json.gz').exists();source=m.load(RUN/'selected-source-records-001.json.gz');visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']};assert len(frames)==65 and not visual['unavailable_numbers'] and not visual['exact_duplicate_groups']
    out=[]
    for row in source['rows']:
        n=row['number'];f=row['fields'];assert f['Υλικό']==['Ψηφιακή φωτογραφία μόνο'] and f['Τύπος']==['Φωτογραφία'];assert f['Επιμέρους συλλογή']==['Δωρεά Κουτσαπλή']
        first,last,precision,display,literal=dates(row);notes=['One distinct photographic composition in the museum-supplied Koutsapli-donation digital collection. The catalogued work is the historical photographic image; digitisation/printing dates and original negative or print support are unspecified. No claim of an original negative or vintage print holding.', 'Literal archive credit names GeorgiosBakouros–LizaKoutsapli. The donor interview corroborates an archive donation, not the individual maker/material/date of every catalogue item. Preserve credit separately; no person authority or unqualified individual authorship is fabricated.', 'Source numeric dates describe the catalogued historical photograph. Dates of buildings, demolition, current condition in2019/2025 or modern digitisation do not replace those dates.']
        if n<=7:notes.append('Date1960 conflicts with1965–70series title; retain both and leave numeric creation dates unknown pending reconciliation. No1960–1970interval invented.')
        if n in [8,48]:notes.append('Same Piraeus church area but distinct exposures: different viewpoint, lamp position, foreground and buses/structures; source labelsMVE26064 versusMVE26066. Not duplicate scans/crops.')
        if n in [39,56]:notes.append('Similar corner buildings are distinct:39has strong rustication/arched ground-floor openings and pedimented facade;56has different cornice, windows and surrounding buildings. Source labelsMVE25705 versusMVE25700.')
        if n in [2,3,35,50]:notes.append('Different Syntagma compositions, viewpoints and foreground arrangements, not repeated scans of one photograph.')
        if n in [14,18,27,38,57]:notes.append('Qualified place identification is preserved as supplied; no certainty inferred from a tentative caption.')
        if n in [34,44,45,51,53]:notes.append('Architects, historical residents and makers/subjects of depicted monuments are not assigned as photographers. The museum connection concerns this photograph, not the depicted building or sculpture.')
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=clean(f['Τίτλος'][0]),original_title=f['Τίτλος'][0],creator_label=None,creator_source_literals=f['Δημιουργός'],artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=literal,work_type='photograph',object_form=None,cultural_context=None,medium_text=f['Υλικό'][0],dimensions_text=None,inventory=None,description_source=[clean(x) for x in f.get('Περιγραφή',[])],decision='existing_comparator' if row['index']['historical_source_match'] else 'proposed_review_artwork',review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],source_receipt=row['receipt'],visual_reference=frames[n],source_image_reviewed=True,date_scope_review_required=first is None,proposed_status='review',museum_connection='Documented museum digital collection, Koutsapli donation; no original negative/vintage-print or current-display assertion.',ready_to_apply=False,applied=False))
    candidates=[x for x in out if x['decision']=='proposed_review_artwork'];assert len(candidates)==55 and sum(x['first'] is None for x in candidates)==7;assert all(x['last'] is None or x['last']<=1970 for x in candidates)
    deps=[c.ref(RUN/name) for name in ['selected-source-records-001.json.gz','metadata-selection-001.json','visual-references-001.json','archive-context-001.json']]
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=out,dependencies=deps,script_reference=c.ref(Path(__file__).resolve()),visual_review=dict(sheets_viewed=3,thumbnails_viewed=65,individual_detail_numbers=[8,48,39,56],exact_duplicate_hash_groups=0,unavailable=0),policy='55distinct photographic-work proposals, pending fresh production counterpart reconciliation. Museum medium says digital photograph only; original support, print date and negative ownership remain unspecified. Seven conflicting source dates kept null. No production changes or image attachments.'))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as f:
        cols=['number','source_id','title','creator_label','first','last','date_precision','work_type','decision','source_url'];w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(out)
    m.save(RUN/'source-review-summary-001.json',dict(at=m.now(),proposed_new_records=55,numeric_dated_candidates=48,unknown_date_candidates=7,existing_comparators=10,held=0,images_selected_for_delivery=0,image_policy='All selected dates1960or1965–1970fall after1955; source thumbnails are research comparison evidence only.',new_production_records=0,source_decisions_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz')))
    print(json.dumps(dict(proposed=55,dated=48,unknown=7,existing=10,images=0)),flush=True)

if __name__=='__main__':main()
