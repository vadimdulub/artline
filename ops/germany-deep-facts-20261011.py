"""Selected primary-source object parsers. Image acquisition is a later step."""
import collections,gzip,importlib.util,json,re,sys,time
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('germany','ops/germany-deep-20261011.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
M={};F=[];H=[]
def museum(slug,name,city,state,url):
    M[slug]=dict(slug=slug,name=name,city=city,state=state,country_code='DE',website_url=url);return slug
def soup(url):
    p=m.page(url);assert p['receipt']['status']==200,(url,p['receipt']['status'])
    return BeautifulSoup(gzip.decompress((m.ROOT/p['receipt']['body_path']).read_bytes()),'html.parser'),p
def date(raw):
    raw=(raw or'').strip();v=raw.replace('–','-').replace('—','-').replace('−','-').replace('/','-').strip();approx=bool(re.match(r'^(?:um|ca\.?|circa|c\.|around) ',v,re.I));v=re.sub(r'^(?:um|ca\.?|circa|c\.|around)\s+','',v,flags=re.I).replace(' (?)','').strip()
    v=re.sub(r'\s*-\s*','-',v);v=re.sub(r'-ca\.?\s*','-',v)
    a=z=None;precision='unknown'
    if re.fullmatch(r'\d{3,4}',v):a=z=int(v);precision='circa'if approx else'exact'
    elif re.fullmatch(r'\d{4}-\d{1,4}',v):
        x,y=v.split('-');a=int(x);z=int(y)if len(y)==4 else int(x[:4-len(y)]+y);precision='circa_range'if approx else'range'
        if z<a:a=z=None;precision='unknown'
    elif re.fullmatch(r'(?:vor|before) \d{4}',v,re.I):z=int(v[-4:]);precision='before'
    elif re.fullmatch(r'(?:nach|after) \d{4}',v,re.I):a=int(v[-4:]);precision='after'
    elif re.fullmatch(r'\d{1,2}\.\s*(?:Jh\.?|Jahrhundert)',v):a=(int(re.match(r'\d+',v)[0])-1)*100+1;z=a+99;precision='century'
    return dict(start=a,end=z,precision=precision,date_display=raw or'Creation date not stated')
def add(mu,title,creator,dt,url,rid,image=None,medium=None,dimensions=None,accession=None,**extra):
    f=dict(key=urlparse(url).netloc+'/'+str(rid),museum_slug=mu,title=title,creator=creator,**date(dt),source_url=url,source_record_id=str(rid),image_url=image,medium=medium,dimensions=dimensions,accession=accession,work_type='painting',locator='Museum object record / caption',view_label='Complete source reproduction; original framing retained, proportional resizing without cropping',rights_status='restricted',rights_label='No open reuse licence stated; museum and source rights retained',creator_credit=M[mu]['name']);f.update(extra)
    if f['end']is not None and f['end']>1970:H.append(dict(key=f['key'],title=title,reason='Creation range extends after 1970',fact=f));return None
    f['image_eligible']=bool(image and f['end']is not None and f['end']<=1955)
    F.append(f);return f
def staedel():
    mu=museum('de-staedel','Städel Museum','Frankfurt am Main','Hesse','https://sammlung.staedelmuseum.de/en/')
    urls={}
    for tail in ['alte-meister-die-highlights','kunst-der-moderne-die-highlights']:
        p=m.page('https://sammlung.staedelmuseum.de/en/album/'+tail)
        for x in p['links']:
            if'/work/'in x['url']:urls[x['url']]=dict(selection='Museum-designated highlight',selection_source=p['url'])
    for u,why in urls.items():
        try:
            s,p=soup(u);fields={dt.get_text(' ',strip=True):dt.find_next_sibling('dd').get_text(' ',strip=True)for dt in s.select('dt')if dt.find_next_sibling('dd')}
            ld=next(json.loads(x.string)for x in s.select('script[type="application/ld+json"]')if x.string and'ImageObject'in x.string)
            visible_date=s.select_one('.dsArtwork__titleYear');dt=visible_date.get_text(' ',strip=True).lstrip(', ')if visible_date else ld.get('dateCreated')
            f=add(mu,fields.get('Title')or ld['name'],fields.get('Painter')or ld.get('author'),dt,u,fields['Inventory Number'],ld.get('image'),fields.get('Physical Description'),fields.get('Malfläche')or fields.get('Dimensions'),fields['Inventory Number'],source_receipt=p['receipt'],source_fields=fields,selection_basis=why,structured_date_preserved=ld.get('dateCreated'))
            if not f:continue
            f.update(rights_label=fields.get('Picture Copyright')or f['rights_label'],creator_credit=fields.get('Creditline')or M[mu]['name'])
            if f['rights_label']=='Public Domain':f['rights_status']='public_domain'
            typ=(fields.get('Object Type')or'').lower()
            if any(x in typ for x in ['sculpt','statue']):f['work_type']='sculpture'
            elif any(x in typ for x in ['drawing','watercolour']):f['work_type']='drawing'
            if f.get('creator')and not isinstance(f['creator'],str):raise ValueError('Creator needs manual review')
            print('STADEL',len(F),f['title'],f['date_display'],flush=True)
        except Exception as e:H.append(dict(url=u,reason=type(e).__name__+': '+str(e)[:180]));print('HOLD',u,str(e)[:150],flush=True)
def pinakothek():
    # The museum itself selects these homepage highlights. Holding collection,
    # rather than temporary display building, determines the assignment.
    p=m.page('https://www.sammlung.pinakothek.de/en/');urls=list(dict.fromkeys(x['url']for x in p['links']if'/en/artwork/'in x['url']))
    for name,key in [('Alte Pinakothek','alte-pinakothek'),('Neue Pinakothek','neue-pinakothek'),('Pinakothek der Moderne','pinakothek-der-moderne'),('Sammlung Schack','sammlung-schack')]:museum('de-'+key,name,'Munich','Bavaria','https://www.sammlung.pinakothek.de/en/')
    for u in urls:
        try:
            s,p=soup(u);fields={}
            for lab in s.select('.artwork__data .label-header'):
                n=lab.get_text(' ',strip=True);parent=lab.parent;lab.extract();fields[n]=parent.get_text(' ',strip=True)
            col=fields.get('Collection','');mus=[k for k,v in M.items()if v['name']in col and k.startswith('de-')]
            if len(mus)!=1:H.append(dict(url=u,reason='Holding collection is not one uniquely identified museum',collection=col));continue
            title=s.select_one('.artwork__title').get_text(' ',strip=True).rstrip(',');creator=s.select_one('.artwork__artist').get_text(' ',strip=True);ds=s.select('.artwork__main .artwork__dates');dt=ds[-1].get_text(' ',strip=True)if len(ds)>1 else''
            im=s.select_one('a.artwork__action.action--download[href]');lic=s.select_one('a.action--creativecommons[href]');native=re.search(r'/artwork/([^/]+)',u)[1]
            f=add(mus[0],title,creator,dt,u,native,urljoin(u,im['href'])if im else None,fields.get('Material / Technology / Carrier'),fields.get('Dimensions of the object'),fields.get('Inventory number'),source_receipt=p['receipt'],source_fields=fields,holding_label=col,display_text_not_asserted=fields.get('Displayed'),selection_basis='Museum-designated homepage highlight')
            if not f:continue
            f['work_type']='painting'if fields.get('Genre')=='Malerei'else'unknown'
            if lic:f.update(license_url=lic['href'],rights_label='CC BY-SA 4.0'if'by-sa/4.0'in lic['href']else lic['href'],rights_status='cc_by_sa'if'by-sa/4.0'in lic['href']else'restricted',creator_credit='Bayerische Staatsgemäldesammlungen, Munich')
            if any(x in dt.lower()for x in ['entwurf','guss']):f.update(image_eligible=False,date_evidence_note='Design date and date of the physical cast must be distinguished; image held pending review.')
            print('PINAKOTHEK',f['museum_slug'],title,dt,flush=True)
        except Exception as e:H.append(dict(url=u,reason=type(e).__name__+': '+str(e)[:180]));print('HOLD',u,str(e)[:150],flush=True)
def finish(label):
    m.h.save(m.RUN/('selection-'+label+'.json'),dict(at=m.h.now(),records=F,museums=[v for k,v in M.items()if any(f['museum_slug']==k for f in F)],held=H,authorization='User requested the same deep museum artwork and authentic-picture research for Germany on 11 October 2026. Continue selected museum-source images dated by 1955, actual rights labels, review metadata and no local database writes.'))
    print('SELECTED',len(F),'IMAGES ELIGIBLE',sum(f['image_eligible']for f in F),'MUSEUMS',collections.Counter(f['museum_slug']for f in F),'HELD',len(H))
if __name__=='__main__':
    name=sys.argv[1];globals()[name]();finish('staedel-reviewed'if name=='staedel'else name)
