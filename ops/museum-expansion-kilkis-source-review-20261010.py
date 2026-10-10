"""Combine reviewed source objects, retaining period uncertainty and physical units."""
import collections
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
ASSEMBLAGE={34,35,37,38,42,45}
EXTRA={
30:'One inscribed boundary stone, individually accessioned and catalogued in the museum collection; retain the epigraphic object type, not a named sculptor or reconstructed monument.',
31:'One inscribed honorary stele. The honouree and civic decree do not become creator or separate artwork records.',
32:'One decorated Illyrian-type bronze helmet. The source describes confronting lions on the brow; neither lion is a separate object.',
33:'One gold lamella with a raised personal-name inscription. No funerary or wearable function is inferred beyond the source; the actual metalwork object counts once.',
36:'One framed votive inscription; Asklepios, Hygieia and the named dedicator are the inscription subjects, not accepted artwork creators.',
39:'One honorary stele for Paramonos. The cow and herd mentioned by the inscription are historical narrative, not separately held artworks. Native Roman period conflicts with aggregator Hellenistic period; preserve both and keep numeric dates unknown.',
40:'One surviving fragment of a dedicatory stele. Names in the inscription are not artist authorities; no missing parent slab is reconstructed as an extra work.',
41:'One marble block reused as a Byzantine impost. Original inscribed base and later architectural reuse remain one physical object; Hellenistic label describes the earlier phase, not a fabricated date for the carving/reuse.',
43:'One inscribed pillar-shaped stone fragment; keep the fragment as supplied without adding an imagined complete monument.',
44:'One individually accessioned inscribed stele fragment. Its distinct outline, text and inventory differ from the other stelae; no shared parent is documented.',
46:'One accessioned pair of bronze greaves, rejoined and restored according to the museum. Count the pair once, not two legs or multiple repaired pieces.',
47:'One inscribed statue base later reused as threshold and possible Christian grave cover. Count the surviving block once, without inventing the absent bronze statue or three burial artworks. The historical Marcus Insteius dates are not an exact manufacture date.'}

def main():
    assert not(RUN/'source-review-001.json.gz').exists()
    old=m.load(c.RESEARCH/'editorial-decisions-001.json.gz')['rows'];extra=m.load(RUN/'remaining-source-records-001.json.gz')['rows'];existing=m.load(RUN/'existing-source-records-001.json.gz')['rows'];rows=[]
    for raw in old+extra+existing:
        v=dict(raw);number=v['number'];v['work_type']=v.get('work_type','unknown');v['medium_text']=v.get('medium_text');v['dimensions_text']=v.get('dimensions_text');v['source_scheme']='searchculture-edm'
        if v.get('source_id') is None:
            v['source_id']=v['lead_key'];v['source_scheme']='museum-catalogue-isbn-9789601226781';rc=m.load(c.RESEARCH/'catalogue-excerpt-capture-001.json');v['source_receipt']=dict(rc,retrieved_at=rc['at']);v['native_receipt']=None;v['native_description']=[]
            v['visual_observation']='Complete scholarly entries03/04 on printed pages34/35 describe different36cm torsos:331has long curls beside the neck/chest and missing arms;2046has a separate fitted right shoulder/arm, muscular twist and a different preservation boundary. Distinct inventories and physical descriptions, not two views of the same torso. Plate5 is absent, so no image match or attachment is claimed.' if v['decision']!='hold' else 'Entry05cuts off; no complete dating or identification argument available.'
        if number in ASSEMBLAGE:
            v.update(decision='hold',decision_reason='unresolved_5044_parent_assemblage',visual_observation='5044A/B/G are related elongated ribbed components;5044D/E spherical pendants and5044STa bead share the accession root and findspot. Images distinguish components but do not establish independent original ornaments. Hold all six rather than inventing a complete necklace or six independent works.')
        elif number in EXTRA:
            v.update(decision='candidate_pending_live_identity',decision_reason='selected_accessioned_museum_object',visual_observation=EXTRA[number],museum_confidence_editorial=.95,museum_confidence_basis='Native accessioned object page explicitly relates the object to the Archaeological Museum of Kilkis, with matching Ephorate provider record. Editorial judgment, not a calibrated probability; holding is not current display.',date_review='Literal native historical period and any conflicting enriched period remain evidence. Numeric creation fields stay null; reuse and historical persons do not supply invented creation years.')
        if v['decision']=='existing_record':v['visual_observation']='Current catalogue identity anchored by exact SearchCulture external identifier; existing title/date/status/holding remain unchanged. Selected photograph still requires full-frame review.'
        v['proposed_status']='review';v['current_display_verified']=False;v['physical_units_counted']=1 if v['decision']!='hold' else 0
        assert v['first'] is None and v['last'] is None and v['creator_label'] is None
        v['image_date_review']='Native ancient or Byzantine period can establish pre1956 image-policy scope without inventing numeric catalogue dates; selected image identity and authentic frame still require review.'
        rows.append(v)
    counts=dict(collections.Counter(v['decision'] for v in rows));assert counts==dict(candidate_pending_live_identity=38,hold=12,existing_record=18),counts
    assert len({v['source_id'] for v in rows})==68
    m.save(RUN/'source-review-001.json.gz',dict(at=m.now(),rows=rows,counts=counts,original_candidates=26,additional_candidates=12,old_catalogue_records=18,held_source_entries=12,source_index_coverage=dict(total=65,metadata_reviewed=65,additional_scholarly_entries=3),scope_review='Individually accessioned inscribed stones, reliefs, architectural fragments, metalwork and the greave pair are actual museum-connected archaeological works. Preserve their supplied forms with unknown controlled type when needed; never label all as paintings or invent larger monuments. Existing art and anonymous/Byzantine priorities remain. Museum object count is not an on-view count.',date_policy='All numeric creation fields remain unknown. Literal historical periods, source discrepancies, discovery dates and qualified scholarly dating remain distinct.',pdf_review=dict(skill='/Users/vadimdulub/.codex/plugins/cache/openai-primary-runtime/pdf/26.614.11602/skills/pdf/SKILL.md',reopened_pages=[3,4,5,6,7],book_entries_with_no_supplied_image=['03','04'],entry05_incomplete=True),dependencies=[c.ref(c.RESEARCH/'editorial-decisions-001.json.gz'),c.ref(RUN/'remaining-source-records-001.json.gz'),c.ref(RUN/'existing-source-records-001.json.gz'),c.ref(RUN/'remaining-visual-references-001.json'),c.ref(c.RESEARCH/'visual-references-001.json'),c.ref(c.RESEARCH/'publication-object-review-001.json')],script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(rows=len(rows),counts=counts)),flush=True)

if __name__=='__main__':main()
