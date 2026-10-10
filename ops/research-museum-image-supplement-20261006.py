#!/usr/bin/env python3
"""Join archived official NGA and Russian Museum images to selected native IDs."""
import collections
import csv
import importlib.util
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('im',Path(__file__).with_name('research-museum-image-sources-20261005e.py'))
im=importlib.util.module_from_spec(spec);spec.loader.exec_module(im);r=im.r;ROOT=im.DEST


def main():
    data=r.load(ROOT/'image-sources-final.json.gz');index=data['by_object_url'];manifest=r.load(ROOT/'snapshots/before/manifest.json')
    selected={};by_nga=collections.defaultdict(list);counts=collections.Counter();receipts=[]
    for entry in manifest['museums']:
        if entry['institution']['slug']not in ['state-russian-museum','national-gallery-of-art']:continue
        for work in r.load(ROOT/entry['path'])['artworks']:
            if work['media']:continue
            selected[im.canonical(work['source_url'])]=work
            for e in work['identifiers']:
                if e['scheme']in ['european-nga-object','nga-object']:by_nga[e['external_id']].append(work)
    path=r.ROOT/'docs/research/museum-gaps-20261005/open-images-01/metadata/nga/nga-published-images.csv'
    rc=r.load(path.with_suffix('.receipt.json'));assert r.sha(path.read_bytes())==rc['sha256']
    rc={**rc,'body_path':str(path.relative_to(r.ROOT)),'body_compression':'none'};receipts.append(rc)
    objects=collections.defaultdict(list)
    with path.open(newline='')as f:
        for row in csv.DictReader(f):
            if row['depictstmsobjectid']in by_nga and row['viewtype']=='primary':objects[row['depictstmsobjectid']].append(row)
    for oid,rows in objects.items():
        choices=[v for v in rows if v['sequence']=='0']if len(rows)>1 else rows
        if len(choices)!=1:counts['nga_ambiguous_primary_held']+=1;continue
        image=choices[0]
        assert image['iiifurl']=='https://api.nga.gov/iiif/'+image['uuid']
        assert image['iiifthumburl'].startswith(image['iiifurl']+'/')
        for work in by_nga[oid]:
            im.add(index,work['source_url'],rc,'direct_catalogue_image',image['iiifthumburl'],
                'National Gallery of Art, Washington',{'source_openaccess':image['openaccess'],'permission_not_inferred':True},
                {'object_id':oid,'image_uuid':image['uuid'],'image_view':'source-designated primary published thumbnail',
                    'image_service':image['iiifurl'],'source_modified':image['modified']})
            counts['nga_exact_object_picture_links']+=1
    base=r.ROOT/'docs/research/russian-painters-20260913/captures'
    for receipt_path in sorted(base.glob('*.json')):
        rc=r.load(receipt_path);path=receipt_path.with_suffix('.html')
        raw=path.read_bytes();assert r.sha(raw)==rc['sha256']
        if '/collections/'not in rc['url']:continue
        rc={**rc,'body_path':str(path.relative_to(r.ROOT)),'body_compression':'none'}
        soup=BeautifulSoup(raw,'html.parser');found=0
        for anchor in soup.select('a[href]'):
            page=urljoin(rc['url'],anchor['href']);key=im.canonical(page)
            if key not in selected or 'rusmuseumvrm.ru/'not in page:continue
            imgs=anchor.select('img[src]')
            if len(imgs)!=1:continue
            image=urljoin(rc['url'],imgs[0]['src'])
            if not image.startswith(page.rsplit('/',1)[0]+'/'):continue
            im.add(index,page,rc,'direct_catalogue_image',image,'State Russian Museum; photographer not credited in listing',
                {'policy_url':'https://rusmuseumvrm.ru/terms/index.php?lang=en','reuse':'Museum source reproduction; separate permission required'},
                {'image_identity_basis':'the exact catalogue-object hyperlink encloses its picture in the official collection listing','image_alt':imgs[0].get('alt'),
                    'historical_capture_date':rc['retrieved_at'],'not_a_fresh_display_observation':True})
            found+=1
        if found:receipts.append(rc);counts['russian_exact_object_picture_links']+=found
    data.update(at=r.now(),by_object_url=index,supplement_counts=dict(counts),supplement_receipts=receipts)
    r.save_gz(ROOT/'image-sources-extended.json.gz',data)
    print('Supplement',dict(counts),'total source pages',len(index),flush=True)


if __name__=='__main__':main()
