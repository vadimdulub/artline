#!/usr/bin/env python3
"""Supplement national directory leads; no placeholder catalogue institutions."""
import importlib.util
from pathlib import Path
from urllib.parse import unquote
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('south-america-1000-20261011.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d

def run():
    data={}
    def add(co,names,url,label,city=''):
        x=c.probe(url);assert not x.get('error') and x['evidence']['status']==200
        for name in names:
            data.setdefault(co,[]).append(dict(directory_id='native-'+d.sha((url+'/'+name).encode())[:16],name=name,locality=city,source_url=url,evidence=x['evidence'],source_family=label,object_gap='Directory/institution evidence alone; individual object eligibility and museum holding sources still required.'))
    add('GY',['Guyana National Museum','Museum of African Heritage','Walter Roth Museum of Anthropology','Dutch Heritage Museum'],'https://portal.gov.gy/services/national-museums-and-gallery-services','Government of Guyana — museum services')
    add('GY',['National Gallery of Art, Castellani House','Linden Museum of Industrial Heritage'],'https://portal.gov.gy/agencies/castellani-house','Government of Guyana — institution and related agencies')
    add('SR',['BISDOMSHUIS','CLEVIA PARK','FORT ZEELANDIA','VERHALEN MUSEUM','KOTO MUSEUM','LALLA ROOKH MUSEUM','NIEUW AMSTERDAM','READYTEX ART','RUMHUIS','SYNAGOGUE','MUSEUM BAKKIE','JODENSAVANNE'],'https://suriname.travel/museums/','Tourism directory leads; mixed museums/heritage venues; template package prices ignored')
    add('VE',['Museo de la Estampa y el Diseño Carlos Cruz-Diez','Museo de Arte Contemporáneo de Caracas Armando Reverón','Galería de Arte Nacional','Museo Arturo Michelena','Museo de Arte de Coro'],'https://www.mincultura.gob.ve/noticias/la-fmn-celebra-el-dia-del-artista-plastico-con-una-variada-programacion/','Ministry of Culture / Fundación Museos Nacionales institution list')
    for name,url,city in [
      ('Museo de Arte de Valencia','https://www.mincultura.gob.ve/noticias/el-museo-de-arte-de-valencia-reabrio-sus-puertas-al-publico-con-ocho-exposiciones/','Valencia'),
      ('Museo de Arte Moderno Jesús Soto','https://www.mincultura.gob.ve/noticias/reinauguracion-del-museo-moderno-jesus-soto-vitrina-de-la-cultura-venezolana-2/','Ciudad Bolívar'),
      ('Museo de Bellas Artes de Caracas','https://www.mincultura.gob.ve/noticias/inaugurada-en-el-museo-de-bellas-artes-la-exposicion-colectiva-sororas-12x12/','Caracas')]:add('VE',[name],url,'Ministry of Culture museum report',city)
    u='https://colecciones-ecuador.skin-web.org/es/pagina/explorar-por-museos/6a79d9c0382a0e1107b121d7';x=c.probe(u)
    names=list(dict.fromkeys(a['text'] for a in x['links'] if a['text'].startswith(('Museo','Centro Cultural')) and '/es/pagina/' in a['url']))
    add('EC',names,u,'National collection platform — museums and reserves; directory source')
    u='https://www.surdoc.cl/museos';x=c.probe(u)
    names=list(dict.fromkeys(a['text'] for a in x['links'] if 'institution:' in unquote(a['url'])))
    add('CL',names,u,'SURDOC participating collection institutions')
    add('GF',['Musée Alexandre-Franconie'],'https://arts-plastiques.dis.ac-guyane.fr/Le-Musee-Alexandre-Franconie.html','French Guiana education authority museum resource','Cayenne')
    add('GF',['Musée des Cultures Guyanaises','Contemporary Art Museum Moengo / Tembe Art Studio'],'https://arts-plastiques.dis.ac-guyane.fr/-amazonian-museum-network-.html','Cross-border Amazonian museum network leads; Moengo is in Suriname, not French Guiana')
    for co,rows in data.items():d.save(c.RUN/co/'native-directory.json.gz',dict(records=rows,completeness='Researched leads only; not an exhaustive national register.'));print(co,len(rows),flush=True)
    d.save(c.RUN/'research-gaps.json',dict(country_gaps={
      'BR':'Ibermuseos registry reconciled; this object delivery is MASP only. Other institutions need native object sources.',
      'CL':'Three selected SURDOC institutions; other participating and national-directory institutions still lack selected objects.',
      'CO':'One bank collection authority; national directory has hundreds of other museums awaiting object records.',
      'EC':'Selected Nahím Isaías objects; other museums/reserves retained as leads.',
      'PE':'Selected MALI highlights; other national directory institutions require object sources.',
      'BO':'Three archival museum holdings. San Pedro title/dimension version conflict held. IDB PDF host denied access; no workaround.',
      'GY':'One named dated National Collection painting; broader government museum service list has no object-level catalogue.',
      'SR':'One lender-catalogue painting. Tourism entries overlap and contain generic template content; museum websites show integrity issues, so no website assigned to the new institution.',
      'VE':'Ibermuseos returns zero and the FMN host does not resolve. Ministry collection captions support MAM works, and approved WikiArt supports the existing GAN painting. Other museums remain leads.',
      'AR':'Prior national directory reused. Only distinct remaining MNBA Neuquén objects added.',
      'UY':'Prior national/registry leads reused. Distinct MNAV inventory objects selected; repeated generic titles retain separate inventory/version identities.',
      'PY':'Prior SNC/ICOM/Ibermuseos leads reused. One additional explicitly dated MNBA catalogue painting selected; source creator is Vicente Forte.'},image_access_holds=['Commons media: earlier HTTP 429, no retry','publications.iadb.org: HTTP 403; no alternate transport/path workaround'],source_soft_blocks=['www.banrepcultural.org returned a security-block page with HTTP 200; no further requests. The independently available colecciones.banrepcultural.org object platform supplied collection records.'],territory_note='French Guiana is reported separately with its French administrative country. Moengo is a Suriname lead on a cross-border French education resource, not a French Guiana museum.'))
if __name__=='__main__':run()
