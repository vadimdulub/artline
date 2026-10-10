"""Literal Southampton object facts; artist/acquisition dates never supply creation."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-southampton-objects-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref;IID='f751c09d-2023-5b1b-935b-3aae9a3f842a'
def checked(d):
 p=m.ROOT/d['path'];assert ref(p)==d;return p
def creation(raw):
 t=(raw or '').strip();match=re.fullmatch(r'(\d{3,4})(?:\s*[-–]\s*(\d{4}))?(\s*\(c\.\))?',t)
 if not match:return dict(first=None,last=None,date_precision='unknown',date_issue='No explicit supported object creation date in Date field')
 first=int(match[1]);last=int(match[2] or match[1]);precision=('circa_range' if match[2] else 'circa') if match[3] else ('range' if match[2] else 'exact')
 if not 100<=first<=last<=1970 or match[3] and last==1970:return dict(first=None,last=None,date_precision='unknown',date_issue='Explicit source creation outside cutoff or uncertain at cutoff')
 return dict(first=first,last=last,date_precision=precision,date_issue=None)
def creator(raw):
 return re.sub(r'\s*\((?:(?:c\.|b\.)?\s*\d{3,4})(?:\s*[-–]\s*(?:c\.)?\s*\d{3,4})?\)\s*$','',raw or '').strip()
def inventory_aliases(raw):
 match=re.fullmatch(r'SOTAG\s*:\s*(\d+(?:/\d+)*)',raw or '');assert match,raw;v=match[1];out={v}
 bits=v.split('/')
 if len(bits)==2 and len(bits[0])==4:out.add('/'.join(reversed(bits)))
 return sorted(out)
def body(cap):
 raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];return raw
def facts(row):
 p=row['parsed'];assert n.parsed(body(row['capture']))==p;fields={v['label']:v['value'] for v in p['fields']};assert len(fields)==len(p['fields']) and set(fields)=={'Medium','Date','Dimensions','Acquisition Number','Credit Line'}
 card=row['card'];cap=row['capture']['receipt'];assert cap['url']==cap['final_url']==card['url'] and card['url'].startswith('https://southamptoncityartgallery.com/object/');assert m.norm(p['object_title'])==m.norm(card['title']);label=creator(p['object_creator']);assert label
 medium=fields['Medium'] or None;worktype='painting' if medium and re.match(r'^(?:oil|acrylic|tempera)\b',medium) else 'watercolor' if medium and re.match(r'^(?:watercolour|gouache)\b',medium) else 'print' if medium=='printing ink on paper' else 'unknown'
 issues=[]
 if not fields['Credit Line']:issues.append('Missing explicit collection acquisition credit')
 if re.search(r'\b(?:loan|lent|deposit|returned|until)\b',fields['Credit Line'],re.I):issues.append('Collection credit requires loan/tenure review')
 if re.search(r'\b(?:attributed|after|copy|copies|replica|workshop|school|circle|follower)\b',label,re.I):issues.append('Qualified creator retained for editorial review')
 return dict(source_id=card['source_id'],source_url=card['url'],title=p['object_title'],titles=[p['object_title']],creator_label=label,native_creator_label=p['object_creator'],source_fields={'ATTRIBUZIONI':label},date_display=fields['Date'] or None,**creation(fields['Date']),inventory=fields['Acquisition Number'],inventory_aliases=inventory_aliases(fields['Acquisition Number']),medium=medium,dimensions_text=fields['Dimensions'] or None,work_type=worktype,object_form=None,native_page_urls=[card['url'].replace('https://southamptoncityartgallery.com/','https://www.southamptoncityartgallery.com/')],native_metadata_urls=[],native_fields=fields,narrative=p['narrative'],rights=None,publisher_heading='Southampton City Art Gallery',native_issues=issues,source_note='Exact native object Date,Medium,Dimensions,Acquisition Number and Credit Line. Literal creator spelling preserved without life dates in creator label; full original label retained here. Asset URL is not an accession. Acquisition and maker life dates do not date the work. Holding does not establish present custody/display. No image rights inferred or reproduction downloaded.')
def rows():
 cap=m.load(RUN/'native-captured-001.json.gz');assert not cap['requests_stopped'] and not cap['unprocessed_numbers'];out=[]
 for v in cap['rows']:
  x=m.load(checked(v['reference']));assert x['state']=='captured_metadata';f=facts(x);out.append(dict(number=x['number'],source_id=f['source_id'],institution_id=IID,facts=f,source_reference=v['reference'],retrieved_at=x['capture']['receipt']['retrieved_at'],state='candidate' if not f['date_issue'] and not f['native_issues'] else 'source_hold'))
 assert len(out)==80;return out
def main():
 dest=RUN/'native-candidates-001.json.gz';assert not dest.exists();rs=rows();m.save(dest,dict(at=m.now(),rows=rs,parser_reference=ref(Path(__file__).resolve()),capture_reference=ref(RUN/'native-captured-001.json.gz'),policy='80 selected native object facts. Date-field precision only; narrative dates need separate editorial evidence. Unknown dates,qualified creators,print editions,sets and near versions are not automatically approved. All existing artwork fields remain untouched.'))
 print(json.dumps(dict(rows=len(rs),states=dict(collections.Counter(v['state'] for v in rs)),holds=[dict(number=v['number'],title=v['facts']['title'],date_issue=v['facts']['date_issue'],native_issues=v['facts']['native_issues']) for v in rs if v['state']!='candidate'])),flush=True)
if __name__=='__main__':main()
