"""Final object/version decisions for184 new records,3 existing links and205 images."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-common-v2-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='larissa-production-001'
LINKS={25:'3f1bb857-c5c5-5568-860a-9c059a9d71c1',56:'314c82c5-1883-5907-bd7c-94fe90f40b51',191:'4802adb0-4c1e-5872-984b-e3d0fe094bda'}
LINK_NOTES={25:'Same Lavrio panorama: dark sea inlet, paired foreground trees, violet mountain bands and yellow field; matching creator and1918–20 date. Existing WikiArt record has no museum. Preserve its metadata, artist and primary image; add the sourced Larissa holding and a labelled museum view.',
56:'Same child in the patterned green dress with hand near mouth and turkeys at both bottom corners; exact window, feet and shadow arrangement. Existing WikiArt record is undated and has no museum/image. Museum dates1925–30 are retained as evidence without rewriting the existing unknown date.',
191:'Same standing female nude with white cloth in one hand, other hand on the red stool, same dark drapery and pose. Matching Moralis creator. Existing WikiArt record is undated with no museum/image. Museum1948date is evidence only; preserve unknown catalogue dating.'}
DISTINCT={
9:'Resolved same-viewpoint concern against National Gallery K.1308. The larger official image shows tall thick cactus/agave leaves in the left foreground; Larissa instead shows thin bare branching stems across the foreground, different mountain contours and painting details. Different physical watercolour versions, not a colour-shifted duplicate photograph. Larissa1896,21.5×50.5cm and National Gallery1890,21×51cm remain separate literal records.',
42:'Same Galanis plate composition, separate physical impressions: Larissa has a prominent handwritten Greek dedication to doctor Georgios Katsigras along its lower margin; the Averoff impression has different lower-margin inscription/signature and paper margins. Larissa source print1921 and Averoff1919 claims remain separate; original-painting dates do not replace impression metadata.',
63:'Larissa64.5×79.5cm still life shows a prominently textured grape basket, jug and watermelon wedge. CourtauldP.1932.SC.179,72.4×92.9cm shows a pale smooth jug, round fruit basket and prominent fish. Different compositions/supports, not the same Gounaropoulos painting under alternate titles.',
72:'Larissa1930black-and-white woodcut with large central jug and curved hatchings is distinct from Rhodes1934oil-and-sand colourful horizontal still life.',
78:'Larissa1934woodcut depicts the entire crescent harbour, fish, boats, hills and inscribed island name. WikiArt1953Hydra and1950Houses at Hydra are different painted building compositions.',
82:'Larissa Galatsi outing shows a group around a seated red-shirted figure and diagonal blue-backed chair/figure. National Gallery Youths Enjoying Themselves in Galatsi shows different standing figures, seating and clothing; it is a distinct painted version of a related subject.',
97:'Larissa1936landscape shows the close hilltop structure, walled paths and foreground doorway. Existing Moralis Athens Landscape1936is a broad city/Acropolis panorama. Same year and landscape subject do not make them identical.',
122:'Larissa is a35×50cm open bifolio, with the illustrated poem on its right panel and continuation/ornamental chalice on the left. The Rhodes36×25.9cm manuscript repeats the design but has different handwriting and line layout: Larissa starts the stanza with a large red decorated initial; Rhodes starts with a black calligraphic initial. Retain distinct physical handwritten versions; no inference from a crop alone.',
142:'Larissa35×50cm tempera/India-ink illustrated bifolio differs from Nikaia13.3×12.2woodcut: different medium/support, handwritten poem layout and image treatment. Retain copy/version identity rather than equating subject and1942date.',
}

def facts(f):
    a,b=f['first'],f['last'];display=f['native_date_literal'] or 'Creation date unknown';precision='unknown' if a is None else 'exact' if a==b else 'range'
    if f['date_basis']=='conflicting_source_dates':display='Conflicting source dates: '+f['source_date_claims']['native_field']+' / '+f['source_date_claims']['native_prose_conflicting_literal']
    kind=f['work_type']
    if f['native_category']=='Υδατογραφία' or (f['native_technique'] or '').startswith('Υδατογραφία'):kind='watercolor'
    description='Documented in the Municipal Art Gallery of Larissa – G.I. Katsigras Museum collection. '+f['physical_unit_basis']
    if f.get('editorial_note') and f['editorial_note'] not in description:description+=' '+f['editorial_note']
    if f['date_basis']!='source_numeric':description+=' '+f['date_review']
    return dict(number=f['number'],source_id=f['source_id'],source_ids=f['source_ids'],source_urls=f['source_urls'],native_urls=f['native_urls'],source_url=f['source_url'],
        title=f['title'],creator_label=f['creator_label'],date_display=display,first=a,last=b,date_precision=precision,work_type=kind,object_form=None,
        medium=f['native_technique'] or f['native_material'],dimensions_text=f['dimensions_text'],inventory=None,description_md=description,
        source_facts=f,metadata_classification_note='17 explicitly watercolour techniques/categories classified as watercolor in this delivery; original research painting classification preserved as historical evidence. No existing artwork type is changed.' if kind=='watercolor' else None)

def build():
    units=m.load(c.RESEARCH/'candidate-physical-units-001.json.gz')['rows'];identity=m.load(RUN/'production-identity-001.json.gz');comparisons={x['number']:x for x in identity['comparisons']}
    focus=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];existing={x['id']:x for x in focus['artworks']};records=[];holdings=[]
    for f in units:
        n=f['number'];assert not comparisons[n]['source_hits'];ff=facts(f);aid=LINKS.get(n) or m.uid(KEY+'/'+f['source_id'])
        action='link_existing' if n in LINKS else 'create_review'
        if n in LINKS:
            prior=existing[aid];assert prior['current_institution_id'] is None and prior['status']=='review'
            assert not [v for v in focus['assertions'] if v['artwork_id']==aid]
        row=dict(artwork_id=aid,slug='museum-expansion-larissa-'+str(n).zfill(3)+'-'+aid[:8],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),
            action=action,facts=ff,retrieved_at=f['source_receipt']['retrieved_at'],confidence=.98 if n in LINKS else .96,
            identity_basis=LINK_NOTES.get(n) or DISTINCT.get(n) or 'Native physical-object page and source image reviewed; exact source IDs/citations absent from existing catalogue. Bounded creator/title comparison and selected visual comparisons found no same physical identity. Repeated titles were not treated as unique identifiers.',
            limitation='Editorial confidence, not a calibrated probability. Holding does not establish current display or legal ownership. Qualified/unknown dates and literal creator labels remain explicit.')
        (holdings if n in LINKS else records).append(row)
    assert len(records)==184 and len(holdings)==3
    assert sum(x['facts']['first'] is not None for x in records)==177
    assert collections.Counter(x['facts']['work_type'] for x in records)==dict(painting=120,drawing=8,print=39,watercolor=17)
    return records,holdings

def main():
    assert not (RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();decisions=m.load(c.RESEARCH/'editorial-source-decisions-001.json.gz')['rows']
    identity=m.load(RUN/'production-identity-001.json.gz');comparisons={x['number']:x for x in identity['comparisons']};existing_mapping={}
    for d in decisions:
        if d['decision']!='existing_comparator':continue
        ids={x['entity_id'] for x in comparisons[d['number']]['source_hits']};assert len(ids)==1;existing_mapping[d['number']]=ids.pop()
    assert len(existing_mapping)==18
    mapping=dict(existing_mapping);mapping.update({x['facts']['number']:x['artwork_id'] for x in records+holdings})
    previews=m.load(RUN/'https-preview-frames-001.json')['rows'];previews={x['number']:x for x in previews};prepared=m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows'];images=[]
    for im in prepared:
        n=im['number'];frame=previews[n];assert frame['status']==200 and frame['same_bytes_as_native'] and frame['sha256']==im['original_reference']['sha256']
        assert frame['url'].startswith('https://www.searchculture.gr/aggregator/thumbnails/edm-record/') and frame['final_url']==frame['url']
        raw=Path(im['prepared_path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==im['sha256'] and len(raw)==im['bytes']<=100000
        primary=im['primary_number'];aid=mapping[primary]
        images.append(dict(im,artwork_id=aid,verified_https_source_image_url=frame['url'],https_source_receipt=frame,native_http_source_image_url=im['image_url'],
            identity_basis='Exact original and prepared files from the reviewed source object. The explicitly displayed SearchCulture HTTPS frame has identical SHA-256 to the captured native HTTP original. Source identity/version decisions mapped to the existing or new physical artwork, with album views labelled separately.',
            view_label=im['view_label'],source_receipt=decisions[n-1]['source_receipt'],image_retrieved_at=frame['at'],ready_to_attach=True))
    assert len(images)==205 and len({x['sha256'] for x in images})==205
    vis=m.load(RUN/'focused-visual-references-001.json');extra=m.load(RUN/'extra-visual-contact-001.json')
    m.save(RUN/'identity-review-001.json',dict(at=m.now(),reviewer='assistant source, physical-support and visual review',bounded_production_records=6086,authority_candidates=252,
        original_source_hits=18,new_exact_source_id_duplicates=0,selected_comparators=53,initial_comparator_frames=45,additional_official_frames=9,
        reviewed_contact_sheets=vis['sheets']+[extra],full_size_details_reviewed=[dict(number=42,comparison='Averoff print margins'),dict(number=9,comparison='National Gallery K.1308foreground plants'),dict(number=122,comparison='Rhodes1062initial and line layout')],
        existing_links=LINKS,link_basis=LINK_NOTES,distinct_version_basis=DISTINCT,
        other_visual_results='Volanakis7/8night paintings differ from observed daylight warship/naval-battle compositions and pencil seascapes. Giallinas9differs from National Gallery coastline/ruin subjects and same-viewpoint variant. Mathiopoulos12single dark-haired sailor-suited boy differs from two blond child heads. Maleas13/14/22/23/29/32/43/44/45/48/49/52/55/58differ from compared scenes;25is the existing Lavrio painting. Nikolaos Lytras30/39/41have distinct mountains/town structures from the observed comparator images; the coastal Wikidata record has no retrieved frame. Triantafyllidis28/33/34/71/73differ from compared cypress/woman/dinner/flower compositions;56matches existing girl;82is a separate Galatsi version. Vitsoris77veiled frontal portrait differs from mother-and-child and black-hatted woman comparators. Moralis97/108differ from broad city panorama/other figures;191matches existing standing nude.',
        title_only_matches='24new-candidate rows have exact/fuzzy Greek title hits, mostly generic landscapes/still lifes or distinct makers. Composition Nu has431near-title hits: no matching Morelou-Orfanou creator/source identity; generic Composition is not a unique artwork key. Existing records and uncertainty preserved.',
        limits='One-time bounded search and source comparison, not exhaustive image matching or a10million-row load test. Artist labels/aliases are candidate search signals; no new authority link is asserted. Other artists incidental to broad search were not researched or modified.',
        held_comparator_frame='Coastal Landscape by Nikolaos Lytras (WikidataQ129719683) lacks a directly captured frame; existing record unchanged. No Commons retry after inherited access hold.',
        source_access='Native Larissa HTTPS exact-image probe timed out once.205explicit SearchCulture HTTPS previews all returned identical native source bytes. No metadata/image substitution, insecure certificate bypass, guessed path, source access workaround or schema change.',script_reference=c.ref(Path(__file__).resolve())))
    dependencies=[c.RESEARCH/'candidate-physical-units-001.json.gz',c.RESEARCH/'editorial-source-decisions-001.json.gz',c.RESEARCH/'image-delivery-prepared-001.json',c.RESEARCH/'image-qa-001.json',RUN/'identity-review-001.json',RUN/'production-identity-001.json.gz',RUN/'focused-comparators-001.json.gz',RUN/'focused-visual-references-001.json',RUN/'extra-comparator-pages-001.json.gz',RUN/'extra-visual-frames-001.json',RUN/'https-preview-frames-001.json',Path(__file__).resolve()]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,existing_source_mapping=existing_mapping,images=images,dependencies=[c.ref(p) for p in dependencies],
        expected_counts=dict(catalogue=205,numeric_date_eligible=193),numeric_count_basis='177numeric new records plus one numeric existing link. The two undated existing links retain unknown dates, so museum eligible count15+177+1=193.',
        existing_primary_images_preserved=13,proposed_new_primary_images=181,proposed_alternate_images=24,proposed_new_artworks=184,proposed_existing_links=3,production_applied=False))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=['number','artwork_id','action','title','creator_label','date_display','first','last','work_type','source_url']);writer.writeheader()
        for v in sorted(records+holdings,key=lambda x:x['facts']['number']):writer.writerow(dict(artwork_id=v['artwork_id'],action=v['action'],**{k:v['facts'][k] for k in ['number','title','creator_label','date_display','first','last','work_type','source_url']}))
    print(json.dumps(dict(new_artworks=184,existing_links=3,source_images=205,proposed_counts=dict(catalogue=205,date_eligible=193))),flush=True)

if __name__=='__main__':main()
