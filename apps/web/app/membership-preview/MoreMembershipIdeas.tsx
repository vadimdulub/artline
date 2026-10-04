"use client";

import { useRef, useState, type ReactNode } from "react";
import { Action, Art, Source, StageHeading, works, type Feature } from "./preview-shared";

export const additionalFeatures: Feature[] = [
  { id: "presentation", title: "Presentation mode", short: "Give your collection an audience.", promise: "Turn a selection of works into a quiet, beautiful talk or classroom presentation.", free: "Explore works and their source records.", paid: "Custom slide sequences, presenter notes, caption controls and reusable talks.", phase: "New idea · For teaching" },
  { id: "rooms", title: "Shared study rooms", short: "Notice more, together.", promise: "A private space to discuss a collection with a friend, class or study group.", free: "Share links to public catalogue pages.", paid: "Private group collections, discussion threads and member permissions.", phase: "New idea · For groups" },
  { id: "discovery", title: "Personal discovery", short: "Find your next fascination.", promise: "Discover a small, explained selection based on the themes you save.", free: "Browse and search the complete public catalogue.", paid: "Personal recommendations, saved discovery queues and adjustable interests.", phase: "New idea · For explorers" },
  { id: "watchlist", title: "Topic watchlists", short: "Let the catalogue come to you.", promise: "Follow artists and traditions, then see meaningful additions to their records.", free: "Read all public record updates on the site.", paid: "Personal update feeds and optional digests for followed topics.", phase: "New idea · For researchers" },
  { id: "offline", title: "Offline study packs", short: "Keep exploring beyond Wi-Fi.", promise: "Take a small collection, its notes and eligible images on a journey.", free: "Explore the online catalogue.", paid: "Bounded offline packs with rights-cleared images, notes and source credits.", phase: "New idea · For travel" },
  { id: "citations", title: "Research citations", short: "Keep a trail back to the source.", promise: "Gather the references behind your collection into a reusable bibliography.", free: "Open sources and read image credits.", paid: "Citation baskets, reusable bibliographies and structured reference exports.", phase: "New idea · For research" },
  { id: "annotations", title: "Detail annotations", short: "Put your thought in the picture.", promise: "Pin a question or observation to the exact detail that caught your attention.", free: "View and zoom individual works.", paid: "Private annotation layers, detail indexes and annotated teaching views.", phase: "New idea · For close looking" },
  { id: "colours", title: "Colour & composition boards", short: "Collect the colours that stay with you.", promise: "Build a visual reference board around a palette, a texture or a composition.", free: "Explore individual artwork reproductions.", paid: "Reusable visual boards, editable study palettes and design-reference exports.", phase: "New idea · For creatives" },
];

function Presentation() {
  const [slide, setSlide] = useState(0);
  const [captions, setCaptions] = useState(true);
  const [notes, setNotes] = useState(false);
  const work = works[slide];
  function move(amount: number) { setSlide(value => (value + amount + works.length) % works.length); }
  return <>
    <StageHeading title="Ways of seeing water" description="A talk from your personal collection"><Action secondary onClick={() => setNotes(!notes)}>{notes ? "Hide speaker notes" : "Show speaker notes"}</Action></StageHeading>
    <section className="mp-presentation" aria-label="Presentation slide" tabIndex={0} onKeyDown={event => { if (event.key === "ArrowRight" || event.key === "ArrowLeft") { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1); } }}>
      <div className="mp-slide-top"><span>Artline / My collection</span><span>{slide + 1} / {works.length}</span></div><Art work={work} />
      {captions && <div className="mp-slide-caption"><h3>{work.title}</h3><p>{work.artist}, {work.date}</p></div>}
      <div className="mp-slide-controls"><button type="button" aria-label="Previous slide" onClick={() => move(-1)}>←</button><div className="mp-slide-dots">{works.map((item, i) => <button key={item.id} type="button" aria-label={`Slide ${i + 1}: ${item.artist}`} aria-pressed={i === slide} onClick={() => setSlide(i)} />)}</div><button type="button" aria-label="Next slide" onClick={() => move(1)}>→</button></div>
    </section><div className="mp-under-slide"><label><input type="checkbox" checked={captions} onChange={event => setCaptions(event.target.checked)} />Show captions</label><span>Focus the slide and use the arrow keys.</span></div>
    {notes && <div className="mp-speaker-notes"><strong>My speaking prompt</strong><p>Give everyone a moment to look. Which shape did they notice first? Where does the eye move next?</p></div>}
  </>;
}

function Rooms() {
  const [partner, setPartner] = useState(false);
  const [role, setRole] = useState("Can comment");
  const [draft, setDraft] = useState("");
  const [comments, setComments] = useState([{ author: "Sample study partner", text: "The curve of the wave holds the whole scene together. What did you notice first?" }]);
  return <><StageHeading title="The Sunday looking club" description="A sample private study room"><Action secondary onClick={() => setPartner(!partner)}>{partner ? "Remove sample member" : "Add sample member"}</Action></StageHeading><div className="mp-room-layout"><div className="mp-room-art"><Art work={works[0]} /><h3>{works[0].title}</h3><p>{works[0].artist}, {works[0].date}</p><Source work={works[0]} /><div className="mp-room-members"><span className="mp-avatar">You</span><div><strong>You</strong><small>Room owner</small></div>{partner && <><span className="mp-avatar mp-avatar-partner">S</span><label><span>Sample member’s permission</span><select value={role} onChange={event => setRole(event.target.value)}><option>Can view</option><option>Can comment</option><option>Can edit collection</option></select></label></>}</div></div><div className="mp-room-discussion"><h3>A conversation around one work</h3><div className="mp-comments" aria-live="polite">{comments.map((comment, i) => <article key={i}><span>{comment.author}</span><p>{comment.text}</p></article>)}</div><form onSubmit={event => { event.preventDefault(); if (!draft.trim()) return; setComments([...comments, { author: "You", text: draft.trim() }]); setDraft(""); }}><label><span>Your observation</span><textarea aria-label="Study room comment" value={draft} onChange={event => setDraft(event.target.value)} placeholder="What do you see?" required maxLength={1200} /></label><button className="mp-button" type="submit">Add comment to preview</button></form><p className="mp-footnote">Sample participants only. Nothing is sent or shared outside this preview.</p></div></div></>;
}

const themes = ["Water", "Light", "Blue"];
function Discovery() {
  const [theme, setTheme] = useState("Water");
  const [queue, setQueue] = useState<string[]>([]);
  const [why, setWhy] = useState<string | null>(null);
  const shown = theme === "Water" ? works.slice(0, 3) : theme === "Light" ? [works[3], works[2], works[1]] : [works[0], works[3], works[2]];
  return <><StageHeading title="Follow a thread of curiosity" description="A small selection, with a reason for each connection." /><div className="mp-discovery-toolbar"><div className="mp-theme-buttons" role="group" aria-label="Discovery interests">{themes.map(item => <button type="button" key={item} aria-pressed={item === theme} onClick={() => { setTheme(item); setWhy(null); }}>{item}</button>)}</div><span role="status">{queue.length} saved for later</span></div><div className="mp-discovery-grid">{shown.map(work => <article key={work.id}><Art work={work} /><span>{work.artist}, {work.date}</span><h3>{work.title}</h3><div><button type="button" className="mp-reason-button" aria-expanded={why === work.id} onClick={() => setWhy(why === work.id ? null : work.id)}>Why this work?</button><button className="mp-queue-button" type="button" aria-label={`${queue.includes(work.id) ? "Remove" : "Save"} ${work.title}`} aria-pressed={queue.includes(work.id)} onClick={() => setQueue(queue.includes(work.id) ? queue.filter(id => id !== work.id) : [...queue, work.id])}>{queue.includes(work.id) ? "✓" : "+"}</button></div>{why === work.id && <p className="mp-reason">{theme === "Water" ? "Water is part of the scene, matching the theme of your sample collection." : theme === "Light" ? "This selection invites a comparison of sunlight, reflection and the time of day." : "Blue is a visual thread in these reproductions. The connection is a study prompt, not a claim of historical influence."}</p>}</article>)}</div><p className="mp-footnote">Example recommendations from four sample works. A real feed would explain the evidence behind each suggestion.</p></>;
}

const topics = ["Claude Monet", "Russian icons", "Byzantine art", "Japanese prints"];
const exampleUpdates = [
  { topic: "Russian icons", title: "A new source for your reading list", detail: "Example alert when a museum reference is added to a followed topic.", kind: "Source added" },
  { topic: "Claude Monet", title: "A record you saved has been updated", detail: "Example alert with a before-and-after summary of an editorial change.", kind: "Record improved" },
  { topic: "Byzantine art", title: "More context around a work", detail: "Example alert for new, source-backed catalogue context.", kind: "Context added" },
  { topic: "Japanese prints", title: "A reproduction is now available", detail: "Example alert when an eligible image is added to a followed record.", kind: "Image added" },
];
function Watchlist() {
  const [following, setFollowing] = useState(["Russian icons", "Claude Monet"]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [read, setRead] = useState<string[]>([]);
  const shown = exampleUpdates.filter(item => following.includes(item.topic) && (!unreadOnly || !read.includes(item.topic)));
  return <><StageHeading title="The things you follow" description="Relevant changes, collected in one place." /><div className="mp-watch-layout"><div className="mp-follow-topics"><h3>My topics</h3>{topics.map(topic => <label key={topic}><input type="checkbox" checked={following.includes(topic)} onChange={() => setFollowing(following.includes(topic) ? following.filter(item => item !== topic) : [...following, topic])} />{topic}</label>)}<p>Choose what matters to you. A digest would always be optional.</p></div><div><div className="mp-feed-heading"><span>Example update feed</span><label><input type="checkbox" checked={unreadOnly} onChange={event => setUnreadOnly(event.target.checked)} />Unread only</label></div>{shown.map(item => <article className="mp-update" key={item.topic}><span>{item.topic} / {item.kind}</span><h3>{item.title}</h3><p>{item.detail}</p><button type="button" aria-pressed={read.includes(item.topic)} onClick={() => setRead(read.includes(item.topic) ? read.filter(topic => topic !== item.topic) : [...read, item.topic])}>{read.includes(item.topic) ? "Mark unread" : "Mark as read"}</button></article>)}{!shown.length && <div className="mp-empty"><h3>You’re all caught up.</h3><p>Follow another topic or show read updates.</p></div>}</div></div></>;
}

function Offline() {
  const [selection, setSelection] = useState([works[0].id, works[1].id]);
  const [notes, setNotes] = useState(true);
  const [prepared, setPrepared] = useState(false);
  return <><StageHeading title="A small atlas for the journey" description="Prepare a personal study pack before you leave." /><div className="mp-offline-layout"><div>{works.map(work => <label className="mp-pack-row" key={work.id}><input type="checkbox" checked={selection.includes(work.id)} onChange={() => { setSelection(selection.includes(work.id) ? selection.filter(id => id !== work.id) : [...selection, work.id]); setPrepared(false); }} /><Art work={work} /><span><strong>{work.title}</strong><small>{work.artist}</small><small>Image eligible for this sample pack</small></span></label>)}</div><div className="mp-pack-summary"><span className="mp-pack-symbol" aria-hidden="true">▤</span><h3>Water &amp; light</h3><p>A personal travel collection</p><dl><div><dt>Selected works</dt><dd>{selection.length}</dd></div><div><dt>Sources &amp; credits</dt><dd>Included</dd></div><div><dt>Personal notes</dt><dd>{notes ? "Included" : "Not included"}</dd></div></dl><label><input type="checkbox" checked={notes} onChange={event => { setNotes(event.target.checked); setPrepared(false); }} />Include my notes</label><Action disabled={!selection.length} onClick={() => setPrepared(true)}>Preview study pack</Action><p className="mp-pack-status" role="status">{prepared ? `Pack preview ready: ${selection.length} works with their source credits.` : "Select the works you want to take."}</p><small>This mockup previews the pack contents. It does not download or cache an offline pack.</small></div></div></>;
}

function Citations() {
  const [selected, setSelected] = useState([works[0].id, works[1].id]);
  const [format, setFormat] = useState("Reading list");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const entries = works.filter(work => selected.includes(work.id));
  const text = entries.map(work => format === "Reading list" ? `${work.artist}. ${work.title}. ${work.date}. ${work.collection}.\n${work.source}` : `@misc{artline-${work.id},\n  author = {${work.artist}},\n  title = {${work.title}},\n  note = {${work.date}; ${work.collection}},\n  url = {${work.source}}\n}`).join("\n\n");
  async function copy() { try { await navigator.clipboard.writeText(text); setCopied(true); setCopyError(false); } catch { setCopyError(true); } }
  return <><StageHeading title="Sources that travel with your ideas" description="A reference basket for a paper, lesson or personal research." /><div className="mp-citation-layout"><div><h3>Your reference basket</h3>{works.map(work => <label className="mp-citation-choice" key={work.id}><input type="checkbox" checked={selected.includes(work.id)} onChange={() => { setSelected(selected.includes(work.id) ? selected.filter(id => id !== work.id) : [...selected, work.id]); setCopied(false); }} /><span><strong>{work.artist}</strong><small>{work.title}</small></span></label>)}<p className="mp-footnote">Dates retain their recorded uncertainty. Sources remain attached to each work.</p></div><div className="mp-reference-output"><div className="mp-citation-tools"><label><span>Reference format</span><select aria-label="Reference format" value={format} onChange={event => { setFormat(event.target.value); setCopied(false); }}><option>Reading list</option><option>BibTeX</option></select></label><Action disabled={!entries.length} onClick={copy}>{copied ? "Copied" : "Copy references"}</Action></div><textarea aria-label="Generated references" readOnly value={text || "Select a work to begin your reference list."} /><p role="status">{copyError ? "Clipboard unavailable. Select and copy the references above." : `${entries.length} references from documented sample records.`}</p></div></div></>;
}

type Pin = { id: number; x: number; y: number; note: string };
function Annotations() {
  const [pins, setPins] = useState<Pin[]>([{ id: 1, x: 46, y: 34, note: "Follow the arch. How does the curve connect the two sides of the garden?" }, { id: 2, x: 61, y: 72, note: "Look at the reflection: where does solid form become a patch of colour?" }]);
  const [selected, setSelected] = useState(1);
  const [placing, setPlacing] = useState(false);
  const [saved, setSaved] = useState(false);
  const current = pins.find(pin => pin.id === selected);
  const canvas = useRef<HTMLDivElement>(null);
  function addPin(x: number, y: number) { const id = Math.max(0, ...pins.map(pin => pin.id)) + 1; setPins([...pins, { id, x, y, note: "" }]); setSelected(id); setPlacing(false); setSaved(false); }
  return <><StageHeading title="A notebook on the surface" description="Your observations, attached to a detail."><Action onClick={() => setPlacing(!placing)}>{placing ? "Cancel new pin" : "Add a detail pin"}</Action></StageHeading><div className="mp-annotation-layout"><div className="mp-annotated-image" ref={canvas}><Art work={works[1]} />{placing && <button className="mp-pin-placement" type="button" aria-label="Place a detail pin on the image; keyboard places it in the centre" onClick={event => { const box = canvas.current!.getBoundingClientRect(); addPin(event.detail === 0 ? 50 : Math.max(4, Math.min(96, (event.clientX - box.left) / box.width * 100)), event.detail === 0 ? 50 : Math.max(4, Math.min(96, (event.clientY - box.top) / box.height * 100))); }} />}{pins.map(pin => <button className="mp-detail-pin" key={pin.id} type="button" aria-label={`Detail pin ${pin.id}`} aria-pressed={pin.id === selected} style={{ left: `${pin.x}%`, top: `${pin.y}%` }} onClick={() => { setSelected(pin.id); setSaved(false); }}>{pin.id}</button>)}</div><div className="mp-pin-editor"><span className="mp-small">My private annotations</span><h3>{current ? `Looking at detail ${current.id}` : "Choose a detail"}</h3><p>{placing ? "Click a point in the image, or focus the image control and press Enter." : "Select a numbered pin to read or edit its note."}</p>{current && <><label><span>Your interpretation</span><textarea aria-label="Detail observation" value={current.note} onChange={event => { setPins(pins.map(pin => pin.id === selected ? { ...pin, note: event.target.value } : pin)); setSaved(false); }} /></label><div className="mp-actions"><Action onClick={() => setSaved(true)}>Save observation</Action><Action secondary onClick={() => { setPins(pins.filter(pin => pin.id !== selected)); setSelected(pins.find(pin => pin.id !== selected)?.id || 0); }}>Remove pin</Action></div><p className="mp-status" role="status">{saved ? "Observation saved in this preview." : `${pins.length} detail pins in this layer.`}</p></>}<Source work={works[1]} /></div></div></>;
}

const palettes = [
  { name: "Wave blues", work: works[0], colours: ["#193b59", "#526f8a", "#a5bbc4", "#d5d6ca", "#ede4cd"] },
  { name: "Garden greens", work: works[1], colours: ["#425943", "#79896a", "#a9ad82", "#c6b5a0", "#d9d1b5"] },
  { name: "Evening light", work: works[2], colours: ["#65788d", "#9badb7", "#c4c9c7", "#d9d3bb", "#ebe2cb"] },
];
function Colours() {
  const [palette, setPalette] = useState(palettes[0]);
  const [background, setBackground] = useState("#ede4cd");
  const [selectedColour, setSelectedColour] = useState("#193b59");
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const colours = palette.colours;
  const css = colours.map((colour, i) => `--study-colour-${i + 1}: ${colour};`).join("\n");
  async function copy() { try { await navigator.clipboard.writeText(css); setCopied(true); setCopyError(false); } catch { setCopyError(true); } }
  return <><StageHeading title="A palette to think with" description="A visual reference board for your next creative project." /><div className="mp-colour-tabs" role="group" aria-label="Study palettes">{palettes.map(item => <button key={item.name} type="button" aria-pressed={item.name === palette.name} onClick={() => { setPalette(item); setBackground(item.colours[4]); setSelectedColour(item.colours[0]); setCopied(false); }}>{item.name}</button>)}</div><div className="mp-colour-layout"><div className="mp-colour-board" style={{ background }}><Art work={palette.work} /><div className="mp-board-swatches">{colours.map(colour => <span key={colour} style={{ background: colour }} />)}</div></div><div className="mp-palette-editor"><span className="mp-small">My selected colours</span><h3>{palette.name}</h3><p>An approximate study palette from this reproduction. Change the surround to see the image differently.</p><div className="mp-palette-swatches">{colours.map(colour => <button type="button" key={colour} aria-label={`Choose colour ${colour}`} aria-pressed={selectedColour === colour} style={{ background: colour }} onClick={() => { setSelectedColour(colour); setBackground(colour); }} />)}</div><output>{selectedColour}</output><Action secondary onClick={() => setBackground("#eeece5")}>Use a neutral surround</Action><pre>{css}</pre><Action onClick={copy}>{copied ? "Palette copied" : "Copy palette as CSS"}</Action>{copyError && <p role="status">Clipboard unavailable. Copy the colour values shown above.</p>}<Source work={palette.work} /></div></div></>;
}

export const additionalPanels: Record<string, () => ReactNode> = { presentation: Presentation, rooms: Rooms, discovery: Discovery, watchlist: Watchlist, offline: Offline, citations: Citations, annotations: Annotations, colours: Colours };
