"""Prepare142 reviewed native full frames, preserving restrictions and source evidence."""
import hashlib,importlib.util,io,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-asfa-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not (RUN/'image-delivery-prepared-001.json').exists()
    selected=[x for x in m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'] if x['image_candidate']];assert len(selected)==142
    folder=PROOF/'prepared-images';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for row in selected:
        n=row['number'];src=row['source_image_reference'];raw=Path(src['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256'] and row['last']<=1955 and row['source_image_reviewed']
        with Image.open(io.BytesIO(raw)) as im:im.load();assert im.format=='JPEG';original=im.size;full=ImageOps.exif_transpose(im).convert('RGB')
        quality=None;mode='source_bytes_unchanged';out=raw;size=original
        if len(raw)>100000:
            found=False;mode='jpeg_reencoded_full_frame'
            for bound in sorted({max(original),1000,800,640,520},reverse=True):
                im=ImageOps.contain(full,(min(bound,max(original)),)*2)
                for quality in [94,90,86,82,78]:
                    buf=io.BytesIO();im.save(buf,format='JPEG',quality=quality,optimize=True);out=buf.getvalue()
                    if len(out)<=100000:found=True;break
                if found:break
            assert found;size=im.size
        assert len(out)<=100000 and abs(size[0]/size[1]-full.width/full.height)<.003
        digest=hashlib.sha256(out).hexdigest();dest=folder/(str(n).zfill(3)+'-'+digest[:16]+'.jpg');assert not dest.exists();dest.write_bytes(out)
        rows.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=row['title'],source_title=row['title'],first=row['first'],last=row['last'],date_precision=row['date_precision'],date_display=row['date_display'],image_url=src['url'],image_source='Athens School of Fine Arts Gallery / native digital collection',source_image_reference=src,original_reference=dict(path=src['path'],sha256=src['sha256']),prepared_path=str(dest),sha256=digest,bytes=len(out),width=size[0],height=size[1],original_width=original[0],original_height=original[1],mime_type='image/jpeg',mode=mode,quality=quality,complete_source_frame=True,rights_status='restricted',rights_label='CC BY-NC-ND 4.0; native terms limit use to personal/academic purposes',rights_url='https://creativecommons.org/licenses/by-nc-nd/4.0/',rights_evidence_reference=c.ref(RUN/'captures/native-terms-001.json'),aggregator_rights_label='CC BY-SA 4.0',aggregator_rights_url='http://creativecommons.org/licenses/by-sa/4.0/',rights_conflict='Native terms are more restrictive than the aggregator item label; preserve both and classify the delivered native image as restricted.',credit='Ανώτατη Σχολή Καλών Τεχνών — Ψηφιακή Συλλογή της Πινακοθήκης της ΑΣΚΤ; artist: '+(row['creator_label'] or 'unidentified')+'; exhibition.asktdigital.gr',changes='Source JPEG bytes retained unchanged.' if mode=='source_bytes_unchanged' else 'Complete source frame proportionally resized and JPEG compressed. Paper edges, signatures, frames and photographed markings retained; no crop, retouch, reconstruction or generated content.',image_identity_confidence_editorial=.98,image_identity_basis='Exact native exhibit page, inventory, literal creator/title/date and complete original frame reviewed against the museum-supplied aggregator record. Repeated class-study subjects and separate print impressions distinguished; global counterpart reconciliation pending.',date_policy_passed=True,user_approved_source_policy='Explicit Greek museum/artist image workflow for selected works created by1955 in docs/ARTLINE_IMAGE_USE.md. User collection/display approval is separate from actual CC BY-NC-ND restrictions and does not claim an independent copyright-holder licence.',prepared=True,ready_to_attach=False,attached=False,production_artwork_id=None))
    sheets=[]
    for start in range(0,len(rows),24):
        batch=rows[start:start+24];canvas=Image.new('RGB',(1440,((len(batch)+5)//6)*240),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            with Image.open(row['prepared_path']) as im:thumb=ImageOps.contain(im,(228,207))
            x=j%6*240;y=j//6*240;canvas.paste(thumb,(x+(240-thumb.width)//2,y+(210-thumb.height)//2));draw.text((x+5,y+216),str(row['number'])+' | '+str(row['bytes'])+' B',fill='black')
        dest=PROOF/('prepared-contact-'+str(start//24+1)+'.jpg');assert not dest.exists();canvas.save(dest,quality=93);sheets.append(dict(path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),numbers=[x['number'] for x in batch]))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=rows,sheets=sheets,source_review_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),existing_primary_images_preserved=True,uploaded=0,attached=0,visual_qa='Prepared contacts require separate inspection before delivery. Native originals and source contacts already reviewed.'))
    print(json.dumps(dict(prepared=len(rows),max_bytes=max(x['bytes'] for x in rows),contacts=len(sheets),uploaded=0)),flush=True)

if __name__=='__main__':main()
