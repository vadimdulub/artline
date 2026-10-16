import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
const index=['museum-guides','artist-guides'].flatMap(folder=>JSON.parse(fs.readFileSync(path.join(process.cwd(),'content/articles',folder,'index.json'),'utf8'))) as {slug:string;locales:string[];count:number}[];
for(const entry of index){
 test(`${entry.slug}: public editions, actual PDF, source links and saved portal views`,async({page,request})=>{
  await page.goto('/guides/'+entry.slug,{waitUntil:'domcontentloaded'});
  await expect(page.locator('main article[id^="work-"]')).toHaveCount(entry.count);
  await expect(page.locator('main nav[aria-label="Guide language"] a')).toHaveCount(10);
  const all=page.getByRole('link',{name:'Artworks in context',exact:false});
  const href=await all.getAttribute('href');const ids=new URL(href!,'https://artlines.org').searchParams.getAll('artwork_id');expect(ids).toHaveLength(entry.count);
  const pdf=await request.get(`/guides/${entry.slug}/pdf/en`);expect(pdf.status()).toBe(200);expect(pdf.headers()['content-type']).toBe('application/pdf');expect(pdf.headers()['content-disposition']).toContain('attachment');expect((await pdf.body()).subarray(0,5).toString()).toBe('%PDF-');
  for(const locale of ['ru','zh','ar']){
   await page.goto(`/guides/${entry.slug}/${locale}`,{waitUntil:'domcontentloaded'});await expect(page.locator('main')).toHaveAttribute('lang',locale);await expect(page.locator('main')).toHaveAttribute('dir',locale==='ar'?'rtl':'ltr');await expect(page.locator('main article[id^="work-"]')).toHaveCount(entry.count);
   for(const width of [390,320]){await page.setViewportSize({width,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);}
  }
 });
}
test('Armenia guide keeps its selected works and populated book/event context',async({page})=>{
 await page.goto('/guides/national-gallery-armenia');await page.getByRole('link',{name:'Artworks in context',exact:false}).click();await expect(page).toHaveURL(/\/all\?.*artwork_id=/);await expect(page.locator('.all-lane')).toHaveCount(3);await expect(page.locator('.all-artwork-strip img').first()).toBeVisible({timeout:30000});await expect(page.locator('main [role=alert]')).toHaveCount(0);
});
test('Guide reading and PDF route reject unknown editions',async({request})=>{
 for(const p of ['/guides/no-such-museum','/guides/louvre/xx','/guides/louvre/pdf/xx','/guides/no-such-museum/pdf/en'])expect((await request.get(p)).status()).toBe(404);
});
test('Translated guide accessibility and responsive reading',async({page},info)=>{
 await page.goto('/guides/national-gallery-armenia/ru');for(const width of [1440,390,320]){await page.setViewportSize({width,height:1000});expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);await page.screenshot({path:info.outputPath(`guide-${width}.png`)});}
});
