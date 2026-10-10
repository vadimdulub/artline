"""Prepare only dated pre1956 candidate source JPEGs; never upload or attach."""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF

def main():
    assert not(RUN/'image-delivery-prepared-001.json').exists()
    decisions=m.load(RUN/'editorial-source-decisions-001.json.gz')['rows'];selected=[x for x in decisions if x['decision']=='proposed_review_artwork' and x['last'] is not None and x['last']<=1955]
    assert len(selected)==39
    target=PROOF/'prepared-images';target.mkdir(parents=True,exist_ok=True);out=[]
    for row in selected:
        image=row['visual_reference'];assert image and row['source_image_reviewed'];assert row['source_fields']['Δικαιώματα']==['http://creativecommons.org/publicdomain/zero/1.0/']
        src=Path(image['path']);raw=src.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest==image['sha256'] and len(raw)<=100000
        dest=target/(str(row['number']).zfill(3)+'-'+digest[:16]+'.jpg');assert not dest.exists();dest.write_bytes(raw)
        with Image.open(dest) as im:assert im.format=='JPEG';width,height=im.size
        out.append(dict(number=row['number'],source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],title=row['title'],date_display=row['date_display'],first=row['first'],last=row['last'],date_precision=row['date_precision'],image_url=image['url'],image_source='SearchCulture / Athens City Museum – Vouros-Eutaxias Foundation',source_image_reference=image,original_reference=dict(path=str(src),sha256=digest),prepared_path=str(dest),sha256=digest,bytes=len(raw),width=width,height=height,mime_type='image/jpeg',rights_label='Public Domain CC0',rights_url='http://creativecommons.org/publicdomain/zero/1.0/',rights_status='public_domain',rights_evidence_reference=c.ref(RUN/'selected-source-records-001.json.gz'),credit='Athens City Museum – Vouros-Eutaxias Foundation; supplied through SearchCulture',changes='Original source thumbnail JPEG retained byte-for-byte; no cropping, repainting, retouching or generated content.',image_identity_confidence_editorial=.98,image_identity_basis='Object-specific source page and source image reviewed in the six contacts. Title, physical form, composition and pictured source labels agree; repeated titles were compared individually. Still pending production counterpart reconciliation.',date_policy_passed=True,user_approved_source_policy='Selected Greek museum/artist images created by1955 under docs/ARTLINE_IMAGE_USE.md. Actual sourceCC0 label preserved; approval does not invent an independently obtained copyright-holder licence.',prepared=True,ready_to_attach=False,attached=False,production_artwork_id=None,quality_limit='Source thumbnail reproduction, generally380pixels wide; native high-resolution file has not been captured.'))
    m.save(RUN/'image-delivery-prepared-001.json',dict(at=m.now(),rows=out,source_review_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),script_reference=c.ref(Path(__file__).resolve()),existing_primary_images_preserved=True,actual_images_uploaded=0,actual_images_attached=0,policy='39 exact sourceJPEGs prepared after metadata/date and visual identity review. Excludes1958/1966, unknown dates, existing artworks and held sources. Global artwork/version reconciliation and pinned plan still required before upload/attachment.'))
    print(json.dumps(dict(prepared=len(out),max_bytes=max(x['bytes'] for x in out),uploaded=0,attached=0)),flush=True)

if __name__=='__main__':main()
