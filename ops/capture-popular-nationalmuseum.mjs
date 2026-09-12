import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';

// Four existing museum objects, no broad scrape or image downloads.
const dir='content/imports/popular-nationalmuseum-20260911';
await mkdir(dir,{recursive:true});
const selected=process.argv[2]==='discovery' ? ['19574','19605','19163','19139','90551','32867'] : ['19486','22374','17587','19182'];
for(const id of selected){
 const url=`https://collection.nationalmuseum.se/en/collection/item/${id}/`;
 const res=await fetch(url,{redirect:'error',signal:AbortSignal.timeout(25000)});
 if(!res.ok)throw new Error(`Source paused HTTP ${res.status}`);
 const bytes=Buffer.from(await res.arrayBuffer());
 if(bytes.length>2000000)throw new Error('Capture size limit');
 const file=`${dir}/${id}.html`;
 await writeFile(file,bytes,{flag:'wx'});
 await writeFile(file+'.snapshot.json',JSON.stringify({url,sha256:createHash('sha256').update(bytes).digest('hex'),retrieved_at:new Date().toISOString()},null,2),{flag:'wx'});
 const data=JSON.parse(bytes.toString().match(/<script id="__NEXT_DATA__" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 await writeFile(`${dir}/${id}.json`,JSON.stringify(data,null,2),{flag:'wx'});
 console.log(id,JSON.stringify(Object.keys(data.props.pageProps)));
 await delay(1200);
}
