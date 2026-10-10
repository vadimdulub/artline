"""Exact museum-published asset facts; preserve unknown fields and versions."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-guildhall-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref;IID='03058adb-4b2a-5a45-849d-2393f4229f9b'
def checked(d):
 p=m.ROOT/d['path'];assert ref(p)==d;return p
def creation(raw):
 t=(raw or '').strip();match=re.fullmatch(r'(c\.)?\s*(\d{3,4})(?:[-–](\d{4}))?',t)
 if not match:return dict(first=None,last=None,date_precision='unknown',date_issue='No explicit supported artwork creation date')
 first=int(match[2]);last=int(match[3] or match[2]);precision=('circa_range' if match[3] else 'circa') if match[1] else ('range' if match[3] else 'exact')
 if not 100<=first<=last<=1970 or match[1] and last==1970:return dict(first=None,last=None,date_precision='unknown',date_issue='Source creation outside cutoff or uncertain at cutoff')
 return dict(first=first,last=last,date_precision=precision,date_issue=None)
def body(c):
 raw=gzip.decompress((m.ROOT/c['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==c['receipt']['sha256'];return raw
def facts(row):
 p=row['parsed'];assert n.g.parsed(body(row['capture']))==p;fields={v['label']:v['value'] for v in p['fields']};assert len(fields)==len(p['fields']);card=row['card'];assert p['headings']==[fields['Title']] and fields['Title']==card['title'] and fields['Creator']==card['creator'];assert row['capture']['receipt']['url']==row['capture']['receipt']['final_url']==card['url'];assert '/partner/guildhall-art-gallery' in p['partner_links'];assert p['publisher_heading'].startswith('Guildhall Art Gallery');text=p['text'];head=p['publisher_heading'];narr=text[text.index(head)+len(head):].split('Details')[0].strip()
 return dict(source_id=card['source_id'],source_url=card['url'],title=fields['Title'],titles=[fields['Title']],creator_label=fields['Creator'],source_fields={'ATTRIBUZIONI':fields['Creator']},date_display=fields.get('Date Created'),**creation(fields.get('Date Created')),inventory=None,medium=None,dimensions_text=None,work_type='unknown',object_form=None,native_page_urls=[],native_metadata_urls=[],native_fields=fields,narrative=narr,rights=fields.get('Rights'),publisher_heading=p['publisher_heading'],native_issues=[] if fields.get('Location')=='Guildhall Art Gallery' and fields.get('Original Source')=='https://www.cityoflondon.gov.uk/guildhallartgallery' else ['Publisher alone does not establish collection membership'],source_note='Museum-published Google Arts and Culture asset metadata. Missing inventory,medium,dimensions and dates remain unknown. Asset IDs are not inventory numbers. Holdings require explicit collection context; publisher branding alone is insufficient. No image or current-display claim.')
def rows():
 cap=m.load(RUN/'native-captured-001.json.gz');assert not cap['requests_stopped'] and not cap['unprocessed_numbers'];out=[]
 for v in cap['rows']:
  x=m.load(checked(v['reference']));assert x['state']=='captured_metadata';f=facts(x);out.append(dict(number=x['number'],source_id=f['source_id'],institution_id=IID,facts=f,source_reference=v['reference'],retrieved_at=x['capture']['receipt']['retrieved_at'],state='candidate' if not f['date_issue'] and not f['native_issues'] else 'source_hold'))
 assert len(out)==36;return out
def main():
 p=RUN/'native-candidates-001.json.gz';assert not p.exists();rs=rows();m.save(p,dict(at=m.now(),rows=rs,script_reference=ref(Path(__file__).resolve()),capture_reference=ref(RUN/'native-captured-001.json.gz'),policy='36 metadata records reviewed before selection. No automatic addition from partner status or source date. Explicit creator qualification,narrative conflicts,related versions and duplicate online presentations need editorial review.'))
 print(json.dumps(dict(rows=len(rs),states=dict(collections.Counter(v['state'] for v in rs)),dated_candidates=[v['number'] for v in rs if v['state']=='candidate'])),flush=True)
if __name__=='__main__':main()
