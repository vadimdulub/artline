// Read-only live browser verification after the pinned production publication.
const {chromium,expect}=require('../apps/web/node_modules/@playwright/test');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../docs/research/south-africa-20261008');
(async()=>{
 const samples=JSON.parse(fs.readFileSync(path.join(root,'live-check-samples.json')));
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1050}});const results=[];const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const forbidden=/\bin review\b|awaiting review|details pending|no details available|image coming soon/i;
 try {
  for(const w of samples.artworks){
   const url='https://artlines.org/museums/'+w.institution_slug+'?work='+w.id;
   await page.goto(url,{waitUntil:'domcontentloaded'});
   const dialog=page.getByRole('dialog',{name:'Museum artwork details',exact:true});
   await expect(dialog).toBeVisible({timeout:45000});await expect(dialog.getByRole('heading',{name:w.title,exact:true})).toBeVisible();
   const text=await dialog.innerText();assert(text.includes(w.date_display));assert(!forbidden.test(text),text);
   results.push({type:'museum_artwork',institution:w.institution_name,title:w.title,url,passed:true});console.log('Live drawer:',w.institution_name,w.title);
  }
  await page.setViewportSize({width:390,height:844});
  for(const w of samples.artworks.filter(w=>['up','jag'].some(k=>w.institution_slug==='south-africa-'+k||w.institution_slug==='africa-'+k))){
   await page.goto('https://artlines.org/museums/'+w.institution_slug+'?work='+w.id,{waitUntil:'domcontentloaded'});
   const dialog=page.getByRole('dialog',{name:'Museum artwork details',exact:true});await expect(dialog).toBeVisible({timeout:45000});
   await expect(dialog.getByRole('heading',{name:w.title,exact:true})).toBeVisible();assert(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth));
   results.push({type:'mobile_drawer',institution:w.institution_name,passed:true});
  }
  await page.screenshot({path:'/tmp/artline-south-africa-20261008/live-mobile.png'});
  await page.setViewportSize({width:1440,height:1050});
  for(const a of samples.artists){
   await page.goto('https://artlines.org/artists/'+a.slug,{waitUntil:'domcontentloaded'});
   await expect(page.getByRole('button',{name:/^View /}).first()).toBeVisible({timeout:45000});
   assert((await page.locator('body').innerText()).includes(a.display_name));assert(!forbidden.test(await page.locator('body').innerText()));
   results.push({type:'artist_artworks',name:a.display_name,url:page.url(),passed:true});console.log('Live artist:',a.display_name);
  }
  await page.goto('https://artlines.org/museums?country=ZA',{waitUntil:'domcontentloaded'});
  await expect(page.getByRole('link').filter({hasText:'University of Pretoria Museums'}).first()).toBeVisible({timeout:45000});
  for(const w of samples.artworks)await expect(page.getByRole('link').filter({hasText:w.institution_name}).first()).toBeVisible();
  assert(!forbidden.test(await page.locator('body').innerText()));await page.screenshot({path:'/tmp/artline-south-africa-20261008/live-directory.png'});
  results.push({type:'country_directory',country:'ZA',collections:samples.artworks.length,passed:true});assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(root,'live-browser-verification.json'),JSON.stringify({at:new Date().toISOString(),checks_passed:results.length,results,errors,browser:'Headless Chrome fallback; in-app runtime failed before execution with missing sandboxPolicy.'},null,2));
  console.log('Passed',results.length,'live browser checks');
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
