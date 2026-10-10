"""Prepare176 authentic complete source thumbnails; preserve resolution and restrictions."""
import hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-nhm-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not (RUN/'image-delivery-prepared-001.json').exists()
    selected=[x for x in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'] if x['decision']=='proposed_review_artwork' and x['last'] is not None and x['last']<=1955];assert len(selected)==176
    failures=[m.load(x) for x in sorted((RUN/'captures').glob('file-page-*-001.json'))];assert len(failures)==5 and all(x['status']==500 for x in failures)
    m.save(RUN/'digital-file-route-hold-001.json',dict(at=m.now(),failures=failures,attempted_numbers=[22,37,38,39,40],unattempted_numbers=[x['number'] for x in selected if x['number'] not in [7,22,37,38,39,40]],prior_successful_wrapper=7,script_reference=c.ref(Path(__file__).with_name('museum-expansion-nhm-digital-files-20261010.py')),policy='Five selected digital-file wrapper requests returnedHTTP500; route stopped, no retries or alternate blob discovery. No sourceTIFF downloaded. Existing251 authentic source thumbnails already captured and reviewed. Deliver176 dated complete thumbnail frames with explicit resolution limitation, including two visually resolved bridge works. Higherresolution originals remain an improvement gap.'))
    folder=PROOF/'prepared-images';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for row in selected:
        n=row['number'];src=row['visual_reference'];raw=Path(src['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256'] and row['source_image_reviewed']
        with Image.open(io.BytesIO(raw)) as im:im.load();assert im.format=='JPEG';original=im.size;full=ImageOps.exif_transpose(im).convert('RGB')
        quality=None;mode='source_bytes_unchanged';out=raw;size=original
        if len(raw)>100000:
            mode='jpeg_reencoded_full_frame';found=False
            for quality in [94,90,86,82,78]:
                buf=io.BytesIO();full.save(buf,format='JPEG',quality=quality,optimize=True);out=buf.getvalue()
                if len(out)<=100000:found=True;break
            assert found;size=full.size
        assert len(out)<=100000 and size==original
        digest=hashlib.sha256(out).hexdigest();dest=folder/(str(n).zfill(3)+'-'+digest[:16]+'.jpg');assert not dest.exists();dest.write_bytes(out)
        rows.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=row['title'],source_title=row['title'],first=row['first'],last=row['last'],date_precision=row['date_precision'],date_display=row['date_display'],image_url=src['url'],image_source='National Historical Museum / SearchCulture museum-supplied thumbnail',source_image_reference=src,original_reference=dict(path=src['path'],sha256=src['sha256']),prepared_path=str(dest),sha256=digest,bytes=len(out),width=size[0],height=size[1],original_width=original[0],original_height=original[1],mime_type='image/jpeg',mode=mode,quality=quality,complete_source_frame=True,rights_status='restricted',rights_label='CC BY-NC-ND 4.0 (museum item rights; aggregator badge differs)',rights_url='https://creativecommons.org/licenses/by-nc-nd/4.0/deed.el',rights_evidence_reference=row['source_receipt'],aggregator_rights_label='CC BY 4.0',aggregator_rights_url='http://creativecommons.org/licenses/by/4.0/',rights_conflict='Museum-supplied item rights state CC BY-NC-ND4.0; aggregator badge and inspected digital-file wrapper state CC BY4.0. Preserve both; classify restricted. Site-footer BY-SA is not an object licence.',credit='Εθνικό Ιστορικό Μουσείο — Ιστορική & Εθνολογική Εταιρεία της Ελλάδος; artist: '+(row['creator_label'] or 'unidentified')+'; museum-supplied reproduction via SearchCulture.gr',changes='Source thumbnail JPEG bytes retained unchanged.' if mode=='source_bytes_unchanged' else 'Complete source thumbnail JPEG recompressed without cropping, resizing, retouching or generated content. Paper edges, signatures, frames and existing markings retained.',image_identity_confidence_editorial=.98,image_identity_basis='Exact museum-supplied object record and reviewed complete thumbnail composition. Two bridge identities additionally supported by different native inventory numbers, dimensions and matching native reproductions.',date_policy_passed=True,user_approved_source_policy='Explicit Greek museum/artist image workflow for selected works created by1955 in docs/ARTLINE_IMAGE_USE.md. User collection/display approval is separate from actual rights labels and does not claim an independent copyright-holder licence.',resolution_limitation='Authentic source thumbnail,380pxwide; fullresolution TIFF not retrieved because selected file-wrapper requests returnedHTTP500. No upscale or invented detail.',prepared=True,ready_to_attach=False,attached=False,production_artwork_id=None))
    sheets=[]
    for start in range(0,len(rows),24):
        batch=rows[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*240),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            with Image.open(row['prepared_path']) as im:thumb=ImageOps.contain(im,(228,207))
            x=j%6*240;y=j//6*240;canvas.paste(thumb,(x+(240-thumb.width)//2,y+(210-thumb.height)//2));draw.text((x+5,y+216),str(row['number'])+' | '+str(row['bytes'])+' B',fill='black')
        dest=PROOF/('prepared-contact-'+str(start//24+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=93);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=rows,sheets=sheets,source_review_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),existing_primary_images_preserved=True,uploaded=0,attached=0,visual_qa='Prepared contact sheets require separate inspection. Source251thumbnails and11contacts already viewed; two native bridge comparisons viewed and resolved.'))
    print(json.dumps(dict(prepared=len(rows),max_bytes=max(x['bytes'] for x in rows),contacts=len(sheets),recompressed=sum(x['mode']!='source_bytes_unchanged' for x in rows),uploaded=0)),flush=True)

if __name__=='__main__':main()
