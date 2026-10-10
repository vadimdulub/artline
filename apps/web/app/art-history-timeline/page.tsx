import Link from "@/components/MemberLink";
import { StructuredData } from "@/components/StructuredData";
import { breadcrumbs, pageMetadata } from "@/lib/seo";

export function generateMetadata() {
  return pageMetadata("Art history timeline: explore artists, artworks & ideas", "Learn to explore art history through overlapping artists’ lives, artwork dates, museum collections, books and events with Artline’s interactive timelines.", "/art-history-timeline");
}

// This guide describes the tools, without embedding catalogue records.
export default function ArtHistoryTimelinePage() {
  return <main id="main-content" className="admin-page prose-page">
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Guides", path: "/guides" }, { name: "Art history timeline", path: "/art-history-timeline" }])} />
    <nav aria-label="Breadcrumb"><Link href="/guides">Guides</Link></nav>
    <h1>Explore art history through time</h1>
    <p>An art history timeline helps you ask what was happening at the same time: which artists’ lives overlapped, when a work was made, and which books or historical events belong beside it. Artline brings these routes together so you can move from a broad period to an individual record and its sources.</p>
    <p><Link href="/">Open the interactive art history timeline</Link>, or start with the <Link href="/artists">artist directory</Link>.</p>

    <h2>Start with a question and a date range</h2>
    <p>Choose a period you want to understand, then narrow the timeline by artist, movement or region. Try a question such as “Which painters worked during this period?” or “How do artists associated with different countries overlap?” A smaller range makes individual lives easier to compare.</p>
    <p>The painter timeline starts with a popular selection. Turn off “Only popular painters” to explore beyond it. Popularity helps you find a starting point; it does not measure artistic quality. Regions and countries describe artists’ recorded associations, while museum filters describe where collections are located.</p>

    <h2>Compare an artist’s life with the dates of their work</h2>
    <p>Open an artist to read the biography and browse artworks by year. A life span and an artwork’s creation date answer different questions: one places a person in time, while the other places a particular object. When several artists overlap, compare the works as well as the people.</p>
    <p>Read the date label on each record. “Circa”, a range of years, and “before” or “after” retain uncertainty that a single timeline position cannot convey. A gap in the catalogue does not mean an artist stopped working, and an undated artwork has no established creation year.</p>

    <h2>Bring books and historical events into the picture</h2>
    <p>Use the <Link href="/all">combined atlas</Link> to explore art, literature and history together. You can also focus on the <Link href="/books">books timeline</Link> or the <Link href="/events">historical events timeline</Link>. Start with a period, then follow the records and source links that help answer your question.</p>
    <p>Sharing a date or place is a reason to investigate a connection, not evidence of influence by itself. Look for documented relationships and supporting sources before concluding that a book, event or artist shaped another work.</p>

    <h2>Follow an artwork to a museum collection</h2>
    <p>The <Link href="/museums">museum directory</Link> offers another way into art history. Explore recorded holdings, then return to the artists and periods behind them. Collection counts describe what is catalogued in Artline, rather than everything a museum owns.</p>
    <p>A work’s holding institution and its current display status are separate facts. Before planning a visit, check the museum’s official page for current exhibitions and access. A collection record alone cannot establish that an artwork is on view.</p>

    <h2>Use the sources to go further</h2>
    <p>Artwork records bring together recorded titles, dates, media, locations and source links. Where an image is available, inspect its details and recorded permissions. Missing information remains unknown; an image’s availability does not establish permission for every reuse.</p>
    <p>Learn <Link href="/about">how the atlas selects content and documents sources</Link>, then use the timelines to develop your own comparisons and reading paths.</p>
  </main>;
}
