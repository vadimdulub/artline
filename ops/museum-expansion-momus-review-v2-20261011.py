"""Review native MOMus objects and prepare selected museum-approved authentic previews."""
import copy,hashlib,importlib.util,io,json,re
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-momus-common-20261011.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
prep=c.module('prep','museum-expansion-jewish-delivery-review-20261010.py')
KEY='momus-production-001'

def build():
    data=m.load(RUN/'candidate-native-records-001.json.gz');records=[]
    for row in data['rows']:
        v=row['native'];n=row['number'];years=row['date_numbers'];first,last=min(years),max(years)
        assert v['momus_museum_s']=='Μουσείο Σύγχρονης Τέχνης' and v['is_public_b'] and first<=1970
        precision='exact' if first==last else 'range';label=row['date_literal']
        typ=v.get('dcterms_type_ss',[]);typelabel='; '.join(typ or v.get('dcterms_type_txt_sort',[]))
        type_map={'Painting work':'painting','Painting':'painting','Drawing':'drawing','Drawing/Sketch':'drawing','Print':'print','Engraving':'print','Engraving work':'print','Sculpture':'sculpture','Photo':'photograph','Photograph':'photograph','Batik':'textile'}
        work_type=next((type_map[t] for t in typ if t in type_map),'unknown')
        medium='; '.join(v.get('dcterms_medium_ss') or v.get('dcterms_medium_txt') or []) or None
        dims=[]
        for field,name in [('height','height'),('width','width'),('length','length'),('depth','depth'),('diameter','diameter')]:
            if v.get('momus_dimension_'+field+'_s'):dims.append(name+': '+v['momus_dimension_'+field+'_s']+' cm')
        maker='; '.join(v.get('dcterms_creator_txt_sort') or v.get('dcterms_creator_ss') or []) or None
        description='Documented MOMus – Museum of Contemporary Art collection object.'
        if typelabel:description+=' Museum object classification: '+typelabel+'.'
        if v.get('momus_collection_txt_sort'):description+=' Collection: '+', '.join(v['momus_collection_txt_sort'])+'.'
        if n in [7725,8005]:description+=' The source gives the broad period 1967–1974; the narrower indexed year is not treated as a verified creation date.'
        if n==17784:description+=' The source describes one multipart work; the primary photograph shows a component.'
        description+=' Current display has not been established.'
        title=v.get('dcterms_title_txt_en') or v['dcterms_title_txt_el']
        f=dict(number=n,title=title,alternate_title=v.get('dcterms_title_txt_el') if v.get('dcterms_title_txt_el')!=title else None,creator_label=maker,artist_id=None,first=first,last=last,date_precision=precision,date_display=label,work_type=work_type,object_form=None,cultural_context=None,medium=medium,dimensions_text='; '.join(dims) or None,inventory=v['momus_uuid_s'],description_md=description,source_scheme='momus-native',source_id=v['id'],source_url=row['native_page_url'],source_ids=[v['id']],source_urls=[row['native_page_url']],source_numbers=[n],source_facts=copy.deepcopy(row))
        aid=m.uid(KEY+'/'+v['id']);records.append(dict(artwork_id=aid,slug='museum-expansion-'+KEY+'-'+str(n),institution_id=c.IID,holding_id=m.uid(KEY+'/holding/'+aid),facts=f,retrieved_at=data['at'],editorial_confidence=.96,identity_basis='Explicit native museum, collection and unique object catalogue identifier; literal creation date and primary image reviewed. Bounded production source/inventory/title/creator comparisons retained.',limitation='Holding does not establish current display. Nine Moralis Angels have separate catalogue identifiers and casting/form differences. Aperghis Figures1/2 have different surfaces, dimensions and identifiers. Multipart works count once. Two source periods cross1970 and remain review records.'))
    assert len(records)==199 and len({v['facts']['inventory'] for v in records})==199
    assert sum(v['facts']['last']>1970 for v in records)==2
    return records,[]

def prepare_image(raw):
    with Image.open(io.BytesIO(raw)) as source:
        source.load();assert source.format=='JPEG';image=ImageOps.exif_transpose(source).convert('RGB');orientation=source.getexif().get(274,1)
    if len(raw)<=100000 and orientation==1:return raw,image.width,image.height,'source_bytes_unchanged','Source JPEG bytes unchanged.'
    for limit in sorted({min(max(image.size),v) for v in [1200,1100,1000,900,800,700,600]},reverse=True):
        sized=image.copy();sized.thumbnail((limit,limit),Image.Resampling.LANCZOS)
        assert sized.width<=image.width and sized.height<=image.height
        for quality in [90,85,80,75,70,65]:
            out=io.BytesIO();sized.save(out,format='JPEG',quality=quality,optimize=True)
            if len(out.getvalue())<=100000:return out.getvalue(),sized.width,sized.height,'proportional_uncropped_jpeg','Complete supplied image JPEG-compressed and reduced only if needed; no crop, enlargement, retouching or generated detail.'
    raise AssertionError('Cannot prepare bounded native preview')

def main():
    dest=RUN/'editorial-reviewed-002.json.gz';assert not dest.exists();records,_=build();visual=m.load(RUN/'visual-references-001.json');by={x['number']:x for x in visual['rows']};images=[];folder=c.PROOF/'prepared-images-v2';folder.mkdir(parents=True,exist_ok=True)
    for v in records:
        f=v['facts'];n=f['number']
        if f['last']>1955:continue
        src=by[n];raw=Path(src['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256']
        result,w,h,mode,changes=prepare_image(raw);digest=hashlib.sha256(result).hexdigest();path=folder/(str(n)+'-'+digest[:16]+'.jpg');assert not path.exists();path.write_bytes(result)
        images.append(dict(number=n,source_id=f['source_id'],source_url=f['source_url'],source_title=f['title'],artwork_id=v['artwork_id'],first=f['first'],last=f['last'],date_precision=f['date_precision'],date_display=f['date_display'],verified_https_source_image_url=src['receipt']['url'],image_source='MOMus – Museum of Contemporary Art — official public collection preview',source_receipt=src['receipt'],image_retrieved_at=src['receipt']['retrieved_at'],original_reference=dict(path=src['path'],sha256=src['sha256']),prepared_path=str(path),sha256=digest,bytes=len(result),width=w,height=h,mime_type='image/jpeg',mode=mode,complete_source_frame=True,rights_status='unknown',rights_label='No image-specific rights label supplied by the native catalogue',rights_url=None,rights_evidence=dict(native_record=f['source_id'],native_fields_with_rights={k:value for k,value in f['source_facts']['native'].items() if any(t in k.lower() for t in ['rights','license','copyright'])},aggregator_collection_label_note='SearchCulture collection previews have their own CC BY-SA4.0 label; that label is not automatically assigned to the different native preview file.'),credit='MOMus – Museum of Contemporary Art; artwork: '+(f['creator_label'] or 'creator unspecified'),changes=changes,image_identity_confidence_editorial=.98,identity_basis='Exact selected native public primary image, at the /large/ URL explicitly used by the museum frontend. All199sourceframes reviewed across7contact sheets; similar sculptures additionally compared.',date_policy_passed=True,user_approved_source_policy='Existing nationwide Greek museum workflow authorizes selected authentic source images for creations through1955. Actual native rights remain unknown; user approval is not an independent licence or public-domain claim. Complete frame <=100000bytes, original preview archived in Library.',resolution_limitation='Official public large preview; no resolution invented. Complete supplied composition and existing frame retained.',view_label='Museum collection image; complete supplied preview',prepared=True,ready_to_attach=True,attached=False))
    assert len(images)==38
    sheets=[]
    for start in range(0,len(images),24):
        batch=images[start:start+24];sheet=Image.new('RGB',(1440,((len(batch)+5)//6)*260),'white');draw=ImageDraw.Draw(sheet)
        for i,x in enumerate(batch):
            with Image.open(x['prepared_path']) as im:thumb=ImageOps.contain(im.convert('RGB'),(228,228))
            px,py=i%6*240,i//6*260;sheet.paste(thumb,(px+(240-thumb.width)//2,py+(230-thumb.height)//2));draw.text((px+5,py+238),str(x['number'])+' '+str(x['bytes'])+'B',fill='black')
        path=c.PROOF/('prepared-contact-v2-'+str(start//24+1)+'.jpg');assert not path.exists();sheet.save(path,quality=92);sheets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    before=m.load(RUN/'production-initial-scope-001.json.gz');old_primary=sum(x['primary_media_id'] is not None for x in before['snapshot']['artworks'])
    review=dict(new_records=199,new_images=38,new_artist_links=0,old_preserved=11,numeric_date_new_records=197,unknown_date_new_records=0,crossing_cutoff_new_records=2,expected_museum_counts=dict(linked=210,eligible=204,primary_images=old_primary+38),source_frames_reviewed=199,contact_sheets_reviewed=7,focused_comparison_sheets=1,prepared_contact_sheets=sheets,ready_to_apply=False,remaining=['Prepared image review','Image hash reconciliation','Pinned plan and backup','Atomic delivery and public verification'])
    m.save(dest,dict(at=m.now(),records=records,holdings=[],images=images,review=review,dependencies=[c.ref(RUN/f) for f in ['candidate-native-records-001.json.gz','production-identity-001.json.gz','visual-references-001.json','visual-similarity-001.json']],script_reference=c.ref(Path(__file__).resolve())))
    print(json.dumps(dict(records=199,images=38,maxbytes=max(x['bytes'] for x in images),review=review)),flush=True)

if __name__=='__main__':main()
