// Render the same reviewed JSON used by the website. No network translation or catalogue writes.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
const repo=path.resolve(import.meta.dirname,'..');
const require=createRequire(path.join(repo,'apps/web/package.json'));
const {chromium}=require('playwright');
const ts=require('typescript');
const source=await fs.readFile(path.join(repo,'apps/web/lib/museum-guide-types.ts'),'utf8');
const {guidePortalLinks,guideSubject,guideLocation}=await import('data:text/javascript;base64,'+Buffer.from(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText).toString('base64'));
const roots=process.env.ARTLINE_GUIDE_CONTENT_ROOT?[process.env.ARTLINE_GUIDE_CONTENT_ROOT]:['artist-guides','museum-guides'].map(folder=>path.join(repo,'apps/web/content/articles',folder));
const locales=process.env.ARTLINE_GUIDE_PDF_LOCALES?.split(',');
const selected=process.argv.slice(2);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const link=(url,text)=>`<a href="${escape(url)}">${escape(text)}</a>`;
const paras=(value,klass='')=>String(value??'').split(/\n\s*\n/).filter(Boolean).map(value=>`<p${klass?` class="${klass}"`:''}>${escape(value)}</p>`).join('');
const browser=await chromium.launch({channel:'chrome',headless:true});
const report=[];
try {
for(const root of roots)for(const dir of await fs.readdir(root,{withFileTypes:true})) {
 if(!dir.isDirectory() || (selected.length&&!selected.includes(dir.name)))continue;
 for(const name of await fs.readdir(path.join(root,dir.name))) {
  if(!name.endsWith('.json')||(locales&&!locales.includes(name.replace(/\.json$/,''))))continue;
  const filename=path.join(root,dir.name,name),g=JSON.parse(await fs.readFile(filename,'utf8')),l=g.labels;
  const images=new Map();
  for(const w of g.works){
   let bytes;
   try{bytes=await fs.readFile(path.join('/tmp/artline-guides-20261010/images',w.id+'.jpg'));}
   catch { const url=new URL(w.image);const local=path.join(repo,'apps/web/public',url.pathname);try{bytes=await fs.readFile(local);}catch{const r=await fetch(w.image);if(!r.ok)throw new Error(`Image ${r.status}: ${w.id}`);bytes=Buffer.from(await r.arrayBuffer());} }
   images.set(w.id,`data:image/jpeg;base64,${bytes.toString('base64')}`);
  }
  const portals=guidePortalLinks(g),editionURL=`https://artlines.org/guides/${g.slug}${g.locale==='en'?'':'/'+g.locale}`;
  const translation=g.locale==='en'?'':`<p class="translation">${escape(l.translation)}</p>`;
  const html=`<!doctype html><html lang="${g.locale}" dir="${g.locale==='ar'?'rtl':'ltr'}"><head><meta charset="utf-8"><title>${escape(g.title)} — Artline</title><style>
  @page{size:A4;margin:16mm 17mm 17mm}*{box-sizing:border-box}html{font:10.5pt/1.5 Arial,'PingFang SC','Hiragino Sans',sans-serif;color:#24211d}body{margin:0;width:176mm}a{color:#703220;text-decoration:underline;text-underline-offset:2px}h1,h2,h3{font-family:Georgia,'Songti SC',serif;font-weight:normal;line-height:1.17}h1{font-size:30pt;margin:6mm 0 4mm}h2{font-size:23pt;margin:3mm 0}h3{font-size:14pt;margin:5mm 0 2mm}p{margin:2.5mm 0}figure{margin:5mm 0 0}figure img{display:block;max-width:100%;max-height:103mm;object-fit:contain;margin:auto}figcaption{font-size:7pt;line-height:1.35;color:#67605a;margin:2mm 0 4mm;overflow-wrap:anywhere}.brand{font:10pt Arial;letter-spacing:2px;text-transform:uppercase;border-bottom:1px solid #cfc8bc;padding-bottom:3mm;margin-bottom:6mm}.place,.meta,.note{color:#625d55}.place{font-size:10pt;text-transform:uppercase;letter-spacing:1px}.subtitle{font-size:14pt;line-height:1.35}.note{font-size:9pt}.translation{font:7.5pt Arial;color:#716d66}.page{break-after:page}.cover img{width:100%;height:58mm;object-fit:contain;background:#f2efe8;margin:4mm 0}.cover>p:not(.place):not(.subtitle):not(.translation):not(.note){font-size:9.5pt;line-height:1.4}.number{font-size:10pt;color:#8f3a29}.contents ol{columns:2;column-gap:9mm;padding-inline-start:5mm}.contents li{break-inside:avoid;margin-bottom:3mm;font-size:9pt}.contents li span{display:block;font-size:8pt;color:#625d55}.portal{border-top:1px solid #cfc8bc;margin-top:6mm;padding-top:4mm}.portal p{font-size:9pt}.portal a{margin-inline-end:5mm;display:inline-block}.meta{font-size:9pt}.work .description,.work .importance{font-size:10.5pt}.work .refs{font-size:8pt;margin-top:4mm}.work{break-inside:avoid}.reading article{margin:6mm 0;border-bottom:1px solid #ded7cc;padding-bottom:4mm}.end{border-top:1px solid #cfc8bc;padding-top:4mm;margin-top:8mm;font-size:8pt}html[lang=ar]{line-height:1.6}html[lang=zh] .work p,html[lang=ja] .work p{line-height:1.7}
  </style></head><body>
  <section class="page cover"><div class="brand">Artline · ${escape(l.guides)}</div><p class="place">${escape(guideLocation(g))}</p><h1>${escape(g.title)}</h1><p class="subtitle">${escape(g.subtitle)}</p>${translation}<img src="${images.get(g.works[0].id)}" alt="">${paras(g.introduction)}<p class="note">${escape(g.selectionNote)}</p></section>
  <section class="page contents"><div class="brand">Artline</div><div class="portal"><h3>${escape(l.explore)}</h3><p>${escape(l.contextNote)}</p><p>${['all','painters'].map(k=>link('https://artlines.org'+portals[k],l[k])).join(' ')}</p><p>${link(editionURL,'artlines.org/guides/'+g.slug)}</p></div><h2>${escape(l.contents)} · ${g.works.length}</h2><ol>${g.works.map(w=>`<li>${link('#work-'+w.id,w.title)}<span>${escape(w.artist)} · ${escape(w.date)}</span></li>`).join('')}</ol></section>
  ${g.works.map((w,i)=>`<article class="page work" id="work-${w.id}"><div class="brand">Artline · ${escape(guideSubject(g))}</div><p class="number">${String(i+1).padStart(2,'0')} / ${g.works.length}</p><h2>${escape(w.title)}</h2><p>${escape(w.artist)}</p><p class="meta">${escape([w.date,w.medium,w.museum].filter(Boolean).join(' · '))}</p><figure><img src="${images.get(w.id)}" alt="${escape(w.title)}"><figcaption>${link(w.imageSource,w.credit)} · ${link(w.licenseUrl||w.imageSource,w.license)}</figcaption></figure>${paras(w.description,'description')}${w.importance?`<h3>${escape(l.importance)}</h3>${paras(w.importance,'importance')}`:''}<p class="refs">${link(w.source,l.source)} · ${link(editionURL+'#work-'+w.id,l.artwork)}${w.accession?' · '+escape(l.inventory)+': '+escape(w.accession):''}</p></article>`).join('')}
  <section class="reading"><div class="brand">Artline</div>${(g.closingSections||[]).map(section=>`<h2>${escape(section.title)}</h2>${section.paragraphs.map(paragraph=>`<p>${escape(paragraph)}</p>`).join('')}`).join('')}<h2>${escape(l.reading)}</h2>${g.books.map(b=>`<article><h3>${link(b.url,b.title)}</h3><p class="meta">${escape(b.author)} · ${escape(b.access)}</p><p>${escape(b.note)}</p></article>`).join('')}${g.closingSections?.length?'':`<h2>${escape(l.visit)}</h2><p>${escape(g.visitNote)}</p>`}<p>${link(g.website,l.website)}${g.officialGuide?' · '+link(g.officialGuide,l.officialGuide):''}</p><p class="note">${escape(l.updated)}: ${g.updated}</p>${translation}<p class="end">${link(editionURL,'Artline · '+g.title)}</p></section></body></html>`;
  const page=await browser.newPage();await page.setContent(html,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);await page.emulateMedia({media:'print'});
  const overflows=await page.locator('.page').evaluateAll(nodes=>nodes.filter(n=>n.getBoundingClientRect().height>995).map(n=>n.id||n.className));
  if(overflows.length)throw new Error(`Potential PDF page overflow ${g.slug}/${g.locale}: ${overflows}`);
  const dest=filename.replace(/\.json$/,'.pdf');await page.pdf({path:dest,format:'A4',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font:8px Arial;width:100%;text-align:center;color:#736d64"><span class="pageNumber"></span> / <span class="totalPages"></span> · artlines.org</div>',tagged:true,outline:true});
  report.push({slug:g.slug,locale:g.locale,bytes:(await fs.stat(dest)).size});await page.close();console.log(g.slug,g.locale,report.at(-1).bytes);
 }
}
} finally {await browser.close();}
await fs.writeFile(process.env.ARTLINE_GUIDE_PDF_REPORT||'/tmp/artline-guides-20261010/pdf-report.json',JSON.stringify(report,null,2));
