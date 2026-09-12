// Reviewed 10-person source crosswalk; no network or database writes.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {parse} from '../apps/web/node_modules/parse5/dist/index.js';
import {nodes,text,clean,attr} from './research-icons.mjs';
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const base = 'https://www.nationalgallery.gr';
const captures = 'content/imports/greek-painter-review-20260910/';
function source(url) {
 const file=captures+hash(url)+'.html',raw=fs.readFileSync(file),receipt=JSON.parse(fs.readFileSync(file+'.snapshot.json'));
 assert.equal(receipt.sha256,hash(raw));assert.equal(receipt.url,url);
 const doc=parse(raw.toString()),main=nodes(doc,n=>n.tagName==='main')[0]||doc;
 return {URL:url,File:file,SHA:hash(raw),CheckedAt:receipt.retrieved_at,Text:clean(text(main)),doc:main};
}
// Birth uncertainty is explicit. No invented exact date and no inference of
// citizenship from a modern country's borders or a place of birth.
const picks=[
 ['gyzis-nikolaos','Nikolaos Gyzis',1842,1901,'1842',false,'the-glory','The Glory','1898',1898,'exact','Π.1701','Pastel','38 x 24 cm','Donated by Epameinondas Simantiras','5ba895f9-f64c-44e6-a4dd-aa44dcec796b'],
 ['iakovidis-georgios','Georgios Iakovidis',1853,1932,'1853',false,'childrens-concert','Children’s Concert','1900',1900,'exact','Π.475','Oil on canvas','176 x 250 cm','',''],
 ['lytras-nikephoros','Nikephoros Lytras',1832,1904,'1832',false,'funeral-flowers-6505','Funeral Flowers','1901',1901,'exact','Π.48','Oil on canvas','80 x 51 cm','Apostolos Chatziargyris Bequest',''],
 ['volanakis-konstantinos','Konstantinos Volanakis',1837,1907,'1837',false,'collecting-the-nets','Collecting the Nets','1871',1871,'exact','Π.10380','Oil on canvas','69 x 135 cm','',''],
 ['maleas-konstantinos','Konstantinos Maleas',1879,1928,'1879',false,'aswan-1291','Aswan','1924',1924,'exact','Κ.1232','Oil and pencil on pasteboard','23 x 23,5 cm','E. Koutlidis Foundation Collection',''],
 ['economou-michael','Michael Economou',1884,1933,'1884 in this museum record; other accounts give 1888',true,'brittany-1509','Brittany','1924',1924,'exact','Κ.461','Oil on flannel','49 x 61 cm','E. Koutlidis Foundation Collection',''],
 ['parthenis-konstantinos','Konstantinos Parthenis',1878,1967,'1878/1879',true,'christ-2','Christ','ca. 1900',1900,'circa','Π.522','Oil on canvas','200 x 200 cm','Donated by the National Bank of Greece',''],
 ['kontoglou-fotis','Fotis Kontoglou',1896,1965,'1896',false,'saint-matthias-5351','Saint Matthias','1956',1956,'exact','Π.2992','Egg tempera on hardboard','103 x 53 cm','Donated by the Ministry of Education',''],
 ['chatzis-vasileios','Vasileios Chatzis',1870,1915,'1870',false,'the-harbour-of-kavala','The Harbour of Kavala','1913',1913,'exact','Π.453','Oil on canvas','25 x 45 cm','',''],
 ['rallis-theodoros','Theodoros Rallis',1852,1909,'1852',false,'lady-in-the-countryside-3278','Lady in the Countryside','1893',1893,'exact','Π.1821','Oil on panel','16 x 21,5 cm','',''],
];
const Artists=[],Works=[];
const Evidence=[];
for(const [Key,Name,Start,End,BirthDisplay,Uncertain,workSlug,Title,Date,Year,Precision,Accession,Medium,Dimensions,Collection,ExistingID] of picks){
 const a=source(base+'/en/artist/'+Key+'/'),w=source(base+'/en/artwork/'+workSlug+'/');
 assert(a.Text.includes(String(Start))&&a.Text.includes(String(End)));
 assert(w.Text.includes(Title+', '+Date)&&w.Text.includes('Inv. Number '+Accession)&&w.Text.includes(Medium+', '+Dimensions));
 assert(nodes(w.doc,n=>n.tagName==='a').some(n=>attr(n,'href')===a.URL),'exact source artist link');
 const museumName=clean(text(nodes(a.doc,n=>n.tagName==='h1')[0]));
 Artists.push({Key,Name,MuseumName:museumName,Start,End,BirthDisplay,Uncertain,ExistingID,URL:a.URL,SourceSHA:a.SHA,
  Biography:Name+' is documented in the National Gallery of Greece’s artist catalogue. This review links the museum’s named artist record to a selected work; it does not claim a complete oeuvre.'+(Uncertain?' Birth dating needs further reconciliation; the numeric birth year remains unset.':'')});
 Works.push({Artist:Key,Key:workSlug,Title,Date,Year,Precision,Accession,Medium,Dimensions,Collection,URL:w.URL,SourceSHA:w.SHA,
  Description:'Selected museum-catalogued work by '+Name+'. '+(Collection?'Collection credit: '+Collection+'. ':'')+'Photograph reuse requires further permission review; no image downloaded. Holding/collection evidence is not a current-display or ownership claim.'});
 for(const s of [a,w]){const {Text,doc,...e}=s;Evidence.push(e)}
}
const {Text,doc,...Policy}=source(base+'/oroi-chrisis/');
const output='docs/research/painter-review/greek-round-01-selection.json';fs.mkdirSync('docs/research/painter-review',{recursive:true});
const payload=JSON.stringify({Version:'greek-painter-review-v1',Created:new Date().toISOString(),Artists,Works,Evidence,Policy},null,2)+'\n';
fs.writeFileSync(output,payload,{flag:'wx',mode:0o600});console.log(output,hash(payload));
