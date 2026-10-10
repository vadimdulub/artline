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
 assert len(out)==36
 history=m.load(RUN/'collection-history-001.json');body(history['capture']);permanent=m.load(RUN/'permanent-galleries-001.json');body(permanent['capture']);ht=history['parsed']['text'];pt=permanent['parsed']['text'];paper=RUN/'scholarly-version-source-001.json';proof=paper.read_text();assert 'Accession Number 577' in proof and 'FAO3' in proof
 for row in out:
  v=row['facts'];num=row['number'];v['supplemental_references']=[];v['derived_fields']=[]
  if num==1:v['creator_label']='Unidentified artist; signature read as J.W.S.';v['derived_fields'].append('qualified_creator_label_from_object_narrative')
  if num==2:v['titles'].append('The Lady of the Wreath')
  if num==5:
   v.update(inventory='577',medium='Oil on canvas',dimensions_text='239 x 174 cm',work_type='painting');v['supplemental_references'].append(ref(paper));v['derived_fields']+=['inventory_medium_dimensions_from_archival_research']
  if num==7:
   assert "Jan Griffier the Younger (1739-40)" in pt;v.update(date_display='1739–1740',first=1739,last=1740,date_precision='range');v['titles'].append('The Thames During the Great Frost of 1739');v['supplemental_references'].append(ref(RUN/'permanent-galleries-001.json'));v['derived_fields'].append('creation_range_from_official_galleries_page_GAC1739_preserved')
  if num==11:v['titles'].append('The Flight of Madeline and Porphyro during the Drunkenness Attending the Revelry')
  if num==20:
   assert 'a full size sketch in oils by John Constable Salisbury Cathedral from the Meadows (1829-31)' in ht;v.update(title='Salisbury Cathedral from the Meadows (full-size oil sketch)',titles=['Salisbury Cathedral','Salisbury Cathedral from the Meadows','Salisbury Cathedral from the Meadows (full-size oil sketch)'],date_display='1829–1831',first=1829,last=1831,date_precision='range',date_issue=None,medium='Oil',work_type='painting',native_issues=[]);v['supplemental_references'].append(ref(RUN/'collection-history-001.json'));v['derived_fields']+=['qualified_fullsize_sketch_title_creation_and_medium_from_official_collection_history']
  if num==23:
   assert "Millais's 1849 watercolour version of Lorenzo and Isabella" in ht;v.update(title='Lorenzo and Isabella (watercolour version)',titles=['Lorenzo and Isabella','Lorenzo and Isabella (watercolour version)'],date_display='1849',first=1849,last=1849,date_precision='exact',date_issue=None,medium='Watercolour',work_type='painting',native_issues=[]);v['supplemental_references'].append(ref(RUN/'collection-history-001.json'));v['derived_fields']+=['qualified_watercolour_version_title_creation_and_medium_from_official_collection_history']
  if num in [1,2,4,7,11,12,15,16,19,21,22,25,26,29,34,36]:
   v['work_type']='painting';v['derived_fields'].append('painting_form_editorially_reviewed_against_publisher_object_narrative_and_collection_context')
  if num==12:v['medium']='Oil';v['derived_fields'].append('oil_medium_from_explicit_oil_study_title_and_narrative')
  row['state']='candidate' if not v['date_issue'] and not v['native_issues'] else 'source_hold'
 return out
def main():
 p=RUN/'native-candidates-002.json.gz';assert not p.exists();rs=rows();m.save(p,dict(at=m.now(),rows=rs,script_reference=ref(Path(__file__).resolve()),capture_reference=ref(RUN/'native-captured-001.json.gz'),policy='36 metadata records reviewed before selection. No automatic addition from partner status or source date. Explicit creator qualification,narrative conflicts,related versions and duplicate online presentations need editorial review.'))
 print(json.dumps(dict(rows=len(rs),states=dict(collections.Counter(v['state'] for v in rs)),dated_candidates=[v['number'] for v in rs if v['state']=='candidate'])),flush=True)
if __name__=='__main__':main()
