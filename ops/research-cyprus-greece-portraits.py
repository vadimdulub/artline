"""Select sourced artist reference portraits; no catalogue artwork creation."""
import importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('x',Path(__file__).with_name('import-cypriot-more.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
x.RUN=x.ROOT/'docs/research/cyprus-greece-portraits-20260914'
rows=x.read('local-before.json')['artists'];pages={}
for f in (x.RUN/'commons-metadata').glob('*.json'):
 b=json.loads(f.read_text())
 for p in b['data']['query']['pages'].values():pages[p['title']]=(p,b['receipt'])
choices=[('Angelos Giallinas','Aggelos Giallinas.JPG'),('Dimitris Vitris','Mimis Vitsoris selfportrait oil on canvas 55x45cm-nodate.jpg'),('Dionysios Tsokos','TSOKOS-SELF.jpg'),('Giorgio de Chirico','Giorgio de Chirico (portrait).jpg'),('Ioannis Altamouras','Ioannis Altamouras - self portrait.jpg'),('Jannis Kounellis','JannisKounellis.jpg'),('Nikolaos Gyzis','Nikolaos Gyzis (1842–1901).png'),('Georgios Roilos','Self-portrait, Geogios Roilos.jpg'),('Nikolaos Lytras','Nikolaos Lytras selfportrait.jpeg'),('Georgios Iakovidis','Georgios Iakovidis (1914).jpg'),('Konstantinos Maleas','Konstantinos Maleas self-portrait charcoal on paper 1920.jpg'),('Konstantinos Parthenis','Kost-parthenis-rubens-circa1900.jpg'),('Konstantinos Volanakis','Konstantinos Bolanakis.JPG'),('Nikephoros Lytras','Selfportrait, Nikiforos Lytras.png'),('Stass Paraskos','Stass Paraskos.jpg'),('Thaleia Flora-Karavia','Thalia Flora-Karavia 1912.jpeg'),('Theodoros Rallis','Theodoros Rallis self portait.jpg'),('Theodoros Vryzakis','Theodoros Vryzakis.jpg'),('Theophilos (Chatzimichael)','Theofilos-photo.jpeg')]
selected=[]
for name,file in choices:
 a=next(a for a in rows if a['display_name']==name);p,r=pages['File:'+file];info=p['imageinfo'][0];m=info['extmetadata'];field=lambda k:x.plain(m.get(k,{}).get('value',''));label=field('LicenseShortName');assert label in ['Public domain','CC BY-SA 2.0','CC BY-SA 3.0']
 credit=field('Artist') or ('Nikolaos Lytras' if name=='Nikolaos Lytras' else 'Artcyprus (copyright-owning uploader; photographer not named)')
 entry=dict(artist=a,provider='Wikimedia Commons',source_page_url=info['descriptionurl'],source_image_url=info['url'],source_record_id=p['title'],receipt=r,source_metadata=p,rights_status='public_domain' if label=='Public domain' else 'cc_by_sa',license_label=label,license_url=field('LicenseUrl').replace('http://','https://') or 'https://creativecommons.org/publicdomain/mark/1.0/',creator_credit=credit,subject_note='Source file description/title identifies this named artist or a self-portrait; existing database identity retained.',view_label='Artist portrait (source frame)',rights_basis='File-specific Commons licence and retained source provenance; no licence inferred from the depicted artist alone.')
 if name=='Stass Paraskos':entry.update(subject_note='File name and historical article usage identify Stass Paraskos. Original uploader Artcyprus explicitly changed the licence to GFDL-self on 20 June 2008; current page documents migration to CC BY-SA 3.0.',history=x.read('stass-history.json'),rights_basis='Original copyright-owning uploader Artcyprus explicitly self-licensed this file in revision 1119284023 and confirmed in 1119284024; current GFDL migration provides CC BY-SA 3.0. Photographer name not supplied; uploader attribution retained.')
 if name=='Jannis Kounellis':entry['rights_basis']='Commons records a 2009 Flickr licence review of this 2004 photograph under CC BY-SA 2.0. The later Flickr licence change does not remove the retained reviewed licence.'
 selected.append(entry)
for name,key,record,title,credit in [('Adamantios Diamantis','diamantis','607929','Adamantios Diamantis, 1960s','Dimitris Papadimos; ELIA–MIET'),('Spyros Papaloukas','papaloukas','427475','Stratis Doukas and Spyros Papaloukas at Mount Athos, 1924','ELIA–MIET; photographer not named'),('Nicolas Ghika','ghika','455655','Thrasos Kastanakis, Elpida, Vivika Empirikou and Nikos Chatzikyriakos-Ghika, 1952','ELIA–MIET, Thrasos Kastanakis archive; photographer not named')]:
 r=x.read('primary-captures/'+key+'-elia.receipt.json');soup=BeautifulSoup((x.ROOT/r['path']).read_text(),'html.parser');thumb=soup.find('meta',attrs={'name':'og:image'}) or soup.find('meta',attrs={'property':'og:image'});assert thumb
 assert '/thumbnails/edm-record/ELIA/' in thumb['content'] and 'creativecommons.org/licenses/by/4.0/' in str(soup)
 selected.append(dict(artist=next(a for a in rows if a['display_name']==name),provider='ELIA–MIET via SearchCulture.gr',source_page_url=r['url'],source_image_url=thumb['content'],source_record_id='ELIA/000100-22_'+record,receipt=r,rights_status='cc_by',license_label='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/',creator_credit=credit,subject_note=title,view_label='Group portrait (full source frame)' if key in ['papaloukas','ghika'] else 'Artist portrait (source frame)',rights_basis='Item-specific national cultural aggregator record explicitly licenses both the digital file and thumbnail under CC BY 4.0; institutional archive and supplied creator credited. Source thumbnail retained without asserting original resolution.'))
selected_ids={v['artist']['id'] for v in selected}
holds={
'Fotis Kontoglou':'ELIA 607837 visually shows an artwork rather than the artist; excluded after image QA.',
'El Greco':'P18 identifies a presumed self-portrait or anonymous man; sitter is uncertain.',
'İsmet Güney':'File claims own photograph in 2014, after artist death in 2009; authorship/date not reconciled.',
'Vasilis Michaelides':'2024 own-work claim on historical portrait is not reconciled; other lead is a modern memorial bust with separate sculpture rights.',
'Telemachos Kanthos':'CC BY archive photograph identifies only surname Kanthos; full sitter reconciliation pending. Full-name Moralis print has In Copyright rights.',
}
gaps=[]
for a in rows:
 if a['id'] in selected_ids:continue
 search=x.read('searches/'+a['slug']+'.json')
 gaps.append(dict(artist=a,reason=holds.get(a['display_name'],'No sufficiently identified, rights-cleared artist portrait selected from the bounded source searches. Artwork images, namesakes, and unsupported provenance excluded.'),search=search))
x.save(x.RUN/'selected.json',dict(at=x.core.now(),purpose='Artist reference portraits only. Not new catalogue artworks; no invented creation dates, sitter identity, biography or publication.',items=selected,gaps=gaps,audited_artists=len(rows)))
print('Selected',len(selected),'portraits; remaining',len(gaps),'gaps')
