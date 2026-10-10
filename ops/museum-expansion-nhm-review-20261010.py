"""Editorial date, medium, copy-role and composition review; identity checks pending."""
import collections,csv,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
HANK={179,182,183,184,188,189,190,191,192,193,196}
UNIDENTIFIED_COPY={33:'Hess Peter von',34:'Hess Peter von',165:'Hess Peter von',174:'Garneray Louis Ambroise'}
SITTER={1,2,3,4,5,6,8,9,11,12,13,14,15,16,17,18,19,20,23,24,25,26,27,28,29,35,36,42,43,67,68,69,185}
MEDIUMS=['μολύβι και υδατογραφία σε χαρτί','μελάνι και υδατογραφία σε χαρτί','κάρβουνο, χρωματιστά μολύβια και σφουμίλι σε χαρτί','κραγιόνια και κιμωλία σε χαρτί','ελαιογραφία σε μουσαμά','ελαιογραφία σε τσίγκο','ελαιογραφία σε χαρτόνι','ελαιογραφία σε χαρτί','ελαιογραφία σε ξύλο','κάρβουνο σε χαρτόνι','υδατογραφία σε χαρτί','μολύβι σε χαρτί','υδατογραφία','μελανογραφία','ελαιογραφία']

def dates():
    out={7:(1601,1700,'17th century','century'),22:(1771,1800,'Late 18th century (source range:1771–1800)','circa_range')}
    for n in range(37,41):out[n]=(1801,1900,'19th century','century')
    for n,y in {41:1806,44:1814,166:1821,175:1828,176:1833,177:1833,178:1833,180:1834,181:1834,187:1836,194:1838,195:1838}.items():out[n]=(y,y,str(y),'exact')
    out[46]=(1815,1817,'1815–1817','range')
    for ns,start,end in [(range(47,67),1817,1820),(range(70,159),1818,1820),(range(159,164),1820,1820),(range(197,241),1838,1845)]:
        for n in ns:out[n]=(start,end,str(start) if start==end else str(start)+'–'+str(end),'exact' if start==end else 'range')
    for n in [201,210,212,217,224,225,228]:out[n]=(1838,1838,'1838','exact')
    return out

def main():
    dest=RUN/'editorial-source-decisions-001.json.gz';assert not dest.exists()
    source=m.load(RUN/'selected-source-records-001.json.gz')['rows'];visual=m.load(RUN/'visual-references-001.json');frames={x['number']:x for x in visual['rows']}
    assert len(frames)==251 and not visual['exact_duplicate_groups'] and not visual['unavailable_numbers']
    context=m.load(RUN/'focused-context-001.json.gz');native={x['number']:x for x in context['rows'] if x['number']}
    dated=dates();out=[]
    for row in source:
        n=row['number'];f=row['fields'];description=[x for x in f.get('Περιγραφή',[]) if x!='Εθνικό Ιστορικό Μουσείο'];caption=' '.join(description)
        creators=f.get('Δημιουργός',[]);creator='; '.join(creators) if creators and creators!=['Άγνωστος δημιουργός'] else None
        first,last,display,precision=dated.get(n,(None,None,'Creation date unknown','unknown'))
        notes=['One museum-catalogued visual work or album composition per source record. Multiple figures, buildings or vignettes on one composition are not split into extra artworks. Exact physical sheet/album collation and unreported dimensions/accessions remain unknown.','All251 source thumbnails and eleven contact sheets inspected. Distinct depicted buildings do not become held museum buildings; the collection connection concerns the artwork. No current-display claim.','Literal Greek title, medium and creator evidence retained. Modern full-timestamp Ημερομηνία δημιουργίας values concern the digital record context, not accepted as creation dates of these historical artworks. Index chronology is separately retained and can reflect a sitter, prototype or event.']
        if n in SITTER:notes.append('The index date reproduces a sitter lifespan; it is not an artwork creation date. Numeric date remains unknown, with source lifespan preserved in evidence.')
        if n in {10,21,45,164,167,172,173,186}:notes.append('Source date concerns the historical scene, sitter office/period or depicted building; creation is not established. Preserve the source claim without assigning it to the artwork.')
        if n in {30,31,32}:
            creator='Πελεκάσης Δημήτριος (copy after Καλλιβωκάς Διονύσιος)';notes.append('Museum explicitly describes a watercolour copy by Pelekasis after Kallivokas.1790–1866 belongs to chronicle author D.Varvianis, not the copy. Do not assign Kallivokas as the direct maker or infer a copy date from either artist lifespan.')
        if n in UNIDENTIFIED_COPY:
            creator='After '+UNIDENTIFIED_COPY[n]+'; copyist unidentified';notes.append('Museum explicitly identifies a copy after the named prototype artist. Copyist and execution date unknown; no direct primary artist link to the prototype maker.')
        if n in HANK:
            creator='Hans Hanke (copy after Koellnberger Ludwig)' if 'Hans Hanke' in creators else 'After Koellnberger Ludwig; copyist unidentified'
            notes.append('Museum publication identifies the series as Hanke watercolour copies after Köllnberger. The1830s dates are prototype dates, not copy dates. Item184does not explicitly name Hanke, so the copyist remains unknown there. The1909commission context is not an exact object execution year; no numerical copy date or image delivery yet.')
        if n==68:
            creator='Attributed to Ιωαννίδης Σ.';notes.append('The literal description places a question mark after the maker; retain this qualified attribution, not an unqualified creator link.68and69are different portrait treatments of the same sitter.')
        if n in {168,169,170,171}:
            display='Creation date unresolved (object:1824; collection:1828–1832)';notes.append('All four object-level descriptions state1824, whereas the museum painting-collection narrative dates its four Botsaris ink works1828–1832. Both authoritative claims retained pending specific inscription/version review; no invented union range and no image delivery while unresolved.')
        if n in {210,230}:notes.append('Two bridge views require focused native object/inventory and higher-resolution comparison before deciding whether they are separate works, a copy or alternate reproduction. No final duplicate decision from thumbnail framing alone.')
        if n in {209,239}:notes.append('The two Navarino views show different shoreline/mountain arrangements and viewpoint; identical subject title is not enough to merge.')
        if n in {233,235}:notes.append('Kaisariani church views show different foreground, framing and architectural placement; retain separate composition review rather than merging by place.')
        if n in {47,56,60,61,62}:notes.append('Related costume studies are different arrangements and poses. Preserve complete sheet composition, including faint pencil studies and existing paper condition.')
        medium=next((x for x in MEDIUMS if x in caption.lower()),None)
        kind='photograph' if n>=241 else 'drawing' if medium and any(x in medium for x in ['μολύβι','μελανογραφία','κάρβουνο','κραγιόνια']) and 'υδατογραφία' not in medium else 'painting'
        if n==46:kind='drawing'
        inventory=dimensions=None;native_url=None
        if n in native:
            block=' '.join(native[n]['object_blocks']);inv=re.search(r'Αριθμός Ταυτότητας\s*:\s*(.+)$',block);dim=re.search(r'Διαστάσεις\s*:\s*(.*?)\s*Αριθμός Ταυτότητας',block)
            inventory=inv[1] if inv else None;dimensions=dim[1] if dim else None;native_url=native[n]['receipt']['url']
        old=row['index']['historical_source_match'];image_candidate=not old and first is not None and last<=1955 and n not in {210,230}
        if old:notes.append('Existing catalogue title/date/creator/primary/status preserved; fresh source claims are comparators only in this pass.')
        out.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=native_url,title=f['Τίτλος'][0],title_source_literals=f['Τίτλος'],creator_label=creator,creator_source_literals=creators,artist_id=None,first=first,last=last,date_precision=precision,date_display=display,source_date_literal=f.get('Ημερομηνία δημιουργίας',[]),source_chronology=row['enrichment'].get('Χρονολογία',[]),work_type=kind,medium_text=medium,dimensions_text=dimensions,inventory=inventory,object_form=None,cultural_context=None,description_source=description,decision='existing_comparator' if old else 'proposed_review_artwork',review_notes=notes,source_fields=f,aggregator_enrichment=row['enrichment'],creator_authorities=row['field_enrichment_links'].get('Δημιουργός',[]),source_receipt=row['receipt'],visual_reference=frames[n],source_image_reviewed=True,image_candidate=image_candidate,image_hold_reason='Existing record preserved' if old else 'Focused bridge version review' if n in {210,230} else 'Unresolved creation date' if not image_candidate else None,date_scope_review_required=first is None,proposed_status='review',ready_to_apply=False,applied=False))
    proposed=[x for x in out if x['decision']=='proposed_review_artwork'];assert len(proposed)==238
    counts=dict(proposed=238,source_dated=sum(x['first'] is not None for x in proposed),unknown_dates=sum(x['first'] is None for x in proposed),image_candidates=sum(x['image_candidate'] for x in proposed),old_comparators=13)
    dependencies=[c.ref(RUN/name) for name in ['selected-source-records-001.json.gz','visual-references-001.json','focused-context-001.json.gz','art-navigation-001.json.gz']]
    m.save(dest,dict(at=m.now(),rows=out,dependencies=dependencies,script_reference=c.ref(Path(__file__).resolve()),counts=counts,visual_review=dict(thumbnails=251,contact_sheets=11,exact_hash_duplicates=0,focused_version_review_pending=[210,230]),policy='Editorial research proposals only. All descriptions and thumbnails reviewed, but global identity, maker matches, bridge physical units, selected image preparation and final date decisions remain pending. No production writes.'))
    with (RUN/'candidate-review-001.csv').open('x',encoding='utf-8-sig',newline='') as handle:
        fields=['number','source_id','title','creator_label','first','last','date_display','work_type','medium_text','inventory','decision','image_candidate','source_url'];writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(out)
    print(json.dumps(counts),flush=True)

if __name__=='__main__':main()
