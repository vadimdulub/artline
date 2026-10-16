#!/usr/bin/env python3
"""Retain four unambiguous Larry Poons index records without requesting their images."""
import importlib.util,copy,gzip,shutil,uuid
from pathlib import Path
sp=importlib.util.spec_from_file_location('d','ops/random-ten-twenty-batches-delivery-20261010.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d);r=d.r;R=d.RUN

def main():
 if (R/'selection-revisions/larry-poons-index-metadata/final-outcome.json').exists():
  print('Preserving the reviewed Larry Poons index outcome.');return
 assert (R/'pages-summary.json').exists()
 assert len(list((R/'selections').glob('*.json.gz')))==200
 assert not (R/'delivery-plans').exists()
 pair=next(p for p in d.m.cohort() if p['source']['url']=='https://www.wikiart.org/en/larry-poons');aid=pair['artist']['id']
 entries=r.load(R/'unlinked-index-entries.json.gz');old=copy.deepcopy(entries);idx=next(x for x in entries if x['artist_id']==aid and x['title']=='www.tate.org.uk')
 raw=gzip.decompress((d.ROOT/idx['receipt']['body_path']).read_bytes());assert r.sha(raw)==idx['receipt']['sha256']
 soup=d.m.BeautifulSoup(raw,'html.parser');li=soup.select('li.painting-list-text-row')[idx['source_row']-1];spans=li.find_all('span',recursive=False)
 assert spans[0].get_text(' ',strip=True)=='Out';idx.update(title='Out',source_date='1967',date=d.m.dates.creation_date('1967'))
 arch=R/'selection-revisions/larry-poons-index-metadata';arch.mkdir(parents=True,exist_ok=True)
 shutil.copy2(R/'unlinked-index-entries.json.gz',arch/'unlinked-index-entries-before.json.gz')
 (R/'unlinked-index-entries.json.gz').unlink();r.save_gz(R/'unlinked-index-entries.json.gz',entries)
 r.save(arch/'parser-correction.json',{'at':r.now(),'before':next(x for x in old if x['source_row']==idx['source_row'] and x['artist_id']==aid),'after':idx,'reason':'Visible direct child spans supply Out and 1967. The external Tate link is a reference, not the artwork title. Original raw source receipt preserved.'})
 api=r.load(R/'translations'/(aid+'-en.json.gz'));titles={'Out','Cutting Water','Mary Queen of Scots','Reuben - As the Mississippi Flows on to the Sea'};rows=[];notes={}
 selected=[x for x in entries if x['artist_id']==aid and x['title'] in titles];assert len(selected)==4,[(x['title'],x['source_date']) for x in entries if x['artist_id']==aid]
 for entry in selected:
  matches=[x for x in api['items'] if x['title']==entry['title'] and str(x['yearAsString'])==entry['source_date']];assert len(matches)==1
  meta=matches[0];sid=str(meta['contentId']);wid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikiart.org/legacy-content/'+sid));assert entry['date']['creation_year_end']<=1970
  rights='Unknown; no per-image rights label available';hold='WikiArt supplies no individual artwork-page link. Retain exact named-creator title/date metadata in review; image identity and version cannot be established from this listing, so no reproduction was requested or attached.'
  page=dict(source_kind='artist_index_entry',url=entry['url'],title=entry['title'],metadata=dict(_id=None,legacyContentId=sid,title=entry['title'],year=entry['source_date'],artistName=meta['artistName'],artistUrl='/en/larry-poons',image=None),legacy_api_metadata={k:v for k,v in meta.items() if k!='image'},image_url=None,date=entry['date'],date_evidence='Exact title and year agree in the visible named-creator index and public artist API.',rights_label=rights,rights_status='unknown',fields={'Date':entry['source_date']},receipt=entry['receipt'],api_receipt=api['receipt'],index_entry=entry)
  row=dict(action='create',artist_id=aid,artwork_id=wid,title=entry['title'],source_id=sid,source_url=entry['url'],source_scheme='wikiart-legacy-content-id',source_rights_label=rights,rights_status='unknown',confidence=.99,creator_evidence_note='Larry Poons is explicitly named in the source artist index and exact matching API record. Artwork-page identity is unavailable; metadata-only review record.',identity_basis='Unique exact named-creator index title and year agree with the public legacy API content ID; no medium, holding, picture or object edition is inferred.',image_hold=hold,index_entry=entry,page=page,record={'index':entry,'outcome':'unlinked_index_entry'},source_policy='User-approved WikiArt collection and incomplete-data preferences; no image attachment.',work=dict(id=wid,slug='wikiart-legacy-'+sid,title=entry['title'],alternate_title=None,normalized_title=d.s.normalized(entry['title']),work_type='unknown',medium_text=None,dimensions_text=None,**entry['date']))
  rows.append(row);notes[wid]=dict(source_url=entry['url'],title=entry['title'],reason=hold,hold_record=False)
 r.save(R/'reviewed-index-only-records.json',dict(at=r.now(),rows=rows,source_count=4,source_receipts_preserved=True))
 for folder,suffix in [('selections','.json.gz'),('selection-pins','.json'),('image-audits','.json')]:
  p=R/folder/(aid+suffix);shutil.move(p,arch/(folder+suffix))
 p=d.BACKUP/'selection-preimages'/(aid+'.json.gz');dest=d.BACKUP/'superseded-selection-preimages'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(p,dest)
 d.s.select();d.audits()
 plan=r.load(R/'selections'/(aid+'.json.gz'));active={x['artwork_id'] for x in plan['rows'] if x['action']=='create'};assert len(active)==3
 r.save(R/'editorial-review-decisions/larry-index.json',{'at':r.now(),'records':{k:v for k,v in notes.items() if k in active}})
 r.save(arch/'final-outcome.json',{'at':r.now(),'metadata_additions':3,'Out':'An existing object candidate was found; no duplicate record or image delivery.'})
 print('Larry Poons: three metadata-only additions; Out retained as an existing-object lead.')
if __name__=='__main__':main()
