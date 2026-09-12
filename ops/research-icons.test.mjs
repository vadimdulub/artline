import {test} from 'node:test';
import assert from 'node:assert/strict';
import {extract,capture} from './research-icons.mjs';
test('extracts literal creator and description independently',()=>{
 const x=extract('<h2>Crucifixion</h2><div class="description columns">Painted in the 14th c.</div><ul><li>Creator: Workshops of Constantinople</li><li>Exhibit Number: BXM 1</li></ul>','https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=33');
 assert.deepEqual(x.description,['Painted in the 14th c.']);
 assert.ok(x.facts.includes('Creator: Workshops of Constantinople'));
 assert.equal(x.headings[0],'Crucifixion');
});
test('rejects API/image/arbitrary/credential URLs before any fetch',async()=>{
 for(const url of ['https://collectiononline.kreml.ru/api/entity/OBJECT/9635','https://collectiononline.kreml.ru/api/spf/image.jpg','https://example.com/','https://user:secret@collectiononline.kreml.ru/entity/OBJECT/9635','https://www.ebyzantinemuseum.gr/admin']){
  await assert.rejects(capture(url),/Unapproved URL|Outside reviewed metadata/);
 }
});
