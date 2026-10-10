"""Reconcile Theocharakis physical artworks against live identity and image evidence."""
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import requests
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-theocharakis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='theocharakis-production-001';ARTIST='96c93b65-37db-4879-9bf7-3bf5a9d8178e';BOAT='733bd5c0-a88e-535d-9e06-e383ce9b3883';BOAT_SOURCE='theocharakis/000163-103169'

def build():
    records=[];holdings=[]
    for root,wave in [(c.RESEARCH,'first'),(c.DATED,'dated')]:
        rows={v['source_id']:v for v in m.load(root/'editorial-source-decisions-001.json.gz')['rows']}
        for u in m.load(root/'candidate-physical-units-001.json.gz')['rows']:
            members=[rows[sid]for sid in u['source_ids']];row=members[0];aid=BOAT if u['primary_source_id']==BOAT_SOURCE else m.uid(KEY+'/'+u['primary_source_id'])
            first,last=u['first'],u['last'];assert (first is None)==(last is None)
            if first is not None:assert first<=last<=1970
            description=u.get('description_note','One source-backed physical artwork; subjects are not additional holdings.')
            if first is None:description+='\n\nCreation date is not supplied by the source; numerical dates remain unknown pending editorial research.'
            for member in members:description+='\n\nSource '+member['native_url']+': '+member['title']+'; '+member['medium_text']+'; '+member['dimensions_text']+'; '+member['date_display']+'.'
            if row.get('image_further_identity_evidence_required'):description+='\n\nImage review: '+row['image_note']
            facts=dict(number=u['primary_number']+(200 if wave=='dated' else 0),research_number=u['primary_number'],research_wave=wave,source_id=u['primary_source_id'],source_url=row['source_url'],source_ids=u['source_ids'],source_urls=[v['source_url']for v in members],native_urls=[v['native_url']for v in members],title=u['title'],creator_label=u['creator_label'],painter_id=ARTIST,first=first,last=last,date_precision='unknown'if first is None else 'exact'if first==last else 'range',date_display=u['date_display'],work_type=u['work_type'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=None,description_md=description,physical_unit=u,source_facts=members)
            basis='Native foundation catalogue and explicit collection label; exact source creator name and1892–1957 lifespan agree with the unique existing artist authority. Physical sheets and versions reconciled from source metadata and visual comparison.'
            if aid==BOAT:basis+=' Existing WikiArt Boat1948 and native Boat at Paros103169 show identical red hull, interior benches, individual wave strokes, background shoreline and lower-right signature; creator, date and Paros subject agree. Reuse existing artwork, preserve its date/title/type and primary image.'
            else:basis+=' Fresh source/artist/title/image lookup and65focused comparison records reveal no same physical work.'
            v=dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['primary_source_id'].split('-')[-1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=facts,retrieved_at=row['source_receipt']['retrieved_at'],identity_basis=basis,editorial_confidence=.98,limitation='Catalogue holding is not current display. Original creator labels, unknown dates and source differences remain in evidence. One physical sheet is counted once.')
            (holdings if aid==BOAT else records).append(v)
    assert len(records)==196 and len(holdings)==1 and sum(v['facts']['first']is not None for v in records)==124
    assert len({v['artwork_id']for v in records+holdings})==197 and sum(len(v['facts']['source_ids'])for v in records+holdings)==205
    return records,holdings

def artist_link(v):
    return dict(artwork_id=v['artwork_id'],artist_id=ARTIST,attribution_role='primary',representative_order=None,attribution_note='Exact unique existing artist name and1892–1957 lifespan agree with the native foundation attribution. Original creator label: '+v['facts']['creator_label']+'; '+v['facts']['source_url'])

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();data=m.load(RUN/'production-identity-001.json.gz');state=data['state'];focus=m.load(RUN/'focused-comparators-001.json.gz');frames=m.load(RUN/'focused-review-inputs-001.json');prepared=m.load(RUN/'image-delivery-prepared-001.json')
    assert state['artist_ids']==[ARTIST] and state['artists'][0]['birth_year']==1892 and state['artists'][0]['death_year']==1957
    assert len(focus['ids'])==65 and len(frames['frames'])==18 and len(prepared['sheets'])==8
    sources={}
    for v in data['comparisons']:
        hits={x['entity_id']for x in v['source_hits']}
        if v['decision']=='existing_record':assert len(hits)==1;sources[v['source_id']]=next(iter(hits))
        else:assert not hits,(v['source_id'],hits)
    assert len(sources)==18 and set(sources.values())==set(state['scoped_ids'])
    targets={sid:v['artwork_id']for v in records+holdings for sid in v['facts']['source_ids']};images=[]
    for raw in prepared['rows']:
        im=dict(raw);aid=targets[im['source_id']];im.update(artwork_id=aid,production_artwork_id=aid,ready_to_attach=True,identity_basis='Full native frame reviewed against individual object metadata and prior physical-sheet comparisons. Eight prepared contact sheets checked for114images; distinct studies/versos retained. Boat103169 matches the existing1948work and attaches as an alternate while preserving the existing primary.')
        assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256']and im['bytes']<=100000
        images.append(im)
    assert len(images)==114 and len({v['artwork_id']for v in images})==111
    fresh=[]
    for key,url in [('foundation','https://thf.gr/en/the-foundation/'),('artist','https://www.nationalgallery.gr/en/artist/papaloukas-spyros/'),('boat','https://www.wikiart.org/en/spyros-papaloukas/boat-1948')]:
        dest=RUN/'captures'/('focused-'+key+'-001.body.gz');receipt=RUN/'captures'/('focused-'+key+'-001.json')
        if receipt.exists():fresh.append(m.load(receipt));continue
        response=requests.get(url,timeout=(15,40));response.raise_for_status();raw=response.content;dest.parent.mkdir(parents=True,exist_ok=True);dest.open('xb').write(gzip.compress(raw,mtime=0));v=dict(at=m.now(),url=url,final_url=response.url,status=response.status_code,sha256=hashlib.sha256(raw).hexdigest(),body_path=str(dest.relative_to(m.ROOT))if dest.is_absolute()else str(dest));m.save(receipt,v);fresh.append(v)
    review=dict(at=m.now(),new_records=196,existing_work_links=1,existing_match=dict(source_id=BOAT_SOURCE,artwork_id=BOAT,confidence_editorial=.99,basis=holdings[0]['identity_basis']),artist_id=ARTIST,artist_resolution='Unique exact native/English creator name plus matching1892–1957 lifespan and existing National Gallery authority URL; no artist metadata changes.',source_mapping=sources,prepared_images_visually_reviewed=114,prepared_contacts=prepared['sheets'],existing_images_reviewed=frames['contact'],additional_fullframes_reviewed=['prepared/103169.jpg','comparison-images/'+BOAT+'.jpg','theocharakis-dated-20261010/comparisons/103449.jpg'],protected_comparators=65,global_comparison_records=3766,
        distinct_decisions=[dict(scope='Five new self-portraits',basis='Native1956oil portrait,1955charcoal head,1955colour drawing,1954pencil portrait and1950watercolour differ in framing, facial contours, brush/drawing strokes, shirt and background from existingWikiArt1941head; all five original references inspected.'),dict(scope='Pantokratoros and Mount Athos subjects',basis='Existing oil views show distant tower/buildings, harbour structures or specific interiors. Selected native watercolour courtyard, Stavronikita buildings, Karyes and monastery study show different architectural viewpoints, supports and compositions.'),dict(scope='Generic unknown-creator matches',basis='28 broad date/unknown-creator leads consist of19wood/metal sculptures,Asian scrolls or period-specific paintings,Byzantine icon/wallpainting records andCyprusAsinoufresco. Recorded materials,dimensions and source descriptions distinguish them from Papaloukas paper studies. KyotoA671 source description identifies two hanging scrolls byIsshiKii; BXM01803icon84x59cm fromEgypt differs from17.5cmPapaloukas pencil/ink drawings; Asinou wallpainting has explicit architectural placement.'),dict(scope='Other attributed title matches',basis='Generic titles likeStillLife orFemaleNude match works attributed to different verified/named creators. They have no native sourceID,imagechecksum orPapaloukas authority match. All3766returned records remain in the bounded search evidence.'),dict(scope='Earlier eighteenTheocharakis objects andfourreverse references',basis='All18sourceIDs securely map to live rows. Prior eightnewtwo-sided sheet groupings andfourproposed existingreverse references remain. Existing dates/statuses/images andidentifiers stay unchanged; unresolved13sourceidentityholds remain excluded.'),dict(scope='Existing boy portrait duplication',basis='GreekBoywithSuspenders andWikiArtBoywearingsuspenders appear to show the same painting. Neither is a newTheocharakis candidate; no merge or museum reassignment in this batch. Recorded for separate reconciliation.')],
        source_checks=fresh,existing_primary_preserved=True,metadata_identity_holds=13,image_metadata_hold='Dated30Study of a pear103308 remains metadata-only due to dimensions/title/image conflict.',image_date_holds='72undated newworks and13works ending after1955 have no new images.',no_current_display_claims=True,confidence_note='Editorial assessments, not calibrated probabilities.')
    m.save(RUN/'identity-review-001.json',review)
    m.save(RUN/'image-qa-001.json',dict(at=m.now(),all114prepared_frames_viewed=True,complete_source_frames_preserved=True,source_sheets=prepared['sheets'],max_bytes=max(v['bytes']for v in images),images=114,physical_artworks=111,unknown_dates_not_imaged=True,rights_labels_preserved='CC BY-SA4.0 actual source label; userGreeksourceapproval separately recorded.',new_primary_expected=110,alternate_expected=4))
    deps=[c.ref(root/f)for root in [c.RESEARCH,c.DATED]for f in ['candidate-physical-units-001.json.gz','editorial-source-decisions-001.json.gz','physical-unit-review-001.json','visual-references-001.json']]
    deps += [c.ref(RUN/f)for f in ['baseline-verification-001.json','production-initial-scope-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-review-inputs-001.json','identity-review-001.json','image-delivery-prepared-001.json','image-qa-001.json']]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,dependencies=deps,expected_counts=dict(linked=215,eligible=137),new_work_types=dict(collections.Counter(v['facts']['work_type']for v in records)),new_unknown_numeric_dates=72,existing_dates_preserved=19,new_primary_images=110,alternate_images=4,artist_links=196))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='')as out:
        fields=['number','artwork_id','action','title','creator_label','first','last','date_precision','date_display','work_type','source_url'];writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
        for v in records+holdings:writer.writerow({k:v['artwork_id']if k=='artwork_id'else('existing_work_link'if v['artwork_id']==BOAT else'new_record')if k=='action'else v['facts'][k]for k in fields})
    print(json.dumps(dict(new=196,existing_links=1,images=114,new_primary_images=110,alternate_images=4,numeric_new=124,unknown_new=72,expected_catalogue=215)),flush=True)
if __name__=='__main__':main()
