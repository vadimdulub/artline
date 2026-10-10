"""Read-only reconstruction of older unaccepted NMNI assertions; no network requests."""
import gzip,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/museum-expansion-20261006/native/britain-four-holdings-20261009'
def ref(p):return dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def main():
 dest=RUN/'additional-network-review-context-001.json.gz';assert not dest.exists();initial=load(RUN/'initial-scope-001.json.gz');source={v['artwork']['id']:v for v in load(RUN/'source-context-001.json.gz')['rows']};rows=[];refs={}
 for h in initial['snapshot']['assertions']:
  if h['institution_id']!='022bf39a-6bac-5a80-a905-e603077e3718' or h['review_state']!='review' or h['superseded_by'] or h['artwork_id'] not in source:continue
  e=json.loads(h['evidence_note']);p=ROOT/e['evidence_path'];raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==e['source_response_sha256'];refs[str(p)]=ref(p);text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True);r=source[h['artwork_id']];assert r['artwork']['accession_number'] in text
  rows.append(dict(number=r['number'],assertion=h,evidence=e,body_reference=ref(p),text=text,review_note='Original unaccepted broader-network candidate preserved unchanged. No extra acceptance or silent supersession.' if r['number']!=42 else 'Original automatic qualified_creator flag is retained as historical evidence. The actual MDS production-person field is unqualified Wilson,James Glen1827-1863,and fresh native object repeats that maker. Probably in the description modifies the ship destination,not artist attribution. Exact BELUM.U178,title and1852 creation agree.'))
 assert len(rows)==21;dest.write_bytes(gzip.compress((json.dumps(dict(rows=rows,body_references=list(refs.values()),script_reference=ref(Path(__file__).resolve()),read_only=True,policy='Preserve these21 older network review assertions unchanged.19 belong to approved objects and2 to held date/scope cases.47 accepted network assertions are separately reviewed for branch refinement. No source evidence or historic review-state mutation.'),ensure_ascii=False,indent=2)+'\n').encode(),mtime=0));print(json.dumps(dict(rows=len(rows),raw_bodies=len(refs))))
if __name__=='__main__':main()
