#!/usr/bin/env python3
"""Use the existing audited image workflow for the additional 1000-object pass."""
import argparse,importlib.util
import io,struct,zlib,time
from pathlib import Path
from PIL import Image,ImageOps,ImageStat
s=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('switzerland-southern-cone-1000-20261011.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
i=c.module('image_delivery','images-switzerland-southern-cone-20261011.py')
i.m=c.d;i.ARCHIVE=Path.home()/'Library/Application Support/Artline/source-images'/c.OP

def prepare_rietberg(phase):
    d=c.d;selection=d.load(c.RUN/phase/'image-selection.json.gz')['records'];folder=c.RUN/phase/'images';folder.mkdir(parents=True,exist_ok=True)
    base='https://data.stadt-zuerich.ch/dataset/mrz_drenowatz_sammlung/download/mrz_drenowatz_sammlung_bilder.zip'
    hold=c.RUN/phase/'image-access-hold.json';results=[]
    def ranged(start,end):
        assert not hold.exists(),'Open-data image provider is access-held'
        time.sleep(.2)
        response=i.requests.get(base,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,60))
        try:
            if response.status_code in [401,403,429]:d.save(hold,dict(at=d.now(),url=base,status=response.status_code))
            assert response.status_code==206,('Selected byte range required; entire archive not downloaded',response.status_code)
            assert response.headers['Content-Range']==f'bytes {start}-{end}/230074577'
            raw=response.raw.read(end-start+2);assert len(raw)==end-start+1;return raw
        finally:response.close()
    for n,row in enumerate(selection,1):
        r=row['record'];aid=r['artwork_id'];entry=r['image_archive_member'];dest=folder/(aid+'.json')
        if dest.exists():results.append(d.load(dest));continue
        try:
            archive=i.ARCHIVE/phase/(aid+'.source');archive.parent.mkdir(parents=True,exist_ok=True)
            if archive.exists():
                raw=archive.read_bytes();download=d.load(archive.with_suffix('.json'));assert d.sha(raw)==download['sha256']
            else:
                head=ranged(entry['header_offset'],entry['header_offset']+29);parts=struct.unpack('<4s5H3L2H',head)
                assert parts[0]==b'PK\x03\x04' and parts[3]==entry['compression']==8
                length,extra=parts[-2:];start=entry['header_offset']+30
                body=ranged(start,start+length+extra+entry['compressed_size']-1)
                assert body[:length].decode('utf-8')==entry['name']
                raw=zlib.decompress(body[length+extra:],-15)
                assert len(raw)==entry['size'] and zlib.crc32(raw)==entry['crc']
                download=dict(at=d.now(),source_url=base,zip_member=entry,sha256=d.sha(raw),bytes=len(raw),transport='Exact selected ZIP local header and member HTTP byte ranges; whole archive not downloaded')
                archive.write_bytes(raw);d.save(archive.with_suffix('.json'),download)
            picture=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
            assert min(picture.size)>=80 and max(ImageStat.Stat(picture).stddev)>3
            original=picture.size
            for size in [1500,1300,1100,900,750,600]:
                picture.thumbnail((size,size),Image.Resampling.LANCZOS)
                for quality in [88,80,72,64,55,45]:
                    out=io.BytesIO();picture.save(out,'JPEG',quality=quality,optimize=True);content=out.getvalue()
                    if len(content)<=100000:break
                if len(content)<=100000:break
            assert len(content)<=100000
            digest=d.sha(content);path='/assets/artworks/imported/'+c.OP+'/'+phase+'/'+aid+'-'+digest[:12]+'.jpg'
            target=d.ROOT/'apps/web/public'/path.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==content
            else:target.write_bytes(content)
            result=dict(artwork_id=aid,source_record_key=r['key'],source_url=r['image_url'],source_archive=str(archive),source_sha256=download['sha256'],source_size=list(original),path=path,sha256=digest,bytes=len(content),width=picture.width,height=picture.height,retrieved_at=download['at'],media_id=d.uid('media/'+phase+'/'+aid+'/'+digest),license_url=r['image_license_url'],license_label=r['image_rights_label'],prepared=True,zip_member=entry)
            d.save(dest,result)
        except Exception as e:result=dict(artwork_id=aid,source_record_key=r['key'],prepared=False,error=str(e)[:300])
        results.append(result)
        if n%10==0:print('Rietberg selected images',n,'/',len(selection),sum(x['prepared'] for x in results),'prepared',flush=True)
    d.save(c.RUN/phase/'image-preparation.json.gz',dict(at=d.now(),records=results))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','prepare','prepare_rietberg','sheets','upload','attach']);p.add_argument('phase');a=p.parse_args()
    prepare_rietberg(a.phase) if a.action=='prepare_rietberg' else getattr(i,a.action)(a.phase)
