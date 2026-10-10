"""Final selection of55distinct photographic works; no image delivery."""
import csv,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-photographs-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='athens-city-photographs-001'

def build():
    out=[]
    for u in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']:
        if u['decision']!='proposed_review_artwork':continue
        description='\n'.join(u['description_source'])+'\n\nSource archive credit: '+'; '.join(u['creator_source_literals'])+'.'
        description+='\nThe museum catalogues this photographic image in the Koutsapli donation and describes its medium as digital photograph only. The original negative or print support, printing date and date of digitisation are unspecified. The archive credit does not establish an individually verified photographer for this record.'
        if u['first'] is None:description+='\nPhotograph date unresolved: the source date field says1960 while the series title says1965–1970. Both are preserved without choosing or inventing a numeric creation date.'
        else:description+='\nThe source date describes the historical photograph; it is not asserted as the date of a physical print or digital file.'
        description+='\nMuseum collection connection is documented; current display is not established.'
        aid=m.uid(KEY+'/'+u['source_id']);facts=dict(number=u['number'],source_id=u['source_id'],source_scheme='searchculture-edm',title=u['title'],creator_label=None,first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],work_type='photograph',medium=u['medium_text'],dimensions_text=None,inventory=None,description_md=description,source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[u['native_url']],source_facts=u)
        out.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000190-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=facts,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis='Museum-supplied photograph page, Koutsapli donation credit and distinct complete composition visually reviewed against the selected archive records, including all10existing photographs. Fresh global source/title/creator/image checks found no established existing-work identity.',editorial_confidence=.96,limitation='Collection connection concerns the museum-catalogued photographic image. Source medium says digital photograph only; original negative or vintage print ownership is not asserted. Photograph date is distinct from digitisation/printing date; current display is unknown.'))
    assert len(out)==55 and len({v['artwork_id'] for v in out})==55
    return out,[]

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();obs=m.load(RUN/'production-identity-001.json.gz');scope=m.load(RUN/'production-initial-scope-001.json.gz');assert set(obs['state']['artwork_ids'])==set(scope['scoped_ids']) and len(scope['scoped_ids'])==153
    mapping={}
    for x in obs['comparisons']:
        hits={v['entity_id'] for v in x['source_hits']}
        if x['decision']=='existing_comparator':assert len(hits)==1;mapping[x['source_id']]=next(iter(hits))
        else:assert not hits
    assert len(mapping)==10 and not obs['state']['matching_media'] and not obs['state']['artist_ids']
    review=dict(at=m.now(),new_records=55,new_existing_links=0,existing_source_mapping=mapping,bounded_artworks=153,bounded_citations=198,bounded_creator_links=2,full_snapshots=153,query_reference=c.ref(RUN/'production-identity-001.json.gz'),comparisons=[dict(numbers=[8,48],decision='distinct_exposures',basis='Piraeus church views differ in camera angle, street lamps, foreground structures and buses; not crops or alternate scans.'),dict(numbers=[39,56],decision='distinct_buildings_and_exposures',basis='Different ground-floor arches/rustication, cornice, windows and adjacent buildings despite similar corner composition.'),dict(numbers=[2,3,35,50],decision='distinct_syntagma_views',basis='Different views and foreground arrangements. Seven source1960 dates remain unresolved against series-title1965–1970, rather than invented corrections.'),dict(numbers=[11,25,30,31,56,65],decision='generic_title_not_identity',basis='Existing11is a planted courtyard and65a busy street. New25shows a junction/building,30a church facade,31a sidewalk under an awning and56a different street corner. All complete source frames reviewed. Same series title is not a work match.')],museum_basis='65museum-supplied individual catalogue records uniformly identify the Koutsapli donation, archive credit and digital photograph only. The2023first-person donor interview corroborates a donation of2200printed photographs, but does not date or identify the original support of these individual records. Numeric dates refer to the historical photographic work; physical print and digital-file dates remain unknown.',creator_basis='No existing matching person authority or aliases found for the supplied archive names. Preserve exact archive credit in public description/citations, without creating a biography or claiming donor/architect/depicted person as photographer.',date_counts=dict(new_numeric_dated=48,new_unknown=7),images=dict(research_thumbnails=65,contacts_viewed=3,individual_frames_viewed=[8,48,39,56],exact_hash_duplicates=0,production_images=0,reason='Source dates are after1955; this Greek image-delivery selection does not include these photographs.'),limitations=['60of1634photograph-index cards selected; five were existing. Five additional existing comparators were captured. The1574unselected photograph-index entries remain unreviewed.','Bounded queries and153full preservation snapshots are not exhaustive all-catalogue duplicate proof or10-million-row performance evidence.','Seven date discrepancies and original photographic support remain open research questions.'])
    m.save(RUN/'identity-review-001.json',review)
    deps=[c.ref(RUN/name) for name in ['baseline-verification-001.json','production-initial-scope-001.json.gz','editorial-source-decisions-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','visual-references-001.json','archive-context-001.json','identity-review-001.json']]
    deps+=m.load(RUN/'editorial-source-decisions-001.json.gz')['dependencies']
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=[],existing_source_mapping=mapping,dependencies=list({v['path']:v for v in deps}.values()),expected_counts=dict(linked=208,eligible=111),new_unknown_numeric_dates=7,new_numeric_dated=48,new_primary_images=0,new_artist_links=0,policy='55historical photographic works with documented museum collection association, preserving digital-only source medium and unknown original support. Seven date conflicts stay null. All records review; no image or old-record updates.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        cols=['number','artwork_id','source_id','title','creator_label','first','last','date_display','work_type','source_url'];w=csv.DictWriter(out,fieldnames=cols);w.writeheader()
        for v in records:w.writerow({k:v['artwork_id'] if k=='artwork_id' else v['facts'][k] for k in cols})
    print(json.dumps(dict(new=55,images=0,expected_catalogue=208,expected_numeric_dates=111)),flush=True)

if __name__=='__main__':main()
