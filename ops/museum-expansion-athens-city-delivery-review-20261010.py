"""Reviewed Athens City physical objects, creator identities and selected CC0 images."""
import collections,csv,hashlib,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-delivery-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='athens-city-production-001'
ARTISTS={103:'6bc44dd0-9a43-4709-8fd4-454ead88bb15',117:'5c005acb-575b-44db-97c8-1680d829a479'}
AUTHORITY={103:'https://www.searchculture.gr/aggregator/persons/-1091820013',117:'https://www.searchculture.gr/aggregator/persons/-1066026377'}

def facts(u):
    n=u['number'];description='\n'.join(u['description_source'])
    if n==88:description='Portrait of Vasileios Markezinis by Dimitrios Kretsis. The museum transcribes a gift inscription on the reverse; no creation date is supplied.'
    if n==31:description+='\nThe source describes a hand-coloured aquatint. The available image shows the reverse; the front composition has not been verified.'
    if n in [27,37]:description+='\nThe source creator field is an institutional or manufacturer credit; the maker remains unidentified.'
    if n==84:description+='\nAttributed to Takis Kalmouchos; the signature is questioned in the museum description.'
    if n==87:description+='\nAttribution unresolved: the source creator field and reported signature disagree.'
    if n==111:description+='\nCreation date unresolved: the source says around 1850 but describes an 1853–1854 prototype. Neither date is adopted as the date of this print.'
    if n in [49,50,62,105,112]:description+='\nDates in inscriptions or the represented subject have not been adopted as the creation date of this physical object.'
    if n in [65,69,70,75,80]:description+='\nTwo drawings on one physical sheet, catalogued as one object.'
    if n==63:description+='\nDecorated wooden frame incorporating a postcard reproduction; this record does not describe the original Tinos icon.'
    if 140<=n<=152:description+='\nAn adolescent study by Vasileios Markezinis, including copies after other compositions; this is the student work, not an original by the copied artist.'
    if u['first'] is None:description+='\nCreation date unknown or unresolved; date-scope review remains open.'
    description+='\nDocumented museum collection object; current display has not been established.'
    return dict(number=n,source_id=u['source_id'],source_scheme='searchculture-edm',title=u['title'],creator_label=None if n in ARTISTS else u['creator_label'],artist_id=ARTISTS.get(n),first=u['first'],last=u['last'],date_precision='exact' if u['date_precision']=='year' else u['date_precision'],date_display=u['date_display'],work_type=u['work_type'],object_form=u['object_form'],cultural_context=u['cultural_context'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=u['inventory'],description_md=description.strip(),source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[u['native_url']],source_facts=u,creator_authority_url=AUTHORITY.get(n))

def build():
    rows=m.load(c.RESEARCH/'editorial-source-decisions-001.json.gz')['rows'];out=[]
    for u in rows:
        if u['decision']!='proposed_review_artwork':continue
        f=facts(u);aid=m.uid(KEY+'/'+u['source_id'])
        out.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000190-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis='Museum-supplied object page, unique source identifier and physical-object description. '+('Source frame reviewed; repeated titles and versions distinguished. ' if u['source_image_reviewed'] else 'Source42 thumbnail unavailable; metadata-only physical identity, no visual match claimed. ')+'Fresh bounded source/title/creator/image reconciliation found no established existing physical-work identity.',editorial_confidence=.96 if u['number']!=42 else .9,limitation='Holding is not current display or a new legal-ownership determination. Unknown creation dates remain null and require scope review; literal maker labels and qualified attributions remain evidence.'))
    assert len(out)==135 and len({v['artwork_id'] for v in out})==135 and len({v['slug'] for v in out})==135
    return out,[]

def artist_link(v):
    f=v['facts'];assert f['number'] in ARTISTS
    return dict(artwork_id=v['artwork_id'],artist_id=f['artist_id'],attribution_role='primary',attribution_note='Museum object creator label and linked SearchCulture person authority agree with the existing painter identity and lifespan. Sitter distinguished from maker. Source: '+f['creator_authority_url'],representative_order=None)

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();target={v['facts']['source_id']:v for v in records};images=[]
    obs=m.load(RUN/'production-identity-001.json.gz');existing={}
    for v in obs['comparisons']:
        hits={x['entity_id'] for x in v['source_hits']}
        if v['decision']=='existing_comparator':assert len(hits)==1;existing[v['source_id']]=next(iter(hits))
        else:assert not hits,(v['number'],hits)
    assert len(existing)==7
    authority=m.load(RUN/'creator-source-corroboration-001.json')['rows'];artists=m.load(RUN/'focused-comparators-001.json.gz')['artist_state']['artists']
    for n,aid in ARTISTS.items():
        a=next(x for x in artists if x['id']==aid);page=next(x for x in authority if x['url']==AUTHORITY[n]);assert str(a['birth_year'])+'-'+str(a['death_year']) in page['title']
    for raw in m.load(c.RESEARCH/'image-delivery-prepared-001.json')['rows']:
        im=dict(raw);v=target[im['source_id']];f=v['facts'];rc=im['source_image_reference']
        assert rc['status']==200 and im['date_policy_passed'] and f['last'] is not None and f['last']<=1955
        assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256']==im['original_reference']['sha256'] and im['bytes']<=100000
        assert im['rights_status']=='public_domain' and im['rights_url']=='http://creativecommons.org/publicdomain/zero/1.0/'
        im.update(artwork_id=v['artwork_id'],production_artwork_id=v['artwork_id'],source_title=f['title'],source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],verified_https_source_image_url=im['image_url'],identity_basis='Object-specific museum-supplied source page and complete source frame reviewed; title, medium, composition and visible inventory labels compared where available. Bounded production identity reconciliation completed; this is the selected physical artwork/version.',view_label='Complete source photograph, including frame and source labels',ready_to_attach=True,role='new_record')
        images.append(im)
    assert len(images)==39 and len({v['sha256'] for v in images})==39
    review=dict(at=m.now(),new_records=135,new_existing_links=0,existing_source_mapping=existing,global_bounded_artworks=1740,global_citations=4079,focused_full_snapshots=135,query_evidence=c.ref(RUN/'production-identity-001.json.gz'),
      comparisons=[
       dict(numbers=[10,11],decision='distinct_objects',basis='Different framed prints with inventory10100 versus10101. Source10 depicts a built harbour and workers;11 open water with a red-sailed ship. Source10 visible inscription appears Dieppe while its supplied title says Dunkerque; retain supplied title and contradictory image evidence, without merging or inventing a correction.'),
       dict(numbers=[14,15,16,18,19,20],decision='distinct_objects',basis='Exact port-title hits identify later oil paintings, drawings or an1882Lalanne lithograph. Athens source19/20 are framed1776prints, unlike existing1762/1754Vernet painted compositions; all four frames compared. Shared place or prototype is not a physical-object match.'),
       dict(numbers=[109],decision='distinct_artist_and_work',basis='Twenty YoungWoman title hits identify other makers including Rops, Frosterus-Saltin, Millet, Hellman, Israels, Hesse, Havrylenko, Krouse, King, Giacometti, Pemba, Haskell, Modigliani, Soutine, Picasso, Morisot and Gorky. Exact source authority identifies VyronKontopoulos1861–1941, not database AlekosKontopoulos1904–1975. No existing Vyron authority found; retain object label.'),
       dict(numbers=[162],decision='distinct_print',basis='Existing EdwardBrandard B1977.14.13883 has a large domed church at left and broad horizontal foreground; Athens print has a receding canal, vertical church at right, different boat/building layout and its own Greek caption, foxed paper and photographed inventory. Different composition, not merely another scan. Other exact Venice hits are Duveneck/Rosenberg prints, Sargent/Brabazon watercolours, Prendergast work or Turner oil37.132. Do not merge or link the unresolved Brandard/Turner creator roles.'),
       dict(numbers=[103,117,133],decision='two_secure_creator_links',basis='Source103 explicitly names Karavia and reports her signature; person authority1871–1960 agrees with the existing artist. Christomanos is the sitter. Source117 labels Iakovidis and linked authority1853–1932 agrees; Thon is the sitter. Full-length oil117 differs from oval1899watercolour133byAmelieCochel. Existing33Iakovidis and20Karavia catalogue works have different source identities/titles and no established same work. Existing authorities and aliases remain untouched.'),
       dict(numbers=[31,84,87,90,106,111,162],decision='retain_unresolved_roles_or_attributions',basis='Generic creator matches cannot resolve designer/engraver roles, questioned signatures or contradictory dates. Preserve original source lists and qualifiers; no forcedprimary links or invented role enums. Source31 reviewed verso, no front-image claim.')],
      image_qa=dict(research_frames_previously_viewed=142,research_contacts=6,new_comparison_frames=3,comparison_contact_frames=11,contact_viewed=True,selected_images=39,max_bytes=max(x['bytes'] for x in images),full_source_frames=True,low_resolution='Generally380pixels wide; no native high-resolution files obtained.'),
      holds=dict(index_post1970=17,scope_hold_numbers=[35,94,108],image_unavailable_number=42),
      limitations=['Only the eight selected art categories have been fully indexed:162unique records of2405mixed source records. Other2243records remain unreviewed, not eligible additions.','Unknown dates remain88new records; those count in the unified catalogue but not numeric creation-date eligibility.','135focused full snapshots and1740bounded projected metadata/creator/citation comparisons are not an exhaustive duplicate guarantee or a10million-row performance test.'])
    m.save(RUN/'identity-review-001.json',review)
    deps=[c.ref(RUN/name) for name in ['baseline-verification-001.json','production-initial-scope-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-review-inputs-001.json','creator-source-corroboration-001.json','identity-review-001.json','schema-constraints-001.json']]
    deps += [c.ref(c.RESEARCH/name) for name in ['editorial-source-decisions-001.json.gz','image-delivery-prepared-001.json','creator-source-corroboration-001.json']]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,existing_source_mapping=existing,dependencies=deps,expected_counts=dict(linked=153,eligible=63),new_work_types=dict(collections.Counter(v['facts']['work_type'] for v in records)),new_unknown_numeric_dates=88,new_numeric_dated=47,new_primary_images=39,new_artist_links=2,icons=14,source_identifier_policy='One immutable SearchCulture object UUID per documented physical unit; pairs and studies stay one per support. Visible inventory labels are comparison evidence, not fabricated canonical accessions.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        fields=['number','artwork_id','source_id','title','creator_label','artist_id','first','last','date_display','work_type','object_form','source_url'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for v in records:w.writerow({k:v['artwork_id'] if k=='artwork_id' else v['facts'][k] for k in fields})
    print(json.dumps(dict(new=135,images=39,artist_links=2,expected_catalogue=153,numeric_dates=63)),flush=True)

if __name__=='__main__':main()
