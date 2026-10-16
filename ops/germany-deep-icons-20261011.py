"""Museum-owned icon research, selected PDF figures and explicit maker roles."""
import runpy,re,sys
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];soup=b['soup'];add=b['add'];museum=b['museum'];F=b['F'];H=b['H']
def frankfurt():
    u='https://sammlung-digital.museumangewandtekunst.de/rundgang/themen/93fa5e50-57b0-447c-aefa-f8ba652c5028';mu=museum('de-ikonenmuseum-frankfurt','Ikonenmuseum Frankfurt','Frankfurt am Main','Hesse',u);s,p=soup(u);ids=list(dict.fromkeys(x['data-obj']for x in s.select('[data-obj]')))
    for rid in ids[:16]:
        url='https://sammlung-digital.museumangewandtekunst.de/detail/collection/'+rid;s,p=soup(url);d={x['data-key']:x.find('span').get_text(' ',strip=True)for x in s.select('li[data-key]')if x.find('span')}
        assert d.get('Systematic_S')=='Ikonenmuseum'
        # Visible catalogue fields expose artist roles, not merely a list of names.
        subjects={k:v for k,v in d.items()if k.startswith('Subjects_')};creator='Unknown maker'
        if rid=='9f30fb12-93a6-400c-9185-6d5c48cac8ca':creator='Alexander Dimitrijewitsch Borozdin (painter); Peter Carl Fabergé (metalwork)'
        elif any(k.startswith('Subjects_Name_')for k in d):
            creator='; '.join(v for k,v in d.items()if k.startswith('Subjects_Name_'))
        im=next((x['url']for x in p['images']if '/collection/'in x['url']),None)
        f=add(mu,d['MainTitle_S'],creator,d.get('Dating_S',''),url,rid,im,d.get('MaterialTechnique_S'),d.get('Dimensions_Dimension_0_S'),d.get('InventoryNumber_S'),source_receipt=p['receipt'],source_fields=d,creator_role_evidence=subjects,holding_note=d.get('Creditline_S','Ikonenmuseum Frankfurt catalogue'))
        if not f:continue
        lo=d.get('YearFrom_I');hi=d.get('YearTo_I')
        if lo and hi and lo.isdigit()and hi.isdigit():f.update(start=int(lo),end=int(hi),precision=f['precision']if f['precision']!='unknown'else'catalogue_range',image_eligible=bool(im and int(hi)<=1955))
        f.update(work_type='icon'if 'Handschrift'not in f['title']else'illuminated_manuscript',creator_credit=d.get('Media_Credits_0_S')or'Ikonenmuseum Frankfurt',rights_label=d.get('Media_Credits_0_S')or'Ikonenmuseum Frankfurt; no open reuse licence stated')
        if f['work_type']=='illuminated_manuscript':f['view_label']='Selected illuminated opening of the manuscript; complete source photograph retained, not the entire manuscript'
        print('FRANKFURT',f['title'],f['date_display'],flush=True)
def recklinghausen():
    u='https://ikonen-museum.com/fileadmin/Ikonen_Museum/Museum/Museumsblog/Maria_Gkina__Signed_and_attributed_icons_in_Recklinghausen.pdf';mu=museum('de-ikonen-museum-recklinghausen','Ikonen-Museum Recklinghausen','Recklinghausen','North Rhine-Westphalia','https://ikonen-museum.com/ikonen-museum/sammlung');receipt=m.h.load(m.RUN/'recklinghausen-catalogue-receipt.json')
    # Catalogue numbers 1–24, metadata transcribed from PDF pages 1–8.
    rows=[
    ('Ivan Antonov','Mother of God of Tichvin','1762','48','31.5 × 26.5 cm',1,None,None),
    ('Nikito Gorbunov','Mother of God “Joy to all who suffer”','middle 18th century','70','35.0 × 29.5 cm',1,None,(1701,1800)),
    ('Ivan (family name unclear)','Aleksandr Nevskij on horseback','end of 18th century','721','29.8 × 26.0 cm',1,None,(1701,1800)),
    ('Kirill (family name unclear)','Painted Cross','1818','864','40.7 × 22.3 cm',1,None,None),
    ('I. Stefan Fedorov','Saint Nicholas with frame','1821','660','31.0 × 28.0 cm',1,None,None),
    ('Nazar’ Kuzmin Demidovo (painter or donor uncertain)','Resurrection of Christ','last quarter of the 19th century','4090','31.2 × 26.2 cm',1,None,(1876,1900)),
    ('Iosif Andreevič Pankryšov','Saint Marina of Béroea (Aleppo)','1892','4089','26.5 × 22.5 cm',2,(2,18,1),None),
    ('Aleksandr Sergeev Egorov','Christ Pantocrator','1880/1890','3460','31.7 × 27.2 cm',2,None,None),
    ("Vasilij Pavlovič Gur’janov",'Archangel Michael with eight saints','1900','3964','31.0 × 26.0 cm',2,(2,19,2),None),
    ('Attributed to Semen-Spyridon Cholmogorec','Evangelist Luke','third quarter of the 17th century','900','55.0 × 43.2 cm',3,(3,23,3),(1651,1675)),
    ('Attributed to the Bogatyrev workshop','Ascension of Christ / Mandylion','first quarter of the 19th century','1140','35.5 × 30.0 cm',3,None,(1801,1825)),
    ('Attributed to the Pesechonov workshop','Saint Nicholas the Wonderworker','middle 19th century','693','34.8 × 28.2 cm',3,None,(1801,1900)),
    ('Nikolaos Tzafoures','Madre della Consolazione','c. 1490/1500','9735','73.0 × 55.3 cm',3,(4,28,4),None),
    ('Melachrinos (?)','Saint Basil the Great','early 17th century','380','51.5 × 38.5 cm',3,None,(1601,1700)),
    ('Elias Moschos','Christ Pantokrator','1653','8','119.0 × 84.5 cm',3,(4,29,5),None),
    ('Konstantinos Tzanes','Dormition of the Virgin','1677','3943','43.5 × 32.0 cm',3,(5,33,6),None),
    ('Victor','Saint Anthony of Padova','end of 17th century','3940','18.5 × 13.5 cm',4,(5,34,7),(1601,1700)),
    ('Philippos Hagiotaphites','The three Patron Saints of the Ionian Islands','1859','669','113.4 × 83.0 cm',4,(6,39,8),None),
    ('Workshop or pupil of Michael Damaskinos (?)','Evangelist Luke','second half of the 16th century','249','31.5 × 26.8 cm',6,None,(1551,1600)),
    ('Attributed to Emmanuel Tzanes (?)','Saint Nicholas','middle of the 17th century','229','29.8 × 21.5 cm',6,None,(1601,1700)),
    ('Attributed to Andreas Ritzos','Mother of God of the Passion','end of 15th century','680','82.2 × 61.5 cm',6,(7,43,9),(1401,1500)),
    ('Attributed to Andreas Ritzos','Akra Tapeinosis','end of 15th century','345','64.5 × 49.5 cm',6,(7,44,10),(1401,1500)),
    ('Attributed to Girgis Al-Musawwir','Baptism of Christ','second half of 18th century','3767','35.3 × 27.5 cm',8,(8,50,11),(1751,1800)),
    ('Dimitâr Andonov','Saints Cosmas and Damian','1887','1135','43.5 × 28.6 cm',8,(8,51,12),None)]
    for i,(cr,title,dt,inv,dim,page,fig,bounds)in enumerate(rows,1):
        f=add(mu,title,cr,dt,u,inv,None,dimensions=dim,accession=inv,source_receipt=receipt,locator='Maria Gkina, Signed and attributed icons in the Icon Museum of Recklinghausen, catalogue no. '+str(i)+', PDF page '+str(page),catalogue_number=i)
        f.update(work_type='icon',rights_label='Ikonen-Museum Recklinghausen / Maria Gkina; no open image reuse licence stated',creator_credit='Ikonen-Museum Recklinghausen; reproduced in Maria Gkina, Signed and attributed icons in the Icon Museum of Recklinghausen')
        if bounds:f.update(start=bounds[0],end=bounds[1],precision='period_bounds',date_evidence_note='Numeric bounds preserve the stated century or explicit half/quarter. Early, middle and late remain qualitative labels; no exact year is inferred.')
        if fig:f.update(pdf_image=dict(path=receipt['path'],page=fig[0],xref=fig[1],figure=fig[2]),image_eligible=True,view_label='Complete embedded catalogue figure '+str(fig[2])+'; source frame retained without cropping. Figure and inventory cross-checked visually.')
    print('RECKLINGHAUSEN',len(rows),'selected metadata, 12 selected figures')
if __name__=='__main__':
    frankfurt();recklinghausen();b['finish']('icons')
