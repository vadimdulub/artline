"""Five selected object pages from two already captured museum-published stories."""
import importlib.util,json,re,gzip
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-guildhall-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n)
SELECTED=[(20,'cuyp-loans-story','salisbury-cathedral-from-the-meadows-john-constable/DAEy9HYrq2u2SA'),(37,'faith-story','early-morning-in-the-wilderness-of-shur-frederick-goodall/nAHlC6L_rXfw2Q'),(38,'faith-story','faith-john-phillip/nAF6Si21YkmNzw'),(39,'faith-story','herod-s-birthday-feast-edward-armitage/eQGuTQQxPcKvmA'),(40,'faith-story','naomi-luke-fildes/0QHrRkN_rnCSaw')]
def main():
 dest=n.RUN/'additional-captured-001.json';assert not dest.exists();out=[]
 for number,story,path in SELECTED:
  origin=n.RUN/(story+'-001.json');x=n.m.load(origin);body=gzip.decompress((n.m.ROOT/x['capture']['body_path']).read_bytes()).decode();assert '/asset/'+path in body;url='https://artsandculture.google.com/asset/'+path;raw,cap=n.g.p.n.capture('guildhall_gac',url);parsed=n.g.parsed(raw);fields={v['label']:v['value'] for v in parsed['fields']};card=dict(source_id=path.rsplit('/',1)[-1],url=url,title=fields['Title'],creator=fields['Creator']);p=n.RUN/'additional-selected-001'/('%03d.json'%number);assert not p.exists();n.m.save(p,dict(number=number,state='captured_metadata',card=card,capture=cap,parsed=parsed,story_reference=n.ref(origin)));out.append(dict(number=number,reference=n.ref(p)));print(json.dumps(dict(number=number,fields=fields,publisher=parsed['publisher_heading'])),flush=True)
 n.m.save(dest,dict(at=n.m.now(),rows=out,script_reference=n.ref(Path(__file__).resolve()),policy='Exact embedded story asset links selected before requests. Four new faith-theme object leads and one identified Guildhall loan. No images.'))
if __name__=='__main__':main()
