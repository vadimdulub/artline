"""Final selected WarMuseum delivery:168reviewworks,90authenticJPEGs,65creatorlinks."""
import copy,csv,hashlib,importlib.util,json
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-war-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='war-production-001';THALIA='6bc44dd0-9a43-4709-8fd4-454ead88bb15';ROILOS='e17bd3cc-0953-5aa6-9e0e-00a16419379d'
AUTHORITIES={THALIA:'https://www.searchculture.gr/aggregator/persons/-1091820013',ROILOS:'https://www.searchculture.gr/aggregator/persons/1652662752'}

def facts(raw):
    u=copy.deepcopy(raw);n=u['number'];artist=THALIA if u['creator_source_literals'][0]=='Θάλεια Φλωρά Καραβία' else ROILOS if n in [3,4,116,124] else None
    assert n!=169
    display=u['date_display'].replace('Early20th','Early 20th').replace('range1900','range: 1900').replace('Circa1725','Circa 1725').replace('circa1700','circa 1700').replace('crosses1970','crosses 1970')
    description=u['description_source'][0] if u['description_source'] else ''
    if u['first'] is None:description+='\n\nThe creation date of this object is unresolved. Historical dates and conflicting version evidence remain in the source citation.'
    elif u['last']>1970:description+='\n\nThe museum supplies a broad creation range crossing 1970. Creation before 1971 has not been established; this remains a review candidate.'
    if n in [13,89,115,151]:description+='\n\nThe museum identifies this work as a copy. The copyist is distinguished from the artist of the prototype.'
    if n==57:description+='\n\nThe museum classifies this object as a photograph. The label SCOTT does not establish the photographer or confirm an original painting.'
    if n==58:description+='\n\nThe caption and creator field use differing artist labels. The maker identity remains unresolved.'
    if n in [184,185]:description+='\n\nThis record concerns the museum cast or replica context, not an ancient original. Its creation date remains the supplied broad modern range.'
    description+='\n\nDocumented War Museum collection object. Current display has not been established.'
    return dict(number=n,source_id=u['source_id'],source_scheme='searchculture-edm',title=u['title'],creator_label=None if artist else u['creator_label'],artist_id=artist,creator_authority_url=AUTHORITIES.get(artist),first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=display,work_type=u['work_type'],object_form=u['object_form'],cultural_context=u['cultural_context'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=None,description_md=description,source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[],source_facts=u)

def build():
    records=[]
    for u in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']:
        if u['decision']!='proposed_review_artwork':continue
        f=facts(u);aid=m.uid(KEY+'/'+u['source_id'])
        records.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000181-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis='Museum-supplied individual object record and bilingual literal metadata, followed by composition/copy/unit review and bounded existing source, title, creator and image reconciliation. No existing same-work identity established. Similar portraits and field drawings retain their distinct compositions.',editorial_confidence=.96,limitation='Holding is distinct from current display and legal ownership. Nine unresolved dates and68creationranges crossing1970 remain review candidates, not numeric-date eligible. SourceURL numbers are not inventory numbers. Six unavailable images and specific identity holds documented separately.'))
    assert len(records)==168 and sum(bool(v['facts']['artist_id']) for v in records)==65
    return records,[]

def artist_link(v):
    f=v['facts'];assert f['artist_id'] in AUTHORITIES
    note='Museum literal maker labels and linked SearchCulture creator authority establish '+('Thalia Flora-Karavia,1871–1960' if f['artist_id']==THALIA else 'Georgios Roilos,1867–1928')+' and match the existing artist identity. Source labels are preserved in citation evidence. No creation date inferred from artist lifespan. '+AUTHORITIES[f['artist_id']]
    return dict(artwork_id=v['artwork_id'],artist_id=f['artist_id'],attribution_role='primary',attribution_note=note,representative_order=None)

def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();records,holdings=build();target={v['facts']['number']:v for v in records};obs=m.load(RUN/'production-identity-001.json.gz');existing={}
    source=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];decision={x['number']:x for x in source}
    for row in obs['comparisons']:
        hits={x['entity_id'] for x in row['source_hits']}
        if decision[row['number']]['decision']=='existing_comparator':assert len(hits)==1;existing[row['source_id']]=next(iter(hits))
        else:assert not hits and not row['inventory_hits'] and not row['title_hits']
    assert len(existing)==12
    focus=m.load(RUN/'focused-comparators-001.json.gz');artists={x['id']:x for x in focus['artist_state']['artists']};assert (artists[THALIA]['birth_year'],artists[THALIA]['death_year'])==(1871,1960);assert (artists[ROILOS]['birth_year'],artists[ROILOS]['death_year'])==(1867,1928)
    auth=m.load(RUN/'creator-source-corroboration-001.json')['rows'];assert len(auth)==2 and all(any(x['url']==url for x in auth) for url in AUTHORITIES.values())
    digital=m.load(RUN/'selected-digital-files-001.json');assert len(digital['rows'])==90 and not digital['held'];thumbs={x['number']:x for x in m.load(RUN/'visual-references-001.json')['rows']};rights={x['number']:x for x in m.load(RUN/'focused-context-001.json.gz')['item_rights']};images=[];folder=c.PROOF/'prepared-images';folder.mkdir(parents=True,exist_ok=True)
    for row in digital['rows']:
        n=row['number'];v=target[n];u=decision[n];rc=row['image'];assert u['image_candidate'] and u['last']<=1955
        assert rc['sha256']==thumbs[n]['sha256'],'Digitalfile and reviewedthumbnail must match exactly'
        raw=Path(rc['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and len(raw)==rc['bytes']<=100000
        with Image.open(rc['path']) as im:im.load();assert im.format=='JPEG' and im.size==(rc['width'],rc['height'])
        assert any(x['text']=='CC BY-SA 4.0' and 'προεπισκόπησης' in x['parent_text'] for x in rights[n]['matches'])
        path=folder/(str(n).zfill(3)+'-'+rc['sha256'][:16]+'.jpg');assert not path.exists();path.write_bytes(raw)
        credit='Πολεμικό Μουσείο; artist: '+(u['creator_label'] or 'unidentified')+'; museum-supplied reproduction via SearchCulture.gr'
        images.append(dict(number=n,source_id=u['source_id'],source_url=u['source_url'],title=v['facts']['title'],source_title=v['facts']['title'],artwork_id=v['artwork_id'],production_artwork_id=v['artwork_id'],first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=v['facts']['date_display'],image_url=rc['url'],verified_https_source_image_url=rc['url'],image_source='War Museum / SearchCulture museum-supplied digital file',source_image_reference=rc,source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],original_reference=dict(path=rc['path'],sha256=rc['sha256']),thumbnail_reference=thumbs[n],prepared_path=str(path),sha256=rc['sha256'],bytes=len(raw),width=rc['width'],height=rc['height'],original_width=rc['width'],original_height=rc['height'],mime_type='image/jpeg',mode='source_bytes_unchanged',complete_source_frame=True,rights_status='cc_by_sa',rights_label='CC BY-SA 4.0',rights_url='http://creativecommons.org/licenses/by-sa/4.0/',rights_evidence_reference=rights[n]['source_receipt'],digital_file_wrapper_reference=row['wrapper_receipt'],credit=credit,changes='Source JPEG bytes unchanged. Complete supplied frame retained.',image_identity_confidence_editorial=.98,identity_basis='Exact museum object record, reviewed thumbnail and source-linked digital JPEG are byte-identical. All189sourceframes,90digitalframes and six existing counterpartframes reviewed; no conflicting object identity found for this selected file.',image_identity_basis='Byte-identical museum source reproduction and reviewed complete object composition.',date_policy_passed=True,user_approved_source_policy='Existing Greek museum/artist workflow in docs/ARTLINE_IMAGE_USE.md for selected works created by1955. Actual source image licence is CC BY-SA4.0; source evidence, attribution and licence URL retained separately from user approval.',resolution_limitation='Source endpoint supplies the same low-resolution JPEG as the thumbnail, at most380pxwide or550pxhigh. Wrapper descriptive dimensions can differ from decodedpixels; actual decodedpixel dimensions retained. No enlargement or invented detail.',view_label='Complete museum-supplied digital image, including supplied frame or paper margins',prepared=True,ready_to_attach=True,attached=False,role='new_record'))
    assert len({x['sha256'] for x in images})==90
    review=dict(at=m.now(),new_records=168,new_existing_links=0,existing_source_mapping=existing,global_bounded_artworks=484,global_citations=1032,focused_full_snapshots=484,creator_links_new=65,numeric_date_new_records=91,unknown_date_new_records=9,crossing_cutoff_new_records=68,new_images=90,expected_museum_counts=dict(linked=180,eligible=103,primary_images=102),source_visual_review=dict(thumbnails=189,source_contacts=8,focused_source_frames=7,digital_files=90,digital_contacts=4,existing_comparator_images=6,existing_comparator_contacts=1,prepared_identical_to_reviewed_digital_files=True),counterpart_review='12oldsourceidentities and their imagehashes preserved. No additional exactsource/titlematches. Existing21Karavia,3Roilos and28Woodville-relatedworks compared by subject/version/medium. SixillustratedKaravia counterparts visually differ: Nikopolisruins; EmminAgaarchedinterior; Tsarouchisportrait; MarieBonaparte; Bizanibatteryrockylandscape; Troupakiscommanderportrait. These are distinct from selected WarMuseum scenes. Mostremainingcreatorsearchhits are unrelated Wells/Jansson/Bellini/Flora substringmatches; not linked.',physical_unit_review='Distinct3/4/124Evzones,87/88Constantinedrawings,107–111nursecompositions,139/140Bursaviewsand145/161Mudanyafigures. Fourphotographs grouped132and threeunillustratedGerontasstudies103–105held for physicalunit reconciliation. Exactsheet/album/rectoverso collation remains unreported.',holds=dict(scope=[10,11,44,53],identity=[31,65,71,81,103,104,105,123,132,135,169],unavailable_images=[103,104,105,138,149,170]),image_policy='90selectedsourceJPEGs, all byte-identical to reviewed thumbnails, preservedunchanged and at most35321bytes. Actualitem anddigitalfile CC BY-SA4.0licence retained. No image for anyunknown/crosscutoffdate orheldidentity.138source-dateddrawinghasemptyimage response and staysunillustrated.',source_gap='1888mixedentries;233distinctselectedarttypeindexleads;195individualobjectpagesread. FiveHTTP500objectpages and33subsequentunattemptedpages retained as accessholds.15scope/identityholds amongcapturedrecords. Not complete museumartwork coverage.',ready_to_apply=True,applied=False)
    dependencies=[c.ref(RUN/n) for n in ['editorial-source-decisions-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','focused-images-001.json','creator-source-corroboration-001.json','selected-digital-files-001.json','focused-context-001.json.gz','source-access-holds-001.json','visual-references-001.json']]
    m.save(dest,dict(at=m.now(),records=records,holdings=holdings,images=images,review=review,dependencies=dependencies,script_reference=c.ref(Path(__file__).resolve())))
    with (RUN/'reviewed-selection-001.csv').open('x',encoding='utf-8-sig',newline='') as h:
        fields=['number','source_id','title','creator_label','artist_id','first','last','date_display','work_type','source_url'];w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(v['facts'] for v in records)
    print(json.dumps(dict(new=168,images=90,artist_links=65,expected=review['expected_museum_counts'])),flush=True)

if __name__=='__main__':main()
