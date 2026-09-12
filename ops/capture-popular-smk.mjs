import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';

// Bounded, exact-object metadata capture. Stop on access restrictions; no mirrors.
const picks = [
  {
    "display_name": "Alfred Sisley",
    "external_id": "KMS3272",
    "title": "The Waterworks at Bougival",
    "creation_year_start": 1873,
    "creation_year_end": 1873
  },
  {
    "display_name": "Amedeo Modigliani",
    "external_id": "KMSr145",
    "title": "Alice",
    "creation_year_start": 1916,
    "creation_year_end": 1919
  },
  {
    "display_name": "Anthony van Dyck",
    "external_id": "KMS3223",
    "title": "Sketch for The Supper at Emmaus",
    "creation_year_start": 1614,
    "creation_year_end": 1641
  },
  {
    "display_name": "Anthony van Dyck",
    "external_id": "KMSsp242",
    "title": "Virgin and Child with Saint Francis",
    "creation_year_start": 1614,
    "creation_year_end": 1641
  },
  {
    "display_name": "Anthony van Dyck",
    "external_id": "KMSsp243",
    "title": "The Entombment of Christ",
    "creation_year_start": 1614,
    "creation_year_end": 1641
  },
  {
    "display_name": "Camille Pissarro",
    "external_id": "KMS3573",
    "title": "Landscape near Pontoise. A Peasant Walking along the Path",
    "creation_year_start": 1878,
    "creation_year_end": 1881
  },
  {
    "display_name": "Camille Pissarro",
    "external_id": "KMS3574",
    "title": "Woodland scene. Spring",
    "creation_year_start": 1878,
    "creation_year_end": 1878
  },
  {
    "display_name": "Camille Pissarro",
    "external_id": "KMS4323",
    "title": "View of Pont-Neuf with Statue of Henri IV",
    "creation_year_start": 1901,
    "creation_year_end": 1901
  },
  {
    "display_name": "Edgar Degas",
    "external_id": "KMS4324",
    "title": "Village Street. Saint-Valéry-sur-Somme",
    "creation_year_start": 1898,
    "creation_year_end": 1898
  },
  {
    "display_name": "Edvard Munch",
    "external_id": "KMS3325",
    "title": "Death Struggle",
    "creation_year_start": 1915,
    "creation_year_end": 1915
  },
  {
    "display_name": "Edvard Munch",
    "external_id": "KMS3823",
    "title": "Workers Coming Home",
    "creation_year_start": 1914,
    "creation_year_end": 1914
  },
  {
    "display_name": "Edvard Munch",
    "external_id": "KMS4179a",
    "title": "Portrait of Professor Daniel Jacobson",
    "creation_year_start": 1908,
    "creation_year_end": 1908
  },
  {
    "display_name": "Eugène Delacroix",
    "external_id": "KMS1956",
    "title": "Peonies",
    "creation_year_start": 1842,
    "creation_year_end": 1846
  },
  {
    "display_name": "Giovanni Battista Tiepolo",
    "external_id": "KMS4548",
    "title": "Apollo and Marsyas",
    "creation_year_start": 1757,
    "creation_year_end": 1757
  },
  {
    "display_name": "Giovanni Battista Tiepolo",
    "external_id": "KMS6683",
    "title": "The Brazen Serpent",
    "creation_year_start": 1711,
    "creation_year_end": 1770
  },
  {
    "display_name": "Gustave Courbet",
    "external_id": "KMS1957",
    "title": "Fighting Stags in a Forest",
    "creation_year_start": 1834,
    "creation_year_end": 1877
  },
  {
    "display_name": "Gustave Courbet",
    "external_id": "KMS3436",
    "title": "The Interior of a Forest",
    "creation_year_start": 1834,
    "creation_year_end": 1877
  },
  {
    "display_name": "Honoré Daumier",
    "external_id": "KMS3268",
    "title": "Don Quixote and Sancho Panza Resting Beneath a Tree",
    "creation_year_start": 1865,
    "creation_year_end": 1865
  },
  {
    "display_name": "Jean-Baptiste-Camille Corot",
    "external_id": "KMS1804",
    "title": "Study from Rome",
    "creation_year_start": 1811,
    "creation_year_end": 1875
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMS3674",
    "title": "Virgin and Child Adored by the Infant St John",
    "creation_year_start": 1512,
    "creation_year_end": 1514
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp718",
    "title": "The Judgement of Paris",
    "creation_year_start": 1527,
    "creation_year_end": 1527
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp720",
    "title": "Portrait of Martin Luther",
    "creation_year_start": 1532,
    "creation_year_end": 1532
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp722",
    "title": "Melancholy",
    "creation_year_start": 1532,
    "creation_year_end": 1532
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp725",
    "title": "Portrait of the Elector John Frederic the Magnanimous of Saxony (1503-1554)",
    "creation_year_start": 1533,
    "creation_year_end": 1533
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp726",
    "title": "Portrait of the Electress Sibyl of Saxony (1510-1569)",
    "creation_year_start": 1533,
    "creation_year_end": 1533
  },
  {
    "display_name": "Lucas Cranach the Elder",
    "external_id": "KMSsp731",
    "title": "The Mystic Marriage of Saint Catherine",
    "creation_year_start": 1510,
    "creation_year_end": 1512
  },
  {
    "display_name": "Nicolas Poussin",
    "external_id": "KMS3889",
    "title": "The Testament of Eudamidas",
    "creation_year_start": 1644,
    "creation_year_end": 1648
  },
  {
    "display_name": "Nicolas Poussin",
    "external_id": "KMSsp691",
    "title": "Joseph Interprets Pharaoh's Dream",
    "creation_year_start": 1609,
    "creation_year_end": 1665
  },
  {
    "display_name": "Paolo Veronese",
    "external_id": "KMSsp149",
    "title": "The Marriage of St Catharine",
    "creation_year_start": 1543,
    "creation_year_end": 1588
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS2019",
    "title": "Garden in Snow",
    "creation_year_start": 1883,
    "creation_year_end": 1883
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3098",
    "title": "Figures in a Garden",
    "creation_year_start": 1880,
    "creation_year_end": 1880
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3142",
    "title": "Landscape from Pont-Aven, Brittany",
    "creation_year_start": 1888,
    "creation_year_end": 1888
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3147",
    "title": "Still Life with Flowers",
    "creation_year_start": 1882,
    "creation_year_end": 1882
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3453",
    "title": "Woman Sewing",
    "creation_year_start": 1880,
    "creation_year_end": 1880
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3567",
    "title": "Winter Scenery",
    "creation_year_start": 1879,
    "creation_year_end": 1879
  },
  {
    "display_name": "Paul Gauguin",
    "external_id": "KMS3568",
    "title": "Coast at Dieppe",
    "creation_year_start": 1885,
    "creation_year_end": 1885
  },
  {
    "display_name": "Peter Paul Rubens",
    "external_id": "KMSsp191",
    "title": "Matthaeus Yrsselius (1541-1629), Abbot of Sint-Michiel's Abbey in Antwerp",
    "creation_year_start": 1622,
    "creation_year_end": 1625
  },
  {
    "display_name": "Peter Paul Rubens",
    "external_id": "KMSsp197",
    "title": "Francesco I de' Medici (1541-1587)",
    "creation_year_start": 1620,
    "creation_year_end": 1624
  },
  {
    "display_name": "Peter Paul Rubens",
    "external_id": "KMSsp198",
    "title": "Johanna of Austria",
    "creation_year_start": 1620,
    "creation_year_end": 1623
  },
  {
    "display_name": "Rembrandt van Rijn",
    "external_id": "KMS1384",
    "title": "The Crusader",
    "creation_year_start": 1659,
    "creation_year_end": 1661
  },
  {
    "display_name": "Vincent van Gogh",
    "external_id": "KMS1840",
    "title": "Landscape from Saint-Rémy",
    "creation_year_start": 1889,
    "creation_year_end": 1889
  }
];
const dir = 'content/imports/popular-smk-20260911';
await mkdir(dir, { recursive: true });
const results = [];
for (const pick of picks) {
  const url = `https://api.smk.dk/api/v1/art/?object_number=${pick.external_id}&lang=en`;
  const response = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(30000) });
  if (!response.ok) throw new Error(`Source paused: HTTP ${response.status} for ${pick.external_id}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length > 2000000) throw new Error('Metadata exceeds bounded capture size');
  const doc = JSON.parse(bytes);
  if (doc.items?.length !== 1 || doc.items[0].object_number !== pick.external_id) throw new Error('Object identity mismatch');
  const record = doc.items[0];
  const file = `${dir}/smk-${pick.external_id}.json`;
  await writeFile(file, bytes, { flag: 'wx' });
  await writeFile(`${file}.snapshot.json`, JSON.stringify({ url, sha256: createHash('sha256').update(bytes).digest('hex'), retrieved_at: new Date().toISOString() }, null, 2), { flag: 'wx' });
  const fact = { ...pick, has_image: record.has_image, public_domain: record.public_domain, rights: record.rights, image_iiif_id: record.image_iiif_id, production: record.production?.map(({creator, creator_lref, creator_date_of_birth, creator_date_of_death, ...rest}) => ({creator, creator_lref, creator_date_of_birth, creator_date_of_death, qualifiers: Object.fromEntries(Object.entries(rest).filter(([k]) => /role|qualif|attribut/.test(k)))})), production_date: record.production_date, titles: record.titles, page: record.frontend_url };
  results.push(fact);
  console.log(JSON.stringify(fact));
  await delay(1500);
}
await writeFile(`${dir}/facts.json`, JSON.stringify(results, null, 2), { flag: 'wx' });
