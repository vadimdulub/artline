"""Review84 Leeds objects;80 supported holdings and four unresolved physical identities."""
import collections,gzip,hashlib,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-leeds-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);s=f.s;m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked
HOLDS={46:'Generic Composition by John Selby-Bigge has an unresolved supplied-CSV John Bigge record without inventory. Known museum versions have distinct dimensions/dates but the CSV identity remains unresolved; preserve all versions until identified.',51:'Object for Meditation I and II have identical118.5x174.2cm formats and unknown dates. Numbered titles and different inventories do not alone establish independent physical compositions.',57:'Object for Meditation II and I share identical118.5x174.2cm dimensions; verify the pair and possible duplicate/version relationship before counting both.',59:'Joseph Rhodes Moot Hall has an1825 Discovery Centre record70x95.5cm and an1825 Art Gallery record70.5x94.9cm. Nearly equal format,shared subject and wider museum service require composition/provenance reconciliation before assigning or duplicating.'}
NOTES={
4:'FreshQ5545665 confirms the exact object-level George W. Joy label; no artist link added.',
11:'Landscape Derivation32.7x63.5cm differs from Figure Derivation43.3x61.8cm in format,subject and inventory. Do not merge these different compositions.',
13:'Basil Taylor remains the source maker of this Bronte Sisters work; do not substitute the famous Branwell Bronte portrait or infer a creation date.',
17:'Figure Derivation43.3x61.8cm and Landscape Derivation32.7x63.5cm are separate source objects. Figure date remains unknown.',
19:'The explicit preparatory study38.1x27.9cm is by Norman Adams. Similar Study Head by J.Ottis Adams has a different maker authority; preserve study qualification.',
20:'Green-vase still life45.7x38.6cm and white-vase still life52x35.6cm differ in named vessel and physical format; inventories remain separate.',
22:'Tom Heron and Tom Laughton name different sitters and differ in date and dimensions; no title-similarity merge.',
23:'Lost Sheep1836 is portrait format28.5x24.1cm; Hepworth Sheep1835 is landscape20.3x30.2cm. Distinct dated compositions and inventories.',
25:'Two nondeprecated collection statements name the same Leeds gallery. Preserve both statements as evidence; count the physical object once.',
41:'FreshQ5545665 confirms George W. Joy. The historical subject does not replace the existing circa1893 creation date.',
45:'Margaret Green and Madeline Green are different makers. The Future1925 in Manchester is not The Table by Margaret Green.',
48:'White vase52x35.6cm is distinct from green vase45.7x38.6cm; both dates remain unknown.',
68:'Village Mill1895,60.9x94cm, differs from Windmill1911,77.2x127cm,in Rochdale. Separate named compositions and physical formats.',
77:'Existing circa1862–1863 range is preserved. Museum-authored discovery story uses1862; a holding-only update does not rewrite dates.'}

def raw_checked():
 cache={}
 def raw(dep,sha):
  p=checked(dep);key=str(p)
  if key not in cache:cache[key]=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
  assert hashlib.sha256(cache[key]).hexdigest()==sha;return cache[key]
 for name in ['source-context-001.json.gz','comparison-source-context-001.json.gz']:
  for r in m.load(RUN/name)['rows']:
   if not r.get('body_reference'):continue
   b=raw(r['body_reference'],r['raw_sha256'])
   if name.startswith('source-'):assert json.loads(b)['entities'][r['source_id']]==r['entity']
 x=m.load(RUN/'selected-authorities-001.json.gz');c=x['capture'];assert json.loads(raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']))['entities']==x['entities']
 for name in ['native-probes-001.json','selected-discovery-stories-001.json.gz']:
  for r in m.load(RUN/name)['rows']:
   c=r['capture'];b=raw(ref(m.ROOT/c['body_path']),c['receipt']['sha256']);assert BeautifulSoup(b,'html.parser').get_text(' ',strip=True)==r['parsed']['text']
 return len(cache)

def build():
 initial=m.load(RUN/'initial-scope-001.json.gz');facts,errors=f.rows();assert not errors;identity=m.load(RUN/'identity-001.json.gz');assert identity['rows']==facts;comps={v['number']:v for v in identity['comparisons']};src={v['number']:v for v in m.load(RUN/'source-context-001.json.gz')['rows']};artists={v['id']:v for v in initial['painters']};auth=m.load(RUN/'selected-authorities-001.json.gz')['entities'];assert auth[s.QID]['labels']['en']['value']=='Leeds Art Gallery';out=[]
 for row in facts:
  n=row['number'];r=src[n];a=r['artwork'];fact=row['facts'];comp=comps[n];assert {v['entity_id'] for v in comp['source_hits']}=={a['id']};state='editorial_hold' if n in HOLDS else 'approved_existing_holding'
  for link in fact['artist_links']:
   ar=artists[link['artist_id']]
   if fact['first']:assert not ((ar['birth_year'] and fact['last']<ar['birth_year']) or(ar['death_year'] and fact['first']>ar['death_year']))
  if state=='approved_existing_holding':
   allowed=[]
   if n in [4,41]:assert auth[fact['creator_qid']]['labels']['en']['value']==fact['creator_label'];assert not fact['artist_links'];allowed.append('creator_authority_requires_reconciliation')
   if n==19:allowed.append('filename_or_title_qualification')
   if 'missing_exact_artuk_collection_reference' in row['issues']:
    assert any(fact['artuk_url'] in s.references(v,'P854') for v in fact['source_collection_statements']);allowed.append('missing_exact_artuk_collection_reference')
   assert not set(row['issues'])-set(allowed),(n,row['issues']);assert fact['last'] is None or fact['last']<=1970
  basis='Exact artwork QID,creator,label and Leeds-gallery-qualified inventory identify the object. Saved collection statements reference the same ArtUK object by identifier or URL. '+NOTES.get(n,'No unresolved same-maker physical-version conflict survives the bounded source,title,inventory and gallery comparison.')
  limitation='Accept Leeds Art Gallery collection membership only. The city-wide fine-art service also includes Temple Newsam and Lotherton; venue and current display are not inferred from a Leeds service label or temporary exhibition. Wikidata/ArtUK statements are correlated secondary evidence,not newly fetched native object confirmation. ArtUK access hold respected. Preserve all existing dates,attributions,creator links,images,status and descriptive metadata. Confidence is editorial,not a calibrated probability.'
  if fact['date_precision']=='unknown':limitation+=' Unknown creation stays excluded from eligible pre1971 totals; accession,exhibition and artist lifespan dates are not creation dates.'
  out.append(dict(number=n,state=state,institution_id=s.IID,source_institution_id=r['institution_id'],existing_artwork_id=a['id'],previous_institution_id=None,pending_assertion_id=r['pending_assertion']['id'],supersede_assertion_ids=[r['pending_assertion']['id']] if state=='approved_existing_holding' else [],facts=fact,comparison=comp,source_reference=r['body_reference'],source_raw_sha256=r['raw_sha256'],retrieved_at=r['pending_assertion']['checked_at'],confidence=.85,basis=basis,limitation=limitation,hold_reason=HOLDS.get(n),metadata_review_note=NOTES.get(n)))
 assert collections.Counter(v['state'] for v in out)=={'approved_existing_holding':80,'editorial_hold':4};assert sum(len(v['supersede_assertion_ids']) for v in out)==80;return out

def main():
 dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();bodies=raw_checked();decisions=build();paths=[RUN/n for n in ['initial-scope-001.json.gz','source-context-001.json.gz','candidate-facts-001.json.gz','identity-001.json.gz','identity-citations-001.json.gz','comparison-source-context-001.json.gz','native-probes-001.json','selected-authorities-001.json.gz','selected-discovery-stories-001.json.gz']];m.save(dest,dict(at=m.now(),decisions=decisions,reviewer_reference=ref(Path(__file__).resolve()),dependencies=[ref(p) for p in paths],verified_raw_bodies=bodies,policy='80 selected existing gallery holdings,58 date-eligible and22undated. Four identity holds. Eight existing gallery holdings and all legacy fields preserved.'))
 print(json.dumps(dict(approved=80,held=4,unknown=22,eligible=58,verified_raw_bodies=bodies)),flush=True)
if __name__=='__main__':main()
