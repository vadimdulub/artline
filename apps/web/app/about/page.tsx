import Image from "next/image";
import Link from "@/components/MemberLink";
import { NavigationIcon } from "@/components/MemberNavigation";
import { StructuredData } from "@/components/StructuredData";
import { absoluteURL, breadcrumbs, pageMetadata } from "@/lib/seo";
import { getAboutPreviews, imageCredit } from "./about-content";
import { PreviewScroller } from "./PreviewScroller";
import { TimelinePreview } from "./TimelinePreview";
import styles from "./about.module.css";

const description = "See art. Discover its world. Explore Artline’s interactive timelines and illustrated museum guides, connecting artists, masterpieces, books and history.";
const startingPoints = [
  { preset: "renaissance", title: "The Renaissance" },
  { preset: "edo", title: "Edo Japan" },
  { preset: "romanticism", title: "Romanticism" },
  { preset: "second-world-war", title: "The Second World War" },
];

export function generateMetadata() {
  return pageMetadata("About Artline: art, timelines & museum guides", description, "/about");
}

export default function AboutPage() {
  // Bounded editorial content; no catalogue query or member session needed.
  const previews = getAboutPreviews();
  const creditedWorks = [...new Map([
    ...previews.artworks.map(item => item.work), ...previews.timeline.map(item => item.work),
    ...previews.guides.map(item => item.work), ...previews.artists.map(item => item.work),
  ].map(work => [work.id, work])).values()];

  return <main id="main-content" className={styles.page}>
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "About Artline", path: "/about" }])} />
    <StructuredData data={{
      "@context": "https://schema.org", "@type": "AboutPage", "@id": absoluteURL("/about#page"),
      url: absoluteURL("/about"), name: "About Artline: art, timelines & museum guides", description, inLanguage: "en",
      isPartOf: { "@type": "WebSite", name: "Artline", url: absoluteURL("/") },
      about: { "@type": "WebSite", name: "Artline", url: absoluteURL("/"), description },
      hasPart: [
        { "@type": "WebPageElement", name: "Artworks to explore", url: absoluteURL("/about#artwork-carousel") },
        { "@type": "WebPageElement", name: "Interactive timelines", url: absoluteURL("/about#timelines") },
        { "@type": "WebPageElement", name: "Museum guides", url: absoluteURL("/about#museum-guides") },
        { "@type": "WebPageElement", name: "Discover artists", url: absoluteURL("/about#discover-artists") },
      ],
    }} />

    <section className={styles.hero} aria-labelledby="about-title">
      <div className={styles.heroCopy}>
        <p className={styles.aboutLabel}>Artline. A world of art, connected.</p>
        <h1 id="about-title">See art.<br />Discover its world.</h1>
        <p className={styles.intro}>Follow a painting into the lives, places and ideas around it.</p>
        <div className={styles.actions}>
          <Link href="/all" className={styles.primaryLink} prefetch={false}>Explore the timeline</Link>
          <a href="#museum-guides" className={styles.heroLink}>Find a museum guide</a>
        </div>
      </div>
      <div className={styles.gallery}>
        <PreviewScroller id="artwork-carousel" label="Artworks to explore" previousLabel="Previous artworks" nextLabel="Next artworks"
          heading={<h2 className={styles.galleryTitle}>Begin with a work.</h2>}
          action={<Link href="/artworks" className={styles.textLink} prefetch={false}>Browse artworks</Link>}>
          <ul className={styles.galleryWorks}>
            {previews.artworks.map(({ guide, work }, index) => <li className={styles.galleryWork} key={work.id}>
              <Link href={`/guides/${guide}#work-${work.id}`} prefetch={false} className={styles.galleryLink} aria-label={`Explore ${work.title} by ${work.artist}`}>
                <span className={styles.galleryImage}><Image src={work.image} alt={work.title} width={600} height={500} unoptimized loading={index < 3 ? "eager" : "lazy"} fetchPriority={index === 0 ? "high" : "auto"} /></span>
                <span className={styles.galleryCaption}><span className={styles.galleryWorkTitle}>{work.title}</span><span className={styles.galleryArtist}>{work.artist}</span><span className={styles.galleryDate}>{work.date}</span></span>
              </Link>
            </li>)}
          </ul>
        </PreviewScroller>
        <div className={styles.galleryFoot}><a href="#timelines">Discover what connects them <span aria-hidden="true">↓</span></a><a href="#image-credits">Image credits</a></div>
      </div>
    </section>

    <section id="timelines" className={styles.timelines} aria-labelledby="timelines-title">
      <TimelinePreview items={previews.timeline} />
      <div className={styles.timelineFoot}><span>Art, books and history. Side by side.</span><nav aria-label="Explore timelines"><Link href="/" prefetch={false}>Painters</Link><Link href="/books" prefetch={false}>Books</Link><Link href="/events" prefetch={false}>Events</Link><Link href="/art-history-timeline">How to explore</Link></nav></div>
      <nav className={styles.startingPoints} aria-label="Explore a period"><span>Or start with an era</span>{startingPoints.map(point => <Link key={point.preset} prefetch={false} href={`/all?preset=${point.preset}&selection=true&type=artwork&type=book&type=event&highlights=false`}>{point.title}</Link>)}</nav>
    </section>

    <section id="museum-guides" className={styles.guides} aria-labelledby="guides-title">
      <PreviewScroller id="guide-carousel" label="Museum guides to explore" previousLabel="Previous guides" nextLabel="Next guides"
        heading={<div><h2 id="guides-title">Step inside a museum.</h2><p>A closer look. A guide to take with you.</p></div>}
        action={<Link href="/guides" className={styles.textLink}>Browse all museum guides</Link>}>
        <ul className={styles.guideCards}>{previews.guides.map(guide => <li key={guide.slug}>
          <Link href={`/guides/${guide.slug}`} className={styles.guideLink} prefetch={false}>
            <div className={styles.guideCover}>
              <span className={styles.guideCity}>{guide.city}</span><h3 className={styles.guideMuseum}>{guide.title}</h3>
              <span className={styles.guideImage}><Image src={guide.image} alt={`${guide.work.title} by ${guide.work.artist}`} width={600} height={440} unoptimized loading="lazy" /></span>
              <span className={styles.guideFormat}><NavigationIcon kind="guide" /><span>{guide.count} artworks</span><span>PDF</span></span>
            </div>
            <span className={styles.guideAction}>Read the guide <span aria-hidden="true">↗</span></span>
          </Link>
        </li>)}</ul>
      </PreviewScroller>
    </section>

    <section id="discover-artists" className={styles.artists} aria-labelledby="artists-title">
      <PreviewScroller id="artist-carousel" label="Artists to explore" previousLabel="Previous artists" nextLabel="Next artists"
        heading={<h2 id="artists-title">Meet the artists.</h2>}
        action={<Link href="/artists" className={styles.textLink} prefetch={false}>All artists</Link>}>
        <ul className={styles.artistCards}>{previews.artists.map(({ work, artist }) => <li key={artist.slug}>
          <Link href={`/artists/${artist.slug}`} className={styles.artistCard} prefetch={false} aria-label={`Explore ${artist.name}`}>
            <span className={styles.artistImage}><Image src={work.image} alt={work.title} width={500} height={400} unoptimized loading="lazy" /></span>
            <h3>{artist.name}</h3><p>{work.title}</p>
          </Link>
        </li>)}</ul>
      </PreviewScroller>
    </section>

    <section className={styles.closing} aria-labelledby="closing-title">
      <h2 id="closing-title">Follow your curiosity.</h2>
      <Link href="/all" className={styles.primaryLink} prefetch={false}>Explore the timeline</Link>
    </section>
    <nav className={styles.directories} aria-label="Explore the collection">
      <Link href="/artists" prefetch={false}><NavigationIcon kind="artists" />Find an artist</Link>
      <Link href="/artworks" prefetch={false}><NavigationIcon kind="artworks" />Browse artworks</Link>
      <Link href="/museums" prefetch={false}><NavigationIcon kind="museum" />Explore museums</Link>
    </nav>
    <div className={styles.notes}>
      <p>Sign in for museum collections and bookmarks.</p>
      <details><summary>Image credits</summary><div id="image-credits">{creditedWorks.map(work => <p key={work.id}><strong>{work.artist}, <cite>{work.title}</cite>.</strong> {imageCredit(work)} <a href={work.imageSource} target="_blank" rel="noreferrer">Image details</a>. <a href={work.licenseUrl || work.imageSource} target="_blank" rel="noreferrer">{work.license}</a>.</p>)}</div></details>
      <details><summary>The first 100 painters</summary><div id="popular-painters"><p>The painter timeline starts with 100 painters from the Pantheon 2025 ranking, with editorial corrections: Hokusai is included; Donatello, primarily a sculptor, is excluded. Popularity is a starting point, not a measure of artistic quality.</p><p>Remove “Top 100 painters” to explore further. “Clear filters” keeps your date range; “Reset view” restores the starting selection and full range.</p><p>Ranking adapted from <a href="https://pantheon.world/data/datasets" target="_blank" rel="noreferrer">Pantheon 2025 / Datawheel</a> under <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>. This licence covers the adapted selection, not the application or artwork images.</p></div></details>
    </div>
  </main>;
}
