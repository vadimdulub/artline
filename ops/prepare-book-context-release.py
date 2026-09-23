#!/usr/bin/env python3
"""Overlay only requested book-context changes onto the deployed source archives."""
import difflib,hashlib,json,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
RELEASE=pathlib.Path('/tmp/artline-book-context-release-20260922')
BACKUP=pathlib.Path.home()/'Library/Application Support/Artline/backups/book-context-20260922'
BACKUP.mkdir(parents=True,exist_ok=True)
changes=[]
def change(kind,name,transform=None,source=None):
    p=RELEASE/kind/name;before=p.read_text() if p.exists() else ''
    after=source.read_text() if source else transform(before)
    assert after!=before,(kind,name)
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(after)
    changes.append({'kind':kind,'file':name,'beforeSha256':hashlib.sha256(before.encode()).hexdigest(),'afterSha256':hashlib.sha256(after.encode()).hexdigest(),'diff':''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name,tofile=name))})
def replace(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def go(s):
    s=replace(s,'type Creator struct {','''// Overview is a retained, attributed introduction; API reads never fetch Wikipedia.
type Overview struct {
 Paragraphs []string `json:"paragraphs"`
 SourceURL string `json:"sourceUrl"`
 SourceTitle string `json:"sourceTitle"`
 Revision int64 `json:"revision"`
 Credit string `json:"credit"`
 LicenseURL string `json:"licenseUrl"`
}
type Creator struct {
 Overview *Overview `json:"overview,omitempty"`''')
    return replace(s,'type Book struct {','type Book struct {\n Overview *Overview `json:"overview,omitempty"`')
change('api','internal/books/books.go',go)
web=ROOT/'apps/web'
for name in ['BookOverview.tsx','BookAuthorDrawer.tsx','TimelineFilterSuggestions.tsx','TimelineOverview.tsx','TimelineGrid.tsx']:
    change('web','components/'+name,source=web/'components'/name)
def types(s):
    definition=(web/'lib/books.ts').read_text().split('export type Book = {')[0]
    s=replace(s,'export type Book = {',definition+'export type Book = {\n  overview?: BookOverview;')
    return replace(s,'creators: { id: string; name: string; description: string;','creators: { id: string; name: string; description: string; overview?: BookOverview;')
change('web','lib/books.ts',types)
def drawer(s):
    s=replace(s,'import { BookCover } from "./BookCover";','import { BookCover } from "./BookCover";\nimport { BookOverview } from "./BookOverview";')
    s=replace(s,'<p>{book.description}</p>','{book.overview ? <BookOverview overview={book.overview} /> : <p>{book.description}</p>}')
    return replace(s,'<p>{creator.description || "A biography has not yet been established for this creator."}</p>','{creator.overview ? <BookOverview overview={creator.overview} /> : <p>{creator.description || "A biography has not yet been established for this creator."}</p>}')
change('web','components/BookDrawer.tsx',drawer)
def timeline(s):
    s=replace(s,'noun={noun} guidanceId="books-density-guidance"','noun={noun} guidanceId={authorView ? "books-density-guidance" : null}')
    s=replace(s,': "A book can appear in each period its recorded dates overlap."}',': null}')
    s=replace(s,'guidanceId="books-density-guidance" onApply=','guidanceId="books-density-guidance" showGuidance={authorView} onApply=')
    s=replace(s,'descriptionId="books-timeline-help"','descriptionId={authorView ? "books-timeline-help" : undefined}')
    line=next(line for line in s.splitlines() if '<p className="timeline-scroll-help" id="books-timeline-help">' in line)
    return replace(s,line,'    {authorView && <p className="timeline-scroll-help" id="books-timeline-help">Years filter authors’ recorded life dates. Dashed lines show uncertainty; a single recorded date appears as a marker.{Boolean(data?.undatedTotal) && ` ${data!.undatedTotal.toLocaleString("en-GB")} authors have no plottable lifespan; find them in the full-range author index.`}</p>}')
change('web','components/BooksTimeline.tsx',timeline)
change('web','components/Books.module.css',lambda s:s+'\n.overviewText p + p { margin-top: 14px; }\n.overviewText .overviewCredit { color: var(--muted); font: 12px/1.6 var(--sans); }\n.overviewCredit a { color: var(--ultramarine); }\n')
for kind in ['api','web']:
    (RELEASE/kind/'.gcloudignore').write_text('.gcloudignore\n.git\n.DS_Store\n.env\n.env.*\n!.env.example\nnode_modules\n.next\nplaywright-report\ntest-results\n*.tsbuildinfo\n')
(BACKUP/'release-source.json').write_text(json.dumps(changes,indent=2))
print('Prepared isolated release with',len(changes),'changed files; review:',BACKUP/'release-source.json')
