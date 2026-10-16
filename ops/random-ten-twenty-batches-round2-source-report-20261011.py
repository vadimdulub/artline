#!/usr/bin/env python3
"""Source-only report: public evidence, explicit verification gaps, no delivery claim."""
import importlib.util,json,html,collections
from pathlib import Path
sp=importlib.util.spec_from_file_location('report','ops/random-ten-twenty-batches-round2-report-20261011.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
b=h.b;r=b.r;RUN=b.RUN

def main():
    sources=[];stats=[];unlinked=r.load(RUN/'unlinked-index-entries.json.gz');pairs=b.cohort()
    def date_key(value):return str(value or '').strip().strip('?').strip()
    for pair in pairs:
        a=pair['artist'];aid=a['id'];index=r.load(RUN/'indexes'/(aid+'.json.gz'));api=r.load(RUN/'translations'/(aid+'-en.json.gz'));lookup=collections.defaultdict(list)
        for item in api['items']:lookup[(b.q.norm(html.unescape(item['title'])),date_key(item.get('yearAsString')))].append(item)
        entries=[dict(x,kind='linked_artwork_page') for x in index['items']]+[dict(x,kind='index_entry_without_artwork_page') for x in unlinked if x['artist_id']==aid]
        rows=[]
        for item in entries:
            page=None;page_outcome='not_requested_after_1970' if item['date'] and item['date']['creation_year_start']>1970 else 'pending_source_page'
            if item['kind']=='linked_artwork_page':
                key=r.sha(item['url'].encode())+'.json.gz'
                for folder in ['page-retries','pages']:
                    path=RUN/folder/aid/key
                    if not path.exists():continue
                    rec=r.load(path);page=rec.get('page');page_outcome=rec['outcome'];break
            else:page_outcome='no_individual_artwork_page'
            matches=lookup[(b.q.norm(html.unescape(item['title'])),date_key(item['source_date']))]
            picture=page.get('image_url') if page else None
            if not picture and len(matches)==1:picture=matches[0].get('image')
            if picture and '/Content/images/FRAME-' in picture:picture=None
            excluded=bool(item['date'] and item['date']['creation_year_start']>1970)
            action='excluded_after_1970' if excluded else 'catalogue_reconciliation_pending'
            reason='Explicit source creation date is after 1970.' if excluded else 'Awaiting fresh production catalogue reconciliation, object/version checks and selected image delivery.'
            if page_outcome=='no_individual_artwork_page':reason+=' The source index supplies no individual artwork-page link.'
            if page_outcome=='source_unavailable':reason+=' Individual source page was unavailable; the captured failure is preserved.'
            row=dict(batch=pair['batch'],artist=a['display_name'],artist_id=aid,title=item['title'],source_date=item['source_date'] or 'Unknown date',source_url=item['url'],source_kind=item['kind'],source_picture_url=picture,source_rights_label=page.get('rights_label') if page else None,action=action,reason=reason,page_outcome=page_outcome,artwork_id=None,artwork_url=None,catalogue_picture_url=None,image_added=False)
            rows.append(row);sources.append(row)
        stats.append(dict(batch=pair['batch'],batch_rank=pair['batch_rank'],artist=a['display_name'],artist_id=aid,artist_url='https://artlines.org/artists/'+a['slug'],wikiart_url=pair['source']['url'],source_entries=len(rows),source_picture_links=sum(bool(x['source_picture_url']) for x in rows),new_works=0,images_added=0,after_works='Pending verification',after_images='Pending verification',verified=False))
    summary=dict(at=r.now(),operation=b.OP,artists=stats,artists_selected=len(pairs),batches_selected=20,source_listings=len(sources),source_picture_links=sum(bool(x['source_picture_url']) for x in sources),source_page_outcomes=dict(collections.Counter(x['page_outcome'] for x in sources)),production_delivery_completed=False,blocker='Google Cloud credentials require user reauthentication.',local_database_connected=False)
    h.write_json(RUN/'source-research-summary.json',summary);h.write_json(RUN/'source-research-artworks.json',sources)
    for n in range(1,21):
        sc=[x for x in sources if x['batch']==n];artists=[x for x in stats if x['batch']==n];folder=RUN/'batches'/f'{n:02d}'
        part=dict(batch=n,artists=artists,totals=dict(new_works=0,images_added=0),verified=False)
        # Render the established, bounded offline table, then label it explicitly as research.
        temp=folder/'source-preview';temp.mkdir(exist_ok=True);h.render_batch(temp,part,sc,[])
        content=(temp/'report.html').read_text().replace('href="../../report.html"','href="../../source-research-report.html"')
        content=content.replace('0 new works · 0 pictures added',f'{len(sc):,} source listings · production reconciliation pending')
        content=content.replace('<option value="catalogue">','<option value="catalogue" disabled>').replace('<option value="sources">','<option value="sources" selected>')
        content=content.replace('Only attached catalogue pictures load inline; source reproductions are linked individually.','Source pictures are linked individually; no image delivery is claimed.')
        content=content.replace('<a href="summary.json">Artist results</a> · <a href="source-artworks.json">Source records</a> · <a href="catalogue-artworks.json">Catalogue records</a>','<a href="source-research-summary.json">Artist results</a> · <a href="source-research-artworks.json">Source records</a>')
        (folder/'source-research.html').write_text(content);(temp/'report.html').unlink();temp.rmdir()
        h.write_json(folder/'source-research-summary.json',part);h.write_json(folder/'source-research-artworks.json',sc)
    table=''.join(f'<tr><td><a href="batches/{n:02d}/source-research.html">Batch {n:02d}</a></td><td>'+html.escape(', '.join(x['artist'] for x in stats if x['batch']==n))+f'</td><td>{sum(x["source_entries"] for x in stats if x["batch"]==n):,}</td><td>{sum(x["source_picture_links"] for x in stats if x["batch"]==n):,}</td></tr>' for n in range(1,21))
    body=f'<h1>Second campaign · 200 artists</h1><p class="count">{len(sources):,} source listings · {summary["source_picture_links"]:,} picture links</p><p>The new random sample contains twenty groups of ten artists, with no overlap with eleven recorded earlier artist cohorts. All 200 accessible WikiArt artist indexes are recorded. This is source coverage, not a complete lifetime catalogue.</p><p><strong>Production delivery is pending.</strong> Google Cloud requires renewed sign-in. No artworks or images have been added by this campaign yet. Individual source-page review and catalogue reconciliation are tracked separately below; linked pictures are source references.</p><div class="scroll"><table><thead><tr><th>Batch</th><th>Artists</th><th>Listings</th><th>Picture links</th></tr></thead><tbody>{table}</tbody></table></div><p><a href="source-research-summary.json">Research summary</a> · <a href="source-research-artworks.json">All source listings and picture links</a> · <a href="cohort.json">Frozen random sample</a></p>'
    (RUN/'source-research-report.html').write_text(h.shell('Second campaign artwork research',body))
    print(json.dumps({k:v for k,v in summary.items() if k!='artists'}))

if __name__=='__main__':main()
