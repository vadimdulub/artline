# Marketing page benchmark — 11 October 2026

A curated review of 20 prominent product and discovery pages, requested for the
Artline About redesign. This is a design benchmark, not a global ranking or a
conversion-rate study. Live pages vary by region and campaign.

## Method

Read the official pages and inspected desktop browser screenshots at 1440 × 1000,
including the opening and the following section. Compared image scale, hierarchy,
copy density, navigation, calls to action and transitions between sections.
Cookie and region prompts were dismissed with the visible reject/stay controls
where available. No accounts, purchases or forms were submitted.

The in-app browser could not initialize (missing `sandboxPolicy`); screenshots
were captured with the repository's Playwright and installed Chrome. The temporary
capture report and contact sheets are in `/tmp/artline-marketing-benchmark/`.
Rimowa returned an access denial and was replaced by Squarespace. Airbnb's
personalized home feed did not render in this session and was replaced by
Duolingo. Spotify's public product page and Polestar's US page were used instead
of the web player and global region selector. Observations concern the rendered
states, not every animation or the entire purchase journey.

## The 20 references

| Page | Observed design decision | Application to Artline |
| --- | --- | --- |
| [Apple](https://www.apple.com/) | Very large product imagery, compact centered copy, a clear action pair, alternating light and dark campaigns. | Make the paintings large enough to matter. Give each section one dominant visual and a clear destination. |
| [Linear](https://linear.app/) | Restrained dark palette; large product interface immediately beneath a concise proposition. | Let the real dated timeline demonstrate the experience. Preserve the atlas's dark surface. |
| [Stripe](https://stripe.com/) | Strong type hierarchy; product examples make a broad platform tangible. | Use bounded, real artwork examples instead of explaining every catalogue capability. |
| [Notion](https://www.notion.com/) | A short central proposition followed by a large, recognizable product demonstration. | Shorten the hero's explanation and increase the art-to-copy ratio. |
| [Figma](https://www.figma.com/) | A layered visual demonstration sits between a concise headline and a primary action. | Use unequal artwork proportions to create a composed gallery, with no overlap that hides a painting. |
| [Framer](https://www.framer.com/) | Product demonstration occupies most of the opening; strong repeated alignment. | Let previews do the persuasion; align section titles, content and actions. |
| [Webflow](https://webflow.com/) | A broad visual strip introduces capabilities; larger demonstrations follow. | Make the artist strip browsable and use a different visual treatment for the timeline. |
| [Vercel](https://vercel.com/) | Large quiet areas, sparse actions, a single central brand form. | Remove small competing labels and ornamental chrome. Keep useful breathing room. |
| [Raycast](https://www.raycast.com/) | A focused hero promise and dark product canvas; details arrive later. | Keep technical and attribution details out of the main promotional reading path. |
| [Readymag](https://readymag.com/) | A vivid collage of actual design work, followed by visual examples. | Artline's own reproductions should supply the colour and identity. |
| [Dropbox](https://www.dropbox.com/) | A straightforward benefit beside the product, followed by a contrasting section. | Make the transition from the light gallery to the dark atlas intentional. |
| [Spotify](https://www.spotify.com/us/premium/) | Oversized type and a recognizable visual form dominate the first screen. | Establish a clear scale difference between the main headline and supporting metadata. |
| [Nike](https://www.nike.com/) | Campaign photography leads; short text and category imagery invite immediate browsing. | Make museum and artist destinations image-led and entirely clickable. |
| [Polestar](https://www.polestar.com/us/) | Large photographic product stages; direct action labels; little surrounding decoration. | Give artwork frames generous space and avoid competing badges. |
| [Sonos](https://www.sonos.com/) | An immersive opening image gives way to a focused product feature and larger editorial heading. | Vary the section rhythm while keeping the same typography and palette. |
| [Bang & Olufsen](https://www.bang-olufsen.com/) | Large contextual product imagery and restrained copy. | Frame the artworks as the objects of attention; avoid a grid of small generic feature boxes. |
| [Nothing](https://nothing.tech/) | Packaging fills the opening; dot-matrix branding and a compact floating navigation give the campaign a distinct identity. | Preserve Artline's recognizable vocabulary and let its own imagery carry the campaign. |
| [Google Arts & Culture](https://artsandculture.google.com/) | Visual category entry points, a large artwork feature and curated recommendations. | Connect every painting to its exact object or artist; make browsing the immediate activity. |
| [Squarespace](https://www.squarespace.com/) | Large atmospheric opening, a concise central action and examples of finished work. | Show what a visitor can explore rather than describe the underlying platform. |
| [Duolingo](https://www.duolingo.com/) | Consistent brand characters, one primary starting action and visual feature explanations. | Keep a recognizable Artline identity across the landing page and the experience it opens. |

## Artline direction: a gallery opening into an atlas

The subject is the art itself. The page should move from looking, to travelling
through time, to choosing a museum or artist. Preserve the approved concept:
short marketing copy, timeline preview, museum cards and artist carousel.

- **Palette:** paper `#f2efe8`, ink `#1b1916`, charcoal `#12110f`, stone `#e8e3d9`,
  rust `#8f3a29`, rule `#d0c9be`. Use the existing CSS variables.
- **Type:** Georgia for the large invitation and collection names; Avenir/system
  sans for actions, dates and quiet captions. No additional font requests.
- **Layout:** a centered, open gallery wall; a dark, edge-to-edge atlas within
  the page gutter; museum guides presented as reading objects; a larger artist
  strip; one closing invitation.
- **Images:** full compositions with authentic identities and credits. No
  generative replacements, decorative cropping, counterfeit browser windows or
  unsupported museum/display claims.
- **Interaction:** real links, native scrolling, explicit previous/next controls,
  keyboard boundaries and reduced-motion support. No scroll lock or autoplay.

```text
                See art. Discover its world.
                  one sentence · primary action
       portrait        large landscape        colour study

  ┌──────────────────── dark atlas ───────────────────────┐
  │ Travel through time.                 Open timeline   │
  │     paintings positioned by their actual dates        │
  └───────────────────────────────────────────────────────┘

  Step inside a museum.                         All guides
       guide cover          guide cover          guide cover
       guide cover          guide cover          guide cover

  Meet the artists.                         All artists  ← →
       large painting       large painting       painting …

                 Follow your curiosity.
```

## Critique before implementation

A copy of Apple's product panels would erase Artline's identity. A set of equal
SaaS feature cards would conceal the actual reason to visit. The previous About
also repeated two dark rectangles and gave its best art too little space.

The revised plan puts the expressive emphasis on one open gallery composition,
uses the dark treatment for the real timeline, and gives guides a reading-oriented
form. Dates, artwork identity and useful links remain real. This is an extension
of Artline's existing visual language, not a new brand system. Do not add logo
walls, invented statistics, testimonials or visual effects merely because the
reference pages have them.
