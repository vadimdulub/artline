import { act, cleanup, fireEvent, render as renderUI, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CatalogueMap } from "./CatalogueMap";
import { apiRequest } from "@/lib/api";
import type { MapRecord, PlaceGroup } from "@/lib/map";
vi.mock("next/dynamic", () => ({ default: () => ({ selected, groups, onSelect, onCluster, previewRecord, focusRequest, onEventSelect, highlightRegions }: { selected: string; groups: PlaceGroup[]; onSelect: (key: string) => void; previewRecord: string; onCluster: (keys: string[]) => void; focusRequest?: { keys: string[]; revision: number }; onEventSelect?: (key: string, record?: string) => void; highlightRegions?: boolean }) => <div aria-label="Mock map" data-preview={previewRecord} data-selected={selected} data-places={groups.length} data-records={[...new Set(groups.flatMap(group => group.entries.map(entry => `${entry.item.kind}:${entry.item.id}`)))].join("|")} data-regions={String(highlightRegions)} data-focus-keys={focusRequest?.keys.join("|")} data-focus-revision={focusRequest?.revision}><button onClick={() => onSelect(groups[0]?.key)}>Open map image</button><button onClick={() => onCluster(groups.map(group => group.key))}>Open nearby connections</button><button onClick={() => onEventSelect?.(groups[0]?.key)}>Open event region</button></div> }));
vi.mock("@/lib/api", () => ({ apiRequest: vi.fn(), errorMessage: (cause: Error) => cause.message }));
const request = vi.mocked(apiRequest);
const connection = { key: "writing", place: "Geneva", relation: "begun near", precision: "area", lat: 46.2, lon: 6.2, start: 1816, end: 1816, note: "Beginning only", sourceLabel: "Author", sourceUrl: "https://example.org/source" };
const publication = { ...connection, key: "publication", place: "London", lat: 51.5, lon: -0.1, relation: "first published in", start: 1818, end: 1818 };
const item = { id: "wd-q150827", kind: "book" as const, title: "Frankenstein" };
const props = { items: [item], total: 20, loading: false, onRetry: vi.fn(), range: { start: 1800, end: 1900 }, onOpen: vi.fn() };
const render = async (ui: ReactElement) => {
 const view = renderUI(ui); fireEvent.click(screen.getByRole("button", { name: "Layers" }));
 await waitFor(() => expect(view.container.querySelector(".map-record-picker summary") ?? view.container.querySelector(".map-panel-intro")).toBeTruthy());
 const summary = view.container.querySelector<HTMLElement>(".map-record-picker summary");
 if (summary) { fireEvent.click(summary); await waitFor(() => expect(screen.getByRole("searchbox")).toHaveFocus()); }
 return view;
};
const details = () => screen.getByRole("complementary", { name: "Map details" });
const recordButton = () => {
 const picker = document.querySelector<HTMLDetailsElement>('[data-layer="book"] details');
 if (picker && !picker.open) fireEvent.click(picker.querySelector("summary")!);
 if (!screen.queryByRole("button", { name: /^Frankenstein/ })) { const search = screen.getByRole("searchbox", { name: "Search books" }); fireEvent.change(search, { target: { value: "Frankenstein" } }); }
 const button = screen.getByRole("button", { name: /^Frankenstein/ }); act(() => button.focus()); return button;
};
beforeEach(() => { vi.clearAllMocks(); window.history.replaceState(null, "", "/"); window.matchMedia = vi.fn().mockReturnValue({ matches: false }); });
afterEach(cleanup);
describe("native map workspace", () => {
 it("groups a country's painter milestones under one name with lifespan and recorded dates", async () => {
  const painters = [
   { id: "repin", kind: "artist" as const, title: "Ilya Repin", years: "1844–1930" },
   { id: "kandinsky", kind: "artist" as const, title: "Wassily Kandinsky", years: "1866–1944" },
   { id: "malevich", kind: "artist" as const, title: "Kazimir Malevich", years: "1879–1935" },
  ];
  const affiliation = { ...connection, key: "affiliation", place: "Russia", precision: "country", relation: "cultural_affiliation", start: null, end: null };
  const birth = { ...affiliation, key: "birth", relation: "birth", start: 1866, end: 1866, dateDisplay: "1866" };
  request.mockResolvedValue({ records: painters.map(painter => ({ id: painter.id, connections: painter.id === "kandinsky" ? [affiliation, birth] : [affiliation], truncated: false })) });
  renderUI(<CatalogueMap {...props} items={painters} total={3} />);
  await screen.findByText("3 of 3 loaded records located · 3 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open map image" }));
  expect(within(details()).getByRole("status")).toHaveTextContent("3 records");
  expect(within(details()).getAllByText("Wassily Kandinsky")).toHaveLength(1);
  const painter = within(details()).getByRole("region", { name: "Wassily Kandinsky" });
  expect(within(painter).getByText("1866–1944")).toBeInTheDocument();
  const milestones = within(painter).getAllByRole("listitem");
  expect(milestones).toHaveLength(2);
  expect(milestones[0]).toHaveAttribute("data-dated", "true");
  expect(milestones[0]).toHaveTextContent("Born in Russia1866");
  expect(milestones[1]).toHaveAttribute("data-dated", "false");
  expect(milestones[1]).toHaveTextContent("Cultural affiliation: RussiaDate not recorded");
  fireEvent.click(within(painter).getByRole("button", { name: /Kandinsky, Russia, Born in, 1866/ }));
  expect(within(details()).getByRole("button", { name: "Back to location" })).toBeInTheDocument();
  expect(within(details()).getByRole("heading", { name: "Wassily Kandinsky" })).toBeInTheDocument();
 });
 it("keeps a phone location list and record drill-down in the information panel", async () => {
  window.matchMedia = vi.fn().mockReturnValue({ matches: true });
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, publication], truncated: false }] });
  renderUI(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open nearby connections" }));
  expect(screen.queryByRole("complementary", { name: "Map layers" })).not.toBeInTheDocument();
  expect(within(details()).getByRole("status")).toHaveTextContent("1 record");
  fireEvent.click(within(details()).getByRole("button", { name: "Expand information" }));
  fireEvent.click(within(details()).getByRole("button", { name: /Frankenstein, London/ }));
  expect(document.querySelector(".map-workspace")).toHaveAttribute("data-expanded", "true");
  expect(within(details()).getByRole("heading", { name: "London" })).toHaveFocus();
  fireEvent.click(within(details()).getByRole("button", { name: "Back to location" }));
  expect(within(details()).getByRole("heading", { name: "2 nearby places" })).toHaveFocus();
  expect(document.querySelector(".map-layer-panel .map-place-choices")).not.toBeInTheDocument();
 });
 it("restores location connections on the right from a saved URL", async () => {
  window.history.replaceState(null, "", "/?map_panel=places&map_place=46.2%2C6.2%2Clocal&map_places=46.2%2C6.2%2Clocal&map_places=51.5%2C-0.1%2Clocal");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, publication], truncated: false }] });
  renderUI(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(within(details()).getByRole("region", { name: "Place connections" })).toHaveTextContent("London");
  expect(screen.queryByRole("complementary", { name: "Map layers" })).not.toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: /Frankenstein, London/ }));
  expect(new URLSearchParams(location.search).getAll("map_places")).toHaveLength(2);
  expect(within(details()).getByRole("button", { name: "Back to location" })).toBeInTheDocument();
 });
 it("prioritises mapped records and retains explicitly searched unlocated evidence", async () => {
  const unknown = { ...item, id: "unknown", title: "An unknown place" };
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }, { id: unknown.id, connections: [], truncated: false }] });
  await render(<CatalogueMap {...props} items={[item, unknown]} />);
  await screen.findByText("1 of 2 loaded records located · 20 matching records");
  expect(screen.queryByRole("button", { name: /^An unknown place/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("checkbox", { name: "Show books" }));
  expect(document.querySelector(".map-record-picker details")).toHaveAttribute("open");
  fireEvent.click(screen.getByRole("checkbox", { name: "Show books" }));
  expect(document.querySelector(".map-record-picker details")).toHaveAttribute("open");
  fireEvent.change(screen.getByRole("searchbox", { name: "Search books" }), { target: { value: "unknown" } });
  expect(screen.getByRole("button", { name: /^An unknown place/ })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Back to layers" }));
  await waitFor(() => expect(document.querySelector(".map-record-picker summary")).toHaveFocus());
  expect(screen.queryByRole("button", { name: "Done" })).not.toBeInTheDocument();
  expect(request).toHaveBeenCalledTimes(1);
 });
 it("starts with a single icon control, without a left panel or bulk/link actions", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  const view = renderUI(<CatalogueMap {...props} />);
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(screen.queryByRole("complementary", { name: "Map layers" })).not.toBeInTheDocument();
  const toggle = screen.getByRole("button", { name: "Layers" });
  expect(toggle).toHaveTextContent(""); expect(toggle.querySelector("svg")).toBeTruthy();
  expect(view.container.querySelectorAll(".map-workspace-toolbar button")).toHaveLength(1);
  fireEvent.click(toggle);
  expect(screen.getByRole("complementary", { name: "Map layers" })).toBeVisible();
  expect(screen.queryByRole("button", { name: /Show all|Show none|Copy map link/ })).not.toBeInTheDocument();
 });
 it("opens connected records on the right after an image click, keeping the left for layers", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  renderUI(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open map image" }));
  expect(screen.queryByRole("complementary", { name: "Map layers" })).not.toBeInTheDocument();
  expect(within(details()).getByRole("region", { name: "Place connections" })).toHaveTextContent("Frankenstein");
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Layers" }));
  expect(within(details()).getByRole("region", { name: "Place connections" })).toBeInTheDocument();
  expect(screen.getByRole("checkbox", { name: "Show books" })).toBeChecked();
 });
 it("uses the existing small outline icon for each layer", async () => {
  const painter = { id: "painter", kind: "artist" as const, title: "Painter" };
  const artwork = { id: "work", kind: "artwork" as const, title: "Work" }, event = { id: "event", kind: "event" as const, title: "Event" };
  request.mockResolvedValue({ records: [] });
  const view = await render(<CatalogueMap {...props} items={[painter, artwork, item, event]} />);
  await screen.findByText("0 of 4 loaded records located · 20 matching records");
  expect(view.container.querySelectorAll(".map-layer-kind-icon svg[aria-hidden=true]")).toHaveLength(4);
 });
 it("retains painter-picker focus while an inspected record refreshes", async () => {
  const mapRecord = { id: item.id, connections: [connection], truncated: false };
  request.mockResolvedValue({ records: [mapRecord] });
  const picker = <div className="map-painter-picker"><input aria-label="Search painters" /></div>;
  const view = await render(<CatalogueMap {...props} layerPicker={picker} />);
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton());
  const input = screen.getByRole("textbox", { name: "Search painters" });
  act(() => input.focus());
  view.rerender(<CatalogueMap {...props} layerPicker={picker} range={{ start: 1801, end: 1900 }} />);
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument());
  expect(input).toHaveFocus();
 });
 it("keeps a layer disabled when another page loads new record identities", async () => {
  const nextBook = { ...item, id: "another-book", title: "Another book" };
  request.mockResolvedValueOnce({ records: [{ id: item.id, connections: [connection], truncated: false }] }).mockResolvedValueOnce({ records: [{ id: nextBook.id, connections: [publication], truncated: false }] });
  const view = await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("checkbox", { name: "Show books" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "0");
  view.rerender(<CatalogueMap {...props} items={[nextBook]} />);
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "0");
  expect(screen.getByRole("checkbox", { name: "Show books" })).not.toBeChecked();
  fireEvent.click(screen.getByRole("checkbox", { name: "Show books" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "1"); expect(request).toHaveBeenCalledTimes(2);
 });
 it("loads all recorded painter life places despite old place filters and the artwork date window", async () => {
  window.history.replaceState(null, "", "/?map_relation=death&map_detail=country");
  const painter = { id: "painter-id", kind: "artist" as const, title: "Painter", years: "1800–1950" };
  request.mockResolvedValue({ records: [{ id: painter.id, truncated: false, connections: [{ ...connection, key: "birth", relation: "born in", start: 1800, end: 1800 }, { ...publication, key: "death", relation: "died in", start: 1950, end: 1950 }] }] });
  await render(<CatalogueMap {...props} items={[painter]} range={{ start: 1880, end: 1890 }} />);
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(request.mock.calls[0][0]).toContain("start=-12000&end=2100"); expect(request.mock.calls[0][0]).not.toContain("relation=");
  fireEvent.click(screen.getByRole("button", { name: /^Painter/ }));
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Next connection" }));
  expect(details().querySelector(".map-journey-current .map-journey-date")).toHaveTextContent("1950");
  expect(screen.queryByText("Place types")).not.toBeInTheDocument();
 });
 it("opens an event from its country, and switches its layer off without hiding a colocated painter", async () => {
  const painter = { id: "monet", kind: "artist" as const, title: "Claude Monet" };
  const event = { id: "revolution", kind: "event" as const, title: "French Revolution", years: "1789–1799" };
  const france = { ...connection, place: "France", countryCode: "FR", precision: "country", start: null, end: null };
  request.mockImplementation(async path => ({ records: [{ id: String(path).includes("kind=artist") ? painter.id : event.id, connections: [france], truncated: false }] }));
  await render(<CatalogueMap {...props} items={[painter, event]} />); await screen.findByText("2 of 2 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open event region" }));
  expect(within(details()).getByRole("region", { name: "Place connections" })).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: /^French Revolution, France/ }));
  fireEvent.click(within(details()).getByRole("checkbox", { name: "Colour event countries" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-regions", "false");
  fireEvent.click(within(details()).getByRole("checkbox", { name: "Show events layer" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-records", "artist:monet");
  expect(within(details()).getByRole("heading", { name: "French Revolution" })).toBeInTheDocument();
  expect(within(details()).queryByRole("button", { name: "Find on map: France" })).not.toBeInTheDocument();
  expect(screen.getByRole("checkbox", { name: "Show painters" })).toBeChecked();
  fireEvent.click(within(details()).getByRole("checkbox", { name: "Show events layer" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-records", "artist:monet|event:revolution");
  expect(within(details()).getByRole("checkbox", { name: "Colour event countries" })).not.toBeChecked();
  expect(request).toHaveBeenCalledTimes(2);
 });
 it("keeps a country event chooser limited to events when painters share the country", async () => {
  const painter = { id: "monet", kind: "artist" as const, title: "Claude Monet" };
  const revolution = { id: "revolution", kind: "event" as const, title: "French Revolution" }, other = { id: "other-event", kind: "event" as const, title: "Another event" };
  const france = { ...connection, place: "France", countryCode: "FR", precision: "country" };
  request.mockImplementation(async path => ({ records: (String(path).includes("kind=artist") ? [painter] : [revolution, other]).map(record => ({ id: record.id, connections: [france], truncated: false })) }));
  await render(<CatalogueMap {...props} items={[painter, revolution, other]} />); await screen.findByText("3 of 3 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open event region" }));
  const choices = screen.getByRole("region", { name: "Place connections" });
  expect(within(choices).queryByText("Claude Monet")).not.toBeInTheDocument();
  expect(within(choices).getByRole("button", { name: /^French Revolution/ })).toBeInTheDocument();
  expect(within(choices).getByRole("button", { name: /^Another event/ })).toBeInTheDocument();
 });
 it("keeps coverage and sourced details without duplicating the record selector on the right", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />);
  expect(await screen.findByText("1 of 1 loaded records located · 20 matching records")).toBeInTheDocument();
  expect(screen.queryByRole("complementary", { name: "Map details" })).not.toBeInTheDocument();
  expect(screen.queryByText("Map options")).not.toBeInTheDocument();
  expect(screen.queryByText(/Without a map location/)).not.toBeInTheDocument();
  fireEvent.click(recordButton());
  expect(screen.queryByRole("button", { name: "Previous connection" })).not.toBeInTheDocument();
  expect(document.querySelector(".map-journey-history")).not.toBeInTheDocument();
  expect(within(details()).queryByRole("button", { name: /Records/ })).not.toBeInTheDocument();
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: "View book" }));
  expect(props.onOpen).toHaveBeenCalledWith(item); expect(request.mock.calls[0][0]).toContain("start=1800&end=1900");
 });
 it("searches all connection places and opens the matching chapter", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, publication], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.change(screen.getByRole("searchbox", { name: "Search books" }), { target: { value: "London" } });
  fireEvent.click(recordButton());
  expect(new URLSearchParams(location.search).get("map_place")).toBe("51.5,-0.1,local");
  expect(within(details()).getByRole("heading", { name: "London" })).toHaveFocus();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "2");
 });
 it("clears an empty map search without changing visibility, selection or evidence", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton());
  const search = screen.getByRole("searchbox", { name: "Search books" });
  const selected = location.search;
  fireEvent.change(search, { target: { value: "No matching city" } });
  expect(screen.getByText(/No records or places match/)).toHaveAttribute("role", "status");
  fireEvent.click(screen.getByRole("button", { name: "Clear search books" }));
  expect(search).toHaveValue(""); expect(search).toHaveFocus();
  expect(recordButton()).toBeVisible(); expect(location.search).toBe(selected);
  expect(await screen.findByRole("checkbox", { name: "Show Frankenstein" })).toBeChecked();
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
  expect(request).toHaveBeenCalledTimes(1);
 });
 it("changes visibility without refetching evidence or hiding the inspected detail", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton());
  fireEvent.click(screen.getByRole("checkbox", { name: "Show Frankenstein" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "0");
  expect(within(details()).getByRole("heading", { name: "Frankenstein" })).toBeInTheDocument();
  fireEvent.click(recordButton()); expect(within(details()).getByText("Hidden on map")).toBeInTheDocument();
  expect(screen.getByRole("checkbox", { name: "Show Frankenstein" })).not.toBeChecked();
  fireEvent.click(within(details()).getByRole("button", { name: "Show on map" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "1");
  expect(request).toHaveBeenCalledTimes(1);
 });
 it("opens nearby connections in the right panel and drills into one member", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection,publication], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton());
  fireEvent.click(screen.getByRole("button", { name: "Open nearby connections" }));
  const choices = within(details()).getByRole("region", { name: "Place connections" });
  expect(within(details()).getByRole("heading", { name: "2 nearby places" })).toBeInTheDocument();
  fireEvent.click(within(choices as HTMLElement).getByRole("button", { name: /London/ }));
  expect(within(details()).getByRole("heading", { name: "London" })).toHaveFocus();
  expect(document.querySelector(".map-place-choices")).not.toBeInTheDocument();
 });
 it("groups right-panel choices by record and preserves selection through zoom and Back", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, publication], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton()); const before = location.search;
  fireEvent.click(screen.getByRole("button", { name: "Open nearby connections" }));
  expect(screen.getByRole("heading", { name: "2 nearby places" })).toHaveFocus();
  expect(screen.getByRole("region", { name: "Place connections" })).toContainElement(screen.getByRole("region", { name: "Frankenstein" }));
  expect(within(details()).getAllByText("Frankenstein")).toHaveLength(1);
  expect(document.querySelector(".map-layer-panel .map-place-choices")).not.toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Layers" })).toBeInTheDocument();
  const selectedLocation = location.search;
  fireEvent.click(screen.getByRole("button", { name: "Zoom to these places" }));
  expect(screen.getByLabelText("Mock map").getAttribute("data-focus-keys")?.split("|")).toHaveLength(2);
  expect(location.search).toBe(selectedLocation); expect(location.search).not.toBe(before); expect(request).toHaveBeenCalledTimes(1);
  fireEvent.click(within(details()).getByRole("button", { name: /Frankenstein, London/ }));
  expect(within(details()).getByRole("heading", { name: "London" })).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: "Back to location" }));
  expect(within(details()).getByRole("heading", { name: "2 nearby places" })).toHaveFocus();
  expect(within(details()).getByRole("region", { name: "Place connections" })).toHaveTextContent("Geneva");
  expect(document.querySelector(".map-layer-panel .map-place-choices")).not.toBeInTheDocument();
 });
 it("can locate the same selected place repeatedly without altering visibility or the URL", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton()); const before = location.search;
  fireEvent.click(screen.getByRole("button", { name: "Find on map: Geneva" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-focus-keys", "46.2,6.2,local");
  fireEvent.click(screen.getByRole("button", { name: "Find on map: Geneva" }));
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-focus-revision", "2");
  expect(location.search).toBe(before); expect(request).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("checkbox", { name: "Show Frankenstein" }));
  expect(screen.queryByRole("button", { name: "Find on map: Geneva" })).not.toBeInTheDocument();
 });
 it("does not offer a zoom action for distinct evidence at an identical reference point", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection, { ...publication, place: "Switzerland", lat: connection.lat, lon: connection.lon, precision: "country" }], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(screen.getByRole("button", { name: "Open nearby connections" }));
  expect(screen.getByRole("heading", { name: "2 nearby places" })).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Zoom to these places" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Frankenstein, Switzerland/ })).toBeInTheDocument();
 });
 it("keeps illustrated index records readable when their thumbnail fails", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} items={[{ ...item, image: "/missing.jpg" }]} />);
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.error(document.querySelector(".map-index-image img")!);
  expect(recordButton()).toHaveTextContent("Frankenstein");
  fireEvent.click(recordButton());
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
 });
 it("preserves focus in external date controls while map evidence refreshes", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  const view = await render(<><input type="range" aria-label="Date control" /><CatalogueMap {...props} /></>);
  await screen.findByText("1 of 1 loaded records located · 20 matching records");
  fireEvent.click(recordButton());
  const handle = screen.getByRole("slider", { name: "Date control" }); handle.focus();
  view.rerender(<><input type="range" aria-label="Date control" /><CatalogueMap {...props} range={{ start: 1801, end: 1900 }} /></>);
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument());
  expect(handle).toHaveFocus();
 });
 it("keeps unsupported locations available in the left selection and full native record", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [{ ...connection, place: "Historical state", lat: null, lon: null, precision: "unlocated" }], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("0 of 1 loaded records located · 20 matching records");
  expect(screen.queryByText(/Without a map location/)).not.toBeInTheDocument();
  fireEvent.click(recordButton());
  expect(within(details()).getByText("Location unresolved · no map marker")).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: "View book" })); expect(props.onOpen).toHaveBeenCalledWith(item);
 });
 it("keeps image failure separate from record availability", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} items={[{ ...item, image: "/missing.jpg" }]} />);
  await screen.findByText("1 of 1 loaded records located · 20 matching records"); fireEvent.click(recordButton());
  fireEvent.error(await screen.findByRole("img", { name: "Frankenstein" }));
  expect(screen.getByText("Image unavailable")).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: "View book" })); expect(props.onOpen).toHaveBeenCalled();
 });
 it("reports failed requests rather than inventing zero coverage", async () => {
  request.mockRejectedValue(new Error("Disconnected")); await render(<CatalogueMap {...props} />);
  const alert = await screen.findByRole("alert"); expect(alert).toHaveTextContent("Places couldn’t load"); expect(alert).not.toHaveTextContent("Disconnected"); expect(screen.queryByText(/0 of 1/)).not.toBeInTheDocument();
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  fireEvent.click(within(alert).getByRole("button", { name: "Try again" }));
  expect(await screen.findByText("1 of 1 loaded records located · 20 matching records")).toBeInTheDocument(); expect(props.onRetry).toHaveBeenCalledOnce();
 });
 it("ignores stale evidence after the years change", async () => {
  let resolveOld!: (value: { records: MapRecord[] }) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValueOnce({ records: [{ id: item.id, connections: [], truncated: false }] });
  const { rerender } = await render(<CatalogueMap {...props} />); await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
  rerender(<CatalogueMap {...props} range={{ start: 1901, end: 2000 }} />);
  expect(await screen.findByText("0 of 1 loaded records located · 20 matching records")).toBeInTheDocument();
  await act(async () => resolveOld({ records: [{ id: item.id, connections: [connection], truncated: false }] }));
  expect(screen.queryByRole("heading", { name: "Geneva" })).not.toBeInTheDocument();
 });
 it("retains relationship filters and an explicitly empty selection", async () => {
  request.mockResolvedValue({ records: [] });
  const artist = { id: "artist-id", kind: "artist" as const, title: "Painter" };
  const { rerender } = await render(<CatalogueMap {...props} items={[artist]} relations={["birth"]} />);
  await waitFor(() => expect(request).toHaveBeenCalledTimes(1)); expect(request.mock.calls[0][0]).toContain("relation=birth");
  rerender(<CatalogueMap {...props} items={[]} relations={[]} />);
  expect(await screen.findByText("No records match these filters.")).toBeInTheDocument(); expect(request).toHaveBeenCalledTimes(1);
 });
 it("follows chronological chapters including unresolved places without isolating the whole map", async () => {
  const unresolved = { ...connection, key: "unknown", place: "Historical country", lat: null, lon: null, start: null, end: null };
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection,publication,unresolved], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records"); fireEvent.click(recordButton());
  expect(screen.getByRole("button", { name: "Previous connection" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Next connection" }));
  expect(screen.getByRole("heading", { name: "London" })).toHaveFocus(); expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "2");
  expect(new URLSearchParams(location.search).get("map_stop")).toBe("publication");
  fireEvent.click(screen.getByRole("button", { name: "Next connection" }));
  expect(screen.getByText("Location unresolved · no map marker")).toBeInTheDocument(); expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "");
  expect(screen.getByRole("button", { name: "Next connection" })).toBeDisabled(); expect(request).toHaveBeenCalledTimes(1);
 });
 it("restores shared chapters and explicitly reports a chapter leaving the year selection", async () => {
  window.history.replaceState(null, "", "/?map_panel=records&map_record=book:wd-q150827&map_stop=publication&map_place=46.2,6.2,local");
  request.mockResolvedValueOnce({ records: [{ id: item.id, connections: [connection,publication], truncated: false }] }).mockResolvedValueOnce({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  const { rerender } = await render(<CatalogueMap {...props} />);
  expect(await screen.findByRole("heading", { name: "London" })).toBeInTheDocument(); expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "51.5,-0.1,local");
  rerender(<CatalogueMap {...props} range={{ start: 1816, end: 1816 }} />);
  expect(await screen.findByText(/That connection is outside this selection/)).toBeInTheDocument(); expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-selected", "");
  fireEvent.click(within(details()).getByRole("button", { name: /Geneva, 1816, Begun near/ }));
  expect(within(details()).getByRole("heading", { name: "Geneva" })).toBeInTheDocument();
 });
 it("distinguishes a stale page link from an empty catalogue", async () => {
  window.history.replaceState(null, "", "/?map_panel=records&map_record=book:another-page&map_stop=writing");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] }); await render(<CatalogueMap {...props} />);
  expect(await screen.findByText(/This record is not on the current page/)).toBeInTheDocument(); expect(recordButton()).toBeInTheDocument();
 });
 it("keeps an omitted evidence row inspectable without inventing a place", async () => {
  request.mockResolvedValue({ records: [] }); await render(<CatalogueMap {...props} />);
  await screen.findByText("0 of 1 loaded records located · 20 matching records"); fireEvent.click(recordButton());
  expect(within(details()).getByRole("heading", { name: "Frankenstein" })).toBeInTheDocument();
  expect(within(details()).getByText(/No documented places/)).toBeInTheDocument();
  fireEvent.click(within(details()).getByRole("button", { name: "View book" })); expect(props.onOpen).toHaveBeenCalledWith(item);
 });
 it("does not retain an invisible place filter from an old shared URL", async () => {
  window.history.replaceState(null, "", "/?map_detail=country&map_panel=missing");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(screen.queryByText("Countries only")).not.toBeInTheDocument();
  expect(screen.queryByText(/Without a map location/)).not.toBeInTheDocument();
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "1");
  expect(recordButton()).toBeVisible(); expect(request).toHaveBeenCalledOnce();
 });
 it("ignores an invalid location precision in a shared URL", async () => {
  window.history.replaceState(null, "", "/?map_detail=invalid");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-places", "1"); expect(screen.queryByText("Cities and areas only")).not.toBeInTheDocument();
 });
 it("opens a real first connection when a shared record has no chapter", async () => {
  window.history.replaceState(null, "", "/?map_record=book:wd-q150827");
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />);
  expect(await screen.findByRole("heading", { name: "Geneva" })).toBeInTheDocument();
  expect(document.querySelector(".map-journey-history")).not.toBeInTheDocument();
 });

 it("previews a focused record without selecting or hiding it or requesting more evidence", async () => {
  request.mockResolvedValue({ records: [{ id: item.id, connections: [connection], truncated: false }] });
  await render(<CatalogueMap {...props} />); await screen.findByText("1 of 1 loaded records located · 20 matching records");
  const name = recordButton(), url = location.search;
  fireEvent.mouseEnter(name.closest(".map-selection-row")!);
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-preview", "book:wd-q150827");
  fireEvent.mouseLeave(name.closest(".map-selection-row")!);
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-preview", "");
  fireEvent.focus(name);
  expect(screen.getByLabelText("Mock map")).toHaveAttribute("data-preview", "book:wd-q150827");
  expect(location.search).toBe(url); expect(request).toHaveBeenCalledOnce();
  expect(screen.queryByRole("complementary", { name: "Map details" })).not.toBeInTheDocument();
 });

});
