#!/usr/bin/env python3
"""Column-aware source inventory; leads only, never automatic exhibition imports."""
import re,json,pdfplumber
import exhibitions_common as c
OUT=c.DATA/'getty-drawings-inventory'
def main():
 receipt=c.load(c.RUN/'london-gallery-project/getty-pdf-download.json')
 path=c.DATA/'getty-european-drawings-1.pdf';assert c.sha(path.read_bytes())==receipt['sha256']
 records=[]
 with pdfplumber.open(path)as doc:
  for i,page in enumerate(doc.pages):
   x0,y0,x1,y1=page.bbox
   text=page.crop((x0,y0,x0+page.width*.51,y1)).extract_text()or''
   match=re.search(r'EXHIBITIONS\s*:',text)
   if not match:continue
   segment=text[match.end():].split('BIBLIOGRAPHY')[0].strip()
   records.append(dict(pdfPage=i+1,heading=text[:text.find('MARKS AND INSCRIPTIONS')].strip(),exhibitionText=segment,noneDeclared=bool(re.match(r'None\.',segment)),reviewState='unreviewed-source-lead',sourceSHA256=receipt['sha256']))
 result=dict(source=receipt,records=records,counts=dict(objectHistoryPages=len(records),withExhibitionLeads=sum(not r['noneDeclared']for r in records),noneDeclared=sum(r['noneDeclared']for r in records)),limitations=['Column boundary may truncate letters; review rendered original before import.','Repeated shows and travelling venues are not separate events without reconciliation.','Publication bibliography is not an exhibition claim.','This is a source inventory, not a delivered exhibition count.'])
 c.save(OUT/'inventory.json.gz',result)
 summary=dict(source=receipt,counts=result['counts'],limitations=result['limitations'],inventoryPath=str(OUT/'inventory.json.gz'))
 c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-drawings-inventory.json',summary)
 print(json.dumps(summary))
if __name__=='__main__':main()
