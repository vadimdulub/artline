import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('unidentified icon creators and traditions render in grid and right panel',async({page})=>{
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});
  await page.goto('/museums/byzantine-christian-museum-athens?q=Constantinople');
  const region=page.getByRole('region',{name:'Museum artwork results'});
  await expect(region.getByRole('button',{name:'Open Crucifixion',exact:true})).toBeVisible();
  await expect(region.getByText('Workshops of Constantinople',{exact:true})).toBeVisible();
  await region.getByRole('button',{name:'Open Crucifixion',exact:true}).click();
  const panel=page.getByRole('dialog',{name:'Museum artwork details',exact:true});
  await expect(panel.getByRole('heading',{name:'Crucifixion',exact:true})).toBeVisible();
  await expect(panel.getByText('Workshops of Constantinople',{exact:true})).toBeVisible();
  await expect(panel.getByText('Byzantine / post-Byzantine icons (museum collection)',{exact:true})).toBeVisible();
  await expect(panel.getByText('Object form',{exact:true})).toBeVisible();
  await expect(panel.getByText('ΒΧΜ 01354',{exact:true})).toBeVisible();
  expect(await panel.evaluate(n=>n.scrollWidth)).toBeLessThanOrEqual(width);
  const scan=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  expect(scan.violations).toEqual([]);
  await page.screenshot({path:`../../docs/screenshots/icons-athens-drawer-${width}.png`});
  await page.keyboard.press('Escape');
  await expect(region.getByRole('button',{name:'Open Crucifixion',exact:true})).toBeFocused();
 }
});

test('tentative Theophanes attribution stays linked and qualified',async({page})=>{
 await page.goto('/museums/moscow-kremlin-museums?artist=theophanes-the-greek-q319403');
 const region=page.getByRole('region',{name:'Museum artwork results'});
 await expect(region.getByRole('button')).toHaveCount(1);
 await region.getByRole('button').click();
 const panel=page.getByRole('dialog',{name:'Museum artwork details',exact:true});
 await expect(panel.getByRole('link',{name:'Theophanes the Greek',exact:true})).toBeVisible();
 await expect(panel.getByText('(attributed to)',{exact:false})).toBeVisible();
 await expect(panel.getByText('Ж-1386',{exact:true})).toBeVisible();
 await expect(panel.getByText('Последняя четверть XIV в.',{exact:true})).toBeVisible();
});
