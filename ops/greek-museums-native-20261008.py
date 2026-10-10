#!/usr/bin/env python3
"""Selected native highlights and explicit undated objects closing directory gaps."""
import argparse, gzip, importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
d.PLAN='native-delivery-plan-v2.json.gz';d.FACTS='native-facts.json'
d.APPLIED='native-catalogue-applied.json';d.AFTER='native-catalogue-transaction-after.json.gz'


def probe(url):
    return d.load(d.RUN/'native-gap-probes'/(d.sha(url.encode())+'.json'))


def soup(x):
    return d.g.BeautifulSoup(gzip.decompress((d.ROOT/x['receipt']['body_path']).read_bytes()),'html.parser')


def facts():
    directory={e['name']:e for e in d.load(d.RUN/'ministry-directory-audit.json')['entries']}
    records=[];museums={}
    def add(name,city,title,sid,url,receipt,first=None,last=None,precision='unknown',display='Date unknown',kind='sculpture',medium=None,dimensions=None,accession=None,creator=None,raw=None,image_url=None,alternate=None):
        e=directory[name];key='ministry-'+e['key'];museums[key]=dict(key=key,name=name,city=city,directory=e,source_url=url)
        records.append(dict(source='native-museum',scheme='greek-native-museum-highlight',source_id=sid,source_url=url,receipt=receipt,museum_key=key,
            title=title,alternate_title=alternate,creator_label=creator,first=first,last=last,precision=precision,date_display=display,
            work_type=kind,medium=medium,dimensions=dimensions,accession=accession,raw=raw,image_url=image_url,holding_confidence=.98,
            holding_basis='Individually identifiable object explicitly described by its custodian or the Greek Ministry museum catalogue. Unknown creation dates and qualified attributions remain in review. Holding only; no current-display claim.'))
    dates={'3092':(-600,-501,'century'),'676':(-6500,-5300,'range'),'5693':(-336,-323,'range'),'2112':(-2700,-2300,'range'),'2733':(-325,-300,'range'),'100':(-450,-450,'circa'),'2253':(-2700,-2300,'range'),'1908':(-525,-500,'range')}
    for sid,(first,last,precision)in dates.items():
        url='https://collections.cycladic.gr/en/objects/details/'+sid;x=probe(url);s=soup(x)
        fields={d.g.clean(n.select_one('.detailFieldLabel')):d.g.clean(n.select_one('.detailFieldValue'))for n in s.select('.detailField.enField')}
        title=d.g.clean(s.select_one('h1'));imgs=[i['src']for i in x['images']if i['src'].endswith('/full')];assert len(imgs)==1
        classification=fields['Classification'];kind='metalwork'if classification.startswith('Metalwork')else'sculpture'if 'Figurines'in classification or 'Plastic'in classification else'stonework'if classification.startswith('Stonework')else'unknown'
        # Schema has no stonework enum; retain the exact classification in evidence.
        if kind=='stonework':kind='unknown'
        add('Museum of Cycladic Art','Athens',title,'cycladic/'+sid,url,x['receipt'],first,last,precision,fields['Date'],kind,fields['Medium'],fields.get('Dimensions'),fields['Object Number'],raw=dict(fields=fields,source_text=x['text'],range_note='2700–2400/2300 BC retains its qualified display; numeric search bounds cover the full supplied interval.'),image_url=imgs[0])
    url='https://delphi.culture.gr/selected-exhibits/';x=probe(url);s=soup(x)
    for tab,title,first,last,precision,display,kind,medium,creator in [
        (6,'The cylix of Apollo',-480,-470,'range','480–470 BCE','ceramic',None,'Attic workshop'),
        (7,'The Charioteer',-480,-470,'range','480–470 BCE','sculpture','Bronze',None),
        (8,'Incense burner in the form of peploforos',-460,-450,'range','Around 460–450 BCE','metalwork','Bronze',None),
        (11,'Torso of an Amazon',None,None,'unknown','Date unknown','sculpture',None,None),
        (12,'Daedalic figurine of Apollo',None,None,'unknown','Date unknown','sculpture',None,None)]:
        block=s.find(id='elementor-tab-content-167'+str(tab));assert block
        imgs=[a['href']for a in block.select('a[href]')if a.find('img')];text=d.g.clean(block)
        receipt=x['receipt'];source=url+'#'+block['id'];extra={}
        if tab==7:
            direct=probe('https://delphi.culture.gr/the-charioteer/');assert '480–470 BC'in direct['text'];source=direct['url'];receipt=direct['receipt'];extra=dict(date_receipt=direct['receipt'])
        add('Archaeological Museum of Delphi','Delphi',title,'delphi/selected-'+str(tab),source,receipt,first,last,precision,display,kind,medium,creator=creator,
            raw=dict(section_text=text,image_options=imgs,selected_exhibits_receipt=x['receipt'],**extra),image_url=imgs[0]if last is not None else None)
    url='https://www.historical-museum.gr/en/collections/el-greco';x=probe(url)
    for sid,title,year,img in [('sinai','View of Mt. Sinai and the Monastery of St. Catherine',1570,next(a['url']for a in x['links']if a['url'].endswith('El_Greco_-_Mount_Sinai_-_WGA10419.jpg'))),('baptism','The Baptism of Christ',1567,None)]:
        assert str(year)in x['text']
        add('Historical Museum of Crete','Heraklion',title,'hmc/el-greco-'+sid,url,x['receipt'],year,year,'exact',str(year),'painting',creator='El Greco',raw=dict(source_text=x['text'],date_note='Current native collection text supplies 1567 for Baptism; the older museum caption/search index says circa 1569. Retain the discrepancy as evidence; no synthetic interval.'),image_url=img)
    url='https://visit-olympia.gr/en/node/196';x=probe(url)
    for sid,title,creator in [('hermes','Hermes of Praxiteles','Praxiteles (traditional attribution)'),('nike','Nike of Paionios','Paionios')]:
        assert title in x['text']
        add('Archaeological Museum of Olympia','Olympia',title,'olympia/'+sid,url,x['receipt'],creator=creator,raw=dict(source_text=x['text'],provider='Ephorate of Antiquities of Ilia; official regional destination page'),display='Creation date not stated in selected source')
    na=d.load(d.RUN/'nationalarchive-object-facts.json')
    for sid,name,city in [(584263,'Archaeological Collection of Apeiranthos','Apeiranthos'),(693213,'Archaeological Museum of Neapolis Voion','Neapolis Voion')]:
        row=next(h['record']for h in na['held']if h.get('record',{}).get('recordId')==sid)
        raw,rc=d.m.capture('https://nationalarchive.culture.gr/portal-api/exhibits/'+str(sid),timeout=30);assert rc['status']==200
        title=row['title'].get('en')or row['title']['gr'];material='; '.join(a.get('en')or a['gr']for a in row['materials'])
        add(name,city,title,str(sid),d.g.NA+'/exhibits/'+str(sid),rc,kind=d.g.na_kind(row),medium=material,raw=row,alternate=row['title']['gr']if row['title']['gr']!=title else None)
        records[-1]['scheme']='greek-national-archive-exhibit';records[-1]['source']='nationalarchive'
    e=directory['Archaeological Collection of Oreoi'];assert 'marble statue of the bull of Oreoi'in e['source_text']
    add(e['name'],'Oreoi','Bull of Oreoi','oreoi/bull',e['source_url'],e['receipt'],medium='Marble',raw=dict(source_text=e['source_text'],date_note='Discovery in 1965 is not a creation date; no creation year inferred.'))
    d.save(d.RUN/d.FACTS,dict(at=d.now(),records=records,museums=list(museums.values()),held=[]))
    print('Native facts',len(records),'objects',len(museums),'museums',flush=True)


def reconcile():
    p=d.load(d.RUN/'native-delivery-plan.json.gz');before=d.load(d.BACKUP/'native-hmc-existing-preimages.json.gz')
    existing=next(x for x in before if x['artwork']['title']=='Mount Sinai')
    wiki=probe('https://www.wikiart.org/en/el-greco/mount-sinai-1570');assert 'Historical Museum of Crete, Heraclion, Greece'in wiki['text']
    selected=[]
    for f in p['records']:
        if f['source_id']=='hmc/el-greco-baptism':
            p['held'].append(dict(facts=f,reason='same_subject_early_El_Greco_versions_require_physical_comparison',existing_candidate='1e2c40c0-c3a4-520e-b194-f9afc327254d',details='Existing WikiArt picture is an arched triptych panel, 24 x 18 cm, dated 1568. Current museum text supplies 1567 and older caption 1569. Native detailed image source returned HTTP 500, and the museum-origin Commons reproduction returned HTTP 403. No reassignment or duplicate inserted without resolved physical-object comparison.'));continue
        if f['source_id']=='hmc/el-greco-sinai':
            f.update(artwork_id=existing['artwork']['id'],before=existing,action='enrich')
            f['raw']['identity_reconciliation']=dict(wikiart=wiki,existing_title=existing['artwork']['title'],basis='Exact El Greco subject and 1570 date; WikiArt explicitly identifies Historical Museum of Crete. Reuse existing painting and primary image; preserve source title variant and existing catalogue date.')
            f['holding_basis']+=' WikiArt independently identifies this exact 1570 painting with the same museum; existing artwork identity and primary image reused.'
        if f['source_id']=='delphi/selected-8':f['precision']='circa_range'
        selected.append(f)
    p['records']=selected;p['at']=d.now();p['editorial_revisions']=['Existing Mount Sinai identity reused with explicit WikiArt museum evidence. Early Baptism version retained as unresolved, avoiding a duplicate or incorrect holding.']
    d.save(d.RUN/d.PLAN,p);d.save(d.BACKUP/(d.PLAN+'.preimages.json.gz'),p)
    print('Native reconciled plan',sum(f['action']=='create'for f in selected),'new,',sum(f['action']=='enrich'for f in selected),'existing,',len(p['held']),'held',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['facts','plan','reconcile','apply']);a=p.parse_args();{'facts':facts,'plan':d.plan,'reconcile':reconcile,'apply':d.apply}[a.action]()
