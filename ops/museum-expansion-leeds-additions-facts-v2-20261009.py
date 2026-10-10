"""Exact selected Cotmania facts preserve uncertainty, paired sides and attributed makers."""
import collections,gzip,hashlib,html,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-leeds-additions-common-20261009.py');o=module('o','museum-expansion-leeds-additions-objects-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked

def bare(v):return re.sub(r',\s*(?:(?:British|English),\s*)?\d{4}\s*-\s*\d{4}$','',v).strip()
def facts(r):
 p=r['parsed'];fs=p['fields'];issues=[];assert not set(p['repeated'])-{'Artist','Associated Person'};assert r['capture']['receipt']['status']==200;assert m.norm(fs['Title'])==m.norm(html.unescape(r['index']['title']));assert fs['Reference']==r['index']['reference'];dates=o.date(fs['Date']);assert dates==tuple(r['date']);assert fs['Object name'] in ['Drawing','Watercolour'];makers=p['repeated'].get('Artist',[fs['Artist']]) if 'Artist' in fs else [];labels=[bare(v) for v in makers];creator='; '.join(labels)
 if not makers:
  assert r['source_id']=='210035' and 'this is not in Cotman' in p['text'] and 'most likely explanation' in p['text'] and 'work of one of his pupils at Hovingham' in p['text'];creator='Unidentified pupil of John Sell Cotman (probably a member of the Worsley family)';labels=[creator];issues.append('source_index_maker_rejected')
 if any(re.search(r'\b(?:attributed|composite|possibly|sometimes|formerly|previously|studio|pupil|after)\b',v,re.I) for v in labels):issues.append('qualified_creator')
 if re.search(r'\b(?:recto|verso|after|copy|copies|pupil|mounted together|two sheets)\b',fs['Title'],re.I):issues.append('physical_sides_or_derivative')
 if re.search(r'\b(?:missing|stolen|lost|returned|restituted|loan)\b',fs.get('Credit Line',''),re.I):issues.append('holding_qualification')
 raw=gzip.decompress((m.ROOT/r['capture']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==r['capture']['receipt']['sha256'];soup=o.n.n.BeautifulSoup(raw,'html.parser');sections={}
 for li in soup.select('ul[uk-accordion] > li'):
  h=li.select_one('.uk-accordion-title');body=li.select_one('.uk-accordion-content')
  if h and body:sections[h.get_text(' ',strip=True)]=body.get_text(' ',strip=True)
 provenance=sections.get('Provenance','')
 if not provenance:issues.append('provenance_section_absent')
 if re.search(r'\b(?:missing|stolen|restituted|deaccessioned)\b',provenance,re.I):issues.append('holding_history_requires_review')
 titles={fs['Title']}
 titles.update(re.findall(r"(?:Called|called|Sometimes called)\s+'([^']+)'",fs['Title']))
 identity_names=[re.sub(r'^(?:Drawn by|Composite of|Possibly by|Sometimes attributed to|Formerly attributed to|Previously attributed to|Studio of|Associated artist|After)\s+','',v,flags=re.I) for v in labels]
 return dict(source_id=r['source_id'],source_url=r['index']['url'],title=fs['Title'],titles=sorted(titles),creator_label=creator,identity_creator_labels=identity_names,source_fields=dict(fs,ATTRIBUZIONI=creator),source_artist_fields=makers,inventory=fs['Reference'],normalized_inventory=fs['Reference'],date_display=fs['Date'],first=dates[0],last=dates[1],date_precision=dates[2],work_type='painting' if fs['Object name']=='Watercolour' else 'drawing',object_form='watercolour' if fs['Object name']=='Watercolour' else 'drawing',medium=fs.get('Medium') or None,dimensions_text=fs.get('Dimensions') or None,provenance=provenance,sections=sections,native_page_urls=[r['index']['url']],native_metadata_urls=[],artuk_url='',museum_qid=s.QID,issues=issues)
def rows():
 out=[];errors=[]
 for name in ['cotmania-objects-001.json.gz','cotmania-extra-objects-001.json.gz']:
  for r in m.load(RUN/name)['rows']:
   try:
    f=facts(r);out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=s.IID,facts=f,issues=f['issues']))
   except Exception as e:errors.append(dict(number=r['number'],error=type(e).__name__+': '+str(e)))
 return out,errors
def main():
 rs,errs=rows();m.save(RUN/'candidate-facts-002.json.gz',dict(at=m.now(),rows=rs,source_fact_holds=errs,source_references=[ref(RUN/n) for n in ['cotmania-objects-001.json.gz','cotmania-extra-objects-001.json.gz']],parser_reference=ref(Path(__file__).resolve()),read_only=True));print(json.dumps(dict(rows=len(rs),holds=errs,issues=dict(collections.Counter(v for r in rs for v in r['issues'])))),flush=True)
if __name__=='__main__':main()
