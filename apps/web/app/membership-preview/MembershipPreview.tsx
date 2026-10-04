"use client";

import { useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Action, Art, Source, StageHeading, WorkCaption, works, type Feature } from "./preview-shared";
import { additionalFeatures, additionalPanels } from "./MoreMembershipIdeas";

const features: Feature[] = [
  { id: "collections", title: "Personal collections", short: "Give your discoveries a home.", promise: "A place to gather the art, books and ideas you want to return to.", free: "Browse everything and try one collection.", paid: "Unlimited private collections, sections and cross-device sync.", phase: "Start here" },
  { id: "notes", title: "A visual notebook", short: "Keep what you notice.", promise: "Write beside the work, collect questions and find your thoughts again.", free: "Read catalogue descriptions and sources.", paid: "Private notes, custom tags and searchable notebooks across devices.", phase: "Start here" },
  { id: "views", title: "Saved explorations", short: "Pick up where you left off.", promise: "Save a period, place and set of filters as a view you can revisit.", free: "Use all public search and timeline filters.", paid: "Save, organize and restore unlimited exploration views.", phase: "Start here" },
  { id: "timelines", title: "Your own timelines", short: "Make the connections visible.", promise: "Place paintings, books and historical events on one personal timeline.", free: "Explore Artline’s existing timelines.", paid: "Build custom timelines, add personal annotations and present them.", phase: "Next release" },
  { id: "compare", title: "The comparison desk", short: "Look more closely, together.", promise: "See two works at once and compare their rhythm, colour and detail.", free: "View and zoom an individual artwork.", paid: "Compare multiple works with linked zoom and a shared notebook.", phase: "Next release" },
  { id: "study", title: "A daily study practice", short: "Remember more of what you love.", promise: "Turn a collection into short lessons and visual recall sessions.", free: "Read the catalogue at your own pace.", paid: "Guided paths, spaced review and progress saved across devices.", phase: "Next release" },
  { id: "visits", title: "Museum visit notebook", short: "Arrive with a little curiosity.", promise: "Build a personal list of works to research before your next museum visit.", free: "Browse museum holdings and sources.", paid: "Save visit plans, checklists and personal notes for each museum.", phase: "Explore later" },
  { id: "exports", title: "Beautiful study sheets", short: "Take your research with you.", promise: "Bring images, notes and citations together in a document worth keeping.", free: "Read source links on every record.", paid: "Export rights-cleared collection sheets, citations and presentation packs.", phase: "Start here" },
  ...additionalFeatures,
];

function Collections() {
  const [collections, setCollections] = useState(["Water, in different worlds", "Rooms filled with light", "My first museum visit"]);
  const [selected, setSelected] = useState(collections[0]);
  const [name, setName] = useState("");
  const [extra, setExtra] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const shown = selected === collections[0] ? works.slice(0, extra ? 4 : 3) : selected === collections[1] ? [works[3]] : [];
  return <>
    <StageHeading title="My collections" description="Small discoveries. A growing personal atlas."><Action onClick={() => dialog.current?.showModal()}>New collection</Action></StageHeading>
    <div className="mp-collection-layout"><div className="mp-collection-list" aria-label="Your collections">{collections.map((item, i) => <button key={item} type="button" aria-pressed={selected === item} onClick={() => setSelected(item)}><span className={`mp-folder mp-folder-${i % 3}`} aria-hidden="true" /><span>{item}</span></button>)}<p>Private to you</p></div>
      <div className="mp-collection-content"><div className="mp-collection-title"><h3>{selected}</h3><span>{shown.length} works</span></div><p className="mp-description">{selected === collections[0] ? "Three ways of looking at water: a wave, a garden and an evening by the sea." : "A collection begins with something you want to look at again."}</p>
      {shown.length ? <div className="mp-work-grid">{shown.map(work => <figure key={work.id}><Art work={work} /><WorkCaption work={work} /></figure>)}</div> : <div className="mp-empty"><span aria-hidden="true">＋</span><h3>What caught your eye?</h3><p>Choose a work to start this collection.</p><Action secondary onClick={() => { setSelected(collections[0]); }}>Explore the sample collection</Action></div>}
      {selected === collections[0] && <Action secondary onClick={() => setExtra(!extra)}>{extra ? "Remove the blue room" : "Add Sunlight in the Blue Room"}</Action>}
      </div></div>
    <dialog className="mp-dialog" ref={dialog}><form onSubmit={event => { event.preventDefault(); if (!name.trim()) return; setCollections([...collections, name.trim()]); setSelected(name.trim()); setName(""); dialog.current?.close(); }}><h2>A new collection</h2><label><span>Collection name</span><input autoFocus value={name} onChange={event => setName(event.target.value)} placeholder="For example, Byzantine colour" required maxLength={100} /></label><p>Your collection is private.</p><div className="mp-actions"><button className="mp-button" type="submit">Create collection</button><Action secondary onClick={() => dialog.current?.close()}>Cancel</Action></div></form></dialog>
  </>;
}

function Notebook() {
  const [note, setNote] = useState("The bridge makes a second horizon. I want to compare its curve with the wave in Hokusai’s print.\n\nLook again: where does the reflection end and the garden begin?");
  const [saved, setSaved] = useState(false);
  const [tags, setTags] = useState(["Water", "Composition"]);
  return <><StageHeading title="My visual notebook" description="Stay with a work a little longer." /><div className="mp-notebook"><figure><Art work={works[1]} /><WorkCaption work={works[1]} /><Source work={works[1]} /></figure><div className="mp-note-paper"><span className="mp-small">Your private note</span><h3>Looking at the bridge</h3><label><span className="sr-only">Your observation</span><textarea aria-label="Your observation" value={note} onChange={event => { setNote(event.target.value); setSaved(false); }} /></label><div className="mp-tags">{tags.map(tag => <span key={tag}>{tag}</span>)}<button type="button" onClick={() => { if (!tags.includes("Look again")) setTags([...tags, "Look again"]); }}>+ Look again</button></div><div className="mp-note-bottom"><Action onClick={() => setSaved(true)}>Save note</Action><span role="status">{saved ? "Saved in this preview" : "Only you can see this note"}</span></div></div></div></>;
}

function SavedViews() {
  const [views, setViews] = useState(["Japan, 1800–1900", "Women painting light", "Water across cultures"]);
  const [selected, setSelected] = useState(views[0]);
  const [saved, setSaved] = useState(false);
  return <><StageHeading title="Saved explorations" description="A good question is worth returning to."><Action onClick={() => { if (!saved) setViews([...views, "My current exploration"]); setSaved(true); }}>Save this view</Action></StageHeading><div className="mp-view-list">{views.map((view, i) => <button type="button" key={view} aria-pressed={view === selected} onClick={() => setSelected(view)}><span className="mp-view-glyph" aria-hidden="true">{["◒", "◐", "◓"][i % 3]}</span><strong>{view}</strong><span>{i === 0 ? "1800–1900 · Japan · Prints" : i === 1 ? "1850–1930 · Painting" : "Personal filters"}</span></button>)}</div><div className="mp-restored"><div><span className="mp-small">Restored view</span><h3>{selected}</h3><p>Your period, places, creators and view settings return together.</p></div><div className="mp-view-strip">{(selected === views[0] ? [works[0]] : selected === views[1] ? [works[3]] : works.slice(0, 3)).map(work => <figure key={work.id}><Art work={work} /><WorkCaption work={work} /></figure>)}</div></div><p className="mp-status" role="status">{saved ? "My current exploration added to your saved views." : "Select a view to try restoring it."}</p></>;
}

function Timelines() {
  const [books, setBooks] = useState(true);
  const [history, setHistory] = useState(true);
  const [annotation, setAnnotation] = useState(false);
  return <><StageHeading title="Water, light & a changing world" description="A personal timeline, 1830–1900."><Action onClick={() => setAnnotation(!annotation)}>{annotation ? "Remove my note" : "Add my note"}</Action></StageHeading><div className="mp-timeline-controls"><span>Show on my timeline</span><label><input type="checkbox" checked={books} onChange={event => setBooks(event.target.checked)} />Books</label><label><input type="checkbox" checked={history} onChange={event => setHistory(event.target.checked)} />History</label></div><div className="mp-timeline"><div className="mp-years">{[1830, 1850, 1870, 1900].map(year => <span key={year}>{year}</span>)}</div><div className="mp-timeline-row"><span>Art</span><div className="mp-art-events">{[works[0], works[3], works[1]].map(work => <figure key={work.id}><Art work={work} /><figcaption><span>{work.date}</span><strong>{work.artist}</strong></figcaption></figure>)}</div></div>{books && <div className="mp-timeline-row"><span>Books</span><div className="mp-book-event"><span>1851</span><strong>Moby-Dick</strong><small>Herman Melville</small></div></div>}{history && <div className="mp-timeline-row"><span>History</span><div className="mp-history-event"><span>1868</span><strong>Meiji Restoration</strong></div></div>}{annotation && <div className="mp-personal-event"><span>My interpretation</span><p>Compare the curves and open spaces. Is the relationship visual, historical, or both?</p></div>}</div><p className="mp-footnote">Your interpretation stays separate from catalogue facts. Approximate dates retain their original ranges.</p></>;
}

function Compare() {
  const [zoom, setZoom] = useState(1);
  const [right, setRight] = useState(works[1]);
  return <><StageHeading title="A closer look" description="One subject. Two very different ways of seeing."><Action secondary onClick={() => { setRight(right.id === "bridge" ? works[2] : works[1]); setZoom(1); }}>Change the second work</Action></StageHeading><div className="mp-compare-tools"><span>Linked zoom</span><input aria-label="Linked zoom" type="range" min="1" max="2.2" step="0.1" value={zoom} onChange={event => setZoom(Number(event.target.value))} /><output>{Math.round(zoom * 100)}%</output><button type="button" onClick={() => setZoom(1)}>Reset</button></div><div className="mp-compare-pair">{[works[0], right].map(work => <figure key={work.id}><div className="mp-zoom-window"><Art work={work} style={{ transform: `scale(${zoom})` }} /></div><WorkCaption work={work} /><p>{work.medium}</p></figure>)}</div><div className="mp-comparison-note"><span aria-hidden="true">✎</span><p>Study prompt: follow the largest curve in each work. Where does your eye go next?</p></div></>;
}

function Study() {
  const [step, setStep] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [complete, setComplete] = useState(false);
  const work = works[step];
  return <><StageHeading title="A little looking, every day" description="Visual recall from your own collection." /><div className="mp-study"><div className="mp-study-image"><Art work={work} /></div><div className="mp-study-question"><div className="mp-study-progress"><span>{complete ? "Session complete" : `Work ${step + 1} of 3`}</span><progress max={3} value={complete ? 3 : step} /></div>{complete ? <><h3>Three works, a little closer.</h3><p>Your next session would revisit the works you found hardest to remember.</p><Action onClick={() => { setStep(0); setRevealed(false); setComplete(false); }}>Try the session again</Action></> : <><h3>{revealed ? work.artist : "Who made this work?"}</h3><p>{revealed ? `${work.title}, ${work.date}.` : "Look at the composition and the surface. Take your time before revealing the answer."}</p>{revealed ? <div className="mp-actions"><Action onClick={() => { if (step === 2) setComplete(true); else setStep(step + 1); setRevealed(false); }}>I remembered</Action><Action secondary onClick={() => { if (step === 2) setComplete(true); else setStep(step + 1); setRevealed(false); }}>Review again later</Action></div> : <Action onClick={() => setRevealed(true)}>Reveal the artist</Action>}</>}<span className="mp-small">No streak pressure. Just a personal practice.</span></div></div></>;
}

function Visits() {
  const [checked, setChecked] = useState<string[]>([]);
  const [note, setNote] = useState("Start with the Japanese prints, then spend time with Monet.");
  return <><StageHeading title="An afternoon at the Met" description="My museum visit notebook" /><div className="mp-visit-summary"><div><span className="mp-small">New York</span><h3>The Metropolitan Museum of Art</h3><p>Two works I want to look into before visiting.</p></div><span className="mp-visit-count">{checked.length}<small> / 2 researched</small></span></div><div className="mp-visit-rows">{works.slice(0, 2).map(work => <div className="mp-visit-row" key={work.id}><Art work={work} /><div><h3>{work.title}</h3><p>{work.artist}, {work.date}</p><span className="mp-display-status">In the collection · Display status not confirmed</span><a href={work.source} target="_blank" rel="noreferrer">Check the museum record</a></div><label><input type="checkbox" checked={checked.includes(work.id)} onChange={() => setChecked(checked.includes(work.id) ? checked.filter(id => id !== work.id) : [...checked, work.id])} /><span>Researched</span></label></div>)}</div><label className="mp-visit-note"><span>My plan</span><textarea value={note} onChange={event => setNote(event.target.value)} /></label></>;
}

function Exports() {
  const [notes, setNotes] = useState(true);
  const [images, setImages] = useState(true);
  return <><StageHeading title="A study sheet to keep" description="Your collection, with its context intact." /><div className="mp-export-layout"><div className="mp-export-settings"><h3>Make it yours</h3><label><input type="checkbox" checked={images} onChange={event => setImages(event.target.checked)} />Include eligible images</label><label><input type="checkbox" checked={notes} onChange={event => setNotes(event.target.checked)} />Include my notes</label><p>Titles, dates, source links and image credits are always included.</p><Action onClick={() => window.print()}>Print / save as PDF</Action><small>Opens your browser’s print dialog. Choose “Save as PDF” for the sample sheet.</small></div><article className="mp-export-sheet"><div className="mp-sheet-heading"><span>Artline / Personal collection</span><h3>Water, in different worlds</h3><p>A study sheet by you</p></div>{works.slice(0, 2).map(work => <div className="mp-sheet-work" key={work.id}>{images && <Art work={work} />}<div><h4>{work.title}</h4><p>{work.artist}, {work.date}<br />{work.medium}</p><Source work={work} /></div></div>)}{notes && <div className="mp-sheet-note"><strong>My observation</strong><p>Follow the largest curve in each work. How does it hold the scene together?</p></div>}<footer>Study concept • Image rights from Artline’s documented source records</footer></article></div></>;
}

const panels: Record<string, () => ReactNode> = { collections: Collections, notes: Notebook, views: SavedViews, timelines: Timelines, compare: Compare, study: Study, visits: Visits, exports: Exports, ...additionalPanels };
const reviewKey = "artline-membership-review-v1";
const emptyReview = '{"shortlist":[],"notes":{}}';
type Review = { shortlist: string[]; notes: Record<string, string> };
function subscribeReview(callback: () => void) {
  window.addEventListener("artline:membership-review", callback);
  window.addEventListener("storage", callback);
  return () => { window.removeEventListener("artline:membership-review", callback); window.removeEventListener("storage", callback); };
}
function readReview() { try { return localStorage.getItem(reviewKey) || emptyReview; } catch { return emptyReview; } }
function parseReview(raw: string): Review {
  try {
    const data = JSON.parse(raw);
    return {
      shortlist: Array.isArray(data?.shortlist) ? data.shortlist.filter((id: unknown) => typeof id === "string" && features.some(item => item.id === id)) : [],
      notes: data?.notes && typeof data.notes === "object" ? Object.fromEntries(Object.entries(data.notes).filter(([key, value]) => features.some(item => item.id === key) && typeof value === "string")) as Record<string, string> : {},
    };
  } catch { return { shortlist: [], notes: {} }; }
}

export function MembershipPreview({ initialIdea }: { initialIdea?: string }) {
  const [active, setActive] = useState(initialIdea && features.some(item => item.id === initialIdea) ? initialIdea : additionalFeatures[0].id);
  const newIdeas = additionalFeatures.some(item => item.id === active);
  const visibleFeatures = newIdeas ? additionalFeatures : features.slice(0, 8);
  function selectIdea(id: string) {
    setActive(id);
    const url = new URL(window.location.href);
    url.searchParams.set("idea", id);
    window.history.replaceState(null, "", url.pathname + url.search);
  }
  const snapshot = useSyncExternalStore(subscribeReview, readReview, () => emptyReview);
  const [fallbackReview, setFallbackReview] = useState<Review | null>(null);
  const { shortlist, notes: reviewNotes } = fallbackReview || parseReview(snapshot);
  const storageUnavailable = fallbackReview !== null;
  const feature = features.find(item => item.id === active)!;
  const Panel = panels[active];
  function saveReview(review: Review) {
    try {
      localStorage.setItem(reviewKey, JSON.stringify(review));
      setFallbackReview(null);
      window.dispatchEvent(new Event("artline:membership-review"));
    } catch { setFallbackReview(review); }
  }
  function setShortlist(value: string[]) { saveReview({ shortlist: value, notes: reviewNotes }); }
  function setReviewNotes(value: Record<string, string>) { saveReview({ shortlist, notes: value }); }
  function downloadReview() {
    const content = features.map(item => ({ idea: item.title, shortlisted: shortlist.includes(item.id), feedback: reviewNotes[item.id] || "", paidValue: item.paid }));
    const url = URL.createObjectURL(new Blob([JSON.stringify(content, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = "artline-membership-review.json"; a.click(); URL.revokeObjectURL(url);
  }
  return <main id="main-content" className="mp-root"><div className="mp-review-banner"><span><strong>Membership concepts</strong> {features.length} ideas to try and review</span><span className="mp-open-status"><i />Local preview · All features open</span></div><div className="mp-layout"><aside className="mp-sidebar"><div className="mp-sidebar-intro"><h1>More room for<br />your curiosity.</h1><p>What should an Artline membership make possible?</p></div><div className="mp-idea-groups" role="group" aria-label="Idea collections"><button type="button" aria-pressed={newIdeas} onClick={() => selectIdea(additionalFeatures[0].id)}>New ideas <span>8</span></button><button type="button" aria-pressed={!newIdeas} onClick={() => selectIdea(features[0].id)}>First ideas <span>8</span></button></div><nav aria-label="Membership concepts">{visibleFeatures.map(item => <button type="button" key={item.id} aria-current={active === item.id ? "page" : undefined} onClick={() => selectIdea(item.id)}><span className="mp-nav-mark" aria-hidden="true">{shortlist.includes(item.id) ? "✓" : ""}</span>{item.title}</button>)}</nav><div className="mp-shortlist-summary"><span>{shortlist.length} of {features.length} shortlisted</span><button type="button" onClick={downloadReview}>Download my review</button><p>{storageUnavailable ? "Browser storage is unavailable. Download your review to keep it." : "Your shortlist and feedback stay in this browser."}</p></div></aside><div className="mp-main"><header className="mp-concept-heading"><div><span className="mp-phase">{feature.phase}</span><h2>{feature.short}</h2><p>{feature.promise}</p></div><button type="button" className="mp-shortlist-button" aria-pressed={shortlist.includes(active)} onClick={() => setShortlist(shortlist.includes(active) ? shortlist.filter(id => id !== active) : [...shortlist, active])}>{shortlist.includes(active) ? "✓ Shortlisted" : "+ Shortlist idea"}</button></header><section className={`mp-stage mp-stage-${active}`} aria-label={`${feature.title} interactive mockup`}><Panel /></section><section className="mp-review-detail" aria-label="Review this idea"><div><span>Always free</span><p>{feature.free}</p></div><div><span>Why someone would pay</span><p>{feature.paid}</p></div><label><span>Your feedback</span><textarea aria-label={`Feedback on ${feature.title}`} placeholder="Keep, change, or skip?" value={reviewNotes[active] || ""} onChange={event => setReviewNotes({ ...reviewNotes, [active]: event.target.value })} /></label></section><p className="mp-preview-note">Interactive mockups for review. Sample feature actions reset when switching ideas; your review feedback is saved locally. No payment or catalogue changes.</p></div></div></main>;
}
