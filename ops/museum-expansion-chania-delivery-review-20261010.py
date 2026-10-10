"""Reconcile source-qualified Chania physical units and prepared image targets."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-chania-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='chania-production-001'
DISTINCT={
 '0fcb8d48-4ae9-515f-9a7e-16ef097800ed':'Chania69 Λ135 is132cm high with a vertical lowered right arm and a different drapery/base. Acropolis NMA350 is88cm with the right arm extended diagonally. Both official frames were inspected; distinct sculptures.',
 '16307734-742f-5e54-971c-ce65ef8a337d':'Chania45 Λ276 is a78cm basin-bearing woman with hip drapery, circular bowl and circular base. NMA91 is22cm, nude with different arm arrangement and a side support; official frames and inventories differ.',
 '4cfd9a65-7acc-53c6-8b48-659392da845d':'Chania45 Λ276 basin-bearer differs from NMA85(19.6cm): the latter has no circular bowl or circular base and has distinct drapery, torso damage and side support. Official frames inspected.',
 'd8548540-03b8-5e54-9665-c76ed6020b12':'Chania45 Λ276 basin-bearer differs from NMA414(17.4cm): different surviving arm position, drapery, rectangular base and adjacent supporting figure. Official frames inspected.',
 'f802b839-8cee-5889-b1a4-17f082fd83ba':'Chania45 Λ276(78cm) differs from NMA294(33cm): the latter is fully draped with a separate adjacent figure on a pedestal, not the basin-bearing nude torso. Official frames inspected.',
 'a682334d-8577-5e67-98be-da7eb6094035':'Chania69 Λ135 is132cm high with a different base and empty lowered hand. The official Cyprus catalogue identifies a48cm sculpture from the House of Theseus, Paphos, P.E.No.1/67, with a snake staff, egg and inscribed base. Distinct accessions, scale, provenance and physical description.',
 'ab2c601a-0f1a-5a17-95b9-5e68a511ddf5':'Chania80 Λ3176 is56cm high and34cm wide, dated385–410CE, with four braids and coloured glass eye traces described in its native catalogue. AIC2002.11 is64.8×47.6×27.3cm, dated140–150CE and catalogued as a Roman object from Rome. Independent official accession, dimensions and dated identity support distinct busts; the shared generic title does not establish a match. Existing captured AIC API bytes verified; fresh site403 not retried.',
 'b438c714-d06c-59ff-a9f4-cdc0be026eb2':'Chania81 Π7247 is43cm high and39cm long, a naturalistic bull with holes along the front of the chest and no snake coils in the reviewed frame. CyprusAI1556 is36.2cm, from Ayia Irini, with two snakes coiling up its back between the horns. Distinct source descriptions, dimensions, accessions and figure details.'}

def facts(u):
    first,last=u['first'],u['last'];assert (first is None)==(last is None)
    if first is not None:assert first<=last<=1970 and first!=0 and last!=0
    approximate='circa' in u['date_review'].lower() or 'approximation' in u['date_review'].lower()
    precision='unknown' if first is None else ('circa_range' if approximate else 'range') if first!=last else ('circa' if approximate else 'exact')
    literal=' / '.join(u['native_dating_claims'])
    display=u['date_review'] if first is None or u['date_basis']=='explicit_range_or_century' else literal
    assert display and u['title'] and u['inventory_literal']
    description=u['native_description'] or ''
    description+='\n\nDating: '+u['date_review']
    if literal:description+='\n\nSource date fields: '+literal
    if u.get('editorial_note'):description+='\n\nSource review: '+u['editorial_note']
    if len(u['source_ids'])>1:description+='\n\nPhysical unit: '+u['physical_unit_basis']
    if u.get('image_hold_reason'):description+='\n\nImage identity review: '+u['image_hold_reason']
    return dict(number=u['number'],source_id=u['source_id'],title=u['title'],creator_label=u['creator_label'],first=first,last=last,date_precision=precision,date_display=display,
        work_type=u['work_type'],medium=u['source_material'],dimensions_text=u['source_dimensions'],inventory=u['inventory_literal'],description_md=description.strip(),
        source_url=u['source_url'],source_ids=u['source_ids'],source_urls=u['source_urls'],native_urls=u['native_urls'],source_facts=u)

def source_mapping():
    data=m.load(RUN/'production-identity-001.json.gz');scope=set(data['state']['scoped_ids']);out={}
    for v in data['comparisons']:
        matches={x['entity_id'] for x in v['source_hits']}
        if v['decision']=='existing_comparator':assert len(matches)==1 and matches<=scope;out[v['number']]=next(iter(matches))
        else:assert not matches,(v['number'],matches)
    assert len(out)==18 and set(out.values())==scope;return out

def build():
    units=m.load(c.RESEARCH/'candidate-physical-units-002.json.gz')['rows'];assert len(units)==174
    out=[]
    for u in units:
        f=facts(u);aid=m.uid(KEY+'/'+u['source_id'])
        out.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('-')[-1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,
            retrieved_at=u['source_receipt']['retrieved_at'],identity_basis=u['holdings_basis']+' '+u['physical_unit_basis']+' Fresh bounded production source/accession/title/image comparison found no same physical artwork; comparison decisions preserved.',
            editorial_confidence=u['holdings_confidence'],limitation='Museum catalogue holding is not a fresh current-display or legal-ownership claim. Qualified makers, dates and source conflicts remain explicit; no named artist authority inferred.'))
    assert len({v['artwork_id'] for v in out})==174 and sum(v['facts']['first'] is not None for v in out)==117
    assert sum(len(v['facts']['source_ids']) for v in out)==180
    return out,[]

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();existing=source_mapping()
    targets={v['facts']['number']:v['artwork_id'] for v in records};targets.update(existing)
    decisions={v['number']:v for v in m.load(c.RESEARCH/'editorial-source-decisions-002.json.gz')['rows']}
    visuals={v['number']:v for v in m.load(c.RESEARCH/'visual-references-001.json')['rows']};images=[]
    for raw in m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows']:
        im=dict(raw);d=decisions[im['number']];frame=visuals[im['number']]
        assert frame['status']==200 and frame['sha256']==im['original_reference']['sha256'] and frame['url']==im['image_url'] and im['image_url'].startswith('https://')
        assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256'] and im['bytes']<=100000
        aid=targets[im['primary_number']]
        im.update(artwork_id=aid,production_artwork_id=aid,source_title=im['title'],verified_https_source_image_url=im['image_url'],image_retrieved_at=frame['at'],source_receipt=d['source_receipt'],native_receipt=d['native_receipt'],original_image_receipt=frame,
            identity_basis='Accessioned native museum object photograph and matching source description, visually reviewed in the preserved physical-unit and image review. Component views attach to the same reconciled physical unit.',
            ready_to_attach=True,remaining_step='Pinned production upload and attachment; preserve existing metadata and image associations.')
        images.append(im)
    assert len(images)==188 and len({x['artwork_id'] for x in images})==183
    assert sum(x['role']=='existing_comparator' for x in images)==16 and len({x['artwork_id'] for x in images if x['role']=='new_description_lead'})==167
    comparisons=m.load(RUN/'production-identity-001.json.gz')['comparisons'];state=m.load(RUN/'production-identity-001.json.gz')['state'];scope=set(state['scoped_ids']);review=[]
    for comp in comparisons:
        for hit in comp['comparison_hits']:
            aid=hit['id']
            if aid in DISTINCT:reason=DISTINCT[aid]
            elif aid in scope:reason='Source IDs resolve the18existing Chania objects. Shared object-type titles do not override the separate native accessions, full object descriptions and reviewed frames in the212-source physical-unit review.'
            else:
                assert hit['reasons']==['accession_key'] and hit['work_type'] in ['painting','print','drawing','unknown'] and (hit['creation_year_start'] is None or hit['creation_year_start']>=1600)
                reason='Incidental accession-normalization collision between unrelated museums: this comparator is a later painting/print/drawing with different title, medium, source identity and creation period, not the accessioned ancient Chania object.'
            review.append(dict(number=comp['number'],comparison_id=aid,reasons=hit['reasons'],decision='same_existing_source' if aid in {x['entity_id'] for x in comp['source_hits']} else 'distinct_physical_work',basis=reason))
    deps=[c.ref(c.RESEARCH/f) for f in ['candidate-physical-units-002.json.gz','editorial-source-decisions-002.json.gz','image-delivery-prepared-001.json','visual-references-001.json','physical-unit-review-001.json','image-qa-001.json']]
    deps += [c.ref(RUN/f) for f in ['baseline-verification-001.json','production-initial-scope-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-source-review-001.json.gz','new-source-access-holds-001.json']]
    focused=m.load(RUN/'focused-source-review-001.json.gz');assert len(focused['verified_sources'])==8 and len(focused['frames'])==5
    deps.extend(focused['dependencies'])
    m.save(RUN/'identity-review-001.json',dict(at=m.now(),decisions=review,existing_source_mapping=existing,new_records=174,existing_work_links=0,source_identifier_count=174,source_record_count=180,physical_units_once=[67,120],protected_comparators=41,reviewed_new_focused_frames=5,reviewed_prepared_frames_again=[45,69,80,81],focused_contact_reviewed=focused['contact'],source_access_holds=c.ref(RUN/'new-source-access-holds-001.json'),remaining_native_records=108,scope_holds=14))
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,existing_source_mapping=existing,dependencies=deps,expected_counts=dict(linked=192,eligible=117),new_work_types=dict(collections.Counter(v['facts']['work_type'] for v in records)),new_unknown_numeric_dates=57,old_dates_preserved=18,new_primary_images=183,alternate_images=5,source_identifier_policy='One canonical external identifier per physical artwork and source scheme. All180source IDs retained in full metadata and image evidence.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        fields=['number','artwork_id','title','inventory','creator_label','first','last','date_precision','date_display','work_type','source_url'];writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
        for v in records:writer.writerow({k:v['artwork_id'] if k=='artwork_id' else v['facts'][k] for k in fields})
    print(json.dumps(dict(new=174,existing_links=0,images=188,new_primary_images=183,alternative_views=5,numeric_dates=117,unknown_numeric_dates=57,expected_catalogue=192)),flush=True)

if __name__=='__main__':main()
