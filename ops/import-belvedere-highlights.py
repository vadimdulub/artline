#!/usr/bin/env python3
"""Import selected official Belvedere highlight facts; no website image reuse."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('import-austrian-catalogue.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
core=a.core;SOURCE='belvedere-official-highlights-20260916';SCHEME='belvedere-object'

def facts(obj,html):
    soup=BeautifulSoup(html,'html.parser');fields={};artists=[]
    for row in soup.select('.detailField'):
        label=row.select_one('.detailFieldLabel');value=row.select_one('.detailFieldValue')
        if not label or not value:continue
        k=label.get_text(' ',strip=True);v=value.get_text(' ',strip=True);fields.setdefault(k,[]).append(v)
        if k=='Artist':artists.append({'name_and_dates':v,'authority_urls':[x['href'] for x in value.select('a[href]')]})
    def one(key):
        values=fields.get(key,[])
        if len(values)!=1:raise ValueError('Missing or multiple official '+key)
        return values[0]
    kind=one('Object type');medium=one('Medium')
    # Two current English records translate Tafelbild as "Blackboard".
    # Their explicit source medium independently establishes a painted panel.
    painted_panel=kind=='Blackboard' and medium in ('Malerei auf Fichtenholz','Painting on limewood')
    if kind!='Painting' and not painted_panel:raise ValueError('Official classification is not a painting; separately review other painted forms')
    if len(artists)!=1:raise ValueError('Artist role is missing or multiple')
    maker=artists[0];text=maker['name_and_dates']
    if re.search(r'attributed|after|workshop|circle|copy|Nachfolge|Werkstatt|zugeschrieben',text,re.I):raise ValueError('Qualified creator requires attribution review')
    name=text.split(' (')[0].strip();years=[int(y) for y in re.findall(r'\b(?:1\d{3}|20\d{2})\b',text)]
    ulan=set()
    for u in maker['authority_urls']:
        match=re.search(r'(?:vocab\.getty\.edu/(?:page/)?ulan/|ulan/)(\d+)',u)
        if match:ulan.add(match[1])
    d=one('Date');norm=re.sub(r'\s+',' ',d).strip();hit=re.fullmatch(r'(c\. |ca\.? |ca\.?)?(\d{4})(?:\s*[/–-]\s*(\d{4}))?',norm)
    if not hit:raise ValueError('Official date needs manual normalization')
    lo,hi=int(hit[2]),int(hit[3] or hit[2])
    if not 1000<=lo<=hi<=1970:raise ValueError('Official creation bounds outside scope')
    fields={k:v for k,v in fields.items() if k in ('Artist','Date','Object type','Medium','Inventory number','Dimensions')}
    return {'object_id':obj['selection']['object_id'],'url':obj['capture']['url'],'title':obj['title'],'creator_name':name,'creator_years':years,'creator_ulan':sorted(ulan),'date_display':d,'creation_year_start':lo,'creation_year_end':hi,'date_precision':('circa' if lo==hi else 'circa_range') if hit[1] else ('exact' if lo==hi else 'range'),'accession_number':one('Inventory number'),'work_type':'painting','medium':one('Medium'),'dimensions':fields.get('Dimensions',[None])[0],'capture':obj['capture'],'selection_url':obj['selection']['selection_url'],'source_fields':fields,'metadata_reuse_basis':'Independently verified factual catalogue fields; no authored description or website image copied','image_status':'Exact native image rights unresolved; no image imported in this pass.'}

def plan(run):
    path=run/'belvedere-highlight-plan.json'
    if path.exists():return
    mp=a.load(run/'metadata-plan.json');authors={};byulan={};bynames=collections.defaultdict(list)
    native_qids=collections.defaultdict(set)
    for entityfile in (run/'wikimedia/entities').glob('Q*.json'):
        entity=a.load(entityfile)['entity']
        if 'Q303139' in a.m.ids(entity,'P195'):
            for oid in a.m.values(entity,'P5823'):
                if isinstance(oid,str):native_qids[oid].add(entity['id'])
    for q,ar in mp['targets']['local']['artists'].items():
        e=a.load(run/'wikimedia/entities'/(q+'.json'))['entity'];authors[q]=ar
        for u in a.m.values(e,'P245'):byulan.setdefault(u,[]).append(q)
        for n in a.r.labels(e):bynames[a.r.norm(n)].append(q)
    rows=[];held=[];root=run/'belvedere';preparsed=[]
    for file in sorted((root/'objects').glob('*.json')):
        obj=a.load(file)
        try:
            html=root/'captures'/(core.sha(obj['capture']['url'].encode())+'.html');assert core.sha(html.read_bytes())==obj['capture']['sha256'];preparsed.append(facts(obj,html.read_bytes()))
        except (ValueError,AssertionError) as exc:held.append({'object_id':obj['selection']['object_id'],'url':obj['capture']['url'],'reason':str(exc)})
    with a.connect('local',True) as db:
        names=[a.r.norm(x['creator_name']) for x in preparsed]
        extra=db.execute("SELECT p.id::text,p.slug,p.display_name,p.birth_year,p.death_year,ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata') qids,ARRAY(SELECT alias FROM artist_aliases n WHERE n.artist_id=p.id) aliases FROM artists p WHERE p.status<>'archived' AND (p.normalized_name=ANY(%s) OR p.id IN(SELECT artist_id FROM artist_aliases WHERE normalized_alias=ANY(%s)))",(names,names)).fetchall()
        for x in preparsed:
            if bynames[a.r.norm(x['creator_name'])]:continue
            matches=[p for p in extra if len(p['qids'])==1 and a.r.norm(x['creator_name']) in {a.r.norm(n) for n in [p['display_name']]+p['aliases']} and x['creator_years']==[p['birth_year'],p['death_year']] and p['birth_year'] is not None and p['death_year'] is not None]
            if len(matches)==1:
                p=matches[0];q=p['qids'][0];authors[q]={'birth':p['birth_year'],'death':p['death_year']};bynames[a.r.norm(x['creator_name'])].append(q)
    for x in preparsed:
        try:
            qs={q for u in x['creator_ulan'] for q in byulan.get(u,[])} or set(bynames[a.r.norm(x['creator_name'])])
            if len(qs)!=1:raise ValueError('Existing creator authority needs further reconciliation')
            q=qs.pop();ar=authors[q]
            if ar['birth'] is not None and ar['death'] is not None and x['creator_years'] and x['creator_years']!=[ar['birth'],ar['death']]:raise ValueError('Official artist lifespan differs from the selected authority')
            x['artist_qid']=q;x['wikidata_ids']=sorted(native_qids[x['object_id']]);rows.append(x)
        except (ValueError,AssertionError) as exc:held.append({'object_id':x['object_id'],'url':x['url'],'reason':str(exc)})
    out={'at':core.now(),'records':rows,'held':held,'targets':{}}
    for target in ('local','cloud'):
        states=[]
        with a.connect(target,True) as db:
            museum=db.execute("SELECT i.id::text,p.country_code FROM institutions i JOIN places p ON p.id=i.place_id WHERE i.slug='belvedere'").fetchone();assert museum and museum['country_code']=='AT';iid=museum['id']
            old=db.execute("SELECT a.id::text,a.slug,a.title,a.accession_number,a.status,a.revision,ARRAY(SELECT artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id) artist_ids FROM artworks a WHERE a.current_institution_id=%s",(iid,)).fetchall()
            for x in rows:
                artists=db.execute("SELECT p.id::text,p.display_name name FROM artists p JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata' WHERE e.external_id=%s AND p.status<>'archived'",(x['artist_qid'],)).fetchall();assert len(artists)==1;artist=artists[0];hits=[w for w in old if a.match.accession_key(w['accession_number'])==a.match.accession_key(x['accession_number'])];reason=None
                if len(hits)>1:reason='Multiple existing institutional accessions'
                existing=hits[0] if len(hits)==1 else None
                linked=db.execute("SELECT a.id::text,a.current_institution_id::text FROM artworks a JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata' WHERE e.external_id=ANY(%s)",(x['wikidata_ids'],)).fetchall()
                if linked:
                    if len(linked)!=1 or linked[0]['current_institution_id']!=iid or existing and existing['id']!=linked[0]['id']:reason='Native object and existing global authority need reconciliation'
                    elif not existing:existing=next(w for w in old if w['id']==linked[0]['id'])
                if len(x['wikidata_ids'])>1:reason='Multiple Wikidata identities use one native record'
                if existing and (existing['artist_ids']!=[artist['id']] or existing['status']=='archived'):reason='Existing accession artist or review context differs'
                if not existing:
                    names=[w for w in old if a.r.norm(w['title'])==a.r.norm(x['title']) and artist['id'] in w['artist_ids']]
                    if names:reason='Same creator/title needs inventory reconciliation'
                native=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(SCHEME,x['object_id'])).fetchall()
                if native and (not existing or len(native)!=1 or native[0]['entity_id']!=existing['id']):reason='Existing native object identity differs'
                states.append({'object_id':x['object_id'],'action':'held' if reason else 'existing' if existing else 'new','reason':reason,'artwork_id':existing['id'] if existing else a.uid('belvedere-highlight/'+x['object_id']),'slug':existing['slug'] if existing else 'belvedere-highlight-'+x['object_id'],'institution_id':iid,'artist_id':artist['id'],'artist_name':artist['name'],'existing':existing})
            b=Path.home()/'Library/Application Support/Artline/backups'/run.name/(target+'-belvedere-highlight-preimages.json');core.save_new(b,old)
        out['targets'][target]=states;print(target,'Official highlights',dict(collections.Counter(x['action'] for x in states)), 'source held',len(held),flush=True)
    core.save_new(path,out);core.save_new(run/'belvedere-highlight-plan-manifest.json',{'sha256':core.sha(path.read_bytes())})

def apply(run,target,limit=0):
    assert a.load(run/'backups.json')['cloud']['status']=='SUCCESSFUL'
    path=run/'belvedere-highlight-plan.json';assert core.sha(path.read_bytes())==a.load(run/'belvedere-highlight-plan-manifest.json')['sha256'];plan=a.load(path);rows={x['object_id']:x for x in plan['records']};sid=a.uid('source/'+SOURCE);counts=collections.Counter()
    with a.connect(target) as db:
        db.execute("INSERT INTO sources(id,slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'Belvedere: selected official highlights','collection_page','https://sammlung.belvedere.at/','https://sammlung.belvedere.at/') ON CONFLICT(id) DO NOTHING",(sid,SOURCE))
        states=plan['targets'][target][:limit] if limit else plan['targets'][target]
        for st in states:
            if st['action']=='held':counts['held']+=1;continue
            x=rows[st['object_id']];aid=st['artwork_id'];oid=x['object_id'];url=x['url'];at=x['capture']['retrieved_at']
            with db.transaction(),db.pipeline():
                db.execute("SET LOCAL lock_timeout='5s'");db.execute('SELECT pg_advisory_xact_lock(559220260916)')
                if db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND entity_id=%s AND source_id=%s AND field_name='official_object_identity'",(aid,sid)).fetchone():counts['already_applied']+=1;continue
                assert db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artist' AND entity_id=%s AND scheme='wikidata' AND external_id=%s",(st['artist_id'],x['artist_qid'])).fetchone(),'Creator import incomplete'
                if st['action']=='new':
                    assert not db.execute('SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s',(st['institution_id'],x['accession_number'])).fetchone(),'Concurrent accession collision'
                    db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,%s,%s,'review',true,%s,%s)",(aid,st['slug'],x['title'],a.r.norm(x['title']),x['date_display'],x['creation_year_start'],x['creation_year_end'],x['date_precision'],x['medium'],x['dimensions'],st['institution_id'],x['accession_number'],core.ACTOR,core.ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Official Belvedere Artist role; Getty ULAN or exact authority name and compatible life dates independently reconciled.')",(aid,st['artist_id']))
                    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,st['institution_id'],sid,url,'Current official Belvedere collection object '+oid+', accession '+x['accession_number']+'. No current display claim.',at))
                else:
                    current=db.execute('SELECT revision,status FROM artworks WHERE id=%s FOR UPDATE',(aid,)).fetchone();assert current and current['status']==st['existing']['status']
                    db.execute("UPDATE artworks SET medium_text=coalesce(nullif(medium_text,''),%s),dimensions_text=coalesce(nullif(dimensions_text,''),%s),updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s AND (nullif(medium_text,'') IS NULL OR nullif(dimensions_text,'') IS NULL)",(x['medium'],x['dimensions'],core.ACTOR,aid))
                    db.execute("UPDATE artworks SET creation_year_start=%s,creation_year_end=%s,date_display=%s,date_precision=%s,updated_at=now(),updated_by=%s,revision=revision+1 WHERE id=%s AND status='review' AND creation_year_start IS NULL AND creation_year_end IS NULL AND date_precision='unknown'",(x['creation_year_start'],x['creation_year_end'],x['date_display'],x['date_precision'],core.ACTOR,aid))
                existing=db.execute("SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(SCHEME,oid)).fetchall()
                if existing:assert len(existing)==1 and existing[0]['entity_id']==aid
                else:db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,oid,url,sid,at))
                if len(x['wikidata_ids'])==1:a.authority(db,'artwork',aid,x['wikidata_ids'][0],sid,at)
                a.citation(db,'artwork',aid,'official_object_identity',sid,oid,url,x,at)
                a.citation(db,'artwork',aid,'museum_highlight_selection',sid,oid,x['selection_url'],{'selection':'Official Belvedere highlights','museum_country':'AT','not_a_personal_masterpiece_selection':True,'not_an_on_view_assertion':True},at)
                db.execute('INSERT INTO source_institutions(source_id,institution_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(sid,st['institution_id']))
            counts[st['action']]+=1
        core.save_new(run/(target+'-belvedere-highlight-result'+('-canary' if limit else '')+'.json'),{'at':core.now(),'counts':dict(counts)});print(target,dict(counts),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud']);p.add_argument('--limit',type=int,default=0);args=p.parse_args();plan(args.run) if args.command=='plan' else apply(args.run,args.target,args.limit)
if __name__=='__main__':main()
