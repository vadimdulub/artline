"""Public museum association directory; no artwork downloading or fixture writes."""
import runpy,re,json
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];soup=b['soup'];out=[]
base='https://www.museumsbund.de/mitgliedsmuseen/'
first=m.page(base);script=next(x['text']for x in first['scripts']if'window.FWP_JSON'in x['text']);cfg=json.loads(script.split('=',1)[1].strip().rstrip(';'));pager=cfg['preload_data']['settings']['pager'];assert pager['total_pages']<=100
for n in range(1,pager['total_pages']+1):
    u=base+('?fwp_paged='+str(n)if n>1 else'');s,p=soup(u)
    js=next(x['text']for x in p['scripts']if'window.FWP_JSON'in x['text']);pg=json.loads(js.split('=',1)[1].strip().rstrip(';'))['preload_data']['settings']['pager'];assert pg['page']==n
    for t in s.select('.teaser__inner'):
        head=t.select_one('h2.teaser__headline a');city=t.select_one('.teaser__excerpt strong')
        if not head or not city:continue
        out.append(dict(name=head.get_text(' ',strip=True),city=city.get_text(' ',strip=True),website_url=head.get('href'),source_url=u,source_receipt=p['receipt'],directory_kind='German Museums Association member institution or branch',research_state='Directory evidence only; country, collection objects and image coverage not implied'))
    if n%8==0:print('DIRECTORY',n,'/',pager['total_pages'],'entries',len(out),flush=True)
assert len(out)==pager['total_rows'],(len(out),pager)
m.h.save(m.RUN/'association-directory.json',dict(at=m.h.now(),records=out,source=base,declared_total=pager['total_rows'],pages=pager['total_pages'],limitations='Association membership directory, including specialised museums and some foreign members; not a complete German national census and not object coverage. No personal contacts or admission terms exported.'))
print('DIRECTORY COMPLETE',len(out),len({(x['name'],x['city'],x['website_url'])for x in out}))
