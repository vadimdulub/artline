#!/usr/bin/env python3
"""Review exact named-creator index metadata; never infer a missing picture page."""
import importlib.util,gzip,uuid,shutil,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('b','ops/random-ten-twenty-batches-round2-20261011.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
r=b.r;RUN=b.RUN

def main():
    dest=RUN/'reviewed-index-only-records.json'
    if dest.exists():print('Preserving reviewed index-only evidence.');return
    entries=r.load(RUN/'unlinked-index-entries.json.gz');changes=[]
    for entry in entries:
        raw=gzip.decompress((b.ROOT/entry['receipt']['body_path']).read_bytes());assert r.sha(raw)==entry['receipt']['sha256']
        soup=b.m.BeautifulSoup(raw,'html.parser');li=soup.select('li.painting-list-text-row')[entry['source_row']-1]
        spans=li.find_all('span',recursive=False)
        assert len(spans)>=2
        title=spans[0].get_text(' ',strip=True);date=spans[1].get_text(' ',strip=True).strip(' ,')
        if (title,date)!=(entry['title'],entry['source_date']):
            changes.append(dict(artist_id=entry['artist_id'],source_row=entry['source_row'],before=dict(title=entry['title'],source_date=entry['source_date']),after=dict(title=title,source_date=date),basis='The direct child spans supply the artwork title and date; an external reference anchor is not the title. Raw source receipt retained.'))
            entry.update(title=title,source_date=date,date=b.m.dates.creation_date(date))
    if changes:
        old=RUN/'unlinked-index-entries.json.gz';archive=RUN/'index-parser-review'/'unlinked-index-entries-before.json.gz';archive.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(old,archive);old.unlink();r.save_gz(old,entries)
        r.save(RUN/'index-parser-review'/'corrections.json',dict(at=r.now(),changes=changes))
    pairs={p['artist']['id']:p for p in b.cohort()};rows=[];notes={};holds=[]
    for entry in entries:
        aid=entry['artist_id'];pair=pairs[aid];api=r.load(RUN/'translations'/(aid+'-en.json.gz'))
        if not entry['date'] or entry['date']['creation_year_end']>1970:
            holds.append(dict(artist_id=aid,title=entry['title'],source_row=entry['source_row'],reason='Creation after 1970' if entry['date'] and entry['date']['creation_year_start']>1970 else 'No individual artwork page and no supported in-scope creation date; preserve the source listing without assuming an edition.'));continue
        matches=[v for v in api['items'] if v['title']==entry['title'] and str(v.get('yearAsString') or '')==entry['source_date']]
        identical=[v for v in entries if v['artist_id']==aid and v['title']==entry['title'] and v['source_date']==entry['source_date']]
        if len(matches)!=1 or len(identical)!=1:
            holds.append(dict(artist_id=aid,title=entry['title'],source_row=entry['source_row'],reason='Nonunique source title/date or absent exact public-API counterpart.'));continue
        meta=matches[0];assert b.q.norm(meta['artistName'])==b.q.norm(pair['source']['name'])
        sid=str(meta['contentId']);assert sid.isdigit();wid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://www.wikiart.org/legacy-content/'+sid))
        rights='Unknown; no per-image rights label available'
        hold='No individual WikiArt artwork-page link is supplied. Retain exact named-creator title/date metadata in review; no image identity, object edition, medium or holding is inferred, and no reproduction is requested.'
        page=dict(source_kind='artist_index_entry',url=entry['url'],title=entry['title'],metadata=dict(_id=None,legacyContentId=sid,title=entry['title'],year=entry['source_date'],artistName=meta['artistName'],artistUrl=b.m.urlsplit(pair['source']['url']).path,image=None),legacy_api_metadata={k:v for k,v in meta.items() if k!='image'},image_url=None,date=entry['date'],date_evidence='Exact title and date agree in the visible named-creator index and public artist API.',rights_label=rights,rights_status='unknown',fields={'Date':entry['source_date']},receipt=entry['receipt'],api_receipt=api['receipt'],index_entry=entry)
        rows.append(dict(action='create',artist_id=aid,artwork_id=wid,title=entry['title'],source_id=sid,source_url=entry['url'],source_scheme='wikiart-legacy-content-id',source_rights_label=rights,rights_status='unknown',confidence=.99,creator_evidence_note=meta['artistName']+' is explicitly named in the source index and exact public-API record; metadata-only review record.',identity_basis='Unique exact named-creator title and date agree with the public legacy content ID; fresh catalogue reconciliation still required.',image_hold=hold,index_entry=entry,page=page,record={'index':entry,'outcome':'unlinked_index_entry'},work=dict(id=wid,slug='wikiart-legacy-'+sid,title=entry['title'],alternate_title=None,normalized_title=b.s.normalized(entry['title']),work_type='unknown',medium_text=None,dimensions_text=None,**entry['date'])))
        notes[wid]=dict(source_url=entry['url'],title=entry['title'],reason=hold,hold_record=False)
    r.save(dest,dict(at=r.now(),rows=rows,source_count=len(rows),source_receipts_preserved=True,catalogue_reconciliation_pending=True))
    r.save(RUN/'index-only-source-review.json',dict(at=r.now(),records=notes,holds=holds,parser_corrections=len(changes),no_reproductions_downloaded=True))
    print(json.dumps({'metadata_candidates':len(rows),'parser_corrections':len(changes),'remaining_index_holds_or_exclusions':len(holds)}))

if __name__=='__main__':main()
