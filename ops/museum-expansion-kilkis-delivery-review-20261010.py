"""Reconcile38selected Kilkis objects and53native images with live catalogue identities."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='kilkis-production-001'

def facts(u):
    assert u['first'] is None and u['last'] is None and u['creator_label'] is None
    description='\n'.join(u.get('native_description',[]))
    if u.get('source_entry'):
        entry=u['source_entry'];description+='\nScholarly catalogue entry '+entry['catalogue_number']+', inventory '+entry['accession']+'. '+entry['note']
        if entry['discovery']:description+='\nDiscovery provenance: '+entry['discovery']+'; this is not a creation date.'
    if u.get('additional_publication_entry'):
        entry=u['additional_publication_entry'];description+='\n\nScholarly comparison: '+entry['title']+'; '+entry['period']+'. '+entry['note']
    description+='\n\nPhysical-object review: '+u['visual_observation']
    description+='\n\nDating: '+u.get('date_review','Qualified historical period from the scholarly entry; no numeric creation interval is established.')
    description+='\n\nCreator not identified. Named deities, dedicators, rulers, book authors or comparison sculptors are not assigned as the maker. Museum holding is separate from current display.'
    return dict(number=u['number'],source_id=u['source_id'],source_scheme=u['source_scheme'],title=u['title'],creator_label=None,first=None,last=None,date_precision='unknown',date_display=u['date_display'],work_type=u['work_type'],medium=u.get('medium_text'),dimensions_text=u.get('dimensions_text'),inventory=u['inventory_literal'],description_md=description.strip(),source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[u['native_url']] if u.get('native_url') else [],source_facts=u)

def build():
    rows=m.load(RUN/'source-review-001.json.gz')['rows'];out=[]
    for u in rows:
        if u['decision']!='candidate_pending_live_identity':continue
        f=facts(u);aid=m.uid(KEY+'/'+u['source_id'])
        out.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('-')[-1].lower(),institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis=u['museum_confidence_basis']+' '+u['visual_observation']+' Fresh bounded source, translated-title, accession and image checks found no established existing-work identity; comparison evidence retained.',editorial_confidence=u['museum_confidence_editorial'],limitation='Holding is not current display or a new legal-ownership determination. Unknown numeric dates and creators remain unknown; historical periods and qualified scholarly identification are explicit.'))
    assert len(out)==38 and len({v['artwork_id'] for v in out})==38 and len({v['slug'] for v in out})==38
    return out,[]

def source_mapping():
    obs=m.load(RUN/'production-identity-001.json.gz');scope=set(obs['state']['scoped_ids']);out={}
    for v in obs['comparisons']:
        hits={x['entity_id'] for x in v['source_hits']}
        if v['decision']=='existing_record':assert len(hits)==1 and hits<=scope;out[v['source_id']]=next(iter(hits))
        else:assert not hits,(v['source_id'],hits)
    assert len(out)==18 and set(out.values())==scope;return out

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();existing=source_mapping();target={v['facts']['source_id']:v['artwork_id'] for v in records};target.update(existing)
    source={v['source_id']:v for v in m.load(RUN/'source-review-001.json.gz')['rows']};images=[]
    for raw in m.load(RUN/'image-inputs-001.json')['rows']:
        im=dict(raw);u=source[im['source_id']];assert u['decision']!='hold' and im['source_id']!='Efa_Kilkis_col/000224-AEMK-2'
        assert im['status']==200 and im['complete_source_frame'] and im['date_policy_passed'] and im['rights_label']=='CC BY-NC-ND 4.0'
        assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256'] and im['bytes']<=100000
        assert hashlib.sha256(Path(im['original_reference']['path']).read_bytes()).hexdigest()==im['original_reference']['sha256']
        aid=target[im['source_id']]
        im.update(artwork_id=aid,production_artwork_id=aid,image_retrieved_at=im['at'],verified_https_source_image_url=im['url'],image_identity_confidence_editorial=.98,identity_basis='Exact accessioned native museum object and matching source heading/description, with full prepared frame visually reviewed. Existing source identifiers resolve the old record directly; no primary image or catalogue date is replaced.',user_approved_source_policy='Specific Greek museum/artist source workflow for works created by1955. Explicit ancient/Byzantine native periods establish earlier creation without invented numeric catalogue dates. Complete frames <=100000bytes. Actual CC BY-NC-ND restrictions and credits remain; no independent copyright-holder licence claimed.',view_label='Source photograph of accessioned object; complete provider frame',ready_to_attach=True,role='existing_record' if im['source_id'] in existing else 'new_record')
        images.append(im)
    assert len(images)==53 and len({v['sha256'] for v in images})==53 and sum(v['role']=='existing_record' for v in images)==17
    focus=m.load(RUN/'focused-comparators-001.json.gz');obs=m.load(RUN/'production-identity-001.json.gz');assert len(focus['ids'])==26
    review=dict(at=m.now(),new_records=38,new_existing_links=0,existing_source_mapping=existing,global_bounded_artworks=267,global_citations=363,focused_full_snapshots=26,query_evidence=c.ref(RUN/'production-identity-001.json.gz'),source_record_review=c.ref(RUN/'source-review-001.json.gz'),
        comparisons=[
          dict(ids=['4bd0d485-0296-5af5-a095-467b6d0cdb8a','8a54084d-b33c-5339-a028-c5cf2dad08ae','a00333ff-4bb8-53ef-9136-84ce89d12306','b1743241-8af7-5506-8c43-83dffe8034f5'],decision='distinct_objects',basis='Four existing Chania oinochoai were compared visually with Kilkis9328 and5409. Chania5586has a tall straight neck and plain pear-shaped body;1820has a black bulbous body and trefoil mouth;6102and4118have different painted patterns, handle geometry and silhouettes. Kilkis9328has a narrow plain body with a dark band;5409has its own sloping lip and horizontal bands. No shared physical vessel identified. Native Chania access hold not retried; existing public Artline frames verified by database checksums.'),
          dict(ids=['6aeb9c99-ec12-5abe-b95a-efa9aad0e3b8','6f17b255-a9d7-5c29-ab18-5bbb6e1e45fb'],decision='distinct_objects',basis='Cleveland1986.183is a silver amphoriskos11.7cm high; LarnacaK-AD811is an Egyptian core-formed glass vessel11.7cm with three handles and coloured festoons. Primary captured API/PDF bytes verified; Cyprus catalogue page166visually checked. Kilkis1091/4154are different clay vessels with distinct photographs and native inventory evidence.'),
          dict(ids=['44fd66c8-e13b-47d7-acd4-ea176e68112e','cd707b2c-803e-4e84-aad1-e068ef515b78'],decision='distinct_objects',basis='Bellows Male Torso1916is a lithograph; reviewed image is a two-dimensional figure study. Tamayo Torso of a Man1969is oil and sand on canvas. Neither is a36cm ancient marble torso in the Kilkis scholarly catalogue.'),
          dict(decision='incidental_inventory_collisions',basis='Other normalized/stripped-inventory hits are named-maker paintings/drawings or unrelated later media with distinct titles and source identities. Bare accession digits are not globally unique. All267projected metadata/creator/citation states retained;26relevant records have full snapshots. No241accession-hit exhaustive visual review is claimed.')],
        scholarly_units=dict(entries=['03','04'],inventories=['331','2046'],distinctness='Same nominal height36cm does not make a duplicate:331has two long curls and missing arms;2046has a fitted shoulder/arm attachment, different muscular twist, preservation boundary and1994findspot. Both complete entry texts visually read; plate5absent. No images attached.',held_entry='05/inventory134incomplete'),
        image_qa=dict(prepared_frames_reviewed=53,prepared_contacts=4,earlier_thumbnail_contacts_reopened=2,additional_thumbnail_contacts=2,comparison_frames=5,comparison_contact_frames=9,old2_source_image_contradiction_held=True,all_full_frames=True,max_bytes=max(v['bytes'] for v in images),originals_separate=True),
        holds=dict(source_entries=12,original_parent_fragment_or_image_or_truncated_entry_holds=6,new_5044_component_holds=6,existing_image_hold_source='Efa_Kilkis_col/000224-AEMK-2'),
        limitations=['Museum65-object public index is fully reviewed, but this is not a complete physical-collection census. The87-sculpture book claim has no complete public inventory crosswalk.','Historical native periods support the ancient/Byzantine context and pre1956image policy;38new numeric dates remain null. No discovery/publication/person lifespan date is used as creation.','No accepted creator inferred from deity, dedicatory name, ruler, mint, comparison artist or book author.','One-off bounded query plans do not prove10-million-row application performance.'])
    m.save(RUN/'identity-review-001.json',review)
    deps=[c.ref(RUN/name) for name in ['baseline-verification-001.json','production-initial-scope-001.json.gz','source-review-001.json.gz','image-inputs-001.json','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-review-inputs-001.json','focused-source-corroboration-001.json','identity-review-001.json']]
    deps+=m.load(RUN/'source-review-001.json.gz')['dependencies'];deps+=m.load(RUN/'focused-source-corroboration-001.json')['dependencies']
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,existing_source_mapping=existing,dependencies=list({v['path']:v for v in deps}.values()),expected_counts=dict(linked=56,eligible=0),new_work_types=dict(collections.Counter(v['facts']['work_type'] for v in records)),new_unknown_numeric_dates=38,old_unknown_numeric_dates_preserved=18,new_primary_images=53,new_record_primary_images=36,existing_record_primary_images=17,alternate_images=0,source_identifier_policy='36SearchCulture canonical object IDs and2ISBN/catalogue inventory IDs; no shared PDF URL identity conflation. Literal accession spellings retained.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        fields=['number','artwork_id','source_scheme','source_id','title','inventory','creator_label','first','last','date_display','work_type','source_url'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for v in records:w.writerow({k:v['artwork_id'] if k=='artwork_id' else v['facts'][k] for k in fields})
    print(json.dumps(dict(new=38,images=53,old_primary_filled=17,expected_catalogue=56,numeric_dates=0)),flush=True)

if __name__=='__main__':main()
