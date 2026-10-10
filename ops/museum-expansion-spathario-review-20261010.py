"""Literal dates, physical units, maker roles and visual scope after156record review."""
import collections,csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-spathario-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
SCOPE={2,4,5,6,9,10,11,13,15,26,50,51,52,53,55,75,87,88,101,113,115,123}
CRIME={23,25,93,125,146,149,150}
MERGED={24:[24,151],149:[149,125]}
PRINTS={3,7,8,12,14,71,74,76,86,102,103,104,105,106,107,122}
CENTURY={38,39,40,41,82,112}

def main():
    dest=RUN/'editorial-source-decisions-001.json.gz';assert not dest.exists()
    source=m.load(RUN/'selected-source-records-001.json.gz')['rows'];visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']}
    assert len(source)==len(frames)==156 and not visual['unavailable'] and not visual['exact_duplicate_groups']
    out=[]
    for row in source:
        n=row['number'];f=row['fields'];desc=f.get('Περιγραφή',[]);title=f['Τίτλος'][0];creator=f.get('Δημιουργός',[None])[0];creator=None if creator=='Άγνωστος Δημιουργός' else creator
        dates=f.get('Ημερομηνία',[]);first=last=int(dates[0]) if dates else None;precision='exact' if dates else 'unknown';display=str(first) if dates else 'Creation date unknown'
        notes=['156 individual museum metadata records and156 authentic thumbnails reviewed in seven contact sheets; originals125/149 and24/151 examined separately.','Greek literal metadata takes precedence over inconsistent English translations; both versions remain evidence. Referenced character designers are distinct from the makers in the literal creator field.','One physical object, documented group or ensemble per catalogue unit. SourceURL IDs are not inventory numbers. Holdings do not establish current display.']
        if n in CENTURY:
            assert any('19' in x for x in desc);first,last,precision,display=1801,1900,'century','19th century (museum description)';notes.append('Index has no date, but literal museum description explicitly supplies19thcentury for this leather puppet. No inferred exactyear.')
        if n in CRIME:
            first=last=None;precision='unknown';display='Creation date unresolved (source:1930)';notes.append('Museum says1930 and describes Athanasopoulos drama. Published memoir research illustrates the performance poster as1931, after the documented crime. Reused earlier puppets versus source dating error unresolved. Preserve1930 as evidence; do not replace it with an invented1931 execution date or approve its image by age.')
        if n in [110,111]:
            first=last=None;precision='unknown';display='Assembly date unknown; source photograph date retained';notes.append('Framed photographic assemblage counted once. Source dates1960/1953 do not separately establish the photograph, carved frame and final assembly dates. No image approved under1955rule.')
            creator='Σωτήρης Σπαθάρης (carved frame; photographer unidentified)' if n==110 else 'Ευγένιος Σπαθάρης (source maker label; role unresolved); photographer unidentified'
        if n==71:creator="HIS MASTER'S VOICE (publisher; cover illustrator unidentified)";notes.append('Publisher label is not a named cover artist. One printed record cover, not the performed work or every pictured puppet.')
        if n==74:creator='ΣΑΛΙΒΕΡΟΣ (publisher; illustrator unidentified)'
        if n==76 or 103<=n<=107:creator='ΑΓΚΥΡΑ (publisher; illustrator unidentified)'
        if n in [74,76] or 102<=n<=107:notes.append('One illustrated printed issue or intact papercraft sheet per record. Multiple characters and paired serial numbers are not separate artworks. Literal publisher placeholders preserved in citations, omitted from displaylabel.')
        if n==17:notes.append('Title and visible poster read The wedding ofKaragiozis; Greek description incorrectly names Karagiozis thecook. Retain the source title and record the conflictingdescription.')
        if n==36:notes.append('One source-described collage of painted scenery oncloth; four pictured designs are not fourartworks.')
        if n==41:notes.append('ChineseFigure5 is the museum supplied title. The tree-shaped theatrical prop is distinct from38–40; geographic/cultural attribution is not independently corroborated, so no inferred origin or namedmaker assigned.')
        if n==122:notes.append('Illustrated miniature theatre screen retained as one printed designobject. The1960source date is not a claim about the adult maker childhood; do not infer dates from the title.')
        if n in [119,120]:notes.append('Two visually distinct skeleton puppets:119left-facing articulated profile;120front-facing spreadlimbs. Shared title/date does not establish a duplicate.')
        if n in [45,46]:notes.append('Different silhouettes and Greek character titles:45Karagiozis;46Kopritis. The repeated EnglishKaragiozis label is a translation error, not duplicate identity.')
        if n in [23,133]:notes.append('Museum records a paired theatrical group. Preserve one group-level unit, not one record per pictured character.')
        if n in [24,151]:notes.append('151is the same red-shorted turner visible alongside the skeleton in24. Retain both source records as one apotheosis scene/ensemble; do not inflate count with a component view. Mechanical assembly boundaries remain qualified.')
        if n in [125,149]:notes.append('125and149 show opposite sides of the same police puppet: mirrored cutout pattern, joints, hatflower, uniform and leg shape. Reverse cardboard printing is visible on125. Preserve bothtitles andsourceIDs in one artwork;149Greek title chosen.')
        if n in SCOPE:decision='scope_hold';notes.append('Utility ticket, text-led advertisement/programme, plaintextpublication, letterreproduction, genericaward, lighting or soundequipment: no selected visual-art case established.')
        elif n==124:decision='identity_hold';notes.append('Stukas title versus supplied aircraft silhouette remains unresolved; do not silently relabel aircraft or accept depictedevent ascreation.')
        elif n in [125,151]:decision='merged_source_component'
        elif row['index']['historical_source_match']:decision='existing_comparator';notes.append('Existing production metadata, sourceidentity, creatorlabel, date, status, holdings and primaryimage are preserved unchanged.')
        else:decision='proposed_review_artwork'
        if n==24:title='Ο σκελετός του Αθανάσιου Διάκου σουβλισμένος — σκηνή με τον χειριστή'
        if n==110:title='Φωτογραφία Ευγένιου Σπαθάρη σε σκαλιστό κάδρο'
        if n==111:title='Φωτογραφία Ευγένιου Σπαθάρη με Δημήτρη Μητρόπουλο σε σκαλιστό κάδρο'
        kind='print' if n in PRINTS else 'painting' if n in [16,17,36] else 'photograph' if n in [110,111] else 'unknown'
        medium=None
        caption=desc[0] if desc else ''
        for term in ['χαρτόνι και χασαπόκολλα','χαρτόνι και πλαστικό','ζελατίνη/πλαστικό','χαρτόνι','δέρμα','δερμάτινη']:
            if term in caption:medium=term;break
        if caption=='Cardboard figure.':medium='Cardboard'
        if n==36:medium='Painted cloth (museum description)'
        selected=decision=='proposed_review_artwork' and first is not None and last<=1955
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],title=title,title_source_literals=f['Τίτλος'],creator_label=creator,creator_source_literals=f.get('Δημιουργός',[]),artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=dates,source_chronology=row['enrichment'].get('Χρονολογία',[]),work_type=kind,medium_text=medium,dimensions_text=None,inventory=None,object_form=None,cultural_context=None,description_source=desc,decision=decision,source_numbers=MERGED.get(n,[n]),review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],creator_authorities=row['field_enrichment_links'].get('Δημιουργός',[]),source_receipt=row['receipt'],visual_reference=frames[n],source_image_reviewed=True,image_candidate=selected,image_hold_reason=None if selected else 'Existing comparator, scope/identityhold, mergedsecondary view, creation after1955 or unresolvedactualcreation.',date_scope_review_required=first is None,proposed_status='review',ready_to_apply=False,applied=False))
    selected=[x for x in out if x['decision']=='proposed_review_artwork'];counts=dict(collection_index=450,metadata=156,old=16,proposed=len(selected),numeric_date_eligible=sum(x['last'] is not None and x['last']<=1970 for x in selected),unknown_dates=sum(x['first'] is None for x in selected),image_candidates=sum(x['image_candidate'] for x in selected),scope_holds=len(SCOPE),identity_holds=1,merged_secondary_records=2)
    assert counts['proposed']==115 and counts['unknown_dates']==8 and counts['numeric_date_eligible']==107
    m.save(dest,dict(at=m.now(),rows=out,counts=counts,dependencies=[c.ref(RUN/x) for x in ['selected-source-records-001.json.gz','visual-references-001.json','focused-context-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz']],script_reference=c.ref(Path(__file__).resolve()),policy='115proposed artworks covering117source entries,16oldcomparators,22scopeholds,1identityhold. Six19thcentury dates recovered from literaldescriptions. Eight actualcreation dates intentionallyunknown, including six Athanasopoulos units and two photographicassemblages. No inventedcreator or narrowerdate. Four focusedframes and seven contacts visuallyreviewed. No databasewrite.'))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=['number','source_id','title','creator_label','first','last','date_display','work_type','decision','image_candidate','source_url'],extrasaction='ignore');w.writeheader();w.writerows(out)
    print(json.dumps(counts),flush=True)

if __name__=='__main__':main()
