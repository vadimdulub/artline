"""Explicit qualified date interpretation for the selected museum source literals."""
import re

def date(row):
    n=row['number'];literal=row['native']['literal_date'];v=literal.lower();display=re.sub(r'\s*\[(?:create|dedication)\]|\s+create$','',literal,flags=re.I).strip().strip('[]').strip()
    if n in [76,154] or 'dedication' in v:
        return None,None,'unknown','Creation date unresolved',('Dedication is not manufacture/assembly; source date retained as evidence.' if 'dedication' in v else 'Source date may refer to prototype or conflicts with maker chronology; actual impression date unresolved.')
    if n==1053:return 1901,2000,'century','20th century (source dates conflict)','Native object says20thcentury, aggregator literal saysEarly20thcentury. Retain broader native range and explicitcutoff review; noimageapproved.'
    if re.fullmatch(r"1930's",display):return 1930,1939,'decade','1930s','Literal decade, not1930exactyear.'
    if re.fullmatch(r'c\.\s*\d{4}',display):
        year=int(re.search(r'\d{4}',display)[0]);return year,year,'circa','c. '+str(year),'Museum approximate date retained.'
    if re.fullmatch(r'\d{4}',display):return int(display),int(display),'exact',display,'Museum explicit creationdate.'
    if '19th' in v and '20th' in v:
        first=1851 if 'second half' in v else 1871
        last=1950 if 'first half' in v else 1930
        return first,last,'range',display,'Qualified period representation: late/end19th=1871–1900, secondhalf19th=1851–1900, early20th=1901–1930, firsthalf20th=1901–1950. Both centuries retained; aggregator index often drops19thcentury.'
    mapping={'18th century':(1701,1800,'century'),'19th century':(1801,1900,'century'),'late 19th century':(1871,1900,'range'),'end of the 19th century':(1871,1900,'range'),'second half of the 19th century':(1851,1900,'range'),'early 19th century':(1801,1830,'range'),'early 20th century':(1901,1930,'range'),'first half of the 20th century':(1901,1950,'range')}
    if display.lower() not in mapping:raise ValueError((n,literal,display))
    first,last,precision=mapping[display.lower()];return first,last,precision,display,'Qualified source period retained; bounds represent the named period, not an inventedexactyear.'
