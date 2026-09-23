"""Bounded, attributed excerpts from retained Wikipedia introductions."""
import re

LICENSE='https://creativecommons.org/licenses/by-sa/4.0/'

def excerpt(text,kind):
    """Use complete introductory sentences, retaining order and attribution."""
    budget=220 if kind=='book' else 140
    paragraphs=[];used=0
    for original in text.splitlines():
        paragraph=original.strip()
        if not paragraph:continue
        count=len(paragraph.split())
        if used+count<=budget:
            paragraphs.append(paragraph);used+=count
        else:
            # Keep full sentences; do not cut a proposition at a word limit.
            ends=[m.end() for m in re.finditer(r'[.!?][”"\']?(?=\s|$)',paragraph)]
            options=[paragraph[:end] for end in ends if len(paragraph[:end].split())<=budget-used]
            if options:paragraphs.append(options[-1])
            break
        if len(paragraphs)==3:break
    return paragraphs

def overview(capture,qid,kind):
    page=capture['page']
    if page.get('pageprops',{}).get('wikibase_item')!=qid:return None,'page_identity_mismatch'
    if 'disambiguation' in page.get('pageprops',{}):return None,'disambiguation'
    revisions=page.get('revisions',[]);text=page.get('extract','').strip()
    if not revisions or len(text)<80:return None,'insufficient_introductory_text'
    if any(marker in text.lower() for marker in ('#redirect','<script','{{','}}')):return None,'malformed_introductory_text'
    paragraphs=excerpt(text,kind)
    if len(' '.join(paragraphs))<80:return None,'no_complete_bounded_excerpt'
    revision=revisions[0]['revid']
    return {'paragraphs':paragraphs,'sourceUrl':'https://en.wikipedia.org/w/index.php?oldid='+str(revision),'sourceTitle':page['title'],'revision':revision,'credit':'Wikipedia contributors','licenseUrl':LICENSE},'sourced_introduction'
