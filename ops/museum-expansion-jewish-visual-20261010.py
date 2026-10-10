"""Selected object thumbnails for identity review; no delivery or catalogue mutation."""
import collections,hashlib,importlib.util,io,json
from pathlib import Path
import requests
from PIL import Image,ImageOps,ImageDraw,UnidentifiedImageError
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-jewish-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not (RUN/'visual-references-001.json').exists()
    rows=[x for x in m.load(RUN/'selected-source-records-002.json.gz')['rows'] if x['decision'] in ['visual_review_candidate','existing_comparator']];assert len(rows)>130
    selection=RUN/'visual-selection-001.json'
    m.save(selection,dict(at=m.now(),numbers=[x['number'] for x in rows],source_reference=c.ref(RUN/'selected-source-records-002.json.gz'),policy='Bounded capturedmetadata-selected objects and8oldcomparators. Native official museum file selected onlyfor creation through1955; old/later/uncertain objects use lowresolutionpreviewforidentityreview. Six failedsourceURLs held, no retry. No exhaustive13533record imagedownload. Nativefilename tokens reconcile duplicateviews but are notaccessionassignments.'))
    folder=PROOF/'selected-source-images';folder.mkdir(parents=True,exist_ok=True)
    images=[];unavailable=[];stop=None
    for row in rows:
        n=row['number'];rp=RUN/'visual-image-receipts'/(str(n).zfill(3)+'.json');assert not rp.exists()
        if stop:
            unavailable.append(dict(number=n,reason='Not attempted after image-stream access error'));continue
        native=row.get('native',{});use_native=row['decision']=='visual_review_candidate' and n not in [48,76,154,185,192,1053] and 'Dedication' not in native.get('literal_date','');url=native['primary_image_url'] if use_native else row['thumbnail_url'];assert url and url.startswith(('https://artifacts.jewishmuseum.gr/wp-content/uploads/','https://www.searchculture.gr/aggregator/thumbnails/edm-record/'))
        try:response=requests.get(url,timeout=(15,45))
        except requests.RequestException as e:
            value=dict(at=m.now(),number=n,source_id=row['source_id'],url=url,error=type(e).__name__);m.save(rp,value);stop=value;unavailable.append(value);continue
        raw=response.content;value=dict(at=m.now(),number=n,source_id=row['source_id'],url=url,final_url=response.url,status=response.status_code,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),content_type=response.headers.get('Content-Type'))
        suffix='.body'
        if response.status_code!=200:
            value['error']='HTTP'+str(response.status_code);stop=value;unavailable.append(value)
        else:
            try:
                with Image.open(io.BytesIO(raw)) as im:
                    im.load();assert im.format in ['JPEG','PNG','GIF'];value.update(width=im.width,height=im.height,format=im.format);suffix={'JPEG':'.jpg','PNG':'.png','GIF':'.gif'}[im.format]
            except (UnidentifiedImageError,OSError) as e:value.update(image_decode_failed=True,error=type(e).__name__);unavailable.append(value)
        dest=folder/(str(n).zfill(3)+suffix);assert not dest.exists();dest.write_bytes(raw);value['path']=str(dest);m.save(rp,value)
        if 'width' in value:images.append(value)
        if n<=3 or n%20==0:print(json.dumps(dict(attempted=n,thumbnails=len(images),unavailable=len(unavailable))),flush=True)
    sheets=[]
    for start in range(0,len(images),24):
        batch=images[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*260),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            with Image.open(row['path']) as im:thumb=ImageOps.contain(ImageOps.exif_transpose(im).convert('RGB'),(228,227))
            x,y=j%6*240,j//6*260;canvas.paste(thumb,(x+(240-thumb.width)//2,y+(230-thumb.height)//2));draw.text((x+7,y+238),str(row['number'])+' | '+str(row['width'])+'x'+str(row['height']),fill='black')
        dest=PROOF/('contact-'+str(start//24+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=93);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    groups=collections.defaultdict(list)
    for row in images:groups[row['sha256']].append(row['number'])
    duplicates=[dict(sha256=k,numbers=v) for k,v in groups.items() if len(v)>1]
    m.save(RUN/'visual-references-001.json',dict(at=m.now(),rows=images,sheets=sheets,exact_duplicate_groups=duplicates,unavailable=unavailable,access_stop=stop,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),visually_reviewed=False,prepared_delivery_images=0,applied=False))
    print(json.dumps(dict(thumbnails=len(images),sheets=len(sheets),duplicates=duplicates,unavailable=len(unavailable),access_stop=stop)),flush=True)

if __name__=='__main__':main()
