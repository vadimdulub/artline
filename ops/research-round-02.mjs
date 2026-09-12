// Explicit second-pass metadata refresh. No image downloads or database writes.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {setTimeout as pause} from 'node:timers/promises';
const dir='content/imports/painter-review-round02-20260911';
const selected={
  smk:['KMS3192','KMS9107','KMS1433','KMS3827','KMS3879','KMS1845','KMS8654','KMS1093','KMS6699','KMS8605','KMS852','KMS8604','KMS9034','KMS9035','KMS8589','KMS9033'],
  cleveland:['129386','108541'],
};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
await fs.mkdir(dir,{recursive:true,mode:0o700});
for(const [source,ids] of Object.entries(selected)){
  for(const id of ids){
    const url=source==='smk'?`https://api.smk.dk/api/v1/art/?object_number=${id}&lang=en`:`https://openaccess-api.clevelandart.org/api/artworks/${id}`;
    const file=`${dir}/${source}-${id}.json`;let raw,snap;
    try{raw=await fs.readFile(file);snap=JSON.parse(await fs.readFile(file+'.snapshot.json'));if(snap.url!==url||snap.sha256!==hash(raw))throw Error('Changed capture');}
    catch(e){
      if(e.code!=='ENOENT')throw e;
      await pause(1500);
      const r=await fetch(url,{redirect:'manual',signal:AbortSignal.timeout(35000),headers:{'User-Agent':'ArtlineResearch/1.0 (selected museum records; local study)',Accept:'application/json'}});
      if(r.status!==200){console.log(JSON.stringify({source,id,status:r.status,outcome:'source paused; no retries'}));break;}
      if(!r.headers.get('content-type')?.includes('json'))throw Error('Unexpected content type');
      const chunks=[];let size=0;for await(const c of r.body){size+=c.length;if(size>2*1024*1024)throw Error('Metadata byte ceiling');chunks.push(c);}
      raw=Buffer.concat(chunks);JSON.parse(raw);
      snap={url,retrieved_at:new Date().toISOString(),sha256:hash(raw),bytes:raw.length};
      await fs.writeFile(file,raw,{flag:'wx',mode:0o600});await fs.writeFile(file+'.snapshot.json',JSON.stringify(snap,null,2)+'\n',{flag:'wx',mode:0o600});
    }
    const doc=JSON.parse(raw),d=source==='smk'?doc.items?.[0]:doc.data;
    if(!d)throw Error('Missing exact source object');
    console.log(JSON.stringify(source==='smk'?{source,id,count:doc.items.length,object:d.object_number,title:d.titles,dates:d.production_date,notes:d.production_dates_notes,artists:d.production?.map(p=>({name:p.creator,id:p.creator_lref,born:p.creator_date_of_birth,died:p.creator_date_of_death})),medium:d.techniques,dimensions:d.dimensions,inscriptions:d.inscriptions,rights:d.rights,has_image:d.has_image,image:d.image_iiif_id,cropped:d.image_cropped}:{source,id,object:d.id,title:d.title,date:d.creation_date,start:d.creation_date_earliest,end:d.creation_date_latest,artists:d.creators,rights:d.share_license_status,medium:d.technique,dimensions:d.measurements}));
  }
}
