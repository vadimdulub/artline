"""Prepare140review artworkunits and131 authentic native museumimages."""
import copy,gzip,hashlib,importlib.util,io,json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-jewish-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
KEY='jewish-production-001'

def build():
    rows=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];by={x['number']:x for x in rows};records=[]
    for u in rows:
        if u['decision']!='proposed_review_artwork':continue
        n=u['number'];parts=[by[k] for k in u['source_numbers']];description=(u['description_source'] or [''])[0]
        if len(parts)>1:description+='\n\nMultiple museum source records document this single object; all source identities are retained.'
        if n in [76,154]:description+='\n\nThe actual manufacture or impression date remains unresolved; the source date is retained in the evidence rather than treated as a verified creation year.'
        if n in [1038,1063,1115]:description+='\n\nThe source date records a dedication. Manufacture and any later assembly date remain unresolved.'
        if n==1053:description+='\n\nThe museum website dates this textile to the twentieth century; the aggregator gives the early twentieth century. The broader range is retained pending reconciliation.'
        if n==1116:description+='\n\nA very similar second museum record remains held for separate-object versus repeat-photograph review.'
        description+='\n\nDocumented Jewish Museum of Greece collection object. Current display has not been established.'
        f=dict(number=n,title=u['title'],creator_label=u['creator_label'],artist_id=None,first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],work_type=u['work_type'],object_form=None,cultural_context=None,medium=u['medium_text'],dimensions_text=u['dimensions_text'],inventory=None,description_md=description,source_scheme='searchculture-edm',source_id=u['source_id'],source_url=u['source_url'],source_ids=[x['source_id'] for x in parts],source_urls=[x['source_url'] for x in parts],source_numbers=u['source_numbers'],source_facts=copy.deepcopy(parts))
        aid=m.uid(KEY+'/'+u['source_id']);records.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+u['source_id'].split('000141-')[1],institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=u['source_receipt']['retrieved_at'],editorial_confidence=.96,identity_basis='Individual museum and aggregator metadata, nativefilename identityevidence, authenticcompositionreview and boundedproduction source/title/creator/image reconciliation.140physicalunits retain143sourceentries.',limitation='Holding is distinct from currentdisplay. Fivecreation dates unknown; one20thcenturyrange crosses1970. Filetokens are notassertedaccessions. Existingcreatorhits remain role/identityresearch, notautomaticallymakers oftheheldimpressions.'))
    assert len(records)==140 and sum(len(v['facts']['source_ids']) for v in records)==143
    return records,[]

def prepare_image(raw):
    with Image.open(io.BytesIO(raw)) as source:
        source.load();assert source.format=='JPEG';im=ImageOps.exif_transpose(source).convert('RGB')
    if len(raw)<=100000:return raw,im.width,im.height,'source_bytes_unchanged','Source JPEG bytes unchanged.'
    for limit in [1200,1100,1000,900,800,700,600]:
        sized=ImageOps.contain(im,(limit,limit))
        for quality in [90,85,80,75,70,65]:
            buf=io.BytesIO();sized.save(buf,format='JPEG',quality=quality,optimize=True)
            if len(buf.getvalue())<=100000:return buf.getvalue(),sized.width,sized.height,'proportional_uncropped_jpeg','Complete supplied image proportionally resized and JPEG-compressed; no crop, retouching, enlargement or generated detail.'
    raise AssertionError('Unable to produce bounded JPEG')

def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();records,holdings=build();target={x['facts']['number']:x for x in records}
    source=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];by={x['number']:x for x in source};obs=m.load(RUN/'production-identity-001.json.gz');existing={}
    for row in obs['comparisons']:
        hits={x['entity_id'] for x in row['source_hits']}
        if by[row['number']]['decision']=='existing_comparator':assert len(hits)==1;existing[row['source_id']]=next(iter(hits))
        elif row['number'] in target:assert not hits and not row['inventory_hits'] and not row['title_hits']
    assert len(existing)==8
    images=[];folder=c.PROOF/'prepared-images';folder.mkdir(parents=True,exist_ok=True)
    for u in source:
        if not u['image_candidate']:continue
        n=u['number'];v=target[n];rc=u['visual_reference'];raw=Path(rc['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==rc['sha256'] and rc['url']==u['native']['primary_image_url']
        doc=BeautifulSoup(gzip.decompress((m.ROOT/u['source_receipt']['body_path']).read_bytes()),'html.parser');rights=[dict(label=a.get_text(' ',strip=True),url=a['href'],context=a.parent.get_text(' ',strip=True)) for a in doc.select('a[href]') if 'rightsstatements.org/' in a['href']];assert len(rights)==1 and rights[0]['label']=='In Copyright (InC)'
        result,w,h,mode,changes=prepare_image(raw);digest=hashlib.sha256(result).hexdigest();path=folder/(str(n).zfill(3)+'-'+digest[:16]+'.jpg');assert not path.exists();path.write_bytes(result)
        credit='The Jewish Museum of Greece; '+(u['creator_label'] or 'maker unidentified')+'; official museum collection photograph'
        images.append(dict(number=n,source_id=u['source_id'],source_url=u['source_url'],source_title=v['facts']['title'],artwork_id=v['artwork_id'],first=u['first'],last=u['last'],date_precision=u['date_precision'],date_display=u['date_display'],verified_https_source_image_url=rc['url'],image_source='The Jewish Museum of Greece — official collection image',source_receipt=dict(rc,retrieved_at=rc['at']),image_retrieved_at=rc['at'],original_reference=dict(path=rc['path'],sha256=rc['sha256']),prepared_path=str(path),sha256=digest,bytes=len(result),width=w,height=h,mime_type='image/jpeg',mode=mode,complete_source_frame=True,rights_status='restricted',rights_label='In Copyright (InC)',rights_url=rights[0]['url'],rights_evidence=rights,rights_evidence_reference=u['source_receipt'],native_rights_evidence_reference=u['native']['receipt'],credit=credit,changes=changes,image_identity_confidence_editorial=.98,identity_basis='Exact primary image URL observed in the captured native museum object page; all153sourceframes and9comparison/contact sheets visuallyreviewed. Duplicateviews reconciled, othermuseumobjects excluded.',date_policy_passed=True,user_approved_source_policy='Existing Greek museum/artist workflow in docs/ARTLINE_IMAGE_USE.md: selectedcreations by1955, authentic completeframes,<=100000bytes. ActualInCopyrightstatement retained asrestrictedwithmuseumcredit. Userworkflowapproval is not a copyright-holderlicence orpublic-domainclaim.',resolution_limitation='Officialmuseumfiles atmost1200pxlongedge. Complete suppliedcamera/digitalimage retained; some textiles are folded or shownpartially. Originalsourcefiles archivedseparately.',view_label='Museum photograph; complete supplied image (textiles may be folded or partially shown)',prepared=True,ready_to_attach=True,attached=False))
    assert len(images)==131 and len({x['sha256'] for x in images})==131
    sheets=[]
    for start in range(0,len(images),24):
        batch=images[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*260),'white');draw=ImageDraw.Draw(canvas)
        for j,x in enumerate(batch):
            im=ImageOps.contain(Image.open(x['prepared_path']),(228,227));px,py=j%6*240,j//6*260;canvas.paste(im,(px+(240-im.width)//2,py+(230-im.height)//2));draw.text((px+7,py+238),str(x['number'])+' | '+str(x['bytes'])+'B',fill='black')
        path=c.PROOF/('prepared-contact-'+str(start//24+1)+'.jpg');assert not path.exists();canvas.save(path,quality=93);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    review=dict(new_records=140,source_records=143,new_images=131,new_artist_links=0,old_preserved=8,numeric_date_new_records=134,unknown_date_new_records=5,crossing_cutoff_new_records=1,expected_museum_counts=dict(linked=148,eligible=142,primary_images=139),existing_source_mapping=existing,source_frames_reviewed=153,contact_sheets_reviewed=7,focused_comparison_sheets=2,merged_units={1021:[1021,1023],1038:[1038,1039],1195:[1195,1194]},scope_holds=[1072],identity_holds=[1117],prepared_contact_sheets=sheets,ready_to_apply=True,applied=False)
    m.save(dest,dict(at=m.now(),records=records,holdings=holdings,images=images,review=review,dependencies=[c.ref(RUN/f) for f in ['editorial-source-decisions-001.json.gz','production-identity-001.json.gz','production-identity-citations-001.json.gz','visual-references-001.json','selected-source-records-002.json.gz']],script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(new_records=140,images=131,maxbytes=max(x['bytes'] for x in images),unchanged=sum(x['mode']=='source_bytes_unchanged' for x in images),review=review)),flush=True)

if __name__=='__main__':main()
