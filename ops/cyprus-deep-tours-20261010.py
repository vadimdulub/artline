"""Research individually captioned objects from officially linked virtual tours."""
import importlib.util,json,re,concurrent.futures,xml.etree.ElementTree as ET
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('cyprus','ops/cyprus-deep-20261010.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
TOURS=['PieridesMuseum','Christian_Art_Museum','KallinikeioMuseum','Byzantine_Museum','Bee_Embroidery_Museum','Lefkara_Museum','Local-Rural-Museum-Kato-Drys']
def one(name):
    base='https://virtuallarnakaregion.com/'+name+'/indexdata/'
    raw,rc=m.h.capture(base+'index.xml');msg,mrc=m.h.capture(base+'index_messages_en.xml')
    if rc['status']!=200 or mrc['status']!=200:return
    root=ET.fromstring(raw);messages={x.attrib.get('name'):x.text for x in ET.fromstring(msg).iter('data')}
    spots={x.attrib.get('onclick'):x.attrib for x in root.iter('hotspot')}
    rows=[]
    for a in root.iter('action'):
        if 'set_modal_data'not in(a.text or''):continue
        spot=spots.get(a.attrib.get('name'),{});label=messages.get('en_'+spot.get('tooltip',''))
        for match in re.finditer(r"set_modal_data\('([^']*)','EN','(.*?)',''\);",a.text or'',re.S):
            files,text=match.groups();files=[urljoin(base,p.replace('%FIRSTXML%/',''))for p in files.split(';')if p]
            rows.append(dict(tour=name,action=a.attrib['name'],title=label,description=text,image_urls=files,spot=spot,source_url=base+'index.xml',receipt=rc,messages_receipt=mrc))
    m.h.save(m.RUN/'tours'/(name+'.json'),dict(tour=name,records=rows,receipt=rc,messages_receipt=mrc))
    print(name,len(rows),'captioned objects',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(one,TOURS))
