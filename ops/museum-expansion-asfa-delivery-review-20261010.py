"""Reviewed ASFA delivery selection:248 new works,2 existing links,142 images."""
import collections,csv,hashlib,importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='asfa-production-001'
EXISTING={17:'6f4e418a-e650-53ba-b654-c0f332ca67e6',24:'a91e096f-7c1b-5313-b336-e3f4dd549d6b'}
CREATORS={'Γιάννης Μόραλης':('3b5fbd54-cae2-5e50-a0b3-f70eabf743cd','https://www.searchculture.gr/aggregator/persons/-659804591'),'Μαθιόπουλος Παύλος':('951faed2-0922-532a-85cc-305f9403a4e0','https://www.searchculture.gr/aggregator/persons/-279158142'),'Νικολάου Νίκος':('f6fbb79f-68f7-5abc-8541-f33ae7d091a0','https://www.searchculture.gr/aggregator/persons/-857081719')}

def facts(u):
    n=u['number'];a=CREATORS.get(u['creator_source_literals'][0]);description='\n'.join(u['description_source'])
    if u['creator_label'] is None:description+='\nCreator unidentified in the source; the label Ορφανό is not a personal name.'
    if n in [131,132,133,140,141]:description+='\nSpecific impression date unresolved. The source gives '+u['source_date_literal']+'; the published Ten White Lekythoi portfolio is dated 1956. The record does not identify an early proof. This is a modern print, not the depicted ancient vessel.'
    if n==198:description+='\nThe source explicitly describes a copy dated 1958. Theofilos is the prototype artist; the copyist is unidentified.'
    if n==199:description+='\nDate and attribution unresolved: the source gives 1958 and names Theofilos, who died in 1934. The copy, transfer or original status of this object needs further evidence.'
    if n in [97,98]:description+='\nThe source inventory labels 00752 and 00752_ZOG727 overlap in numeric stem but refer to different pictured portraits; the complete labels are retained.'
    if n in [134,137,138,139,171,172]:description+='\nOne separately inventoried print impression. Other impressions of the composition are recorded separately where the physical sheets, signatures and condition differ.'
    if n>=196 and n!=258:description+='\nThe catalogue entry concerns this museum artwork or study; a depicted church, furnishing or historic subject is not itself a museum holding.'
    description+='\nDocumented Athens School of Fine Arts Gallery collection object. Current display has not been established.'
    return dict(number=n,source_id=u['source_id'],source_scheme='searchculture-edm',title=u['title'],creator_label=None if a else u['creator_label'],artist_id=a[0] if a else None,creator_authority_url=a[1] if a else None,first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],work_type=u['work_type'],object_form=u['object_form'],cultural_context=u['cultural_context'],medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=u['inventory'],description_md=description.strip(),source_url=u['source_url'],source_ids=[u['source_id']],source_urls=[u['source_url']],native_urls=[u['native_url']],source_facts=u)

def build():
    records=[];holdings=[]
    for u in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']:
        if u['decision']!='proposed_review_artwork':continue
        f=facts(u);n=u['number'];aid=EXISTING.get(n,m.uid(KEY+'/'+u['source_id']))
        basis='Exact museum-supplied and native object pages, full inventory, literal creator/title/date evidence and reviewed full source composition. '
        if n==17:basis+='Same sitter pose, clothing folds, flower arrangement and signed1924composition as the existing WikiArt JohnPolemis portrait. Preserve existing primary image and all original metadata; native full-frame view may be an alternate.'
        elif n==24:basis+='Same seated male model, linked hands, torso outline and background as existing WikiArt DrawingofaMan. Native source1930 versus existing WikiArt1929 date conflict retained in evidence; do not rewrite the existing date or title.'
        else:basis+='Bounded source, full inventory, creator, title and image reconciliation found no established existing physical-work identity; classroom studies and individual print impressions distinguished.'
        v=dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000187-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],identity_basis=basis,editorial_confidence=.98 if n in EXISTING else .96,limitation='Holding is not current display or a new legal-ownership determination. Unknown creation dates, source attribution and role uncertainty remain explicit. Original source values and complete inventories remain evidence.')
        (holdings if n in EXISTING else records).append(v)
    assert len(records)==248 and len(holdings)==2 and len({x['artwork_id'] for x in records+holdings})==250
    return records,holdings

def artist_link(v):
    f=v['facts'];assert f['artist_id']
    return dict(artwork_id=v['artwork_id'],artist_id=f['artist_id'],attribution_role='primary',attribution_note='Museum creator field and the linked person authority identify the existing painter with the same lifespan. Original Greek labels are preserved in citation evidence. '+f['creator_authority_url'],representative_order=None)

def main():
    assert not (RUN/'editorial-reviewed-001.json.gz').exists();records,holdings=build();units=records+holdings;target={x['facts']['source_id']:x for x in units};obs=m.load(RUN/'production-identity-001.json.gz');focus=m.load(RUN/'focused-comparators-001.json.gz');old={x['id']:x for x in focus['snapshot']['artworks']};authorities=m.load(RUN/'creator-source-corroboration-001.json')['rows'];artist_state=focus['artist_state'];existing={}
    for row in obs['comparisons']:
        hits={x['entity_id'] for x in row['source_hits']}
        if row['decision']=='existing_comparator':assert len(hits)==1;existing[row['source_id']]=next(iter(hits))
        else:assert not hits and not row['inventory_hits']
    assert len(existing)==8
    for label,(aid,url) in CREATORS.items():
        artist=next(x for x in artist_state['artists'] if x['id']==aid);authority=next(x for x in authorities if x['url']==url);assert str(artist['birth_year'])+'-'+str(artist['death_year']) in authority['title']
    for n,aid in EXISTING.items():assert old[aid]['current_institution_id'] is None
    assert old[EXISTING[17]]['date_display']=='1924' and old[EXISTING[24]]['date_display']=='1929'
    images=[]
    for raw in m.load(RUN/'image-delivery-prepared-001.json')['rows']:
        im=dict(raw);v=target[im['source_id']];rc=im['source_image_reference'];assert hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest()==im['sha256'] and im['bytes']<=100000 and im['last']<=1955 and im['rights_status']=='restricted'
        im.update(artwork_id=v['artwork_id'],production_artwork_id=v['artwork_id'],source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],verified_https_source_image_url=im['image_url'],identity_basis='Exact native object image, inventory and composition reviewed, with original/thumbnail and prepared contact checks. Global counterpart reconciliation maps17and24to existing records; all other selected images belong to distinct new museum works.',view_label='Complete native source photograph, including supplied frame or paper margins',ready_to_attach=True,role='existing_record' if v in holdings else 'new_record');images.append(im)
    assert len(images)==142 and len({x['sha256'] for x in images})==142
    review=dict(at=m.now(),new_records=248,new_existing_links=2,existing_links=EXISTING,existing_source_mapping=existing,global_bounded_artworks=197,global_citations=278,focused_full_snapshots=197,creator_links_new=10,
      counterpart_review=dict(contact_viewed=True,frames=15,existing_images=9,matched_numbers=[17,24],distinct_comparators=[1,3,4,5,6,7,8],basis='C2 matches17 in pose, suit folds, flower sprig and1924signature. C9 matches24 in clasped hands, seated body, head and shading;1929/1930 discrepancy is not a different work. C1 is an older nude man in profile with arms behind him, unlike7 frontal bearded man gesturing. C3–C6 are different female nudes, unlike58 raised-arm frontal study. C7 clothed boy differs33 male life study. C8 broad Athens panorama differs49 narrow path and cypresses.'),
      title_review='Existing generic male/female studies include the eight original ASFA objects, works by other makers and the separately reviewed Moralis/Mathiopoulos comparisons. Existing13Dormition title hits are older icons or other makers, unlike source197modern1957study byM.Spentzas. Existing ceiling andSaintDimitrios title hits identify older different makers/objects. Similar titles alone did not establish identity.',
      physical_unit_review='Three print pairs134/137,138/139,171/172are separate impressions, supported by distinct complete inventory labels, different pencil signatures, inking, abrasions/foxing and margins.97/98different portraits share only the inventory stem00752, not the full inventory or composition. Copies after older religious/historical models retain their own source dates and maker labels.',
      unresolved_dates=[131,132,133,140,141,199],qualified_copy_number=198,creator_identity_limits='Only Moralis,Mathiopoulos,Nikolaou identities verified against creator-field authority pages. New links10; existing two links preserved. LuisdeMorales aliasMoralis and OleksaNovakivskyi substring hit are unrelated. Other creator spellings remain unlinked labels; no biographies created.',
      image_qa=dict(thumbnails=258,thumbnail_contacts=11,native_originals=148,native_contacts=7,prepared_images=142,prepared_contacts=6,all_contacts_viewed=True,complete_frames=True,max_bytes=max(x['bytes'] for x in images),primary_images_expected=141,alternate_images_expected=1),rights='Native CC BY-NC-ND4.0 restrictions override a less restrictive aggregatorBY-SA4label for delivery classification. Both source claims retained; user Greek image workflow approval recorded separately without asserting copyright-holder permission.',
      limitations=['Only270index cards plus one existing off-index object reviewed;3741of4012source entries remain outside this selection. Thirteen documents/books excluded before object capture.','Six proposed numeric creation dates remain null; holdings do not establish current display.','Bounded197record reconciliation and query plans are not an exhaustive globalduplicate guarantee or10million-row performance proof.'])
    m.save(RUN/'identity-review-001.json',review)
    deps=[c.ref(RUN/name) for name in ['baseline-verification-001.json','production-initial-scope-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-comparators-001.json.gz','creator-source-corroboration-001.json','counterpart-images-001.json','identity-review-001.json','editorial-source-decisions-001.json.gz','image-delivery-prepared-001.json']]
    m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),records=records,holdings=holdings,images=images,existing_source_mapping=existing,dependencies=deps,expected_counts=dict(linked=258,eligible=251),new_work_types=dict(collections.Counter(x['facts']['work_type'] for x in records)),new_unknown_numeric_dates=6,new_numeric_dated=242,new_images=142,new_primary_images=141,new_alternate_images=1,new_artist_links=10,applied=False,source_identifier_policy='One immutable SearchCulture identifier for each new physical work; source identifiers for existing matches remain citations unless a separately reviewed identifier update is explicitly included. Full inventory suffixes remain intact.'))
    with (RUN/'reviewed-delivery-ledger-001.csv').open('x',encoding='utf-8-sig',newline='') as out:
        fields=['number','artwork_id','action','source_id','title','creator_label','artist_id','first','last','date_display','work_type','inventory','source_url'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for v in units:w.writerow({k:v['artwork_id'] if k=='artwork_id' else 'existing_holding' if k=='action' and v in holdings else 'new_record' if k=='action' else v['facts'][k] for k in fields})
    print(json.dumps(dict(new=248,existing_links=2,images=142,new_primary=141,new_alternate=1,artist_links=10,expected_catalogue=258,expected_numeric=251)),flush=True)

if __name__=='__main__':main()
