"""Prepare19 already-reviewed source frames under existing Greek source authorization."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from PIL import Image, ImageOps

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-zongolopoulos-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
m,RUN,PROOF=r.m,r.RUN,r.PROOF


def main():
    reviewed=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows']
    selected=[v for v in reviewed if v['decision']=='candidate_primary'and v['last']<=1955]
    assert len(selected)==19
    dest=PROOF/'prepared-images';dest.mkdir(parents=True,exist_ok=True);rows=[]
    for row in selected:
        original=Path(row['image_reference']['path']);raw=original.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==row['image_reference']['sha256']
        with Image.open(original)as im:
            im.load();size=im.size
            if im.format=='JPEG'and len(raw)<=100000:
                output=raw;change='Exact source JPEG bytes retained; no crop, resize, recompression or colour changes.'
            else:
                image=ImageOps.exif_transpose(im).convert('RGB')
                for quality in [94,90,85,80,75,70]:
                    buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=quality,optimize=True);output=buffer.getvalue()
                    if len(output)<=100000:break
                assert len(output)<=100000
                change='Complete source frame converted to JPEG; no cropping or invented detail.'
        digest=hashlib.sha256(output).hexdigest();suffix=row['source_id'].rsplit('-',1)[1]
        path=dest/(suffix+'-'+digest[:16]+'.jpg');assert not path.exists();path.write_bytes(output)
        with Image.open(path)as decoded:assert decoded.size==size
        rows.append(dict(number=row['number'],source_id=row['source_id'],source_url=row['source_url'],title=row['title'],
            creator_label=row['creator_label'],source_creation_date=row['date_display'],first=row['first'],last=row['last'],
            original_reference=row['image_reference'],prepared_path=str(path),sha256=digest,bytes=len(output),width=size[0],height=size[1],
            source_resolution='Provider thumbnail supplied through SearchCulture; not claimed as a high-resolution original.',
            complete_source_frame=True,changes=change,image_source='George Zongolopoulos Foundation via SearchCulture / National Documentation Centre',
            credit='Ίδρυμα Γεωργίου Ζογγολόπουλου; SearchCulture / National Documentation Centre',
            rights_status='restricted',rights_label='CC BY-NC-ND 4.0',rights_links=row['rights_links'],
            user_approved_source_policy='Selected Greek museum/artist source reproductions created by1955; source restrictions preserved separately. No independently obtained licence claimed.',
            image_identity_confidence_editorial=.98,image_identity_basis='Exact image attached to the selected source object page, visually reviewed; ambiguously additional sculpture records are held separately.',
            required_alt_note='Maquette/model'if row['number']in [18,21]else None,
            ready_to_attach=False,attached=False,production_artwork_id=None,
            remaining_step='Fresh live artwork identity, new-record reconciliation and authenticated production delivery. Do not assign assets by title alone.'))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=rows,prepared_count=19,production_uploaded=0,production_attached=0,
        policy_reference=r.ref(RUN/'image-policy-review-001.json'),decisions_reference=r.ref(RUN/'editorial-source-decisions-001.json.gz'),
        script_reference=r.ref(Path(__file__).resolve()),quality_limit='Preserve actual thumbnail resolution and frame. These files do not improve detail beyond the source. All <=100000bytes; no cropping.'))
    print(json.dumps(dict(prepared=19,maximum_bytes=max(v['bytes']for v in rows),exact_original_bytes=sum(v['sha256']==v['original_reference']['sha256']for v in rows),production_attached=0)),flush=True)


if __name__=='__main__':main()
