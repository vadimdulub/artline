// Dated source-access audit and read-only museum coverage export. No artwork
// writes, external writes, redirects, credentials or arbitrary directory crawling.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {lookup} from 'node:dns/promises';
import {isIP} from 'node:net';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../..');
const input=path.join(root,'docs/research/us-europe-coverage/assembled/museum-directory.json');
const records=JSON.parse(fs.readFileSync(input,'utf8'));
assert.equal(records.length,5869);
const sources=records.filter(r=>r.source==='supplied-registry');assert.equal(sources.length,111);
const save=(file,value)=>fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n',{flag:'wx',mode:0o600});
const sql=q=>JSON.parse(execFileSync('psql',['postgres://localhost/artline?sslmode=disable','-X','-At','-v','ON_ERROR_STOP=1','-c',q],{encoding:'utf8',maxBuffer:12<<20}));

function publicAddress(a){
 if(a.includes(':'))return !/^(::|fc|fd|fe[89ab])/i.test(a);
 const p=a.split('.').map(Number);
 return !([0,10,127,169].includes(p[0])||p[0]>=224||p[0]===192&&p[1]===168||p[0]===172&&p[1]>=16&&p[1]<=31||p[0]===100&&p[1]>=64&&p[1]<=127);
}

if(process.argv[2]==='probe'){
 const dir=path.join(here,'access');fs.mkdirSync(dir,{recursive:true});
 let next=0;
 await Promise.all(Array.from({length:4},async()=>{
  while(next<sources.length){
   const row=sources[next++],file=path.join(dir,row.record_id+'.json');
   if(fs.existsSync(file))continue;
   const address=row.raw.collection_url||row.raw.official_website;
   const result={source_id:row.record_id,url:address,method:'HEAD',checked_at:new Date().toISOString(),status:null,decision:'not_checked',note:'Reachability only: not a terms, object coverage, image-rights or current-operation verification.'};
   try{
    const u=new URL(address);
    assert(u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&!isIP(u.hostname)&&u.hostname.includes('.'),'Unapproved URL form');
    const addresses=await lookup(u.hostname,{all:true});assert(addresses.length&&addresses.every(a=>publicAddress(a.address)),'Non-public DNS address');
    const res=await fetch(u,{method:'HEAD',redirect:'manual',headers:{'User-Agent':'ArtlineMuseumResearch/1.0 (metadata source-access audit)'},signal:AbortSignal.timeout(18000)});
    result.status=res.status;
    result.decision=res.status>=200&&res.status<300?'reachable_catalogue_review_needed':res.status>=300&&res.status<400?'redirect_review':res.status===401||res.status===403||res.status===429?'access_restricted_no_retry':res.status===405?'head_unsupported':'route_unavailable';
    if(res.status>=300&&res.status<400)result.redirect=res.headers.get('location');
    if(res.body)await res.body.cancel();
   }catch(e){result.decision='unavailable_or_review_required';result.error=e.message;}
   save(file,result);console.log(row.record_id,result.status,result.decision);
   await new Promise(resolve=>setTimeout(resolve,400));
  }
 }));
 const all=sources.map(r=>JSON.parse(fs.readFileSync(path.join(dir,r.record_id+'.json'),'utf8')));
 save(path.join(here,'access-summary.json'),{checked_at:new Date().toISOString(),sources:all.length,states:all.reduce((a,r)=>(a[r.decision]=(a[r.decision]||0)+1,a),{}),records:all});
}else if(process.argv[2]==='export'){
 const phase=process.argv[3];assert(['before','after'].includes(phase));
 const institutions=sql(`SELECT jsonb_agg(x ORDER BY country,name,slug) FROM (SELECT i.id,i.slug,i.name,i.wikidata_id,i.website_url,p.country_code AS country,p.name AS city,count(a.id) AS works FROM institutions i LEFT JOIN places p ON p.id=i.place_id LEFT JOIN artworks a ON a.current_institution_id=i.id GROUP BY i.id,p.country_code,p.name) x`);
 const byQID=new Map(institutions.filter(i=>i.wikidata_id).map(i=>[i.wikidata_id,i]));
 const bySlug=new Map(institutions.map(i=>[i.slug,i]));
 const sourceAliases={met_museum:'the-met',cleveland_museum:'cleveland-museum-of-art',artic:'art-institute-of-chicago',nga_washington:'national-gallery-of-art',prado:'museo-del-prado',louvre:'musee-du-louvre',musee_orsay:'musee-orsay',pinacoteca_brera:'pinacoteca-di-brera',national_gallery_london:'national-gallery-london',rijksmuseum:'rijksmuseum',van_gogh_museum:'van-gogh-museum',staedel:'staedel-museum',thyssen_bornemisza:'museo-thyssen-bornemisza'};
 const rows=records.map(r=>{
  let inst=r.source==='wikidata'?byQID.get(r.record_id):r.source==='museofile'?bySlug.get('joconde-'+r.record_id.toLowerCase()):bySlug.get(sourceAliases[r.record_id]);
  const probe=path.join(here,'access',r.record_id+'.json');
  const access=r.source==='supplied-registry'&&fs.existsSync(probe)?JSON.parse(fs.readFileSync(probe,'utf8')):null;
  return {source:r.source,source_id:r.record_id,name:r.name,country:r.country,kind:r.kind,source_url:r.source_url,discovery_decision:r.decision,linked_institution:inst?.slug||'',imported_works:inst?.works??null,access_decision:access?.decision||'not_probed_directory_candidate',access_checked_at:access?.checked_at||'',catalogue_url:r.raw.collection_url||'',next_action:inst?'Expand remaining eligible records; reconcile exclusions and refresh evidence':r.kind==='catalogue_source'?'Review access/terms and build source-specific adapter':'Verify official identity and object-level catalogue before import'};
 });
 const linked=new Set(rows.map(r=>r.linked_institution).filter(Boolean));
 for(const i of institutions.filter(i=>!linked.has(i.slug)))rows.push({source:'local-catalogue',source_id:i.id,name:i.name,country:i.country,kind:'represented_institution_or_collection',source_url:i.website_url,discovery_decision:'sourced_local_catalogue',linked_institution:i.slug,imported_works:i.works,access_decision:'see_import_source_receipts',access_checked_at:'',catalogue_url:'',next_action:'Expand remaining eligible records; no current-display claim'});
 save(path.join(here,`museum-register-${phase}.json`),{created_at:new Date().toISOString(),directory_input_sha256:createHash('sha256').update(fs.readFileSync(input)).digest('hex'),source_rows:records.length,represented_institution_rows:institutions.length,total_register_rows:rows.length,warning:'Source rows overlap. Not a unique museum census; null coverage means unmapped, not zero. HEAD reachability is not catalogue completeness or permission.',institutions,rows});
 const columns=['source','source_id','name','country','kind','source_url','discovery_decision','linked_institution','imported_works','access_decision','access_checked_at','catalogue_url','next_action'];
 const cell=v=>'"'+String(v??'').replace(/^[=+@-]/,"'$&").replaceAll('"','""')+'"';
 fs.writeFileSync(path.join(here,`museum-register-${phase}.csv`),[columns.map(cell).join(','),...rows.map(r=>columns.map(c=>cell(r[c])).join(','))].join('\r\n')+'\r\n',{flag:'wx',mode:0o600});
 console.log({phase,rows:rows.length,represented:institutions.length,linkedSourceRows:rows.filter(r=>r.linked_institution).length});
}else throw new Error('Use probe or export before|after');
