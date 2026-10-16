import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { MuseumPageTabs } from "./MuseumPageTabs";

const state = vi.hoisted(() => ({ session: { user: null as { id: string } | null }, refresh: vi.fn(), request: vi.fn() }));
vi.mock("./MemberSession", () => ({ useMemberSession: () => ({ session: state.session }) }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: state.refresh }) }));
vi.mock("@/lib/museum-studio", async original => ({ ...await original<typeof import("@/lib/museum-studio")>(), studioRequest: state.request }));
vi.mock("./MuseumPublicationEditor", () => ({ PublicationEditor: ({ kind, item, close, saved }: { kind: string; item?: { id: string }; close: () => void; saved: (action: string) => void }) => <div role="dialog" aria-label={`Edit ${kind}`}><p>{item?.id ?? "new"}</p><button onClick={close}>Close</button><button onClick={() => saved("publish")}>Publish</button></div> }));
const props = { slug: "national-gallery-london", museumName: "National Gallery", initialSearch: "", hasProfile: false, panels: { collection: <p>Collection content</p>, exhibitions: <p>Exhibition content</p>, guides: <p>Read-only prepared guide</p>, visit: <p>Visit content</p> } };
beforeEach(() => { state.session = { user: null }; state.request.mockReset(); state.refresh.mockReset(); window.history.replaceState(null, "", "/museums/national-gallery-london"); });
afterEach(cleanup);
it("switches tabs by keyboard without losing collection filters and follows history and old hashes", () => {
  window.history.replaceState(null, "", "/museums/national-gallery-london?q=Monet&image_only=1");
  render(<MuseumPageTabs {...props} />);
  fireEvent.keyDown(screen.getByRole("tab", { name: "Collection" }), { key: "ArrowRight" });
  expect(screen.getByRole("tab", { name: "Exhibitions" })).toHaveFocus();
  expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Exhibitions");
  expect(new URLSearchParams(window.location.search).get("q")).toBe("Monet");
  expect(new URLSearchParams(window.location.search).get("image_only")).toBe("1");
  expect(screen.queryByText("Collection content")).not.toBeInTheDocument();
  fireEvent.keyDown(screen.getByRole("tab", { name: "Exhibitions" }), { key: "End" });
  expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Visit & about");
  act(() => { window.history.replaceState(null, "", "/museums/national-gallery-london#guides"); window.dispatchEvent(new PopStateEvent("popstate")); });
  expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Guides");
  expect(screen.getByText("Read-only prepared guide")).toBeVisible();
  fireEvent.keyDown(screen.getByRole("tab", { name: "Guides" }), { key: "Home" });
  expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Collection");
});
it("keeps public reading available while hiding mutation controls from visitors and denied staff", async () => {
  const view = render(<MuseumPageTabs {...props} />);
  expect(state.request).not.toHaveBeenCalled();
  for (const name of ["Collection", "Exhibitions", "Guides", "Visit & about"]) {
    fireEvent.click(screen.getByRole("tab", { name }));
    expect(screen.queryByRole("button", { name: /^(Add|Edit)/ })).not.toBeInTheDocument();
  }
  state.session = { user: { id: "non-staff" } }; state.request.mockRejectedValue(new Error("Museum access required"));
  view.rerender(<MuseumPageTabs {...props} />);
  await waitFor(() => expect(state.request).toHaveBeenCalled());
  expect(screen.queryByRole("button", { name: /^(Add|Edit)/ })).not.toBeInTheDocument();
  expect(screen.getByRole("tabpanel")).toHaveAccessibleName("Visit & about");
});
it("opens matching staff editors and reuses the private museum profile instead of creating a second one", async () => {
  state.session = { user: { id: "curator" } };
  state.request.mockImplementation((path: string) => Promise.resolve(path.includes("content?kind=profile") ? { items: [{ id: "existing-profile-draft" }] } : { name: "National Gallery" }));
  const view = render(<MuseumPageTabs {...props} />);
  for (const [tab, action, kind] of [["Collection", "Add artwork", "artwork"], ["Exhibitions", "Add exhibition", "exhibition"], ["Guides", "Add guide", "guide"]]) {
    fireEvent.click(screen.getByRole("tab", { name: tab }));
    fireEvent.click(await screen.findByRole("button", { name: action }));
    expect(screen.getByRole("dialog")).toHaveAccessibleName(`Edit ${kind}`);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
  }
  fireEvent.click(screen.getByRole("tab", { name: "Visit & about" }));
  fireEvent.click(screen.getByRole("button", { name: "Add details" }));
  expect(await screen.findByText("existing-profile-draft")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Publish" }));
  expect(state.refresh).toHaveBeenCalledOnce();
  expect(screen.getByRole("status")).toHaveTextContent("Published");
  expect(screen.getByRole("button", { name: "Add details" })).toHaveFocus();
  state.session = { user: null }; view.rerender(<MuseumPageTabs {...props} />);
  expect(screen.queryByRole("button", { name: "Add details" })).not.toBeInTheDocument();
});
