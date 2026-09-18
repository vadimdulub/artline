#!/usr/bin/env python3
"""Render exact primary PDF covers beside prepared photos; never approve them."""
import argparse
import importlib.util
from pathlib import Path
import re
import subprocess
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('primary','ops/italy-primary-photo-research.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);c,w=p.c,p.w

def main(label):
    run=c.RUN/label;rows=[]
    for path in sorted((run/'images'/p.PROVIDER).glob('*.json')):
        im=c.load(path);raw=im['raw'];receipt=raw['primary_catalogue_pdf'];pdf=ROOT/receipt['path']
        if c.core.sha(pdf.read_bytes())!=receipt['sha256']:raise ValueError('Exact PDF checksum mismatch')
        text=(ROOT/raw['primary_catalogue_text_path']).read_text();pages=text.split('\f')
        inventory=re.findall(r'^Numero:\s*(.+)$',text,re.M)
        inventory_pages=[n for n,page in enumerate(pages,1) if re.search(r'^Numero:\s*',page,re.M)]
        definitions=text.split('DEFINIZIONE CULTURALE',1)[-1].split('DATI TECNICI',1)[0]
        rows.append({'source_id':im['external_id'],'artwork_id':im['artwork_id'],'title':im['title'],
            'artist':im['artist'],'catalogue_dates':[im['creation_year_start'],im['creation_year_end']],
            'catalogue_creator_definition':definitions,'inventory_candidates':inventory,
            'inventory_pages':inventory_pages,'raw_date_fields':re.findall(r'^(?:Da|A):\s*.+$',text,re.M),
            'primary_holdings':re.findall(r'^Denominazione struttura conservativa.+$',text,re.M),
            'primary_pdf':receipt,'image_sha256':im['sha256'],'image_path':im['path'],
            'actual_authorities':{q:{'creators':sorted(w.ids(e,'P170')),'holding':sorted(w.ids(e,'P195')),
                'inventory':w.values(e,'P217'),'dates':w.values(e,'P571'),
                'creator_qualifier_keys':[list(k.get('qualifiers',{})) for k in w.claims(e,'P170')]}
                for q,e in raw['actual_authorities'].items()},'status':'Awaiting actual visual/metadata review'})
    digest=c.core.sha(c.core.encode([(r['artwork_id'],r['image_sha256']) for r in rows]))[:12]
    temp=Path('/tmp/artline-italy-primary-photo-qa')/label/digest;temp.mkdir(parents=True,exist_ok=True)
    for row in rows:
        destination=temp/row['source_id']
        subprocess.run(['pdftoppm','-f','1','-l','1','-scale-to','1000','-png','-singlefile',
            str(ROOT/row['primary_pdf']['path']),str(destination)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        row['rendered_cover']=str(destination)+'.png'
    comparisons=[]
    for start in range(0,len(rows),3):
        sheet=Image.new('RGB',(1000,1920),'#eeeae0');draw=ImageDraw.Draw(sheet)
        for j,row in enumerate(rows[start:start+3]):
            yy=j*640;draw.text((12,yy+5),row['source_id']+' | '+row['title'][:115],fill='black')
            for xx,path in [(0,Path(row['rendered_cover'])),(480,ROOT/'apps/web/public'/row['image_path'].lstrip('/'))]:
                im=Image.open(path).convert('RGB');im.thumbnail((480,600))
                sheet.paste(im,(xx+(480-im.width)//2,yy+30+(600-im.height)//2))
        destination=temp/('comparison-%02d.jpg'%(start//3+1));sheet.save(destination,quality=94)
        comparisons.append({'path':str(destination),'source_ids':[r['source_id'] for r in rows[start:start+3]]})
    manifest=run/'primary-qa'/digest/'manifest.json'
    c.save(manifest,{'generated_at':c.core.now(),'rows':rows,'comparison_sheets':comparisons,'approval_recorded':False})
    print(manifest)
    for item in comparisons:print(item['path'],','.join(item['source_ids']))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--label',required=True);args=a.parse_args();main(args.label)
