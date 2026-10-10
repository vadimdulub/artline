"""Physical-unit, creation-date and literal creator review of selected ASFA works."""
import collections,csv,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
PRINT_DATE_REVIEW={131,132,133,140,141}
UNKNOWN_DATES=PRINT_DATE_REVIEW|{199}
TYPE={'Ζωγραφική':'painting','Νωπογραφία':'painting','Σχέδιο':'drawing','Χαρακτική':'print','Γλυπτική':'sculpture'}

def main():
    assert not (RUN/'editorial-source-decisions-001.json.gz').exists()
    rows=m.load(RUN/'selected-source-records-001.json.gz')['rows'];native={x['number']:x for x in m.load(RUN/'native-source-records-001.json.gz')['rows']};visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']};originals={x['number']:x for x in m.load(RUN/'original-image-references-001.json')['rows']}
    assert len(frames)==258 and not visual['exact_duplicate_groups'] and not visual['unavailable_numbers'];out=[]
    for row in rows:
        n=row['number'];f=row['fields'];v=native[n];literal=f.get('Ημερομηνία δημιουργίας',[''])[0];creator=f['Δημιουργός'][0];kind=f['Τύπος'][0]
        assert v['title']==f['Τίτλος'][0] and v['description_blocks'][0]==creator and v['description_blocks'][-1]==row['source_id'].split('000187-')[1]
        assert literal in v['description_blocks'] if literal else n==258
        if literal:
            assert re.fullmatch(r'\d{4}(?: - \d{4})?',literal),literal;years=list(map(int,re.findall(r'\d{4}',literal)));first,last=years[0],years[-1];precision='exact' if first==last else 'range';display=literal
        else:first=last=None;precision='unknown';display='Creation date unknown'
        notes=['One individually catalogued physical artwork with a native exhibit page, full inventory label and matching source composition; studies of the same classroom model or shared subject are compared as separate works, not merged by title.', 'Native Greek title and creator spellings retained. Literal English translations remain evidence, including mistranslations; no new artist authority or biography is inferred. The gallery connection is a collection holding, not current display.']
        if creator=='Ορφανό':creator=None;notes.append('Ορφανό / Orphan is treated as an unidentified creator label, not a person name.')
        if n in UNKNOWN_DATES:
            first=last=None;precision='unknown'
            if n in PRINT_DATE_REVIEW:
                display='Impression date unresolved (source: '+literal+')';notes.append('The museum calls this a print from Ten White Lekythoi. Its source date'+literal+'may concern design/proof production; the National Archaeological Museum dates the published portfolio1956. The specific impression/proof is not established. Keep both claims, numeric creation dates null, no image delivery under pre1956policy. No automatic1956rewrite; the ancient vase is not this print.')
            else:
                display='Creation date unresolved (source:1958; attribution to Theofilos)';creator='Χατζημιχαήλ Θεόφιλος (source attribution; creator role unresolved)';notes.append('The source attributes this fresco to Theofilos1873–1934 but dates it1958; possible copy/transfer/version or metadata discrepancy is unresolved. No direct artist link, invented original date or image delivery. The source depiction and museum collection identity are retained in review.')
        if n==198:
            creator='After Χατζημιχαήλ Θεόφιλος; copyist unidentified';notes.append('Title explicitly says copy, with source1958date after Theofilos died1934. Record the1958museum-catalogued copy, qualify Theofilos as prototype artist, and leave the copyist unidentified. Do not make this an original painting by Theofilos.')
        if n in [97,98]:notes.append('Both records share numeric inventory stem00752and supplied1945dimensions, but full native labels00752 versus00752_ZOG727 and source compositions differ: frontal bald moustached man in blue versus three-quarter dark-haired man in a dark coat. Retain full source identities; do not normalize away suffixes or equate by stem. Attribution/date remain supplied review claims.')
        if n in [134,137]:notes.append('Separate print impressions, XAR364versusXAR363: pencil signatures differ in stroke/placement, margins and ink wear differ, and right foot/foreground abrasions differ. Same block composition does not mean the same physical sheet.')
        if n in [138,139]:notes.append('Separate signed print impressions, XAR368versusXAR369:138has pronounced fine vertical abrasion across the head/body and irregular lower black inking,139has different lower scratches/ink coverage and a different pencil signature. Distinct sheets, not resized copies of one photograph.')
        if n in [171,172]:notes.append('Separate1956portrait impressions, XAR426versusXAR427:172has visibly different foxing near the face and shoulder, lower plate edge, margins and pencil signature; frame dimension differs33.5versus35.5. Same plate, distinct physical impressions. Research images only because1956exceeds image cutoff.')
        if n==168:notes.append('Source person authority832207424identifies YiannisFaitakis1926–2012. Do not conflate with SteliosFaitakis or create a modern-artist conflict from surname similarity.')
        if n>=196 and n!=258:notes.append('Religious/historical/architectural subjects and copied inscriptions date the prototype or depicted event, not automatically this museum study. Preserve explicit copy wording and1957/1958source dates. These records do not establish ownership of depicted church furnishings or buildings.')
        existing=row['index']['historical_source_match'];image_candidate=not existing and last is not None and last<=1955
        if image_candidate:assert n in originals and not originals[n]['research_only']
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=v['title'],original_title=f['Τίτλος'][0],title_source_literals=f['Τίτλος'],creator_label=creator,creator_source_literals=f['Δημιουργός'],artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=literal,work_type=TYPE[kind],object_form=None,cultural_context=None,medium_text=None,dimensions_text=f.get('Έκταση (μέγεθος ή διάρκεια)',[None])[0],inventory=v['description_blocks'][-1],description_source=f.get('Περιγραφή',[]),decision='existing_comparator' if existing else 'proposed_review_artwork',review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],authority_links_unscoped=row['creator_authorities'],native_metadata=v,source_receipt=row['receipt'],visual_reference=frames[n],source_image_reference=originals.get(n),source_image_reviewed=True,image_candidate=image_candidate,image_hold_reason='Existing record preserved' if existing else 'Physical impression/date review' if n in UNKNOWN_DATES else 'Source creation date after1955 or range crossing1955' if not image_candidate else None,date_scope_review_required=first is None,proposed_status='review',ready_to_apply=False,applied=False))
    candidates=[x for x in out if x['decision']=='proposed_review_artwork'];assert len(candidates)==250 and sum(x['first'] is None for x in candidates)==6 and sum(x['image_candidate'] for x in candidates)==142
    deps=[c.ref(RUN/name) for name in ['selected-source-records-001.json.gz','native-source-records-001.json.gz','visual-references-001.json','original-image-references-001.json','publication-context-001.json']]
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=out,dependencies=deps,script_reference=c.ref(Path(__file__).resolve()),visual_review=dict(source_contacts_viewed=11,source_thumbnails_viewed=258,native_contacts_viewed=7,native_originals_viewed=148,individual_original_numbers=[134,137,138,139,171,172],exact_thumbnail_duplicates=0),policy='250distinct proposed physical works,244numeric-date candidates and6unresolved date claims;8existing records unchanged.142original image candidates. Sourcecreator authority-links list is unscoped and may include sitters; it is NOT an approved artist mapping. Global identity reconciliation and selected-image preparation pending. No production writes.'))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as f:
        fields=['number','source_id','title','creator_label','first','last','date_display','work_type','inventory','decision','image_candidate','source_url'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(out)
    m.save(RUN/'source-review-summary-001.json',dict(at=m.now(),proposed=250,numeric_dated=244,unknown_dates=6,existing_comparators=8,image_candidates=142,index_cards=270,excluded_documents=13,source_objects_reviewed=258,indexed_source_objects=270,total_collection_source_entries=4012,source_entries_outside_index_and_existing_comparators=3741,new_production_records=0,source_decisions_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz')))
    print(json.dumps(dict(proposed=250,dated=244,unknown=6,image_candidates=142)),flush=True)

if __name__=='__main__':main()
