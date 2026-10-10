"""Prepare selected authentic, complete source frames; preserve museum watermarks."""
import hashlib
import importlib.util
import io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-larissa-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF,ref=r.m,r.RUN,r.PROOF,r.ref

def main():
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];selected=[x for x in decisions if x['image_candidate']];assert len(selected)==205
    frames={x['number']:x for x in m.load(RUN/'visual-references-001.json')['rows']};dest=PROOF/'prepared-images';dest.mkdir(parents=True,exist_ok=True);rows=[]
    for d in selected:
        n=d['number'];src=frames[n];raw=Path(src['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==src['sha256']
        with Image.open(io.BytesIO(raw))as im:im.load();original_size=im.size;source_format=im.format;complete=im.convert('RGB')
        assert source_format=='JPEG'
        if len(raw)<=100000:output=raw;quality=None;size=original_size;mode='source_bytes_unchanged'
        else:
            found=False
            for bound in sorted({max(original_size),800,640,520},reverse=True):
                image=ImageOps.contain(complete,(min(bound,max(original_size)),)*2)
                for quality in [94,90,86,82,78]:
                    buf=io.BytesIO();image.save(buf,format='JPEG',quality=quality,optimize=True);output=buf.getvalue()
                    if len(output)<=100000:found=True;break
                if found:break
            assert found
            size=image.size;mode='jpeg_reencoded_full_frame'
        assert len(output)<=100000
        digest=hashlib.sha256(output).hexdigest();path=dest/(str(n).zfill(3)+'-'+digest[:16]+'.jpg');assert not path.exists();path.write_bytes(output)
        with Image.open(path)as im:im.load();assert im.format=='JPEG'and im.size==size
        assert abs(size[0]/size[1]-original_size[0]/original_size[1])<0.003
        rows.append(dict(number=n,primary_number=d['primary_number'],source_id=d['source_id'],source_url=d['source_url'],native_url=d['native_url'],image_url=src['url'],
            source_title=d['original_title'],candidate_title=d['title'],role=d['role'],source_date_claims=d['source_date_claims'],date_review=d['date_review'],first=d['first'],last=d['last'],
            original_reference=d['source_image_reference'],prepared_path=str(path),sha256=digest,bytes=len(output),width=size[0],height=size[1],original_width=original_size[0],original_height=original_size[1],
            mode=mode,quality=quality,mime_type='image/jpeg',complete_source_frame=True,watermark_preserved=True,
            changes='Original JPEG bytes retained unchanged.'if mode=='source_bytes_unchanged'else'Full frame JPEG compression and proportional scaling only when needed. Museum watermark, paper margins and signatures preserved; no crop, retouch, reconstruction or resolution enhancement.',
            image_source='Municipal Art Gallery of Larissa – G.I. Katsigras Museum / public digital collection',
            credit='Δημοτική Πινακοθήκη Λάρισας – Μουσείο Γ. Ι. Κατσίγρα; larissa-katsigras-gallery.gr; metadata via SearchCulture / National Documentation Centre',
            rights_status='restricted',rights_label=d['rights_label'],rights_url=d['rights_url'],rights_links=d['rights_links'],user_approved_source_policy=d['user_image_authorization'],
            image_identity_confidence_editorial=d['image_identity_confidence'],image_date_basis=d['image_date_basis'],view_label=d['image_view_label'],
            ready_to_attach=False,attached=False,production_artwork_id=None,remaining_step='Fresh production identity reconciliation, protected metadata plan/apply, image storage upload and verified attachment while preserving existing pictures and metadata.'))
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1250,1200),'white');draw=ImageDraw.Draw(canvas)
        for k,d in enumerate(batch):
            x=k%5*250;y=k//5*300;draw.text((x+4,y+4),str(d['number'])+' | '+str(d['bytes'])+' bytes',font=font,fill='black')
            with Image.open(d['prepared_path'])as im:
                thumb=ImageOps.contain(im,(244,266));canvas.paste(thumb,(x+(250-thumb.width)//2,y+28+(266-thumb.height)//2))
        p=PROOF/('prepared-contact-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=92);sheets.append(dict(ref(p),numbers=[d['number']for d in batch]))
    m.save(RUN/'image-policy-review-001.json',dict(at=m.now(),policy_reference=ref(m.ROOT/'docs/ARTLINE_IMAGE_USE.md'),actual_rights='CC BY-NC4.0 per image item link; BY-SA4.0 footer recorded separately.',independent_licence_claimed=False,
        authorization='Existing explicit Greek museum/artist policy supports selected authentic images created by1955 while preserving restricted labels and credits.',
        prepared=205,new_candidate_works_with_images=182,existing_comparator_images=12,extra_album_plate_views=11,
        date_holds=[dict(number=n,reason=decisions[n-1]['image_hold_reason'])for n in sorted(r.DATE_IMAGE_HOLDS)],missing_image_holds=sorted(r.MISSING_IMAGES),
        conflicts_eligible_for_images=sorted(r.CONFLICTS),conflict_basis='All competing literal physical-object date claims precede1955; numeric catalogue dates remain unresolved.',
        museum_watermark_preserved=True,production_uploaded=0,production_attached=0))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=rows,prepared_count=len(rows),sheets=sheets,production_uploaded=0,production_attached=0,
        decisions_reference=ref(RUN/'editorial-source-decisions-001.json.gz'),policy_reference=ref(RUN/'image-policy-review-001.json'),script_reference=ref(Path(__file__).resolve()),
        visual_qa='Prepared sheets require separate review; source frames already reviewed in physical-unit-review-001.json.'))
    print(dict(prepared=len(rows),maximum_bytes=max(x['bytes']for x in rows),unchanged=sum(x['mode']=='source_bytes_unchanged'for x in rows),
        resized=sum((x['width'],x['height'])!=(x['original_width'],x['original_height'])for x in rows),contacts=len(sheets),uploaded=0,attached=0))

if __name__=='__main__':main()
