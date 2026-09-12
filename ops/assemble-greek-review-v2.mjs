// Individually reviewed September 11 cohort. Offline, immutable, metadata only.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {parse} from '../apps/web/node_modules/parse5/dist/index.js';
import {nodes, text, clean, attr} from './research-icons.mjs';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const base = 'https://www.nationalgallery.gr';
const captures = 'content/imports/greek-painter-review-20260911/';
function source(url) {
  const file = captures + hash(url) + '.html', raw = fs.readFileSync(file);
  const r = JSON.parse(fs.readFileSync(file + '.snapshot.json'));
  assert.equal(r.sha256, hash(raw)); assert.equal(r.url, url);
  const doc = parse(raw.toString()), main = nodes(doc, n => n.tagName === 'main')[0] || doc;
  return {URL: url, File: file, SHA: hash(raw), CheckedAt: r.retrieved_at, Text: clean(text(main)), doc: main};
}
const people = [
  {Key:'laskaridou-sofia', Name:'Sofia Laskaridou', Start:1876, End:1965, BirthDisplay:'1876 in the online museum catalogue; 1882 in other museum/authority records', Uncertain:true,
    Biography:'Sofia Laskaridou studied painting in Athens, Munich and Paris. Her work includes landscapes, portraits and domestic scenes, with an interest in impressionist approaches to light and colour. She returned to Greece in 1916.\n\nBirth dating remains unresolved: the [museum artist page](https://www.nationalgallery.gr/en/artist/laskaridou-sofia/) gives 1876, while [SearchCulture’s authority record](https://www.searchculture.gr/aggregator/persons/-1625244741?language=en) gives 1882. The numeric birth year is intentionally unset.'},
  {Key:'flora-karavia-thaleia', Name:'Thaleia Flora-Karavia', Start:1871, End:1960, BirthDisplay:'1871', Uncertain:false,
    Biography:'Thaleia Flora-Karavia trained in Munich and spent three decades in Alexandria, where she ran an art school. Alongside portraits and landscapes, she documented military campaigns through sketches and a diary. Her painting developed from academic training toward impressionism and work outdoors.'},
  {Key:'papaloukas-spyros', Name:'Spyros Papaloukas', Start:1892, End:1957, BirthDisplay:'1892', Uncertain:false,
    Biography:'Spyros Papaloukas studied in Athens and Paris. His stay on Mount Athos in 1923–1924 brought the study of Byzantine art into dialogue with landscape painting. He later decorated the cathedral of Amfissa and taught painting. His work connects Byzantine visual traditions with modern approaches to colour and form.'},
  {Key:'theophilos-chatzimichael', Name:'Theophilos (Chatzimichael)', Start:1873, End:1934, BirthDisplay:'c. 1873', Uncertain:true,
    Biography:'Theophilos painted scenes of daily life, folklore and Greek history, including wall paintings for shops and cafés in Thessaly. He returned to Lesbos in 1927. Tériade supported his later work and subsequently founded the Theophilos Museum.\n\nThe online artist catalogue prints 1873; the museum’s [Four Centuries exhibition catalogue](https://www.nationalgallery.gr/wp-content/uploads/2021/10/4centuries_en.pdf) qualifies that year as uncertain. No exact numeric birth year is asserted.'},
];
const picks = [
  ['laskaridou-sofia','la-belle-epoque','La Belle Epoque','1910 - 1915',1910,1915,'range','Π.10508','Oil on canvas','66 x 51 cm',''],
  ['laskaridou-sofia','boats-on-the-lido-canal','Boats on the Lido Canal','1908 - 1912',1908,1912,'range','Π.3510','Oil on canvas','46 x 33 cm','Sofia Laskaridou Bequest'],
  ['flora-karavia-thaleia','water-carriers-on-the-nile','Water-Carriers on the Nile','c. 1909',1909,1909,'circa','Π.2110','Oil on canvas','33,5 x 41 cm','Antonios Benakis Bequest'],
  ['flora-karavia-thaleia','boy-reading','Boy Reading','ca 1906',1906,1906,'circa','Π.4166','Oil on canvas','62,5 x 52,5 cm',''],
  ['papaloukas-spyros','guest-quarters-at-lavra-monastery-on-mt-athos','Guest Quarters at Lavra Monastery on Mt. Athos','1924',1924,1924,'exact','Π.3941','Oil on pasteboard','52 x 59 cm',''],
  ['papaloukas-spyros','boy-with-suspenders','Boy with Suspenders','1925',1925,1925,'exact','Π.3300','Oil on pasteboard','60,5 x 51 cm',''],
  ['theophilos-chatzimichael','the-beautiful-adriana-of-athens','The Beautiful Adriana of Athens','1930',1930,1930,'exact','Π.6829','Thinned oil (?) on canvas','92 x 43,7 cm',''],
  ['theophilos-chatzimichael','adam-and-eve-2','Adam and Eve','1932',1932,1932,'exact','Π.10169','Oil on canvas','91,5 x 84 cm',''],
];
const Evidence = [], Artists = [], Works = [], authors = new Map();
function evidence(s) { const {Text,doc,...e} = s; Evidence.push(e); }
for (const a of people) {
  const s = source(base + '/en/artist/' + a.Key + '/');
  assert(s.Text.includes(String(a.Start)) && s.Text.includes(String(a.End)));
  const MuseumName = clean(text(nodes(s.doc, n => n.tagName === 'h1')[0]));
  Artists.push({...a, MuseumName, URL:s.URL, SourceSHA:s.SHA}); authors.set(a.Key,s); evidence(s);
}
for (const [Artist,Key,Title,Date,Year,LastYear,Precision,Accession,Medium,Dimensions,Collection] of picks) {
  const s = source(base+'/en/artwork/'+Key+'/'), a = authors.get(Artist);
  assert(s.Text.includes(Title+', '+Date) && s.Text.includes('Inv. Number '+Accession) && s.Text.includes(Medium+', '+Dimensions), Key);
  if (Collection) assert(s.Text.includes(Collection));
  assert(nodes(s.doc,n=>n.tagName==='a').some(n=>attr(n,'href')===a.URL),'exact named attribution');
  assert(nodes(a.doc,n=>n.tagName==='a').some(n=>attr(n,'href')===s.URL),'listed in artist catalogue');
  const name = Artists.find(a=>a.Key===Artist).Name;
  let Description = `Museum-catalogued ${Medium.toLowerCase()} by ${name}, dated ${Date}. `;
  if (Key === 'boy-with-suspenders') Description += 'The museum relates this portrait to the artist’s study of Byzantine iconography on Mount Athos and to his use of structured forms and colour. ';
  if (Key === 'the-beautiful-adriana-of-athens') Description += 'Adriana plays a guitar in a garden. The museum discusses the flattened space, clear outlines and vivid colours. The medium remains uncertain in the source. ';
  Description += (Collection ? `Collection credit: ${Collection}. ` : '') + 'This catalogue connection is not an ownership or current-display claim. Photograph reuse remains subject to further permission review.';
  Works.push({Artist,Key,Title,Date,Year,LastYear,Precision,Accession,Medium,Dimensions,Collection,URL:s.URL,SourceSHA:s.SHA,Description}); evidence(s);
}
const {Text,doc,...Policy} = source(base+'/oroi-chrisis/');
const output = 'docs/research/painter-review/greek-round-01-selection-v2.json';
const payload = JSON.stringify({Version:'greek-painter-review-v2',Created:new Date().toISOString(),Artists,Works,Evidence,Policy},null,2)+'\n';
fs.writeFileSync(output,payload,{flag:'wx',mode:0o600}); console.log(output,hash(payload));
