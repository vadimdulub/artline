// Offline, individually reviewed factual mappings. Does not infer creator lives,
// copy museum essays, fetch images, publish, or touch the database.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import assert from 'node:assert/strict';
import {extract} from './research-icons.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const sha=b=>createHash('sha256').update(b).digest('hex');
async function captured(url){
 const file=join(root,'content/imports/icons-primary-20260910',sha(url)+'.html');
 const b=await readFile(file),r=JSON.parse(await readFile(file+'.snapshot.json'));
 assert.equal(r.url,url);assert.equal(r.sha256,sha(b));assert.equal(r.bytes,b.length);
 return {html:b.toString(),receipt:r};
}
async function save(file,data){const b=JSON.stringify(data,null,2)+'\n';await writeFile(file,b,{flag:'wx',mode:0o600});return sha(b);}
// Century envelopes deliberately retain early/late/mid wording without inventing
// a specific year. Explicit half/quarter intervals use their full closed ranges.
const athens=[
 [233,'12th century',1101,1200,'century'],
 [238,'14th century',1301,1400,'century'],
 [230,'15th century',1401,1500,'century'],
 [234,'late 14th century',1301,1400,'century'],
 [232,'14th century',1301,1400,'century'],
 [248,'third quarter of the 14th century',1351,1375,'range','Possibly a Venetian or Greek-Venetian workshop'],
 [64,'early 13th c.',1201,1300,'century','Possibly a Cypriot workshop'],
 [219,'2nd half of 14th c.',1351,1400,'range'],
 [63,'first half of the 14th century',1301,1350,'range','Attributed to a workshop in Constantinople'],
 [33,'14th c.',1301,1400,'century'],
 [235,'14th century',1301,1400,'century'],
 [43,'early 15th c.',1401,1500,'century','Cretan Workshop (catalogue stylistic attribution)'],
 [56,'mid-15th c.',1401,1500,'century','Unidentified Cretan artist'],
 [28,'late 14th c. or early 15th c.',1301,1500,'range','Unidentified artist associated with workshops of Constantinople'],
 [41,'a few years prior to 1501',null,1501,'before','Related stylistically to Nikolaos Tzafouris (catalogue comparison)'],
];
// Reviewed literal production dates, not dates of acquisitions or restorations.
const kremlin=[
 [9635,'Около 1698-1699',1698,1699,'circa_range','Mother of God, from a Deesis tier'],
 [11029,'Конец XVI-начало XVII вв.',1501,1700,'range','Mother of God of the Sign'],
 [9453,'Последняя четверть XIV в.',1376,1400,'range','Mother of God, from the Annunciation Cathedral Deesis tier'],
 [11296,'Конец XVII - начало XVIII в. (?)',1601,1800,'circa_range','Mother of God of Kazan'],
 [10239,'XVII - XIX вв.',1601,1900,'range','Mother of God Enthroned; Mother of God of the Caves'],
 [365504,'Около 1567',1567,1567,'circa','Two-part icon: Raising of Lazarus and Mother of God'],
 [9679,'Середина XIIв.',1101,1200,'century','Mother of God of Tenderness'],
];
async function run(source){
 const greek=source==='athens',name=greek?'Byzantine and Christian Museum':'Moscow Kremlin Museums';
 const src='icons-'+source,host=greek?'www.ebyzantinemuseum.gr':'collectiononline.kreml.ru';
 const website=greek?'https://www.byzantinemuseum.gr':'https://kreml.ru';
 const rightsURL=greek?'https://www.ebyzantinemuseum.gr/?i=bxm.en.terms':'https://collectiononline.kreml.ru/terms-of-use';
 const works=[],painters={};
 for(const [id,literal,first,last,precision,qualifier] of greek?athens:kremlin){
  const url=greek?`https://${host}/?i=bxm.en.exhibit&id=${id}`:`https://${host}/entity/OBJECT/${id}`;
  const {html,receipt}=await captured(url);
  let title,acc,medium='',dimensions='',creator='',place='',origin='',raw;
  let context='Byzantine / post-Byzantine icons (museum collection)';
  let painter='',role='primary',attribution='';
  if(greek){
   const x=extract(html,url);assert.equal(x.description.length,1);
   assert.ok(x.description[0].includes(literal),`Unverified date ${id}`);
   const field=k=>x.facts.find(s=>s.startsWith(k+':'))?.slice(k.length+1).trim()||'';
   assert.equal(field('Collection'),'Icons and Wood-Carvings');
   title=x.headings.at(-1);acc=field('Exhibit Number');dimensions=field('Measurement');origin=field('Origin');
   creator=qualifier||field('Creator')||'Unidentified artist (not named in catalogue)';
   if(id===41) place='Chandax (Herakleion)';
   if(id===63||id===33) place='Constantinople (catalogue attribution)';
   raw={title,accession:acc,date_evidence:literal,creator_label:field('Creator'),origin,dimensions,collection:field('Collection')};
  } else {
   // KAMIS embeds these facts in the allowed HTML object page. No /api/ request:
   // that route is disallowed by this host's robots.txt.
   const state=JSON.parse(html.match(/<script id="my-app-state"[^>]*>(.*?)<\/script>/s)[1].replaceAll('&q;','"').replaceAll('&a;','&').replaceAll('&l;','<').replaceAll('&g;','>'));
   const obj=state['/api/entity/OBJECT/'+id];assert.equal(obj.id,String(id));assert.equal(obj.deleted,false);
   const field=k=>obj.data.find(f=>f.attribute===k)?.value?.join('; ')||'';
   assert.equal(field('date'),literal);
   title=field('object_title');acc=field('record_id');place=field('place');dimensions=field('dimensions');
   assert.match(field('techniq'),/Темпера|темпера/);assert.match(field('material'),/Дерево|дерево/);
   medium=field('material')+'; '+field('techniq');
   creator=field('author')||'Unidentified artist (not named in catalogue)';
   context='Russian icon painting';
   if(id===9453){
    assert.equal(creator,'Автор: Феофан Грек (?)');
    painter='Q319403';painters[painter]=painter;role='attributed_to';attribution=creator;
    context='Icon painting in Moscow; attributed to Theophanes the Greek';
   }
   raw={id:String(id),fields:obj.data.filter(f=>['object_title','date','material','techniq','dimensions','record_id','author','place','publication'].includes(f.attribute))};
  }
  assert.ok(title&&acc,`Missing identity ${id}`);
  const notes=`Individually reviewed icon record. Source date wording retained; broad early/late/mid century dates use a conservative century envelope. ${origin?'Source provenance (not assumed production place): '+origin+'. ':''}Two-sided or multi-part titles describe one source accession, not separate invented objects. Creator wording is catalogue attribution, not an independently authenticated authorship. No current-display claim or museum-highlight designation. No museum essay or photograph reproduced.`;
  works.push({painter,title,institution:src,accession:acc,url,source_object_id:String(id),source_publisher:name,
   date_display:literal,creation_date:{first,last,precision},attribution_role:role,attribution,
   unlinked_creator_label:painter?'':creator,cultural_context:context,object_form:'icon',work_type:'painting',medium,dimensions,creation_place_text:place,
   aliases:greek?[]:[qualifier],notes,source_raw:raw,source_capture:receipt,
   description_md:`${greek?title:qualifier} — ${literal}.\n\n${painter?'Catalogue attribution: Theophanes the Greek (uncertain).':creator+'.'}${origin?' Source provenance: '+origin+'.':''}\n\n${medium?'Medium: '+medium+'. ':''}${dimensions?'Dimensions: '+dimensions+'. ':''}Collection number: ${acc}.\n\n[${name} — object record](${url}). Catalogue facts checked 10 September 2026. Holding is not confirmation of current display. Image permissions are not cleared.`});
 }
 const dir=join(root,'docs/research/icons-20260910',source+'-v1');await mkdir(dir,{recursive:true});
 const inventory={schema_version:2,accessed_on:'2026-09-10',source:src,painters,
  definitions:{[src]:{Slug:greek?'byzantine-christian-museum-athens':'moscow-kremlin-museums',Source:src,Website:website,Host:host}},
  institutions:[{id:src,name,city:greek?'Athens':'Moscow',country:greek?'GR':'RU',data_url:website,data_route:'Selected official HTML catalogue object pages; no bulk API or image requests',rights:'Restricted museum website content; local personal research facts only. Images and authored narratives not reproduced. Public reuse requires a separate review.',rights_url:rightsURL}],works};
 const hash=await save(join(dir,'chunk-001.json'),inventory);
 const pin=await save(join(dir,'manifest.json'),{source:src,chunks:[{file:'chunk-001.json',sha256:hash,works:works.length}]});
 console.log({source:src,works:works.length,pin});
}
assert.ok(['athens','kremlin'].includes(process.argv[2]),'Choose athens or kremlin');
await run(process.argv[2]);
