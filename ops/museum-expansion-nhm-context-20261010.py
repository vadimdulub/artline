"""Primary object and collection evidence for disputed dates and creator roles."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode,urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-nhm-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    dest=RUN/'focused-context-001.json.gz';assert not dest.exists()
    targets=[
        ('hanke-publication-001',None,'https://nhmuseum.gr/ekdoseis/zografiki/item/139-eikones-apo-tin-ellada-1833-1838'),
        ('hanke-exhibition-001',None,'https://hps.gr/notos2021/index.php/die-grundung-der-griechischen-post/'),
        ('iatridis-168-001',168,'https://nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou/item/1319-othanatostoumarkoumpotsarimelanografiatouathanasiouiatridiodissos1824'),
        ('iatridis-169-001',169,'https://nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou/item/1320-othanasimostraumatismostoumarkoumpotsarimelanografiatouathanasiouiatridi1824'),
        ('iatridis-170-001',170,'https://nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou/item/1321-ikideiatoumarkoumpotsaristomesologgito1823melanografiatouathanasiouiatridi1824'),
        ('iatridis-171-001',171,'https://nhmuseum.gr/tmimata/mesa-stis-sylloges-tou-mouseiou/item/9448-omarkosmpotsarisepitithetaistontourkopasakatatinepicheirisienantiontoutourkikoustratopedoustokefalobrusokarpenisioutonaugoustotou1823melanografiatouathanasiou'),
    ]
    browse=next(x for x in m.load(RUN/'art-navigation-001.json.gz')['rows'] if x['key']=='native-browse-001');form=browse['forms'][0]
    assert form['action']=='/component/k2/itemlist/search?Itemid=358' and any(x['name']=='searchword' for x in form['inputs'])
    targets.append(('bridge-search-001',None,urljoin(browse['receipt']['final_url'],form['action'])+'&'+urlencode({'searchword':'γέφυρα της Αλαμάνας','categories':'38'})))
    rows=[]
    for key,number,url in targets:
        doc,rc=src.capture(key,url)
        row=dict(key=key,number=number,receipt=rc,text=src.clean(doc.get_text(' ',strip=True)),object_blocks=[src.clean(x.get_text(' ',strip=True)) for x in doc.select('.itemIntroText,.itemFullText,.itemExtraFields')],images=[dict(url=urljoin(rc['final_url'],x['src']),alt=x.get('alt')) for x in doc.select('.itemImage img[src]')],links=[dict(title=src.clean(x.get_text(' ',strip=True)),url=urljoin(rc['final_url'],x['href'])) for x in doc.select('a[href]') if '/item/' in x['href'] or '.jpg' in x['href']])
        rows.append(row)
        print(json.dumps(dict(key=key,status=rc['status'],blocks=row['object_blocks'],images=row['images'],links=row['links'] if key=='bridge-search-001' else []),ensure_ascii=False),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,script_reference=c.ref(Path(__file__).resolve()),policy='Museum object pages and publication, plus NHM-exhibitor history in the philatelic exhibition; exact painting dates and copy execution remain separate from prototype/commission dates. Native collection list dates the four Iatridis works1828–1832 while object pages state1824; preserve conflict pending editorial resolution.'))

if __name__=='__main__':main()
