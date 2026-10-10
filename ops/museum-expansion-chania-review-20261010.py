"""Review physical identities and literal dating claims; no database access."""
import collections
import csv
import importlib.util
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-chania-visual-20261010.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
m,RUN,PROOF=v.m,v.RUN,v.PROOF
IID='80780566-c37f-51e6-a861-f43c834027d8'
SECONDARY={108:120,109:120,133:120,143:120,144:120,151:67}
UNKNOWN_DATE={8,20,67,78,99,151}
IMAGE_HOLDS={38:'Native and aggregator images show a banded translucent sealstone, whereas the accessioned text describes a clay disk. Filename L2055 does not authorize replacing KH2055.',
    110:'Native and aggregator images show a one-handled flask, whereas the accessioned text describes an inscribed clay disk. Filename P2014 does not authorize replacing KH2014.',
    161:'Accession agrees, but the source describes a bearded bust while the frame shows a detached head with surface wear and an unclear beard. Image identity remains below the editorial threshold; no substituted identity.'}
FIELD_NUMBERS={1,2,4,11,14,15,17,24,29,33,34,40,44,53,58,60,61,72,74,80,83,86,87,88,91,94,95,101,107,112,116,117,123,125,126,128,130,139,140,148,150,154,155,156,157,158,159,160,164,165,166,167,170,171,172,175,176,177,180,182,183,184,185,192,193,194,198,199,201,204,205,207,212}
MANUAL={
    3:(-100,-1,'Native first century BCE'),5:(101,150,'Prose first half second century CE; retain wider field 99–199 CE'),
    6:(-299,-200,'Native reported bounds, not an exact year'),7:(-900,-801,'Prose ninth century BCE; retain field 899–800 BCE'),
    13:(-100,400,'Native first century BCE through fourth century CE; both endpoints retained'),
    18:(-400,-301,'Prose fourth century BCE preferred to inconsistent field 499–300 BCE/Hellenistic'),
    21:(-800,-701,'Prose eighth century BCE preferred to wider Geometric bounds'),22:(-900,-801,'Prose ninth century BCE'),
    25:(-200,-101,'Native second century BCE'),27:(-400,-201,'Envelope of native fourth/third century BCE alternatives, not a narrower exact range'),
    28:(201,300,'Native third century CE'),31:(-1050,-700,'Outer envelope of explicit 1050/1025–700 BCE; alternate starting date retained'),
    35:(-31,324,'Native Roman period bounds 31 BCE–324 CE; not an exact year'),41:(-400,-301,'Prose fourth century BCE; discovery 1962 is not creation'),
    45:(101,400,'Native second through fourth century CE; no selection of only first date field'),
    47:(-1500,-1401,'Native fifteenth century BCE'),49:(-200,-151,'Native first half second century BCE'),
    52:(-1050,-700,'Native Geometric bounds with 1050/1025 starting alternatives retained'),
    55:(-400,-301,'Native fourth century BCE'),56:(1,200,'Native first–second century CE'),57:(-400,-301,'Native fourth century BCE'),
    59:(201,300,'Native third century CE; entire mosaic floor counts once'),
    62:(-1525,-1450,'Outer envelope of prose 1525/1500–1450 BCE; alternate beginning retained'),
    65:(-900,-801,'Prose ninth century BCE'),68:(-300,-201,'Native third century BCE'),
    69:(-400,-201,'Native fourth–third century BCE with Classical/Hellenistic phase labels retained'),71:(201,300,'Explicit native range'),
    73:(-1500,-1401,'Native fifteenth century BCE'),77:(-1050,-700,'Native Geometric range'),
    79:(-300,-201,'Prose third century BCE; native 299–200 BCE boundary convention retained'),81:(-400,-1,'Native fourth–first century BCE'),
    85:(-1400,-1200,'Explicit prose Late Minoan IIIA/B range'),89:(-800,-701,'Prose eighth century BCE preferred to broader Geometric field'),
    92:(-700,-601,'Prose seventh century BCE conflicts with field 720 BCE; both retained'),96:(-400,-301,'Native fourth century BCE'),
    98:(-1525,-1450,'Outer envelope of explicit prose 1525/1500–1450 BCE'),100:(-1400,-1200,'Explicit prose Late Minoan IIIA/B range'),
    104:(-100,100,'Envelope of native first century BCE/first century CE alternatives, with no year zero assigned'),
    105:(1,100,'Prose first century CE'),113:(-400,-301,'Native fourth century BCE'),
    118:(-1350,-1301,'Prose second half fourteenth century BCE; source 1350–1300 bounds retained'),
    131:(-1400,-1300,'Prose Late Minoan IIIA 1400–1300 BCE preferred to conflicting native field IIIB/1300–1200 BCE'),
    135:(-1400,-1200,'Explicit prose Late Minoan IIIA/B range'),146:(-3200,-2000,'Explicit prose Early Cycladic range; May 1900 is donation'),
    152:(-350,-340,'Prose circa 350–340 BCE; approximation retained'),168:(-3200,-2000,'Explicit prose Early Cycladic range; May 1900 is donation'),
    179:(-100,400,'Native first century BCE through fourth century CE; both endpoints retained'),
    188:(-200,-101,'Native second century BCE'),189:(-400,-301,'Native fourth century BCE'),191:(-1300,-1200,'Explicit prose Late Minoan IIIB range'),
    195:(-1700,-1425,'Outer envelope of prose circa 1700/1650–1425 BCE; approximation and alternative starting point retained'),
    197:(1,50,'Prose first half first century CE; Tiberius reign 14–37 is not substituted'),202:(-700,-601,'Prose seventh century BCE'),
    206:(-900,-801,'Prose ninth century BCE'),208:(-500,-401,'Prose fifth century BCE'),
    209:(-2300,-1800,'Outer envelope of prose Early Minoan III 2300/2100–2000 and Middle Minoan I 2100/2000–1800 BCE; alternatives retained')}
PERIOD_NOTES={
    9:'Late Minoan IB; field 1450 is not treated as an exact creation year.',10:'Late Minoan IB; phase qualifiers retained.',
    12:'Geometric period; existing row is a comparator only.',16:'Middle Minoan III.',19:'Early Hellenistic period stated in prose.',
    23:'Late fourth–third century BCE; possibly Dionysus, not a certain identification.',26:'Late Minoan IIIA/B.',
    30:'Hellenistic prose with late fourth–first century BCE field qualifiers.',32:'Early seventh century BCE in prose.',
    36:'Probably a Roman copy of a Hellenistic work; date of the original is not assigned to the copy.',
    37:'Sub-Neolithic date in prose; vessel and lid are one physical work.',38:'Late Minoan IB in prose; image held separately.',
    39:'Late Minoan IB.',42:'Late fourth through first half first century BCE; no arbitrary meaning for late.',43:'Early seventh century BCE in prose.',
    48:'Late Minoan IB in prose.',50:'Trajan period, without inventing numeric reign bounds.',51:'Hellenistic period.',54:'Late third century BCE.',
    63:'Early third century BCE prose versus wider field; retain the qualified prose.',64:'Late fourth–early third century BCE prose versus field 299–200.',
    66:'Late eighth century BCE prose; do not invent an exact meaning for late.',70:'Hellenistic prose; field 399–300 BCE and female-title/male-description conflict retained.',
    75:'Late Minoan IIIA/B in prose and native phase fields.',76:'Hellenistic period.',82:'Late Minoan period.',
    84:'Late Minoan IIIA2/B prose versus narrower 1400–1300 field; no synthetic numeric expansion.',90:'Late fourth century BCE.',
    93:'Early fifth century BCE; plain inscribed funerary stele, not an invented figural relief.',97:'Middle seventh century BCE.',
    102:'Late Minoan IB in prose.',103:'Roman period.',108:'Component of cauldron 120; ancient date claims conflict across component records.',
    109:'Component of cauldron 120; ancient date claims conflict across component records.',110:'Late Minoan IB in prose; image held separately.',
    111:'Prose Late Minoan IB/1450 versus field IA and 1600/1500/1450; explicit conflict remains.',119:'Prose Late Minoan IIIB versus native Late Helladic IIIB; retain both.',
    120:'One cauldron; most fragments 799–700 BCE but component 143 also says 1500 BCE. Numeric date unresolved.',
    122:'Late second century BCE.',127:'Middle first century BCE.',129:'Late Minoan IB in prose.',132:'Late Minoan period.',
    133:'Component of cauldron 120; ancient date claims conflict across component records.',134:'Native 1200 and 1599 BCE appear in reversed order; preserve both without resolving the interval.',
    137:'Middle fourth century BCE; field 350 is not silently promoted to precise creation.',138:'Late Minoan IB in prose.',
    141:'Late third century BCE.',142:'Late third century BCE.',143:'Component of cauldron 120; source includes conflicting 799/700/1500 BCE.',
    144:'Component of cauldron 120.',145:'Late Minoan IB in prose.',149:'Late Minoan IB in prose.',
    153:'Circa third–second millennium BCE; preserve approximation.',161:'Trajan period; image identification is separately held.',
    169:'Middle Minoan III.',174:'Late Minoan IB.',178:'Early Hellenistic.',181:'Prose Middle Minoan IA/II versus narrower field IA.',
    186:'Late fourth century BCE in prose.',187:'Possibly first–second century CE in prose; qualified dating requires review and image remains held.',
    200:'Circa second millennium BCE in prose; native 2000–1900 is retained without claiming exact creation.',
    210:'Prose Late Minoan IIIA versus field 1300–1200 BCE/III; retain phase discrepancy.',211:'Early Cycladic period.'}
SCULPTURE={8,13,23,25,27,28,36,45,50,51,57,66,69,70,71,76,77,80,81,92,94,96,105,112,128,130,131,132,137,150,161,178,179,180,185,188,189,197,201,207,208}
UNKNOWN_TYPE={26,59,75,83,85,93,99,100,119,134,135,146,168,186,211}
NOTES={
    4:'Native 250–230 BCE/Middle Classical and aggregator enrichment disagree; native literal numeric range retained as reported, not independently validated.',
    8:'Source photograph includes reconstructed/supporting portions; preserve source frame and existing metadata, no fresh display inference.',
    36:'Focused native/aggregator comparison supports the relief image; sleeping Eros identification remains the source claim.',
    37:'Vessel Π155 and lid Π156 counted together.',52:'Amphoriskos Π4092 and lid Π4146 counted together.',
    54:'Askos Π5514 with Pan handle Π5530 counted together.',59:'Whole mosaic floor counted once, not individual panels.',
    67:'Two gold hair ornaments, same pair on sources 1396 and 836; accession M763A/B aggregate reconciled to one pair.',
    70:'Title says female figurine; detailed description and image show a seated boy. Literal title retained and conflict explicit.',
    75:'Object h4 and aggregator title are blank. Use Περιδέραιο from native browser title and image alt, corroborated by short description. Do not change Λ2038 to the image filename M2038.',
    77:'Bull toy and attached wheels are one object.',83:'Exaleiptron Λ1007 with lid Λ1030 counted together.',
    85:'Λ2036A is a distinct necklace from Λ2036B and Λ2036Γ; shared base accession does not merge three differently described and pictured objects.',
    91:'Pair of Nike earrings counted once.',93:'Inscribed funerary memorial retained; no relief type inferred from aggregator tags.',
    99:'Λ2036B separately described/pictured necklace; physical creation date unknown.',100:'Λ2036Γ separately described/pictured necklace.',
    102:'Source frame is a detail of the impression on a clay disk; do not label it a complete disk view.',
    113:'Image shows one coin face; do not claim both sides.',120:'Primary accession M825 A–ΣΤ encompasses six separately photographed fragments; one cauldron, six evidence pages, no reconstruction.',
    123:'Image shows one coin face; do not claim both sides.',130:'Carved plaque with possible goddess/priestess; probable attachment does not create a separate box/coffin.',
    131:'Carved plaque; probable coffin attachment not a separate invented object.',132:'Hut model and miniature contents count once.',
    137:'Probably a Boeotian workshop, retained as a qualified object-level attribution, not a painter link.',
    145:'Source frame is a detail of a seal impression on the disk.',150:'Carved sphinx plaque, possible attachment to another object; no invented parent box.',
    156:'Both coin faces are shown; do not infer conventional obverse/reverse order in the source frame.',
    185:'117–138 CE is the full source range, not an exact 117 creation year.',195:'Gold votive axe selected as decorative metalwork; probable findspot remains qualified.',
    200:'Decorated dagger M27 and gold handle M53 count as one work.',204:'ze-ra-to/wa may name a producer of contents or royal association; no accepted artist inferred.',
    210:'Native prose identifies a product of the Kydonia workshop; retained as object-level workshop attribution, no named painter.',
    211:'Double stone vessel counts once.'}

def date_claims(f):
    result=[];active=False
    for label,value in f['native_table_rows']:
        if label=='Χρονολόγηση':active=True
        elif label and active:break
        if active and value:result.append(value)
    return result

def dates(f,claims):
    n=f['number']
    if n in MANUAL:return (*MANUAL[n],'explicit_range_or_century')
    if n in FIELD_NUMBERS:
        values=[]
        for claim in claims:
            for part in claim.split('|'):
                if re.search(r'αι\.|χιλιετ',part):continue
                if 'π.Χ' in part or 'μ.Χ' in part:
                    sign=-1 if 'π.Χ' in part else 1
                    values.extend(sign*int(x)for x in re.findall(r'\d+',part))
        assert values and all(-10000<x<1971 and x!=0 for x in values),(n,claims,values)
        return min(values),max(values),'Reported native numeric dating claim; retain all phase labels, alternative boundaries and conflicting enrichment. This is not an independent exact-date determination.','reported_native_numeric'
    if n in UNKNOWN_DATE:return None,None,'No physical creation date established. Do not infer from style, museum scope, accession or related objects.','unknown'
    if n in v.SCOPE_HOLDS:return None,None,'Outside the selected art scope in this pass; literal date evidence retained without proposing catalogue dates.','scope_hold'
    assert n in PERIOD_NOTES,(n,claims)
    return None,None,PERIOD_NOTES[n],'qualified_period_review'

def work_type(f):
    n=f['number']
    if n in SCULPTURE:return 'sculpture'
    if n in UNKNOWN_TYPE:return 'unknown'
    if f['source_material']in {'Άργυρος','Χρυσός','Χαλκός'}or n==60:return 'metalwork'
    if f['source_material']=='Πηλός'or n in {20,32,43,48,62,74,206}:return 'ceramic'
    return 'unknown'

def main():
    facts=m.load(RUN/'candidate-facts-001.json.gz')['rows'];sources={r['number']:r for r in m.load(RUN/'selected-source-records-001.json.gz')['rows']}
    visual=m.load(RUN/'visual-references-001.json');frames={r['number']:r for r in visual['rows']}
    comp=m.load(RUN/'comparison-references-001.json');rows=[]
    for f in facts:
        n=f['number'];s=sources[n];claims=date_claims(f);first,last,note,kind=dates(f,claims)
        if f['role']=='existing_comparator':decision='existing_comparator'
        elif n in v.SCOPE_HOLDS:decision='hold_art_scope'
        elif n in SECONDARY:decision='same_physical_work_secondary'
        else:decision='candidate_primary'
        title=f['title']
        if n==75:
            assert not title and s['native_page_title'].startswith('Περιδέραιο [Λ 2038]')and s['native_images'][0]['alt']=='Περιδέραιο'
            title='Περιδέραιο'
        date_pass=n not in UNKNOWN_DATE|{187}|v.SCOPE_HOLDS
        image_pass=date_pass and n not in IMAGE_HOLDS and n in frames
        label='Source photograph of accessioned object; complete provider frame'
        if n in {108,109,120,133,143,144}:label='Cauldron fragment view; one component of accession Μ 825 Α–ΣΤ'
        elif n in {102,145}:label='Detail of a seal impression on the accessioned clay disk'
        elif n in {113,123}:label='Single face of the accessioned coin'
        elif n in {67,151,91}:label='Pair photographed together; one catalogue work'
        creator='Anonymous / maker not identified'
        if n==137:creator='Probably a Boeotian workshop (source-qualified attribution)'
        if n==210:creator='Kydonia workshop (source attribution)'
        rows.append(dict(f,number=n,title=title,title_basis='native_browser_title_and_image_alt_and_short_description'if n==75 else f['title_basis'],
            institution_id=IID,decision=decision,primary_number=SECONDARY.get(n,n),first=first,last=last,date_scope='eligible'if first is not None else'requires_editorial_review',
            native_dating_claims=claims,date_review=note,date_basis=kind,creator_label=creator,painter_id=None,work_type=work_type(f),
            holdings_confidence=0.96,holdings_basis='Accessioned native museum collection entry, institutional archive/provider fields, and matching museum-supplied SearchCulture entry; editorial assessment, not calibrated probability.',
            image_date_policy_passed=date_pass,image_date_basis='Literal ancient numeric/period attribution on this object; no numerical year invented from the phase.'if date_pass else'Physical creation date unresolved or item outside selected art scope.',
            image_identity_confidence=0.96 if image_pass else None,image_candidate=image_pass,image_hold_reason=IMAGE_HOLDS.get(n)or(None if date_pass else'Physical date eligibility not securely established in this pass.'),
            source_image_reference=v.ref(frames[n]['path'])if n in frames else None,image_view_label=label,editorial_note=NOTES.get(n),
            native_browser_title=s['native_page_title'],image_attributes=s['native_images'],metadata_retained_despite_image_hold=n in IMAGE_HOLDS,
            rights_label='CC BY-NC-ND 3.0 GR',rights_url='http://creativecommons.org/licenses/by-nc-nd/3.0/gr/',
            rights_basis='Item image rights link; separate BY-SA footer is not used as the image licence.',
            user_image_authorization='Specific Greek museum/artist workflow, creations by 1955, complete frame and <=100000 bytes; permission recorded separately from actual source rights. No independent copyright-holder licence claimed.',
            proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False))
    by={r['number']:r for r in rows};units=[]
    for r in rows:
        if r['decision']!='candidate_primary':continue
        members=[r['number']]+sorted(n for n,p in SECONDARY.items()if p==r['number'])
        units.append(dict(r,source_numbers=members,source_ids=[by[n]['source_id']for n in members],source_urls=[by[n]['source_url']for n in members],
            native_urls=[by[n]['native_url']for n in members],inventories=[by[n]['inventory_literal']for n in members],
            image_source_numbers=[n for n in members if by[n]['image_candidate']],physical_unit_basis=NOTES.get(r['number'],'One separately accessioned and described physical object; no known same-object match in this bounded source comparison.'),
            fresh_global_identity_check_complete=False))
    assert len(units)==174 and len(rows)==212
    assert collections.Counter(r['decision']for r in rows)==dict(candidate_primary=174,existing_comparator=18,hold_art_scope=14,same_physical_work_secondary=6)
    assert len({sid for u in units for sid in u['source_ids']})==180
    assert not any(r['source_creator_labels']for r in rows)
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=rows,source_reference=v.ref(RUN/'candidate-facts-001.json.gz'),script_reference=v.ref(Path(__file__).resolve()),
        policy='Review metadata and image decisions separately. A documented accessioned work can remain unillustrated when source images conflict. Preserve literal source and qualified dates. Existing records are read-only comparators. No database plan or production readiness claimed.'))
    m.save(RUN/'candidate-physical-units-001.json.gz',dict(at=m.now(),institution_id=IID,rows=units,last_verified_catalogue_count=18,last_verified_dateeligible_count=0,
        conditional_catalogue_total_before_live_reconciliation=192,fresh_counts=False,applied=False,decisions_reference=v.ref(RUN/'editorial-source-decisions-001.json.gz')))
    m.save(RUN/'physical-unit-review-001.json',dict(at=m.now(),reviewer='assistant editorial source/image review',all_source_descriptions_reviewed=212,
        native_frames_reviewed=198,initial_contacts_reviewed=visual['sheets'],focused_sheets_reviewed=comp['sheets'],
        same_work_groups=[dict(primary=120,sources=[120,108,109,133,143,144],basis=NOTES[120]),dict(primary=67,sources=[67,151],basis=NOTES[67])],
        distinct_work_comparisons=[dict(numbers=[7,22],basis='Different gold bosses M489/M490, distinct missing sections and piercings.'),dict(numbers=[75,85,99,100],basis='Distinct necklace accessions, bead compositions/counts and images.'),dict(numbers=[32,43],basis='Distinct skyphoi P4641/P4642, vessel profiles and painted bands.'),dict(numbers=[60,88,148],basis='Distinct mirrors and ivory/bone/hippopotamus-tooth handles; original materials and accessions retained.')],
        image_holds=IMAGE_HOLDS,metadata_policy='The three image-held works retain concordant native/aggregator accessioned metadata as unillustrated candidates. Wrong imagery does not authorize an object swap.',
        single_composite_numbers=[37,52,54,59,67,77,83,91,120,132,200,211],
        caveat='Within-selection physical review does not establish global uniqueness; bounded live source/accession/title comparators remain required.',script_reference=v.ref(Path(__file__).resolve())))
    fields=['number','source_id','native_url','title','inventory_literal','role','decision','primary_number','work_type','creator_label','first','last','date_scope','date_review','image_candidate','image_hold_reason','editorial_note']
    with(RUN/'review-ledger-001.csv').open('x',encoding='utf-8-sig',newline='')as out:
        writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(dict(candidates=len(units),numeric_dates=sum(u['first']is not None for u in units),period_or_unknown_dates=sum(u['first']is None for u in units),prepared_image_candidates=sum(r['image_candidate']for r in rows),new_works_with_images=sum(bool(u['image_source_numbers'])for u in units),types=dict(collections.Counter(u['work_type']for u in units))))

if __name__=='__main__':main()
