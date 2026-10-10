"""Final NHM selection:238newreviewworks,176authenticimages,44existingmakerlinks."""
import copy,csv,hashlib,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='nhm-production-001'
SKENE='0b969b0e-ec3e-5c85-8772-d5768b521db8'
AUTHORITY='https://www.getty.edu/vow/ULANFullDisplay?find=&nation=&role=&subjectid=500016543'

def facts(raw):
    u=copy.deepcopy(raw);n=u['number'];a=SKENE if 197<=n<=240 else None
    if n in [210,230]:
        b=next(x for x in m.load(RUN/'bridge-native-comparators-001.json')['rows'] if x['number']==n);block=' '.join(b['blocks'])
        u.update(native_url=b['receipt']['url'],inventory=re.search(r'Αριθμός Ταυτότητας\s*:\s*(.+)$',block)[1],dimensions_text=re.search(r'Διαστάσεις\s*:\s*(.*?)\s*Αριθμός Ταυτότητας',block)[1],image_candidate=True,image_hold_reason=None)
        u['review_notes'].append('Final clarification: native inventories15153-52and15153-7,dimensions0.42x0.21mand0.30x0.24m,and reviewed native/aggregator frames establish separate works.210wide rectangular river view;230oval composition with bridge/mountain repositioned. Preliminary bridge hold resolved, without rewriting preliminary evidence.')
        u['bridge_evidence']=b
    description='\n'.join(u['description_source'])
    if u['first'] is None:description+='\nArtwork creation date is unresolved. Source chronology may describe a sitter, event or prototype and has not been assigned as the creation date of this object.'
    if n in [168,169,170,171]:description+='\nObject pages give1824; the museum painting-collection account dates its four Botsaris ink works1828–1832. Both claims are retained; the conflict needs further review.'
    if n in [30,31,32,33,34,165,174,179,182,183,184,188,189,190,191,192,193,196]:description+='\nThis source describes a copy. The qualified maker label distinguishes the copyist from the prototype artist; no prototype date is assigned to the copy.'
    if n==68:description+='\nThe source questions the attribution; the maker remains qualified.'
    description+='\nDocumented National Historical Museum collection artwork. Current display has not been established.'
    return dict(number=n,source_id=u['source_id'],source_scheme='searchculture-edm',title=u['title'],creator_label=None if a else u['creator_label'],artist_id=a,creator_authority_url=AUTHORITY if a else None,first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],work_type=u['work_type'],object_form=u['object_form'],cultural_context=u['cultural_context'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=u['inventory'],description_md=description.strip(),source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[u['native_url']] if u['native_url'] else [],source_facts=u)

def build():
    records=[]
    for u in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']:
        if u['decision']!='proposed_review_artwork':continue
        f=facts(u);aid=m.uid(KEY+'/'+u['source_id'])
        records.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000042-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis='Exact museum-supplied object record, literal maker/title/date evidence and reviewed complete source composition. Bounded source, full known accession, creator, informative title and image reconciliation found no established existing-work identity. Repeated subjects and copies retain their own object identity; physical album collation remains unknown.',editorial_confidence=.96,limitation='Holding is not current display or a new legal-ownership determination. Unknown creation dates and qualified creator/copy roles remain explicit. One catalogue composition per source record; multiple figures or buildings are not split into extra records.'))
    assert len(records)==238 and len({x['artwork_id'] for x in records})==238
    return records,[]

def artist_link(v):
    f=v['facts'];assert f['artist_id']==SKENE
    return dict(artwork_id=v['artwork_id'],artist_id=SKENE,attribution_role='primary',attribution_note='Museum literal creator Skene James and its1838–1845publication identify the Scottish artist. Getty ULAN500016543 supplies JamesSkeneofRubislaw,1775–1864,and WikidataQ4421861, matching the existing painter. Source labels preserved in citation evidence. '+AUTHORITY,representative_order=None)

def main():
    assert not(RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();target={v['facts']['source_id']:v for v in records};obs=m.load(RUN/'production-identity-001.json.gz');focus=m.load(RUN/'focused-comparators-001.json.gz');existing={}
    for row in obs['comparisons']:
        hits={x['entity_id'] for x in row['source_hits']}
        if row['decision']=='existing_comparator':assert len(hits)==1;existing[row['source_id']]=next(iter(hits))
        else:assert not hits and not row['inventory_hits'] and not row['title_hits']
    assert len(existing)==13 and not focus['bridge_accession_hits']
    artist=focus['artist_state']['artists'][0];assert artist['id']==SKENE and artist['birth_year']==1775 and artist['death_year']==1864
    authority=next(x for x in m.load(RUN/'creator-source-corroboration-001.json')['rows'] if x['url']==AUTHORITY);assert all(x in authority['text'] for x in ['1775-1864','Rubislaw','Q4421861'])
    images=[]
    for raw in m.load(RUN/'image-delivery-prepared-001.json')['rows']:
        im=dict(raw);v=target[im['source_id']];rc=im['source_image_reference'];assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256'] and im['bytes']<=100000 and im['last']<=1955
        im.update(artwork_id=v['artwork_id'],production_artwork_id=v['artwork_id'],native_url=v['facts']['native_urls'][0] if v['facts']['native_urls'] else None,source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],verified_https_source_image_url=im['image_url'],identity_basis='Exact museum-supplied object thumbnail and complete composition reviewed. Source thumbnail, source contacts and all prepared contacts inspected; two bridges resolved with native inventories and matching native images. No existing-work identity found in the bounded source/creator/title/accession checks.',view_label='Complete museum-supplied source thumbnail, including supplied frame or paper margins',ready_to_attach=True,role='new_record');images.append(im)
    assert len(images)==176 and len({x['sha256'] for x in images})==176
    review=dict(at=m.now(),new_records=238,new_existing_links=0,existing_source_mapping=existing,global_bounded_artworks=78,global_citations=185,focused_full_snapshots=78,creator_links_new=44,
      source_visual_review=dict(thumbnails=251,source_contacts=11,prepared_contacts=8,native_bridge_contact_viewed=True),
      counterpart_review='Only13oldNHMsourceidentities found. ExistingJamesSkene records are AberdeenKeratia1841,SwissChristening1821andSwissFuneral1821, different named subjects, dates and inventories from the44NHMviews. NikosGeorgiadis differsAndreasGeorgiadis; Hankey andSchanker are substringfalsepositives forHanke. Hess/Garneray are prototypeartists, not makers of unidentifiedcopies; Garneray duplicateauthorities retained unresolved.',
      physical_unit_review='251completeframes individuallyreviewed. DistinctPitzamanoscompositions/costumestudies andRouxships retained; multiplefigures ononecomposition are not split. Album/sheet/rectoversocollation remainsunknown. TwoAlamana bridges have differentnativeinventories,dimensionsandcompositions. Navarino209/239andKaisariani233/235differinviewpoint andforeground.',
      numeric_date_new_records=176,unknown_date_new_records=62,unresolved_iatridis_dates=[168,169,170,171],
      image_policy='176authentic380pxwidefullsourceframes,restrictedrights,14JPEGsrecompressedunder100000bytes. SourceTIFFroute stoppedafterfiveHTTP500responses; resolutionimprovementgapexplicit. No imagesfor62unresolveddates. SourceBYNCND andaggregatorBYclaimsretained separately.',
      creator_identity_limits='44Skene links only. Othernames retained as objectlabels; unidentified/copyist/qualifiedattributions explicit. No newartistauthority/alias orprototypeprimarylink.',
      source_gap='4727mixedsourceentries,1006paintingfacetrecords,580date-sortedpaintingrecords; onlyfirst240paintingcards and11oldphotocomparators individuallyreviewed. Datesort excludes426undatedpaintingleads. Directory/facet totals are not eligibleobject totals. Fullmuseumcoverage remainsunfinished.',
      preimage_global_reconciliation_passed=True,ready_to_apply=True,applied=False)
    dependencies=[c.ref(RUN/n) for n in ['editorial-source-decisions-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','creator-source-corroboration-001.json','bridge-native-comparators-001.json','bridge-image-references-001.json','image-delivery-prepared-001.json','digital-file-route-hold-001.json']]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,review=review,dependencies=dependencies,script_reference=c.ref(Path(__file__).resolve())))
    fields=['number','source_id','title','creator_label','artist_id','first','last','date_display','inventory','work_type','source_url']
    with (RUN/'reviewed-selection-001.csv').open('x',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(v['facts'] for v in records)
    print(json.dumps(review),flush=True)

if __name__=='__main__':main()
