"""Prepare115review artwork units and64unchanged authentic sourceJPEGs."""
import copy,hashlib,importlib.util,json
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-spathario-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='spathario-production-001'

def build():
    rows=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];by={x['number']:x for x in rows};records=[]
    for u in rows:
        if u['decision']!='proposed_review_artwork':continue
        n=u['number'];parts=[by[k] for k in u['source_numbers']];description=u['description_source'][0] if u['description_source'] else ''
        if n==24:description+='\n\nOne theatrical ensemble: the skeleton on the spit with its operating figure. The separately catalogued operating figure is retained as a component source, not another artwork.'
        if n==149:description+='\n\nThe two museum records show opposite sides of the same cardboard police puppet.'
        if n==17:description+='\n\nThe source title and visible poster identify the wedding of Karagiozis; the description names a different performance.'
        if n in [110,111]:description+='\n\nPhotograph and carved frame catalogued as one assemblage. Photographer and assembly date are unresolved; maker roles remain qualified.'
        if u['first'] is None:description+='\n\nThe actual creation date remains unresolved. The museum date and conflicting context are retained in the source evidence.'
        if n==41:description+='\n\nThe museum title attributes this tree-shaped theatrical prop to China; that origin has not been independently corroborated.'
        description+='\n\nDocumented Spathario Shadow Theatre Museum collection object. Current display has not been established.'
        f=dict(number=n,title=u['title'],creator_label=u['creator_label'],artist_id=None,first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],work_type=u['work_type'],object_form=None,cultural_context=None,medium=u['medium_text'],dimensions_text=None,inventory=None,description_md=description,source_scheme='searchculture-edm',source_id=u['source_id'],source_url=u['source_url'],source_ids=[x['source_id'] for x in parts],source_urls=[x['source_url'] for x in parts],source_numbers=u['source_numbers'],source_facts=copy.deepcopy(parts))
        aid=m.uid(KEY+'/'+u['source_id']);records.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000223-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],editorial_confidence=.96,identity_basis='Individual museum metadata and authentic composition review, with literal maker-role/date evidence and global source/title/image reconciliation.115physicalunits retain117source records; paired views/components reconciled.',limitation='Holding is distinct from currentdisplay or legal ownership. Eight creation dates unresolved. Generic theatre characters are not automatically distinct objects; sourceURLnumbers are not accessionnumbers.'))
    assert len(records)==115 and sum(len(x['facts']['source_ids']) for x in records)==117
    return records,[]

def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();records,holdings=build();target={x['facts']['number']:x for x in records}
    source=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];by={x['number']:x for x in source};obs=m.load(RUN/'production-identity-001.json.gz');existing={}
    assert len(obs['state']['artwork_ids'])==16 and not obs['state']['artist_ids']
    for row in obs['comparisons']:
        hits={x['entity_id'] for x in row['source_hits']}
        if by[row['number']]['decision']=='existing_comparator':assert len(hits)==1;existing[row['source_id']]=next(iter(hits))
        else:assert not hits and not row['inventory_hits'] and not row['title_hits']
    assert len(existing)==16
    rights={x['number']:x for x in m.load(RUN/'focused-context-001.json.gz')['item_rights']};images=[];folder=c.PROOF/'prepared-images';folder.mkdir(parents=True,exist_ok=True)
    for u in source:
        if not u['image_candidate']:continue
        n=u['number'];v=target[n];rc=u['visual_reference'];raw=Path(rc['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and len(raw)==rc['bytes']<=100000
        with Image.open(rc['path']) as im:im.load();assert im.format=='JPEG' and im.size==(rc['width'],rc['height'])
        assert len(rights[n]['matches'])==1 and rights[n]['matches'][0]['text']=='CC BY-NC-SA 4.0' and 'προεπισκόπησης' in rights[n]['matches'][0]['parent_text']
        path=folder/(str(n).zfill(3)+'-'+rc['sha256'][:16]+'.jpg');assert not path.exists();path.write_bytes(raw)
        credit='Σπαθάρειο Μουσείο Θεάτρου Σκιών Δήμου Αμαρουσίου; maker: '+(u['creator_label'] or 'unidentified')+'; museum-supplied preview via SearchCulture.gr'
        images.append(dict(number=n,source_id=u['source_id'],source_url=u['source_url'],source_title=v['facts']['title'],artwork_id=v['artwork_id'],first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],verified_https_source_image_url=rc['url'],image_source='Spathario Shadow Theatre Museum / SearchCulture museum-supplied preview',source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],original_reference=dict(path=rc['path'],sha256=rc['sha256']),prepared_path=str(path),sha256=rc['sha256'],bytes=len(raw),width=rc['width'],height=rc['height'],mime_type='image/jpeg',mode='source_bytes_unchanged',complete_source_frame=True,rights_status='restricted',rights_label='CC BY-NC-SA 4.0',rights_url='http://creativecommons.org/licenses/by-nc-sa/4.0/',rights_evidence_reference=rights[n]['source_receipt'],credit=credit,changes='Source JPEG bytes unchanged. Complete supplied frame retained.',image_identity_confidence_editorial=.98,identity_basis='Exact museum source-record preview, all156frames and sevencontact sheets reviewed. No same-object conflict found for thisselectedimage.',date_policy_passed=True,user_approved_source_policy='Existing Greek museum/artist workflow in docs/ARTLINE_IMAGE_USE.md: selected creations by1955, authentic completeframes,<=100000bytes, actualrights andcredits. CC BY-NC-SA4.0label retained asrestricted; userworkflowapproval is not a copyright-holder licence or public-domain claim.',resolution_limitation='Museum-supplied SearchCulture preview, up to380pxwide or550pxhigh. No higherresolutiondigitalfile link on source object records; native public page returns JavaScript frontend shell. No enlargement, retouching or generateddetail.',view_label='Complete museum-supplied preview, including source margins',prepared=True,ready_to_attach=True,attached=False))
    assert len(images)==64 and len({x['sha256'] for x in images})==64
    dependencies=[c.ref(RUN/x) for x in ['editorial-source-decisions-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','focused-context-001.json.gz','visual-references-001.json','native-context-001.json.gz','selected-source-records-001.json.gz']]
    review=dict(new_records=115,source_records=117,new_images=64,new_artist_links=0,old_preserved=16,numeric_date_new_records=107,unknown_date_new_records=8,crossing_cutoff_new_records=0,expected_museum_counts=dict(linked=131,eligible=123,primary_images=71),existing_source_mapping=existing,source_frames_reviewed=156,contact_sheets_reviewed=7,focused_frames_reviewed=[24,125,149,151],merged_units={24:[24,151],149:[149,125]},scope_holds=22,identity_holds=[124],ready_to_apply=True,applied=False)
    m.save(dest,dict(at=m.now(),records=records,holdings=holdings,images=images,review=review,dependencies=dependencies,script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(review),flush=True)

if __name__=='__main__':main()
