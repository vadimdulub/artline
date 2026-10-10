"""One bounded native art-index page and an exact linked object page."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');n=module('n','museum-expansion-britain-nine-native-20261009.py');m=s.m;RUN=s.RUN;n.RUN=RUN
def main():
 dest=RUN/'harris-art-index-001.json.gz';assert not dest.exists();tax=m.load(RUN/'harris-taxonomy-001.json.gz');art=next(x for x in tax['rows'][0]['data'] if x['id']==31);assert art['slug']=='fine-art-collections';base=art['_links']['wp:post_type'][0]['href'];url=base+'&'+urlencode({'per_page':12,'page':1,'orderby':'id','order':'asc','_fields':'id,link,slug,title,content,acf,meta,collections,hf_cat_collection-item'});raw,cap=n.capture('harris',url);data=json.loads(raw);assert isinstance(data,list) and len(data)<=12 and all(31 in x['collections'] for x in data);print(json.dumps(dict(rows=len(data),sample=data[0]),ensure_ascii=False)[:9000],flush=True);selected=data[0];b,c=n.capture('harris',selected['link']);parsed=n.parsed(b);m.save(dest,dict(at=m.now(),url=url,capture=cap,data=data,selected_object=dict(id=selected['id'],url=selected['link'],capture=c,parsed=parsed),taxonomy_reference=s.ref(RUN/'harris-taxonomy-001.json.gz'),script_reference=s.ref(Path(__file__).resolve()),policy='12native Art index records maximum,one exact linked page to assess available date/inventory/creator evidence. No image downloads,publication-time date inference or database writes.'));print(json.dumps(dict(object_id=selected['id'],text=parsed['text'][-10000:]),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
