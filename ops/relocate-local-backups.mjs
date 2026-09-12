// One-time, non-destructive relocation of the 22 inspected Artline backup folders.
// No database connection, deletion, glob expansion, overwrite or recursive cleanup.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const source='/Users/vadimdulub/Documents';
const destination='/Users/vadimdulub/Library/Application Support/Artline/backups';
const folders=[
 'artline-all-museums-backup-20260910.c3iw6D','artline-backup-20260909.Ln5ZKd',
 'artline-catalogue-backup-20260909.KE0Qr5','artline-continuation-backup-20260910.7CKc3G',
 'artline-deep-backup-20260909.2JQfPK','artline-europe-backup-20260910.SYGBdy',
 'artline-greek-review-backup-20260910.xGJWei','artline-greek-round1-batch2-backup-20260911.xi7XwI',
 'artline-icons-backup-20260910.9hv0UW','artline-masterpieces-backup-20260910.R133SB',
 'artline-nationalmuseum-backup-20260911.Win8KS','artline-normandy-backup-20260910.puTRiw',
 'artline-painter-images-backup-20260910.Z1NL9z','artline-popular-backup-20260911.1aUWbM',
 'artline-popular-cycle-backup-20260911.Aw17ht','artline-popular-europe-session-backup-20260911.l1B9ac',
 'artline-popular-followup-backup-20260911.KVoZS1','artline-popular-resume-20260911-backup.xM3Mcm',
 'artline-popular-smk-backup-20260911.LNLOsL','artline-round2-images-backup-20260911.sxrkHo',
 'artline-russia-italy-backup-20260909.CXyVhG','artline-us-europe-backup-20260909.GXhXuL',
];
const receipt=process.argv[2];assert(receipt&&!fs.existsSync(receipt),'new receipt path required');
const hash=async(file)=>{const h=crypto.createHash('sha256');for await(const b of fs.createReadStream(file))h.update(b);return h.digest('hex')};
const plan=[];
for(const folder of folders){
 const from=path.join(source,folder),to=path.join(destination,folder);
 assert(fs.lstatSync(from).isDirectory()&&!fs.lstatSync(from).isSymbolicLink());assert(!fs.existsSync(to),'destination exists');
 const files=[];
 for(const name of fs.readdirSync(from)){
  const file=path.join(from,name),stat=fs.lstatSync(file);
  assert(/^before-[a-z0-9-]+\.dump$/.test(name)&&stat.isFile()&&!stat.isSymbolicLink(),'unexpected backup content');
  const fd=fs.openSync(file,'r'),header=Buffer.alloc(5);fs.readSync(fd,header,0,5,0);fs.closeSync(fd);assert.equal(header.toString(),'PGDMP');
  files.push({name,bytes:stat.size,sha256:await hash(file)});
 }
 assert(files.length>0);plan.push({from,to,files});
}
fs.mkdirSync(destination,{recursive:true,mode:0o700});
fs.mkdirSync(path.dirname(receipt),{recursive:true});
const journal=fs.openSync(receipt,'wx',0o600);
fs.writeSync(journal,JSON.stringify({phase:'preflight',at:new Date().toISOString(),plan})+'\n');fs.fsyncSync(journal);
let bytes=0,files=0;
for(const item of plan){
 assert(!fs.existsSync(item.to));fs.renameSync(item.from,item.to);
 for(const f of item.files){assert.equal(await hash(path.join(item.to,f.name)),f.sha256);bytes+=f.bytes;files++;}
 fs.writeSync(journal,JSON.stringify({phase:'moved-and-hash-verified',at:new Date().toISOString(),from:item.from,to:item.to})+'\n');fs.fsyncSync(journal);
}
fs.writeSync(journal,JSON.stringify({phase:'complete',folders:plan.length,files,bytes,deleted:0,at:new Date().toISOString()})+'\n');fs.closeSync(journal);
console.log(JSON.stringify({folders:plan.length,files,bytes,deleted:0,destination,receipt}));
