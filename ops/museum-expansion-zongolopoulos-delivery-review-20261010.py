"""Selected Foundation delivery after fresh source, physical-unit and live identity review."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='zongolopoulos-production-001'
VENICE_HOLD='ZoggopoulosF/000041-64302'
VENICE_BASIS='The preserved source and preservation previews share the foreground three-figure gondola, architecture and curved boat at right. Different framing, colour and oblique photography do not establish separate physical watercolours. Retain fuller source64304 as one candidate; hold64302 as an unresolved additional work, without forcing a duplicate alias or attaching its photograph.'

def selected():
    out=[]
    for root,wave in [(c.RESEARCH,'first'),(c.DATED,'paintings')]:
        decisions={v['source_id']:v for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']}
        for u in m.load(root/'candidate-physical-units-001.json.gz')['rows']:
            if u['primary_source_id']==VENICE_HOLD:continue
            d=decisions[u['primary_source_id']];assert d['decision']=='candidate_primary'
            out.append((wave,u,d))
    assert len(out)==198
    return out

def facts(wave,u,d):
    first,last=u['first'],u['last'];assert (first is None)==(last is None)
    if first is not None:assert first<=last<=1970
    assert u['inventory_literal'] is None and u['painter_id'] is None
    precision='unknown' if first is None else 'exact' if first==last else 'range'
    description='\n'.join(d['source_description'])
    for key,label in [('date_note','Dating'),('creator_note','Creator review'),('inventory_note','Inventory review'),('work_type_basis','Object type review')]:
        if d.get(key):description+='\n\n'+label+': '+d[key]
    description+='\n\nPhysical unit: one source-supported object; multiple motifs, views, or opposite sides are not separate catalogue works.'
    if u.get('two_sided_support'):description+=' Source describes a two-sided support; both sides belong to this one record.'
    if u.get('reused_support'):description+=' Source reports a reused support; no additional work is counted for the underlying image.'
    if first is None:description+='\n\nCreation date remains unknown and requires editorial review; creator lifespan is not an artwork date.'
    if u['primary_source_id']=='ZoggopoulosF/000041-64304':description+='\n\nRelated source review: '+VENICE_BASIS
    return dict(number=u['primary_number'],research_wave=wave,source_id=u['primary_source_id'],title=u['title'],creator_label=u.get('catalogue_creator_label',u['creator_label']),first=first,last=last,date_precision=precision,date_display=u['date_display'],work_type=u['work_type'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=None,description_md=description,source_url=d['source_url'],source_ids=u['source_ids'],source_urls=[d['source_url']],native_urls=[],source_facts=dict(unit=u,source=d),inventory_source_literal=u['inventory_source_literal'])

def build():
    out=[]
    for wave,u,d in selected():
        f=facts(wave,u,d);aid=m.uid(KEY+'/'+f['source_id'])
        out.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+f['source_id'].split('-')[-1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=d['source_receipt']['retrieved_at'],identity_basis=d['museum_confidence_basis']+' '+d['decision_reason']+' Fresh production source/title/literal-inventory/creator/image comparison found no established existing physical-object match; full focused comparisons and limitations are retained.',editorial_confidence=d['museum_confidence_editorial'],limitation='Museum-supplied collection evidence establishes a holding, not current display. Native collection host remains unavailable. Unknown dates, qualified creators and literal unverified export inventories are preserved; no artist authority is invented.'))
    assert len({v['artwork_id'] for v in out})==198 and sum(v['facts']['first'] is not None for v in out)==49
    assert sum(v['facts']['source_facts']['unit'].get('two_sided_support',False) for v in out)==16
    return out,[]

def source_mapping():
    data=m.load(RUN/'production-identity-001.json.gz');scope=set(data['state']['scoped_ids']);out={}
    for v in data['comparisons']:
        matches={x['entity_id'] for x in v['source_hits']}
        if v['decision']=='existing_record':assert len(matches)==1 and matches<=scope;out[v['source_id']]=next(iter(matches))
        else:assert not matches,(v['source_id'],matches)
    assert len(out)==18 and set(out.values())==scope;return out

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();existing=source_mapping()
    targets={v['facts']['source_id']:v['artwork_id'] for v in records};decisions={v['source_id']:v for v in m.load(c.RESEARCH/'editorial-source-decisions-001.json.gz')['rows']};visuals={v['source_id']:v for v in m.load(c.RESEARCH/'visual-references-001.json')['rows']};images=[]
    for raw in m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows']:
        if raw['source_id']==VENICE_HOLD:continue
        im=dict(raw);d=decisions[im['source_id']];frame=visuals[im['source_id']]
        assert frame['status']==200 and frame['sha256']==im['original_reference']['sha256']
        assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256'] and im['bytes']<=100000 and im['last']<=1955
        assert frame['url'].startswith('https://')
        aid=targets[im['source_id']]
        im.update(artwork_id=aid,production_artwork_id=aid,source_title=im['title'],verified_https_source_image_url=frame['url'],image_url=frame['url'],image_retrieved_at=frame['at'],source_receipt=d['source_receipt'],original_image_receipt=frame,identity_basis=im['image_identity_basis']+' Selected physical source unit reconciled against current production; Venetian64302 held separately.',mime_type='image/jpeg',rights_url='http://creativecommons.org/licenses/by-nc-nd/4.0/',view_label='Complete source image',ready_to_attach=True,remaining_step='Pinned production upload and attachment.')
        images.append(im)
    assert len(images)==18 and len({x['artwork_id'] for x in images})==18
    focused=m.load(RUN/'focused-comparators-001.json.gz');assert len(focused['ids'])==64
    review=dict(at=m.now(),existing_source_mapping=existing,new_records=198,existing_work_links=0,source_identifier_count=198,source_record_count=198,protected_comparators=64,global_bounded_artworks=949,global_citations=1924,new_artist_links=0,
        venice_hold=dict(source_id=VENICE_HOLD,retained_source='ZoggopoulosF/000041-64304',basis=VENICE_BASIS,preview_reference=c.ref(RUN/'venice-comparison-inputs-001.json')),
        inherited_holds=dict(first_wave_ambiguous_casts_models_or_versions=61,painting_source_image_conflict=1),
        focused_decisions=[
            dict(ids=['36d0ee12-4be9-5f83-94b8-8046de8dacc0','4e79f2d0-da2c-5e0b-bfe5-4d31410a05f5'],basis='National Gallery portrait of Mrs M.K. has a long neck, elongated face and parted wavy hair; existing Foundation child head has a rounded face, smooth short hair and rough truncated neck. New1943 plaster portrait and Irene Meitani Politi have different faces and source medium/identity. Shared Head of Girl title does not establish a duplicate.'),
            dict(ids=['9d7a8ae8-1dbc-5963-ab45-d2606ecbe3df'],basis='Larissa1935 Vouliagmeni watercolour33x39.5cm shows a blue bay and brown shore framed by two trees. Foundation selected landscape arrangements differ; no shared source identifier or exact composition was identified. Existing protected Larissa record remains unchanged.'),
            dict(ids=['cee507c7-f9cc-540d-95b3-dc7c3744368d'],basis='Lela Paschali1950 etching of paired leaning pines is an incidental surname lead, not Helen Paschalidou; separate named maker, medium and reviewed image.'),
            dict(ids=['13996032-918c-5302-ad03-0bdc35d32935','7d2f481c-dbcc-5f29-9679-dfaaafb78b58','c90bab8f-aed9-5c06-9347-e6a5b1896f9b'],basis='Three source frames compared with37anonymous Foundation candidates. ASFA abstract has horizontal ochre/brown bands and a near-right vertical yellow line; Foundation64222 has green fields, central blue band and large circular geometry, visibly different. Lekakis black/white looping and angular designs differ from the coloured Foundation geometries and figurative scenes. No common physical work identified.'),
            dict(ids=focused['ids'],basis='32existing primary images and3additional source frames reviewed, plus19prepared source frames, both Venice preservation previews and37anonymous candidate frames. Literal export-digit collisions with unrelated named European paintings/prints do not establish an accession match. First-wave model/cast identity and16two-sided painting supports retain prior detailed visual decisions. Twelve generic-title foreign comparators lack an exposed source thumbnail in captured citations; no visual comparison is claimed for those. Generic titles alone are insufficient to merge or assign holdings.' )],
        limitations=['No George or Helen artist authority found in expanded live names and aliases; retain explicit and qualified object-level labels.','949bounded candidates include936exact-title leads; not all936were visually reviewed. Focused64records cover literal Greek titles, creator and literal inventory leads. Generic English Untitled/Abstract not globally enumerated; no exhaustive duplicate guarantee.','Native provider403/timeout holds remain; authoritative museum-supplied SearchCulture captures support this selection.','Existing18records include unresolved cast/version duplication flags; total catalogue count is not a certification of distinct historical physical holdings.','149unknown creation dates remain editorial-review records, not numerically pre1971 eligible.','One-off bounded query plans are retained;10-million-row load performance remains untested.'])
    m.save(RUN/'identity-review-001.json',review)
    deps=[c.ref(root/name) for root in [c.RESEARCH,c.DATED] for name in ['candidate-physical-units-001.json.gz','editorial-source-decisions-001.json.gz','physical-unit-review-001.json','visual-references-001.json']]
    deps += [c.ref(c.RESEARCH/'image-delivery-prepared-001.json')]
    deps += [c.ref(RUN/name) for name in ['baseline-verification-001.json','production-initial-scope-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-review-inputs-001.json','additional-comparisons-001.json','anonymous-comparison-inputs-001.json','venice-comparison-inputs-001.json','identity-review-001.json']]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,existing_source_mapping=existing,dependencies=deps,expected_counts=dict(linked=216,eligible=67),new_work_types=dict(collections.Counter(v['facts']['work_type'] for v in records)),new_unknown_numeric_dates=149,old_dates_preserved=18,new_primary_images=18,alternate_images=0,source_identifier_policy='One canonical source identifier per selected physical object. Literal repeated export digits remain evidence, not invented accessions.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        fields=['research_wave','number','artwork_id','title','creator_label','first','last','date_precision','date_display','work_type','source_url'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for v in records:w.writerow({k:v['artwork_id'] if k=='artwork_id' else v['facts'][k] for k in fields})
    print(json.dumps(dict(new=198,images=18,unknown=149,numeric=49,expected_catalogue=216)),flush=True)

if __name__=='__main__':main()
