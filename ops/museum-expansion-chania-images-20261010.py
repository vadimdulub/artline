"""Prepare complete source-frame JPEGs from reviewed native museum reproductions."""
import hashlib
import importlib.util
import io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-chania-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF

def main():
    decisions=m.load(RUN/'editorial-source-decisions-002.json.gz')['rows'];selected=[row for row in decisions if row['image_candidate']]
    assert len(selected)==188
    dest=PROOF/'prepared-images';dest.mkdir(parents=True,exist_ok=True);rows=[]
    frames={row['number']:row for row in m.load(RUN/'visual-references-001.json')['rows']}
    for row in selected:
        source=row['source_image_reference'];path=Path(source['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        with Image.open(path)as raw:
            raw.load();original_size=raw.size;rgba=raw.convert('RGBA');bg=Image.new('RGBA',raw.size,'white');bg.alpha_composite(rgba);complete=bg.convert('RGB')
        found=False
        for bound in [max(original_size),1280,1100,960,800]:
            image=ImageOps.contain(complete,(bound,bound))
            for quality in [94,90,86,82,78]:
                buf=io.BytesIO();image.save(buf,format='JPEG',quality=quality,optimize=True);output=buf.getvalue()
                if len(output)<=100000:found=True;break
            if found:break
        assert found and len(output)<=100000
        digest=hashlib.sha256(output).hexdigest();sid=row['source_id'].rsplit('-',1)[1];p=dest/(sid+'-'+digest[:16]+'.jpg');assert not p.exists();p.write_bytes(output)
        with Image.open(p)as check:check.load();assert check.size==image.size
        assert abs(image.width/image.height-original_size[0]/original_size[1])<0.002
        rows.append(dict(number=row['number'],primary_number=row['primary_number'],source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],image_url=frames[row['number']]['url'],
            title=row['title'],inventory_literal=row['inventory_literal'],role=row['role'],source_creation_claims=row['native_dating_claims'],date_review=row['date_review'],first=row['first'],last=row['last'],
            original_reference=source,prepared_path=str(p),sha256=digest,bytes=len(output),width=image.width,height=image.height,original_width=original_size[0],original_height=original_size[1],quality=quality,
            mime_type='image/jpeg',complete_source_frame=True,changes='Complete native PNG frame converted to JPEG on white; original transparent PNG preserved. Only proportional scaling and JPEG compression, no crop, retouch, reconstruction or invented detail.',
            image_source='Archaeological Museum of Chania / Ephorate of Antiquities of Chania',credit='Εφορεία Αρχαιοτήτων Χανίων – Αρχαιολογικό Μουσείο Χανίων; amch.gr; metadata via SearchCulture / National Documentation Centre',
            rights_status='restricted',rights_label=row['rights_label'],rights_url=row['rights_url'],rights_links=row['rights_links'],user_approved_source_policy=row['user_image_authorization'],
            image_identity_confidence_editorial=row['image_identity_confidence'],image_date_basis=row['image_date_basis'],view_label=row['image_view_label'],
            ready_to_attach=False,attached=False,production_artwork_id=None,remaining_step='Authenticated live source/accession reconciliation, protected metadata delivery, image storage upload and verified attachment. Preserve existing artwork images and metadata.'))
    sheets=[];font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    for page,start in enumerate(range(0,len(rows),20),1):
        batch=rows[start:start+20];canvas=Image.new('RGB',(1250,1200),'white');draw=ImageDraw.Draw(canvas)
        for j,row in enumerate(batch):
            x,y=(j%5)*250,(j//5)*300;draw.text((x+4,y+4),str(row['number'])+' | '+str(row['bytes'])+' bytes',font=font,fill='black')
            with Image.open(row['prepared_path'])as im:
                thumb=ImageOps.contain(im,(244,266));canvas.paste(thumb,(x+(250-thumb.width)//2,y+28+(266-thumb.height)//2))
        p=PROOF/('prepared-contact-'+str(page)+'.jpg');assert not p.exists();canvas.save(p,quality=92)
        sheets.append(dict(r.v.ref(p),numbers=[row['number']for row in batch]))
    m.save(RUN/'image-policy-review-001.json',dict(at=m.now(),policy_reference=r.v.ref(m.ROOT/'docs/ARTLINE_IMAGE_USE.md'),scope='Selected Greek museum images, creation by1955; literal ancient periods can establish the cutoff without invented numeric years.',
        actual_rights='CC BY-NC-ND3.0GR per item link; BY-SA4.0 site footer kept separate.',independent_licence_claimed=False,
        prepared=188,new_candidate_works_with_images=167,existing_comparator_images=16,extra_cauldron_component_views=5,
        public_image_holds=[dict(number=n,reason='Unknown physical date or only possible ancient dating')for n in sorted(r.UNKNOWN_DATE|{187})]+[dict(number=n,reason=reason)for n,reason in r.IMAGE_HOLDS.items()],
        no_approval_requested='Existing explicit user authorization covers selected images; restrictions are recorded, not silently cleared.',production_uploaded=0,production_attached=0))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=rows,prepared_count=len(rows),sheets=sheets,production_uploaded=0,production_attached=0,
        decisions_reference=r.v.ref(RUN/'editorial-source-decisions-002.json.gz'),policy_reference=r.v.ref(RUN/'image-policy-review-001.json'),script_reference=r.v.ref(Path(__file__).resolve()),
        visual_qa='Prepared contact sheets await separate visual verification; original source frame review is pinned in physical-unit-review-001.json.'))
    print(dict(prepared=len(rows),maximum_bytes=max(row['bytes']for row in rows),resized=sum((row['width'],row['height'])!=(row['original_width'],row['original_height'])for row in rows),contacts=len(sheets),attached=0))

if __name__=='__main__':main()
