#!/usr/bin/env python3
"""Selected Russian Museum gaps: native object evidence and WikiArt versions."""
import argparse
import collections
import copy
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup

s=importlib.util.spec_from_file_location('wiki',Path(__file__).with_name('recover-local-wikiart-approved-images-20261006.py'))
wiki=importlib.util.module_from_spec(s);s.loader.exec_module(wiki)
base,core=wiki.base,wiki.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-images-20261006'
AUDIT=RUN.parent/'local-wikiart-russian-leads-20261006'
wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-russian-version-review-v1'
IDS=['92b7b4c7-4f0a-495c-94e0-015b53e60db4','47e59b14-ad3d-4957-b749-7e1a426cff3f','3de994ef-c09b-4f09-92a9-c330f96c55f6','51a05a30-0285-48ad-b51a-40beba78876e','f0cd28da-678d-49fb-9430-915bc91815c6','fa139040-882d-4970-91f7-94cf6da4e5f3','a12a7bc4-6ade-48fb-8125-d9193455a90d','415a6924-b64f-46a8-9dad-762a8af1f179']
ARTISTS={
 '366c4612-1b9a-4240-8749-ab9512e2d390':dict(qid='Q4768',native='bryullov_kp',label='Брюллов К. П.',life='12 (23) декабря 1799, Санкт-Петербург — 23 июня 1852, Манциана близ Рима',birth=1799,death=1852),
 '0604627e-59cd-4203-82b2-9aa77423e5cc':dict(qid='Q313275',native='kustodiev_bm',label='Кустодиев Б. М.',life='1878, Астрахань – 1927, Ленинград',birth=1878,death=1927),
}
original_facts,original_attach=wiki.page_facts,wiki.attach
TITLE_CONCORDANCES={
 ('92b7b4c7-4f0a-495c-94e0-015b53e60db4','https://www.wikiart.org/en/boris-kustodiev/bathing-1921','Купание','Купальщица'):'Exact oil painting ЖС-569 visually compared: seated figure, birch trunk, townscape, red rug and second bather. Keep both source titles and unchanged catalogue title.',
}
BASIS='Existing exact Russian Museum object URL, accession, creator authority and title; current WikiArt original-language title and exact page/photo, independent creator QID crosswalk and individual physical-version visual comparison. Current WikiArt source date and actual rights labels retained separately from catalogue values and user source approval. Local image-only attachment; no catalogue publication or independent copyright-holder permission asserted.'

def snapshot():
 if (RUN/'candidates.json').exists():return
 audit=json.loads((AUDIT/'discovery.json').read_bytes());leads={x['work']['id']:x for x in audit['leads']}
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
   to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review'
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) ORDER BY a.id''',(IDS,)).fetchall()
  if len(rows)!=len(IDS):raise ValueError('Selected current gaps changed')
  arts=sorted({x['creator_links'][0]['artist_id'] for x in rows})
  artists={x['record']['id']:x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(arts,))}
  aliases,identifiers=collections.defaultdict(list),collections.defaultdict(list)
  for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY id',(arts,)):aliases[x['record']['artist_id']].append(x['record'])
  for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(arts,)):identifiers[x['record']['entity_id']].append(x['record'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:
  lead=leads[c['artwork_id']];aid=c['creator_links'][0]['artist_id']
  if c['roles']!=['primary'] or len(c['creator_links'])!=1 or aid!=lead['work']['artist_id']:raise ValueError('Unique creator changed')
  if any(c[k]!=lead['work'][k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','work_type')):raise ValueError('Audited object changed')
  matches=[x for x in lead['candidates'] if x['completitionYear'] and c['creation_year_start']<=x['completitionYear']<=c['creation_year_end']]
  if len(matches)!=1:raise ValueError('Unique lead version absent')
  selected=matches[0];filename=urlparse(selected['image']).path.split('/')[-1].split('!',1)[0].removesuffix('.jpg')
  page='https://www.wikiart.org/en/'+lead['source_artist_slug']+'/'+filename
  es=[e for e in c['identifiers'] if e['scheme']=='european-russian-session-museum-object']
  if len(es)!=1:raise ValueError('Unique native object absent')
  e=es[0]
  c.update(provider=wiki.PROVIDER,scheme=e['scheme'],external_id=e['external_id'],source_id=e['source_id'],museum_page=e['canonical_url'],page=page,artist=artists[aid]['display_name'],target_ids={'local':c['artwork_id']},creator_authorities=[dict(artist_record=artists[aid],artist_aliases=aliases[aid],artist_identifiers=identifiers[aid])],prior_index_lead=selected)
 core.save_new(RUN/'prior-discovery.json',(AUDIT/'discovery.json').read_bytes())
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows,selection='Eight specific existing Russian Museum records from six-artist metadata discovery. Titles and year intervals supply leads only; exact physical version and source image require individual review. No catalogue creation, merge or publication.'))
 docs=[]
 for source in ('AGENTS.md','docs/ARTLINE_IMAGE_USE.md'):
  data=(core.ROOT/source).read_bytes();capture='metadata/authorization/'+Path(source).name;core.save_new(RUN/capture,data);docs.append(dict(source_path=source,capture=capture,sha256=core.sha(data)))
 core.save_new(RUN/'source-authorization.json',dict(at=core.now(),source='WikiArt',target='local',record_actual_rights_separately=True,documents=docs,user_instruction='see new md file - wiki art is fully approved',scope='Selected existing Russian Museum artwork image gaps; preserve actual source rights, unknown fields, creators and catalogue status.'))
 print('Snapshotted eight native museum records',flush=True)

def capture(url,path):
 if path.exists():
  data=path.read_bytes();rc=json.loads(path.with_suffix('.receipt.json').read_bytes())
  if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:raise ValueError('Capture changed')
  return data,rc
 if urlparse(url).hostname not in ('rusmuseumvrm.ru','www.wikiart.org'):raise ValueError('Unexpected source host')
 fetch=core.Fetcher(RUN/'metadata');core.provider_rate_slot(urlparse(url).hostname)
 with fetch.session.get(url,timeout=(15,45),allow_redirects=False) as response:
  response.raise_for_status()
  if response.status_code!=200 or len(response.content)>6000000:raise ValueError('Unexpected source response')
  data=response.content
 rc=dict(url=url,at=core.now(),bytes=len(data),sha256=core.sha(data),path=str(path.relative_to(core.ROOT)))
 core.save_new(path,data);core.save_new(path.with_suffix('.receipt.json'),rc);return data,rc

def sources():
 snapshot();fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  try:
   capture(c['museum_page'],RUN/'metadata/museum'/(c['artwork_id']+'.html'))
   wiki.capture_page(c,fetch)
   qids=[x['external_id'] for x in c['creator_authorities'][0]['artist_identifiers'] if x['scheme']=='wikidata']
   if len(qids)!=1:raise ValueError('Unique creator QID absent')
   fetch.metadata('https://www.wikidata.org/wiki/Special:EntityData/'+qids[0]+'.json')
   print('Captured pair',c['title'],c['accession_number'],flush=True)
  except Exception as error:
   core.event(RUN,dict(provider=wiki.PROVIDER,artwork_id=c['artwork_id'],outcome='source_unavailable',reason=str(error)))
   print('Source held',c['artwork_id'],str(error),flush=True)
   if getattr(getattr(error,'response',None),'status_code',None) in (403,429,502,503,504):raise

def pinned(path,url):
 data=path.read_bytes();rc=json.loads(path.with_suffix('.receipt.json').read_bytes())
 if rc['url']!=url or core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:raise ValueError('Pinned source changed')
 return BeautifulSoup(data,'html.parser'),rc

def native_facts(c):
 if c['institution_slug']!='state-russian-museum' or c['roles']!=['primary'] or len(c['creator_links'])!=1:raise ValueError('Native institution/creator scope differs')
 proof=c['creator_authorities'][0];ar=proof['artist_record'];a=ARTISTS[ar['id']]
 if c['creator_links'][0]['artist_id']!=ar['id'] or (ar['birth_year'],ar['death_year'])!=(a['birth'],a['death']):raise ValueError('Creator life identity differs')
 qids=[x['external_id'] for x in proof['artist_identifiers'] if x['scheme']=='wikidata']
 if qids!=[a['qid']]:raise ValueError('Creator authority differs')
 ids=[x for x in c['identifiers'] if x['scheme']=='european-russian-session-museum-object']
 if len(ids)!=1 or (ids[0]['external_id'],ids[0]['canonical_url'])!=(c['external_id'],c['museum_page']):raise ValueError('Native object identifier differs')
 soup,rc=pinned(RUN/'metadata/museum'/(c['artwork_id']+'.html'),c['museum_page'])
 title=soup.select_one('.work__title').get_text(' ',strip=True)
 if wiki.norm(title)!=wiki.norm(c['title']):raise ValueError('Native title differs')
 accession=soup.select_one('[title="Инвентарный номер"]').get_text(' ',strip=True)
 if c['accession_number'] and accession!=c['accession_number']:raise ValueError('Native accession differs')
 author_url='https://rusmuseumvrm.ru/reference/classifier/author/'+a['native']+'/index.php'
 links=soup.select('.work__author a[href]')
 if len(links)!=1 or urljoin(c['museum_page'],links[0]['href'])!=author_url or links[0].get_text(' ',strip=True)!=a['label']:raise ValueError('Native creator attribution differs')
 life=soup.select_one('.work__desc').get_text(' ',strip=True)
 lives=(a['life'],*a.get('life_aliases',[]))
 if life not in lives:raise ValueError('Native creator biography differs')
 author,arc=pinned(RUN/'metadata/authors'/(a['native']+'.html'),author_url)
 if not any(value in author.get_text(' ',strip=True) for value in lives):raise ValueError('Native linked author biography differs')
 dates=soup.select_one('.period').get_text(' ',strip=True)
 medium=soup.select_one('[title="Материал"]').get_text(' ',strip=True)
 dimensions=soup.select_one('[title="Размер"]').get_text(' ',strip=True)
 for field,value in [('medium_text',medium),('dimensions_text',dimensions)]:
  before=c['before_record'][field]
  if before and wiki.norm(before)!=wiki.norm(value):raise ValueError('Native '+field+' differs')
 photo=[x for x in soup.select('img.rsImg') if x.get('src','').endswith('_mainfoto_03.jpg')]
 if len(photo)!=1:raise ValueError('Unique native reference image absent')
 reference=urljoin(c['museum_page'],photo[0]['src'])
 aliases={
  '2066756c-0b41-4996-9d06-b4c5137cd161':'https://rusmuseumvrm.ru/data/collections/painting/19_20/kuindzhi_ai_more_krim_1898_zh_1516/3900_mainfoto_03.jpg',
  '99ed72b7-5dca-4327-b55b-6689204b48a8':'https://rusmuseumvrm.ru/data/collections/painting/19_20/mashkov_i.i._bahchisaray._1925._zh-8142/15657_mainfoto_03.jpg',
  'b2f1af48-c5a0-4519-b103-e37be5faf42a':'https://rusmuseumvrm.ru/data/collections/painting/19_20/mashkov_i._i._portret_malchika_v_raspisnoy_rubashke._1909._zhb-1499/20752_mainfoto_03.jpg',
  'd73fcf2a-5371-4842-92ee-0cc7f26bd898':'https://rusmuseumvrm.ru/data/collections/painting/19_20/mashkov_ii_natyurmort_s_ananasom_1908_zh_6618/3103_mainfoto_03.jpg',
  'a6793a02-d460-43ba-84e8-e5ff7029725d':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_a._k._glazunova._1887._zh-4014/18451_mainfoto_03.jpg',
  'b0548b1b-4516-45c5-b79e-874180eb1f8e':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_tatyani_mamontovoy._1878._r-7845/19983_mainfoto_03.jpg',
  'b1f7cf95-5e32-4dd5-ac8a-6f306e659225':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_vladimira_spasovicha._1891._zh-4067/19881_mainfoto_03.jpg',
  'ccadbc88-461b-4f2a-8b00-b36aa943e2c8':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._mat_kormyaschaya_rebenka._nabrosok._1911._r-1799/11088_mainfoto_03.jpg',
  'd88ce259-f5d5-48d8-96fb-0c48556d9a8c':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._golova_konya._1912._r-52497/11140_mainfoto_03.jpg',
  '4c1ea354-6070-403f-b619-5954351e8f03':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_knyazya_mihaila_hilkova._19011903._zh-4024/19919_mainfoto_03.jpg',
  '5b7a75d2-8e03-4f93-9d52-2f9abcb93698':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_ivana_panova._1867._zh-4041/19870_mainfoto_03.jpg',
  'b7879f2b-e1ca-4ba7-8667-2c91cccccfd9':'https://rusmuseumvrm.ru/data/collections/painting/19_20/serov_va__portret_knyazya_f_f_yusupova_grafa_sumarokova_elstona_1903/2712_mainfoto_03.jpg',
  'ca12a488-5186-4dfc-b73c-c8afcc97e0d5':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_mitrofana_belyaeva._1886._zh-4012/19868_mainfoto_03.jpg',
  '4ad8c467-81dd-4948-abbb-b1e6c8e1cca4':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_natalii_nordman-severovoy._1911._zh-5540/19900_mainfoto_03.jpg',
  '4ca04900-e579-4f6f-8d98-2fbb746c1fd6':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_nikolaya_ermakova._1911._r-7923/20210_mainfoto_03.jpg',
  '6eed328e-2ecf-41f3-a0b8-3bd6265b5a12':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._portret_a.p._petrovoy_materi_hudozhnika._1925._rs-1422_/11103_mainfoto_03.jpg',
  '8aa0bf1f-e898-4ed2-9bd0-d64e800cb1b7':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._ispanka_zhenskiy_portret._1907._zh-11848/11040_mainfoto_03.jpg',
  '9b894d2a-ee60-4453-bc00-3776c4c253e9':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._portret_a.p._petrovoy-vodkinoy._1909._zh-2396/11029_mainfoto_03.jpg',
  'ce509251-d9d0-456b-aae8-3223bc0fcb7c':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._krestyanin._1878._zh-9269/19906_mainfoto_03.jpg',
  'd532e171-ea3a-4bb5-bbe6-bf4eb615448f':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._igrayuschie_malchiki_tri_malchika._1916._r-57963/11096_mainfoto_03.jpg',
  'f4c17656-8d24-420c-8f62-bb7b299e84ac':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._poyuschiy_krestyanin._1879._zh-6276/19901_mainfoto_03.jpg',
  'f801760b-1b57-4b52-be18-d56ac1e2a022':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._stoyaschaya_naturschica._1910._r-1787/11121_mainfoto_03.jpg',
  '0b4decaf-e808-40c5-ac75-7d2717fc9b86':'https://rusmuseumvrm.ru/data/collections/engraving/gr-39982/31530_mainfoto_03.jpg',
  '071bb78e-c89e-40ca-a50d-91201d6bd963':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_ie__portret_hudozhnika_arhipa_ivanovicha_kuindzhi_18421910_1877_zh_4076/2909_mainfoto_03.jpg',
  '0c30a4a8-f4d7-4e76-88b4-7a4668add8e8':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._priezd_carey_ioanna_i_petra_alekseevi-_chey_na_semenovskiy_poteshniy_dvor_gor._moskvi_i_/20238_mainfoto_03.jpg',
  '43b2f853-edfa-4d4b-80dc-eb817e8af22f':'https://rusmuseumvrm.ru/data/collections/painting/19_20/kustodiev_b._m._portret_i._e._grabarya._1916._zh-4359/18192_mainfoto_03.jpg',
  '73b4592d-ed12-46ec-b764-f5dac6623a19':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._stepan_razin._1918._rs-1437/11199_mainfoto_03.jpg',
  '86072ea6-bd53-4a9a-be9f-579346f8987d':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_vladimira_behtereva._1913._zh-6545/19904_mainfoto_03.jpg',
  '8dd94493-125b-4bc1-84b5-c3a8d45997aa':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._eskiz_k_kartine_trevoga._1925._rs-1424/11104_mainfoto_03.jpg',
  '923ab017-a604-49fa-a5c3-041d89c79e8f':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_aleksandra_zhirkevicha._1891._r-7932/20216_mainfoto_03.jpg',
  '92e13678-098e-4a69-a6c5-b011e44082a3':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._yunosha-naturschik._1913._r-49538/11134_mainfoto_03.jpg',
  '9f2dcf3b-9e5a-4262-b264-6441c65e5d82':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_vasiliya_schegolenka._1879._zh-4085/19896_mainfoto_03.jpg',
  'cf76eb86-5772-423d-b563-132e50001c65':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._shah-i-zinda._samarkand._1921._zhb-1274/11062_mainfoto_03.jpg',
  'e8a78552-c65f-4f7c-b9d2-a13bf70f6e3a':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov_vodkin_ks_polden_1917_zh_1263/4538_mainfoto_03.jpg',
  '1ba2fdaf-82f1-452a-82e6-837fcf52e8e8':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._portret_malchika-uzbeka._1921._/11367_mainfoto_03.jpg',
  '38948ae9-4e97-422c-9264-a484a008876c':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._malchik-uzbek._1921._zh-10968/11064_mainfoto_03.jpg',
  '4d96405a-86e4-430f-a0ce-8861e5dadd15':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._semya_rabochego_v_pervuyu_godovschinu_oktyabrya._1927._rs-1431/11198_mainfoto_03.jpg',
  '64c74f67-1a02-4a5a-bf79-9195bc1024a1':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_natalii_nordman_v_shlyape._1901._r-7839/19982_mainfoto_03.jpg',
  '7d9f19d6-6bcb-41bd-9fa9-934badb8e0bd':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._v_oazise_negrityanskaya_derevnya._1907._zhb-1248/11031_mainfoto_03.jpg',
  '88735144-fe7b-40d3-958a-85feb53f737a':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_konstantina_pobedonosceva._1903._zh-4027/19922_mainfoto_03.jpg',
  '99cd4917-7bd7-4f15-b6f7-4ec2b7b0e0bd':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._v_osazhdennoy_moskve._1912._zh-2777/19857_mainfoto_03.jpg',
  '9fc267bc-5e7b-4a40-a2d9-3a9fc3bf2f5c':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._sidyaschaya_zhenschina._1907-1908.r-1788/11122_mainfoto_03.jpg',
  'a9a4f1f6-652b-46bf-918f-48acf5138f28':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._muzhchina_i_zhenschina_za_stolikom._dve_sidyaschie_zhenschini._muzhchina_natyagivayuschi/19898_mainfoto_03.jpg',
  'ab4ed7b8-23b6-45bb-844d-3698e10d9b4b':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_a._g._rubinshteyna._1887._zh-4074/18452_mainfoto_03.jpg',
  'c94e155b-f720-4723-844e-2d725bffd36a':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._eskiz_kostyuma_yurodivogo_k_spektaklyu_boris_godunov._1923-1924._rs-24301/11264_mainfoto_03.jpg',
  'fdf5c736-ddb4-410d-b841-285cbbbf16b5':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_grafa_alekseya_ignateva._1902._zh-4031/19924_mainfoto_03.jpg',
  'f97f8392-d2f2-43d0-827c-c0efc2041ab6':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._aleksandr_pushkin_na_akte_v_licee_8_yanvarya_1815_goda._1910._zh-2776/19856_mainfoto_03.jpg',
  '451edf40-7221-4e52-bb38-d0fa5093ee45':'https://rusmuseumvrm.ru/data/collections/painting/19_20/kustodiev_b._m._portret_rene_notgaft._1914._zh-8516/17890_mainfoto_03.jpg',
  '3de3ce24-772f-4845-a757-95cd70e7dfcc':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_ivana_tarhanova._1892._zh-4077/19890_mainfoto_03.jpg',
  '466c09f9-173f-4f42-b6b7-2218443d6826':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._portret_knyazya_mihaila_volkonskogo._19011903._zh-4020/19916_mainfoto_03.jpg',
  'dd3bb3af-9e38-4792-b1b7-6ac96d14e2ee':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._dama_opirayuschayasya_na_stul._1875._zh-4058/19878_mainfoto_03.jpg',
  'b2c79f11-f949-44a5-a563-6662285c8c4f':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._koncert_v_dvoryanskom_sobranii._1888._r-7880/20193_mainfoto_03.jpg',
  'd1835326-64df-4c0c-be8c-b767cdb059de':'https://rusmuseumvrm.ru/data/collections/drawings/kustodiev_b._m._u_vhoda_v_park_usadbi_kupavinoy._1915._r-54733/39263_mainfoto_03.jpg',
  '65b88d1d-df11-45c7-86e9-34cd475b3ed5':'https://rusmuseumvrm.ru/data/collections/painting/19_20/kustodiev_b_prazdnik_v_chest_ii_kongressa_kominterna_19_iyulya_1920_goda_demonstraciya_na_ploschadi_/8576_mainfoto_03.jpg',
  'a2a71d0e-429c-4fda-913a-f0a281086970':'https://rusmuseumvrm.ru/data/collections/painting/19_20/zh_4305/2293_mainfoto_03.jpg',
  '2dd786e9-c014-4acc-81db-15c0ec736ecb':'https://rusmuseumvrm.ru/data/collections/engraving/sgr-2719/39239_mainfoto_03.jpg',
  '19fce6c4-7c8b-4fc5-97da-a5cd508509e4':'https://rusmuseumvrm.ru/data/collections/engraving/sgr-2715/39237_mainfoto_03.jpg',
  'bf8c8ebb-52fa-46dd-9ba2-306abd476496':'https://rusmuseumvrm.ru/data/collections/engraving/sgr-2734/39242_mainfoto_03.jpg',
  '027c5a45-4f79-4d70-83fa-3da7573ec857':'https://rusmuseumvrm.ru/data/collections/engraving/sgr-11759/39247_mainfoto_03.jpg',
  '3de994ef-c09b-4f09-92a9-c330f96c55f6':'https://rusmuseumvrm.ru/data/collections/painting/17_19/bryullov_k.p._portret_velikoy_knyazhni_marii_nikolaevni._1837._zh-3342/16861_mainfoto_03.jpg',
  'fa139040-882d-4970-91f7-94cf6da4e5f3':'https://rusmuseumvrm.ru/data/collections/painting/18_19/zh_5084_bryullov_kp_posledniy_den_pompei/1918_mainfoto_03.jpg',
  '4ebec1df-9151-40f9-8d04-fe6c7975e738':'https://rusmuseumvrm.ru/data/collections/painting/19_20/kustodiev_bm__portret_yue_kustodievoy_1903/2659_mainfoto_03.jpg',
  'ffa60685-732d-4a80-9b6a-69d167a7b6b9':'https://rusmuseumvrm.ru/data/collections/painting/17_19/bryullov_k._p._avtoportret._1833._zh-5077/18496_mainfoto_03.jpg',
  '4fed8a9d-7e08-4e60-86e6-c7e457b2debb':'https://rusmuseumvrm.ru/data/collections/painting/19_20/rerih_n._k._poceluy_zemle._1912._zh-1982/18995_mainfoto_03.jpg',
  '05826144-a9c0-4723-8567-16e9c34fc432':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov_vodkin_ks_avtoportret_1918_zh_2400/7204_mainfoto_03.jpg',
  '28bcba94-66a0-4740-9c58-45d4765713b1':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._avtoportret._1926-1927._zh-2414/11060_mainfoto_03.jpg',
  '7c586e7c-4902-4103-9e5d-1c10cb59bc81':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._avtoportret._1922._rs-1417/11101_mainfoto_03.jpg',
  '808fe8e3-4eda-4da3-8996-6eb4bb165f74':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._avtoportret._1926._rs-1426/11106_mainfoto_03.jpg',
  '9285f5e6-bf7e-4d10-a5f1-32757ebe1dfc':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._avtoportret._1921._rs-1415/11100_mainfoto_03.jpg',
  '19a070d5-2f2a-483e-98c2-87f3a2bcecb7':'https://rusmuseumvrm.ru/data/collections/painting/19_20/petrov-vodkin_k.s._golova_devochki._1921._zhs-1077/11069_mainfoto_03.jpg',
  '87fac0c1-8a09-4118-9f6e-219f1224ae5f':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._zhenskaya_golova._1918._rs-1413/11193_mainfoto_03.jpg',
  '86234326-3f7c-4451-98a3-25feceddcf90':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._interer._1926._rs-1428/11197_mainfoto_03.jpg',
  '9132051e-646d-4184-bc8a-1b7cfa5b374d':'https://rusmuseumvrm.ru/data/collections/drawings/petrov-vodkin_k.s._portret_m.f._petrovoy-vodkinoy._1925._rs-1425/11105_mainfoto_03.jpg',
  '5eb77ac9-ab10-4518-94ee-b4a8e9268001':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._idi_za_mnoyu_satano._1895_._zh-2779/19860_mainfoto_03.jpg',
  'cd6d1886-f0b8-4e80-8948-0121167f4547':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._arest_propagandista._1879._r-7869/20001_mainfoto_03.jpg',
  'd6793c7f-d5e1-4881-8385-42013feff0d8':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._burlak._1870._zh-4055/19876_mainfoto_03.jpg',
  '3b6d09c5-cb56-4d10-a83e-5ff517c3798c':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._burlaki_na_volge._1870._zh-7928/19905_mainfoto_03.jpg',
  '12d6c39a-3067-48aa-a5d9-07b135066b53':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._piknik._1875._zh-4073/19889_mainfoto_03.jpg',
  'a0ba8c5c-92a4-4395-844b-42cd98257aff':'https://rusmuseumvrm.ru/data/collections/drawings/repin_i._e._portret_veri_repinoy._1896._r-7927/20214_mainfoto_03.jpg',
  '1c3bc019-78fd-48af-a47c-aa5f79299421':'https://rusmuseumvrm.ru/data/collections/drawings/repin_ie_portret_m_k_tenishevoy_1896_r_7808/3397_mainfoto_03.jpg',
  '61a8ae7d-c91c-4689-afe1-137b81ff62d4':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i.e._portret_voennogo._1916._zh-12079/11795_mainfoto_03.jpg',
  '3d527db8-b89f-4154-9a22-6ebee3854deb':'https://rusmuseumvrm.ru/data/collections/painting/19_20/repin_i._e._ukrainskaya_hata._1876._zh-6311/19903_mainfoto_03.jpg',
  'b3abc0f1-27f5-47ec-bac3-c1cf5fa80c2e':'https://rusmuseumvrm.ru/data/collections/painting/19_20/rerih_nk_zamorskie_gosti_1902_zh_1974/6907_mainfoto_03.jpg',
  'd3dc6c1c-ad91-4c49-a482-2ace94085cde':'https://rusmuseumvrm.ru/data/collections/painting/19_20/rerih_n._k._poloveckiy_stan._1909._zh-1983/18994_mainfoto_03.jpg',
 }
 if not reference.startswith(c['museum_page'].rsplit('/',1)[0]+'/') and aliases.get(c['artwork_id'])!=reference:raise ValueError('Native photo is another object')
 return dict(capture=rc,title=title,accession=accession,period=dates,medium=medium,dimensions=dimensions,author_url=author_url,author_label=a['label'],author_life=life,author_capture=arc,reference_image_url=reference)

def page_facts(c,data,rc):
 reviews=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'];review=reviews[c['artwork_id']]
 native=native_facts(c)
 if native!=review['native_facts']:raise ValueError('Native identity review changed')
 if review['decision']!='continue_to_visual_review':raise ValueError(review['reason'])
 soup=BeautifulSoup(data,'html.parser')
 original=[li.get_text(' ',strip=True).split(':',1)[1].strip() for li in soup.select('.wiki-layout-artwork-info article li') if li.get_text(' ',strip=True).startswith('Original Title:')]
 if len(original)!=1:raise ValueError('Unique original-language title absent')
 if wiki.norm(original[0])!=wiki.norm(c['title']):
  concordance=review.get('individual_title_concordance')
  expected=TITLE_CONCORDANCES.get((c['artwork_id'],rc['url'],original[0],c['title']))
  if not expected or concordance!=expected:raise ValueError('Original-language source title differs')
 adapted=copy.deepcopy(c);adapted['external_id']=review['wikiart_id'];adapted['alternate_title']=review['wikiart_title']
 facts=original_facts(adapted,data,rc)
 if urlparse(facts['source_image_url']).path.split('!',1)[0]!=urlparse(c['prior_index_lead']['image']).path.split('!',1)[0]:raise ValueError('Source photo differs from selected metadata lead')
 facts['native_object_review']=review;facts['native_original_title']=original[0]
 return facts

wiki.page_facts=page_facts
wiki.select=lambda limit:snapshot()

def references():
 reviews=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks']
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  if reviews[c['artwork_id']]['decision']!='continue_to_visual_review':continue
  url=native_facts(c)['reference_image_url'];path=base.ARCHIVE/'source-images'/RUN.name/'private-museum-reference'/(c['artwork_id']+'.image');receipt=RUN/'metadata/reference-images'/(c['artwork_id']+'.json')
  if receipt.exists():continue
  fetch=core.Fetcher(RUN/'metadata');core.provider_rate_slot(urlparse(url).hostname)
  with fetch.session.get(url,timeout=(15,45),allow_redirects=False) as response:
   response.raise_for_status()
   if response.status_code!=200 or len(response.content)>15000000:raise ValueError('Unexpected reference response')
   data=response.content
  core.save_new(path,data);core.save_new(receipt,dict(url=url,at=core.now(),path=str(path),sha256=core.sha(data),bytes=len(data),usage='Private visual identity reference only; WikiArt is the approved attached source.'))
  print('Private native reference',c['title'],c['accession_number'],flush=True)

def version(im,approved=False):
 rows=json.loads((RUN/'object-version-review.json').read_bytes())['images'];matches=[r for r in rows if r['artwork_id']==im['artwork_id']]
 if len(matches)!=1:raise ValueError('Individual physical-version review missing')
 review=matches[0]
 if approved and review['decision']!='approved':raise ValueError('Physical version remains held')
 if any(review[k]!=im[k] for k in ('source_sha256','sha256','source_image_url','external_id','scheme')):raise ValueError('Reviewed version changed')
 if review!=im['raw'].get('object_version_review') or review['note'] not in im['attribution_text']:raise ValueError('Individual version evidence omitted')
 ref=json.loads((RUN/'metadata/reference-images'/(im['artwork_id']+'.json')).read_bytes());data=Path(ref['path']).read_bytes()
 if review['reference_capture']!=ref or core.sha(data)!=ref['sha256'] or len(data)!=ref['bytes'] or ref['url']!=native_facts(im)['reference_image_url']:raise ValueError('Native visual reference changed')
 if review.get('additional_reference'):
  extra=review['additional_reference'];data=Path(extra['path']).read_bytes()
  if extra!=json.loads((RUN/'metadata/bookplate-print-reference.json').read_bytes()) or core.sha(data)!=extra['sha256'] or len(data)!=extra['bytes']:raise ValueError('Additional physical-version reference changed')

def attach(db,im,target):
 version(im,True);result=original_attach(db,im,target)
 if result=='attached':db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',(BASIS,im['media_id']))
 return result

base.m.attach=attach

def verify():
 for im in base.prepared():wiki.verify_image(im);version(im)
 wiki.verify()
 with base.connect() as db:
  for row in json.loads((RUN/'apply-receipt.json').read_bytes())['receipts']:
   if row['result']!='attached':continue
   im=json.loads((RUN/'images'/(row['artwork_id']+'.json')).read_bytes());version(im,True)
   if db.execute('SELECT rights_basis FROM media_rights_evidence WHERE media_id=%s',(im['media_id'],)).fetchone()['rights_basis']!=BASIS:raise ValueError('Stored identity basis differs')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','references','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':wiki.research(8)
 elif a.phase=='prepare':wiki.prepare()
 elif a.phase=='apply':base.apply()
 else:globals()[a.phase]()
