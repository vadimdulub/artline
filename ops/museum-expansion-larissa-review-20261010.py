"""Pin source-backed Larissa physical units, qualified dates and image decisions."""
import collections
import csv
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-comparisons-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF,ref=c.m,c.RUN,c.PROOF,c.ref
IID='d843489b-7a33-5cbb-916a-4eecb0dac8b8'
ALBUM=[176,177,178,179,180,181,182,183,184,185,186,188]
SECONDARY={n:176 for n in ALBUM[1:]}
CONFLICTS={51:'Native date field and SearchCulture say1924–25; the native description explicitly dates this self-portrait to1912. Neither claim is silently preferred; numeric bounds remain null. Both claims precede1955.',
    54:'Native date field and SearchCulture say1924–25; the native description explicitly dates Girls Embroidering to1920–22. Numeric bounds remain null and both claims are retained. Both precede1955.',
    102:'Native date field and SearchCulture say1936; the native description explicitly calls Seated Nude a1927 work. Numeric bounds remain null; design/impression chronology is not invented. Both reported creation dates precede1955.'}
PROSE_DATES={51:'1912',54:'1920-22',102:'1927'}
DATE_IMAGE_HOLDS={32,168,211,212,213,214,215,216}
MISSING_IMAGES={46,67,92}
DRAWINGS={13,14,15,32,55,86,110,146,211}
DISTINCT=[dict(numbers=[118,119],basis='Separate native pages/images show a standing male nude holding a jug and a standing female nude with a hat beside a chair. Same title,1940–46 date and70×120cm dimensions do not make these the same work.'),
    dict(numbers=[109,187],basis='Different Nikolaou gardens:1937 oil on canvas63×82cm shows a broad open garden with lamp, fountain and ball-playing children;1946 oil-tempera61×80cm shows prominent tree trunks. Distinct compositions and physical media.'),
    dict(numbers=[155,159],basis='Papanikolaou National Garden paintings1944:37.5×46.5cm oil on cardboard shows two central bare trees;18.5×30.5cm oil on canvas shows a central branching plane tree and figures. Separate source images and supports.'),
    dict(numbers=[7,8],basis='Separate Volanakis maritime compositions: the named Aris ship and the other night scene have different vessel arrangements; neither is merged merely for a shared artist/subject.'),
    dict(numbers=[30,39],basis='Separate Nikolaos Lytras landscapes with different mountain/tree arrangements. Reciprocal catalogue303/304 references are printed-catalogue cross-references, not invented accession identifiers.')]
NOTES={27:'One documented print from the1919 Quatre Natures Mortes publication. The reference to four woodcuts does not authorize three additional placeholder works.',
    32:'Native After1920 is an open interval. Retain an actual review candidate with unknown numeric bounds; do not infer an upper bound from the artist lifespan.',
    42:'The source distinguishes an original painting made1919 from its later engraved version. Retain this native print record date1921; do not assign the painting date to this impression.',
    50:'Existing comparator only. Source range1924–35 extends beyond the source artist death1928; retain literal evidence and existing metadata, without clipping the range using a lifespan.',
    52:'Literal monastery title retained; the source description and image specifically show a decorated fountain and a boy. No title rewrite from subject inference.',
    70:'Andreas Georgiadis copy/study after El Greco,1930; the physical maker is Georgiadis, not El Greco. Source identifies the Cardinal Nino de Guevara model.',
    84:'Source creator lifespan1903–2004 differs from aggregator1903–2005; no biography update.1935 watercolour33×39.5cm is a Larissa holding. Fresh cross-institution object reconciliation remains required.',
    90:'Andreas Georgiadis copy/study after Rembrandt,1936–37. The Louvre reference describes the model painting, not the holding institution of this copy.',
    91:'Andreas Georgiadis copy/study of a portion of an El Greco composition,1936–37. Preserve its own physical support and maker; no original El Greco identity or date substituted.',
    99:'Native technique identifies this work as a woodcut; the prose mentions an aquatint version separately. Preserve this version.',
    129:'Native/aggregator wording varies slightly (hat/article), not subject identity. This is the source1941–44 lithograph, not an oil portrait inferred from its coloured reproduction.',
    168:'Native range1945–60 is wholly within catalogue scope but crosses the1955 museum-image cutoff; metadata candidate retained, public image held.',
    193:'The museum supplies only initials L.C.; the observed native artist page has no identifying biography. Preserve unresolved object-level initials without a painter ID or invented expansion.',
    212:'Existing comparator has no creator/date. Preserve unknowns; engraving is not dated from apparent style.',
    213:'Existing gypsum relief comparator remains undated; physical date is not inferred from iconography.'}

def work_type(f):
    if f['native_category']in {'Χαρακτική','Γκραβούρα'}:return 'print'
    if f['number']==213:return 'sculpture'
    if f['number']in DRAWINGS:return 'drawing'
    assert f['native_category']in {'Ζωγραφική','Υδατογραφία'},f
    return 'painting'

def main():
    facts=m.load(RUN/'candidate-facts-001.json.gz')['rows'];visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']}
    comparison=m.load(RUN/'comparison-references-001.json');album=m.load(RUN/'album-reference-001.json.gz');rows=[]
    bifolios=[f['number']for f in facts if f['native_technique']=='Τέμπερα και σινική μελάνη'];assert len(bifolios)==18
    for f in facts:
        n=f['number'];frame=frames[n];first,last=f['first'],f['last'];kind=f['date_basis'];note='Full native object-date field retained; ranges are not reduced to their first endpoint or to the index display.'
        if n in CONFLICTS:first=last=None;kind='conflicting_source_dates';note=CONFLICTS[n]
        elif kind=='source_qualified_before':note='Literal '+f['native_date_literal']+' retained without an invented lower bound or an exact creation year.'
        elif kind=='source_open_after':note=NOTES[32]
        elif kind=='unknown':note='No native physical creation date. Unknown bounds preserved; no date inferred from biography, style or institutional history.'
        date_pass=n not in DATE_IMAGE_HOLDS
        image_pass=date_pass and bool(frame['path'])
        image_reason=None
        if n in MISSING_IMAGES:image_reason='Observed native image URL returned404; metadata remains a documented, unillustrated work. No guessed replacement URL.'
        elif not date_pass:image_reason='Physical creation by1955 is not established: '+(f['native_date_literal']or'unknown date')+'.'
        label='Complete museum-supplied reproduction, including its watermark where present.'
        if n in ALBUM:label='Album plate: '+f['title']+'; one view within12 σχέδια από τη Κατοχή, not a separate additional catalogue work.'
        elif n in bifolios:label='Illustrated poem/bifolio: complete supplied open-sheet view, counted once.'
        elif n in {70,90,91}:label='Complete supplied reproduction of the Georgiadis copy/study; not the source master painting.'
        editorial=NOTES.get(n)
        if n in ALBUM:editorial='Native descriptions identify an album of12 lithographs. Count the documented series as one conservative physical aggregate with12 separately labelled plate views; no additional album-plus-plates count. The Parliament catalogue corroborates publication title/year, not identity of its copy with Larissa holdings.'
        elif n in bifolios:editorial='One separately documented illustrated-poem support/bifolio, counted once rather than once per page. Source medium is tempera and India ink; Byzantine visual influence is not a medieval creation date. No claim all18 are bound into one album.'
        rows.append(dict(f,institution_id=IID,original_title=f['title'],
            title='12 σχέδια από τη Κατοχή'if n==176 else f['title'],title_basis='Explicit album title from Parliament catalogue148/149, corroborated by all12 Larissa album descriptions; native plate titles retained separately.'if n==176 else'native_object_title',
            decision='existing_comparator'if f['role']=='existing_comparator'else'same_album_plate_secondary'if n in SECONDARY else'candidate_primary',primary_number=SECONDARY.get(n,n),
            first=first,last=last,date_basis=kind,date_scope='eligible'if first is not None else'requires_editorial_review',date_review=note,
            source_date_claims=dict(native_field=f['native_date_literal'],native_prose_conflicting_literal=PROSE_DATES.get(n),index_display=f['index_date']),
            work_type=work_type(f),creator_label=f['creator_label']or'Anonymous / maker not identified',painter_id=None,
            creator_qualification='unresolved_initials'if n==193 else'copy_maker_after_named_artist'if n in {70,90,91}else'unknown'if not f['creator_label']else'literal_source_creator',
            holdings_confidence=0.96,holdings_basis='Concordant native museum digital collection and museum-supplied SearchCulture object records. Editorial assessment, not a calibrated probability. No current-display claim.',
            image_candidate=image_pass,image_hold_reason=image_reason,image_date_policy_passed=date_pass,
            image_date_basis='Both explicit conflicting source dates precede1955; exact chronology remains unresolved.'if n in CONFLICTS else'Literal native before-date establishes creation before1955 without numeric invention.'if kind=='source_qualified_before'else'Native physical-object date/range ends by1955.'if date_pass else'Physical creation by1955 is not established.',
            image_identity_confidence=0.96 if image_pass else None,source_image_reference=ref(frame['path'])if frame['path']else None,image_view_label=label,
            metadata_retained_despite_image_hold=not image_pass,editorial_note=editorial,
            rights_label='CC BY-NC 4.0',rights_url='http://creativecommons.org/licenses/by-nc/4.0/',rights_status='restricted',
            rights_basis='SearchCulture item image-rights link. The separate BY-SA4.0 site footer is not the image licence.',
            user_image_authorization='Existing Greek museum/artist workflow, creations by1955, complete frames and <=100000 bytes. Actual restricted source label retained separately; no independent copyright-holder licence claimed.',
            ready_to_apply=False,applied=False,proposed_status='review',current_display_verified=False))
    by={r['number']:r for r in rows};units=[]
    for r in rows:
        if r['decision']!='candidate_primary':continue
        ns=ALBUM if r['number']==176 else[r['number']]
        units.append(dict(r,source_numbers=ns,source_ids=[by[n]['source_id']for n in ns],source_urls=[by[n]['source_url']for n in ns],native_urls=[by[n]['native_url']for n in ns],
            component_titles=[by[n]['original_title']for n in ns],image_source_numbers=[n for n in ns if by[n]['image_candidate']],
            physical_unit_basis=r['editorial_note']if r['number']==176 else'One separately documented native physical work. Repeated-title pairs were compared using source images, media and dimensions.',
            fresh_global_identity_check_complete=False))
    assert len(rows)==216 and len(units)==187
    assert collections.Counter(r['decision']for r in rows)==dict(candidate_primary=187,existing_comparator=18,same_album_plate_secondary=11)
    assert len({sid for u in units for sid in u['source_ids']})==198
    assert sum(u['first']is not None for u in units)==180
    assert sum(r['image_candidate']for r in rows)==205
    assert sum(bool(u['image_source_numbers'])for u in units)==182
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=rows,source_reference=ref(RUN/'candidate-facts-001.json.gz'),script_reference=ref(Path(__file__).resolve()),
        policy='Separate physical unit, date and image review. Unknown/conflicting dates remain explicit. Existing18 records are comparators; no metadata or status updates authorized by this offline file.'))
    m.save(RUN/'candidate-physical-units-001.json.gz',dict(at=m.now(),institution_id=IID,rows=units,last_verified_catalogue_count=18,last_verified_dateeligible_count=15,
        last_verified_at='2026-10-09',conditional_catalogue_total_before_live_reconciliation=205,conditional_numeric_dateeligible_total_before_live_reconciliation=195,
        fresh_counts=False,applied=False,decisions_reference=ref(RUN/'editorial-source-decisions-001.json.gz')))
    m.save(RUN/'physical-unit-review-001.json',dict(at=m.now(),reviewer='assistant editorial source/image review',source_records_reviewed=216,unique_full_descriptions=191,native_frames_reviewed=213,missing_frames=sorted(MISSING_IMAGES),
        initial_contacts_reviewed=visual['sheets'],focused_sheets_reviewed=comparison['sheets'],repeated_title_distinct_work_comparisons=DISTINCT,
        nearest_hash_review='All12 closest dHash pairs are among Vassiliou illustrated bifolios. Complete contact7/8 and descriptions show different poems and illustrations; shared paper/background/layout is not duplicate identity.',
        album=dict(primary=176,source_numbers=ALBUM,title='12 σχέδια από τη Κατοχή',year=1946,unit_count=1,plate_views=12,
            evidence_reference=ref(RUN/'album-reference-001.json.gz'),pdf_pages_reviewed=[148,149,153,199,206],additional_cover_render=ref(PROOF/'reference-pdf/kanas-page-149.png'),
            scope='Publication-level corroboration only. No Parliament image is prepared or attached; museum holdings/impressions derive from Larissa pages.'),
        bifolios=bifolios,date_conflicts=CONFLICTS,qualified_before_numbers=[30,39,80],open_after_number=32,
        no_accessions_inferred='No explicit accession field. Image filenames and prose printed-catalogue cross-references remain evidence, not invented canonical inventories.',
        source_comparison='Native and aggregator titles/date fields agree. Full-description variants10/129 differ in honorific/articles and hat spelling; both literal versions retained.',
        remaining='Fresh institution-scoped and bounded global source/title/creator/image identity checks are still required before any production plan.',script_reference=ref(Path(__file__).resolve())))
    fields=['number','source_id','native_url','title','original_title','role','decision','primary_number','work_type','creator_label','creator_qualification','native_date_literal','first','last','date_scope','date_review','image_candidate','image_hold_reason','editorial_note']
    with(RUN/'review-ledger-001.csv').open('x',encoding='utf-8-sig',newline='')as out:
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(dict(candidates=len(units),numeric_dates=180,qualified_or_conflicting=7,image_frames=205,new_works_with_images=182,types=dict(collections.Counter(u['work_type']for u in units))))

if __name__=='__main__':main()
