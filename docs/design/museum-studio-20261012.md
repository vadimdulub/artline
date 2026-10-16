# Museum studio and public pages

Local implementation; no migration or deployment applied to the real catalogue.

Design: retain Artline paper #f2efe8, ink #1b1916, stone #e8e3d9, line #d0c9be,
white #faf8f3 and rust #8f3a29 through existing tokens. Georgia titles and the
existing Avenir/sans controls. Left-aligned content, generous uncropped imagery.

Public page: museum name and introduction beside one authentic collection work;
section links beneath, then museum-authored programme and the existing searchable
historical collection. Studio: museum selector, content tabs, search, ruled rows,
then a native editor dialog with explicit save-draft and publish actions.

    Museum / introduction      | full artwork
    Visit / collection         | title and creator
    Collection — Exhibitions — Guides — Visit
    Museum publications
    Existing historical collection and filters

    Museum studio             Public page
    Museum selector           Manage another museum
    Artworks / Exhibitions / Guides / Museum page
    Search                    Add artwork
    Title                     Draft / Published / Edit

Review against the brief: a generic dashboard with analytics cards does not help
museum staff publish. Use a content register and direct editing. The memorable
public element is the museum's real artwork; no fabricated statistics, building
photos, hours or official endorsement. Contemporary content stays outside the
historical artwork/exhibition tables. Public visitors never see draft content.

Refinement: every form field carries a Required/Optional label. Guide and
exhibition editors combine a formatting toolbar with an ordered artwork list,
per-work notes, and a searchable collection picker. New artworks open a second
native dialog so the parent draft remains intact. Image upload sits beside the
image preview and its required credit, using the existing paper/stone palette,
Georgia headings and left-aligned forms. Avoid a separate asset dashboard: the
image and the artwork should stay together. Collection references retain their
identity and source; museum drafts cannot leak through a published guide.

Prepared Artline guides: keep the existing paper/ink/stone surfaces and Georgia
headings. In the Guides tab, a compact image-and-title reading list precedes the
museum's editable publications. Each prepared guide has an explicit Read-only
label and Read guide link; no Edit/Publish control. Search covers both lists via
bounded Go responses. Reuse authentic guide covers and existing public language
and PDF pages. The museum page also links these prepared guides directly.

Museum page tabs: replace section-jump navigation with one visible panel. Keep
Collection first, followed by Exhibitions, Guides and Visit & about. The existing
paper/ink palette, serif panel heading and underlined active tab remain the
visual language. A staff action sits beside each panel heading and opens the
existing editor in place. Preserve public reading, immutable Artline guides,
collection query filters, old section hashes and browser back/forward. On phones,
use two tab columns and let the panel heading/actions wrap without shrinking.
