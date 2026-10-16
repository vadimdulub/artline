# Guide exploration: four review concepts

Brief: replace the four text links with two inviting, illustrated destinations.
Remove standalone Historical events and Books timeline links. Rename the combined
explorer and painter lifespan diagram. Prepare concepts only; article changes
depend on the user's choice.

Use the actual Munich guide: 30 artworks, 25 linked artists. Reuse its approved
reproductions, preserving image files and source credits in `assets.json`.
The artwork destination remains the guide's filtered All view; the artist
destination remains its filtered artist timeline. Books and historical context
remain inside the first destination, without separate links here.

## Shared tokens

- Paper `#f2efe8`; surface `#faf8f3`; ink `#1b1916`; muted `#625d55`;
  rule `#d0c9be`; existing Artline accent `#8f3a29`.
- Georgia for titles; Avenir Next / system sans for descriptions and controls.
- Full artwork compositions in previews wherever possible. Portraits are actual
  self-portraits from this guide, not invented representations of the artists.
- Left-aligned readable copy; clear clickable surfaces; generous keyboard focus.
- Responsive layouts, no auto-animation, no production changes.

## Directions

A. Gallery pair — two balanced illustrated destinations, each with a large preview
and a title below. The left shows works; the right combines self-portraits and a
real lifespan preview. Recommended for immediate comprehension.

    [ Explore beyond the guide                          ]
    [ artwork triptych        ][ portraits + timeline  ]
    [ Explore the artworks    ][ Artists across time   ]

B. Exhibition spread — artwork takes most of the section, with an intimate
portrait feature beside it. Strongest visual emphasis and clearest hierarchy.

    [ See the collection in a new way                   ]
    [ large painting + two    ][ artist portrait        ]
    [ Explore the collection  ][ Meet the artists       ]

C. Compact invitations — two horizontal rows with substantial images and a
short invitation. Close to the original section's footprint; useful within a
long guide where vertical space matters.

    [ Keep exploring                                   ]
    [ three works ][ View the collection ][ Open view   ]
    [ portraits   ][ Follow the artists  ][ See timeline]

D. Live preview — an artwork strip with years, beside a picture-led lifespan
preview, so each link shows the kind of exploration it opens.

    [ Find your next connection                        ]
    [ selected artwork chronology ][ artist lifespans  ]
    [ Artworks in context         ][ Who lived when?   ]

Review against the brief: keep the site's cream/Georgia/Avenir identity because
it is established Artline design, not a new generic palette. Differentiate the
options through image composition and interaction hierarchy, not arbitrary
colour themes. Removed a tabbed option because it would add an unnecessary click
before entering Artline. No numbered steps, decorative data or invented counts.

The in-app browser connection failed before initialization; isolated headless
Chromium renders are used for local visual QA. This preview is not a deployment.

## D revision: static imagery

The user selected D and requested still imagery instead of its timeline previews.
Keep D's typography, palette, two-card layout and destinations. Replace the left
chronology with three fixed, labelled illustrations: an artwork from the guide,
a real book title page and an event depiction. Replace the right lifespan chart
with one static Dürer self-portrait. Remove axes, bars and timeline markers from
the mockup. The links still open the filtered explorer and artist timeline.

    [ artwork | book title page | event ][ Dürer self-portrait ]
    [ Artworks in context              ][ Who lived when?     ]

Use already approved Artline imagery and preserve source credits. These are
context examples, without an assertion that the book or event influenced the
pictured work. This remains a mockup for review, not an article deployment.

## Guide integration: right side only

The user clarified that the existing heading, introduction and five artwork
thumbnails stay on the left. Apply D's two static image cards only to the right
side of the actual guide component. Preserve the established palette and type
tokens above, existing alignment and guide-specific destination filters.

    [ Explore this selection in Artline ][ artwork/book/event ][ artist's work ]
    [ existing explanation             ][ Artworks in context][ Who lived when?]
    [ existing five thumbnails         ][ Explore collection ][ Open timeline  ]

Use full-frame reproductions. Prefer a guide self-portrait for the artist card
where available; otherwise illustrate it with a work by a linked artist, without
calling the image a portrait. Select later book/event imagery for the Armenian
and Le Havre guides so the examples fit their periods. At mobile widths stack
the section and then the two cards. The review against the brief removes D's
replacement section heading and full-width layout: the user's original left
column is the anchor. No live diagrams or separate book/event destinations.
