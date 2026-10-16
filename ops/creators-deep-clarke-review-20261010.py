#!/usr/bin/env python3
"""Selected full-page Clarke illustration identities, checked against a primary edition."""
import copy,importlib.util,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('creators-deep-4h-20261010.py'))
x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x);x.configure('harry-clarke')
plan=x.r.load(x.RUN/'research-selection.json.gz');allrows=plan['rows'];edition=x.r.load(x.RUN/'spring-book-plates.json')
cross={r['index']:r for r in x.r.load(x.RUN/'native-image-crosswalk-spring-final.json.gz')}
plates={4:('The Lake Isle of Innisfree','Frontispiece'),13:('April','31'),14:('The Fiddler of Dooney','32'),16:('Cradle-Song','35'),17:('The Donkey','36'),19:('Sea Fever','41'),22:('A Ballad of the Captains','47'),23:('A Ballad of the Captains','48'),27:('The Song of the Mad Prince','56'),28:('The Shepherdess','59'),29:('The Dead','60'),30:('The Great Lover','62'),31:('The Great Lover','64'),33:('If I Had a Broomstick','74'),34:('The Dying Patriot','80'),35:('The Dying Patriot','82'),36:('Star-Talk','84'),39:('Overheard on a Saltmarsh','94'),41:('To the Coming Spring','103'),42:('Alms in Autumn','106'),43:('Very Nearly!','109'),44:('All Is Spirit and Part of Me','115'),45:('Black and White','126')}
pdf=x.r.load(x.RUN/'ngi-library-report-receipt.json')
result=[]
for i,(subject,page) in plates.items():
 row=copy.deepcopy(allrows[i-1]);w=row['work'];ref=cross[i]
 locator='frontispiece' if page=='Frontispiece' else 'plate on page '+page
 duplicate_subject=subject in ['A Ballad of the Captains','The Great Lover','The Dying Patriot']
 title=subject+(' — plate '+page if duplicate_subject else '')+" (The Year's at the Spring)"
 w.update(title=title,normalized_title=x.q.norm(title),alternate_title="The Year's at the Spring")
 # WikiArt identifies the illustration and year but not a physical original's
 # materials. Do not pretend the book reproduction identifies those materials.
 assert w['work_type']=='unknown' and w['medium_text'] is None and w['dimensions_text'] is None
 row['selection_index']=i;row['confidence']=.99
 note=('Exact image composition matched to '+locator+' of The Year\'s at the Spring, Brentano\'s, New York, 1920, credited to Harry Clarke on the title page. '
       'The primary edition\'s list of illustrations supplies the poem title and plate locator. The source WikiArt title is the generic book title and is preserved as an alternate. '
       'This is an individual illustration composition, not a new whole-book or page-decoration record. Original drawing medium, physical dimensions, repository and date of execution are not established; retain unknown type/material fields. '
       'The source year 1920 is retained and corroborated as the publication year, not a claim of a dated original drawing. Distinct plates for the same poem have explicit page numbers. '
       'Existing source 1920-21 is Arabia (page 51), visually distinct and excluded. No current museum holding or display claim is introduced.')
 row['identity_basis']+=' '+note;row['editorial_review']=note
 row['image_identity_review']='All six provisional comparison sheets reviewed; first three corrected comparison sheets re-reviewed after fixing ordering. Every selected composition matched by figures, linework, borders and colour blocks to the digitized primary edition. '+note
 row['native_sources']=[dict(url=edition['source']+'#'+Path(ref['image_url']).stem,publisher='Brentano\'s 1920 edition, digitized by Internet Archive and Project Gutenberg',receipt=edition['receipt'],record_id='pg51488-'+Path(ref['image_url']).stem,locator=locator+'; list of illustrations pp. 29–30 and title page',facts=dict(illustration_subject=subject,plate=page,book="The Year's at the Spring: An Anthology of Recent Poetry",illustrator='Harry Clarke',compiler="L. D'O. Walters",publisher="Brentano's, New York",publication_year=1920,image_url=ref['image_url'],original_drawing_medium=None,original_drawing_location=None),review=note,confidence=.99),
  dict(url=pdf['url'],publisher='National Gallery of Ireland: Annual Report 2015',receipt=pdf,record_id='NGI-Art-Library-8001282',locator='Printed page 45; PDF page 49, visually checked',facts=dict(book="The Year's at the Spring",illustrator='Harry Clarke',edition='George G. Harrap and Co. Ltd., London, 1920, first edition',library_accession='8001282',scope='Bibliographic context only. A different physical edition from the Brentano scan; not proof of ownership of individual original drawings.'),review='Rendered PDF page 49 and read printed page 45. The report identifies a 1920 Harrap book acquired for the art library. Keep that separate from the original illustrations and the digitized American edition; no institution link or accession is applied to the individual compositions.',confidence=.99)]
 result.append(row)
plan['rows']=result
plan['held'] += [dict(title=row['work']['title'],source_url=row['source_url'],reason='Existing exact source object; unchanged.' if i in [2,24] else 'Outside selected full-page Spring illustrations; no production creation or image attachment. Row 15 is a Saint Peter/key page ornament, not Cradle-Song.') for i,row in enumerate(allrows,1) if i not in plates]
plan['reviewed_at']=x.r.now();plan['reviewer']='Codex source, caption and visual review'
plan['additional_identity_inventory']=dict(path=str((x.RUN/'expanded-existing-records.json.gz').relative_to(x.ROOT)),sha256=x.r.sha((x.RUN/'expanded-existing-records.json.gz').read_bytes()),records=7)
plan['research_limitations']=['Original drawings are not located or assigned invented materials. Publication-year evidence is explicit.','The physical copy in the National Gallery of Ireland library is not the copy scanned by Internet Archive/Project Gutenberg. Neither establishes original-drawing holdings.','Crawford returned HTTP 403; that host is paused and not bypassed. V&A collection browsing was denied by robots.','Four existing Harry Clarke raw-label records and one ambiguous surname-only Clarke record were compared and preserved. The 1860–65 Fort Moultrie record predates this creator and is not linked.','A bounded 23 of 70 direct source candidates are selected; no claim of complete creator coverage.']
x.c.validate(plan);x.r.save_gz(x.RUN/'reviewed-plan.json.gz',plan);x.r.save_gz(x.RUN/'image-selection.json.gz',plan)
x.r.save(x.RECOVERY/x.SLUG/'cloud-backup.json',x.r.load(x.RECOVERY/'cloud-backup.json'))
print(json.dumps(dict(new=len(result),native_citations=2*len(result),holdings=0,verified_source_bodies=x.c.validate(plan))))
