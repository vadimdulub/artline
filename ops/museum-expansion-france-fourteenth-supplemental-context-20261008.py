"""Check transferred-object URL aliases and repair slash-bearing source-ID extraction."""
import gzip,hashlib,importlib.util,json
from pathlib import Path
from urllib.parse import urljoin,unquote
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-fourteenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m
def main():
    dest=f.RUN/'supplemental-context-001.json.gz';assert not dest.exists()
    cp=f.RUN/'physical-comparison-context-002.json.gz';ctx=f.RUN/'paris-object-context-checked-003.json.gz';cit=f.RUN/'identity-citations-002.json.gz'
    primary=m.load(cp);contexts=m.load(ctx);cs=m.load(cit)['citations'];resolved=[];deps={cp,ctx,cit,Path(__file__).resolve()}
    for miss in primary['unresolved_primary_records']:
        aid=miss['existing_artwork_id'];url=miss['source_url'];sid=unquote(url.split('/notice/joconde/',1)[1].rstrip('/'))
        assert sid=='0643D-3/2-1967' and miss['source_record_id']=='2-1967'
        c=next(v for v in cs if v['entity_id']==aid and v['source_url']==url);n=json.loads(c['evidence_note'])
        p=m.ROOT/(n.get('body_path') or n.get('evidence_path'));raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==(n.get('source_receipt',{}).get('sha256') or n.get('source_response_sha256'))
        rr=[r for r in json.loads(raw)['data'] if r['Reference']==sid];assert len(rr)==1;deps.add(p)
        resolved.append(dict(existing_artwork_id=aid,source_record_id=sid,source_url=url,literal_primary_record=rr[0],evidence_reference=f.ref(p),basis='The original helper split on the final slash and truncated a slash-bearing Joconde identifier. The cited body does contain the complete literal identifier; no source error or missing record is inferred. Frozen context002 is retained and supplemented.'))
    aliases=[]
    for c in contexts['rows']:
        if c['number'] not in [317,390]:continue
        p=f.checked(c['body_reference']);deps.add(p);soup=BeautifulSoup(gzip.decompress(p.read_bytes()),'html.parser')
        links=soup.select('#infos-secondaires-prolongement .field-name-field-oeuvres-en-rapport a');assert len(links)==1
        a=links[0];path=a['href'];assert 'Numéro radié' in a.get_text(' ',strip=True)
        cards=soup.select('article[about]');card=next(v for v in cards if v['about']==path);node=card['id'].removeprefix('node-');assert node=={317:'102005',390:'102009'}[c['number']]
        aliases.append(dict(number=c['number'],source_id=c['source_id'],body_reference=c['body_reference'],literal_relationship=a.get_text(' ',strip=True),path=path,node_id=node,urls=[urljoin(c['final_url'],path),'https://www.parismuseescollections.paris.fr/node/'+node],basis='The bottom related-object field supplies the specific transfer relationship. The matching article about/id attributes establish the node alias; unrelated recommendation cards do not establish relationships.'))
    urls=sorted({v for a in aliases for u in a['urls'] for v in [u,u+'/',u.replace('https:','http:'),u.replace('https:','http:')+'/']});nodeids=sorted(a['node_id'] for a in aliases)
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        citations=db.execute("SELECT entity_id::text,source_url,source_record_id,field_name FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url,field_name",(urls,)).fetchall()
        external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (external_id=ANY(%s) AND (scheme ILIKE '%%paris%%' OR scheme ILIKE '%%carnavalet%%'))) ORDER BY entity_id,scheme,external_id",(urls,nodeids)).fetchall()
    logs=[]
    for suffix in ['', '-r2','-r3']:
        p=Path('/Users/vadimdulub/Library/Logs')/('artline-france-fourteenth-comparison-context-002'+suffix+'-20261008.log')
        logs.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),outcome={'':'failed_assertion_before_artifact','-r2':'interrupted_before_artifact_due_to_redundant_1.1GB_CSV_rehashing','-r3':'success_after_caching_unchanged_CSV_reference'}[suffix]))
    m.save(dest,dict(at=m.now(),resolved_primary_records=resolved,transferred_object_aliases=aliases,query_urls=urls,query_node_ids=nodeids,citation_hits=citations,external_hits=external,read_only=True,database_writes=0,comparison_helper_attempts=logs,dependencies=[f.ref(p) for p in sorted(deps)],policy='Evidence supplement only. No existing catalogue changes. Missing or related source identifiers cannot authorize duplicate physical objects.'))
    print(json.dumps(dict(artifact=f.ref(dest),resolved_primary=len(resolved),transfer_aliases=len(aliases),citation_hits=len(citations),external_hits=len(external))),flush=True)
if __name__=='__main__':main()
