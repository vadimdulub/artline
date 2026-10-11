import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
const state = vi.hoisted(() => ({ path: "/books", back: vi.fn(), signedIn: false }));
vi.mock("next/navigation", () => ({ usePathname: () => state.path, useRouter: () => ({ back: state.back }) }));
vi.mock("./MemberSession", () => ({ useMemberSession: () => ({ session: state.signedIn ? { user: { id: "member" } } : null }) }));
vi.mock("@/components/MemberLink", () => ({ default: ({ children, prefetch, ...props }: React.ComponentProps<"a"> & { prefetch?: boolean }) => { void prefetch; return <a {...props}>{children}</a>; } }));
import { ContextualBackLink, ContextualParentLink, PageBackNavigation, backDestination } from "./BackNavigation";
const nativeReplace = window.history.replaceState;
beforeEach(() => { state.path = "/books"; state.back.mockReset(); state.signedIn = false; nativeReplace.call(history, {}, "", "/books"); sessionStorage.clear(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const push = async (url: string) => { await act(async () => history.pushState({ __NA: true }, "", url)); };
it.each([["/artists/monet/works/123", "/artists/monet"], ["/artists/monet", "/artists"], ["/museums/louvre", "/museums"], ["/guides/louvre/ar", "/guides"], ["/studies/123", "/studies"], ["/shared/studies/token", "/"], ["/privacy", "/"]])("provides a direct-entry fallback for %s", (path, expected) => { expect(backDestination(path)).toBe(expected); });
it("uses a named parent on direct entry, ignoring unrelated history", () => { render(<ContextualBackLink />); expect(screen.getByRole("link", { name: "Explore the timeline" })).toHaveAttribute("href", "/"); expect(history.state.artlineReturn).toBeUndefined(); });
it("names the actual prior page and preserves Next state", async () => {
  render(<ContextualBackLink />); await push("/artists"); expect(history.state).toMatchObject({ __NA: true, artlineReturn: { href: "/books", label: "Books" } });
  fireEvent.click(screen.getByRole("link", { name: "Back to Books" })); expect(state.back).toHaveBeenCalledOnce();
});
it("captures the source label before Next renders the destination", async () => {
  state.path = "/guides/louvre"; nativeReplace.call(history, {}, "", state.path);
  const workPath = "/artists/monet/works/123";
  const view = render(<><PageBackNavigation /><main id="main-content" data-return-label="Louvre guide" data-return-path={state.path}><a href={workPath} onClick={e => e.preventDefault()}>Open artwork</a></main></>);
  fireEvent.click(screen.getByRole("link", { name: "Open artwork" })); state.path = "/artists/monet/works/123";
  view.rerender(<><PageBackNavigation /><main id="main-content" data-return-label="artwork" data-return-path={state.path} /></>); await push(state.path);
  expect(screen.getByRole("link", { name: "Back to Louvre guide" })).toHaveAttribute("href", "/guides/louvre");
});
it("retains source filters and anchors in the actual return href", async () => {
  nativeReplace.call(history, {}, "", "/artists?country=fr#results"); render(<ContextualBackLink />); await push("/books");
  expect(screen.getByRole("link", { name: "Back to artists" })).toHaveAttribute("href", "/artists?country=fr#results");
});
it("does not intercept modified clicks", async () => { render(<ContextualBackLink />); await push("/artists"); fireEvent.click(screen.getByRole("link", { name: "Back to Books" }), { ctrlKey: true }); expect(state.back).not.toHaveBeenCalled(); });
it("preserves the return destination across filter replacements", async () => {
  render(<ContextualBackLink />); await push("/artists"); await act(async () => history.replaceState({ __NA: true }, "", "/artists?country=fr"));
  expect(history.state).toMatchObject({ __NA: true, artlineReturn: { href: "/books", label: "Books" } });
});
it("does not mistake an initial filter replacement for navigation", async () => {
  render(<ContextualBackLink />); await act(async () => history.replaceState({ __NA: true }, "", "/books?start=1800")); expect(history.state.artlineReturn).toBeUndefined();
});
it("names a prior filter or overlay state the previous view", async () => { render(<ContextualBackLink />); await push("/books?start=1800"); expect(screen.getByRole("link", { name: "Back to previous view" })).toHaveAttribute("href", "/books"); });
it("reads each entry's return target after back/forward traversal", async () => {
  render(<ContextualBackLink />); await push("/artists");
  await act(async () => { nativeReplace.call(history, { artlineReturn: { href: "/privacy", label: "Privacy" } }, "", "/books"); window.dispatchEvent(new PopStateEvent("popstate")); });
  expect(screen.getByRole("link", { name: "Back to Privacy" })).toHaveAttribute("href", "/privacy");
});
it("never shows Back on the main timeline", async () => { state.path = "/"; render(<><PageBackNavigation /><ContextualBackLink /></>); await push("/?artist=monet"); expect(screen.queryByRole("link")).toBeNull(); expect(screen.queryByRole("navigation")).toBeNull(); });
it("keeps a distinct artist destination beside a guide return", () => {
  nativeReplace.call(history, { artlineReturn: { href: "/guides/louvre", label: "Louvre guide" } }, "", "/artists/monet/works/123");
  render(<><ContextualBackLink /><ContextualParentLink href="/artists/monet" label="Claude Monet" /></>); expect(screen.getByRole("link", { name: "Claude Monet" })).toHaveAttribute("href", "/artists/monet");
});
it.each([null, { href: "/artists/monet?work=123", label: "Claude Monet" }])("does not duplicate the artist destination: %j", previous => { nativeReplace.call(history, { artlineReturn: previous }, "", "/artists/monet/works/123"); render(<ContextualParentLink href="/artists/monet" label="Claude Monet" />); expect(screen.queryByRole("link")).toBeNull(); });
it.each([false, true])("respects member access on return (signed in: %s)", async signedIn => {
  state.signedIn = signedIn; nativeReplace.call(history, {}, "", "/museums/louvre"); render(<ContextualBackLink />); await push("/books");
  fireEvent.click(screen.getByRole("link", { name: "Back to museum" })); expect(state.back).toHaveBeenCalledTimes(signedIn ? 1 : 0);
});
it.each(["https://other.example/", "javascript:alert(1)"])("rejects unsafe return destinations: %s", href => { nativeReplace.call(history, { artlineReturn: { href, label: "Untrusted" } }, "", "/books"); render(<ContextualBackLink />); expect(screen.getByRole("link", { name: "Explore the timeline" })).toHaveAttribute("href", "/"); });
it.each([true, false])("handles plain-anchor document returns (fresh label: %s)", fresh => {
  nativeReplace.call(history, {}, "", "/artists/monet/works/123"); vi.spyOn(document, "referrer", "get").mockReturnValue(window.location.origin + "/guides/louvre");
  sessionStorage.setItem("artline:return-navigation", JSON.stringify({ from: { href: "/guides/louvre", label: "Louvre guide" }, to: "/artists/monet/works/123", at: fresh ? Date.now() : 0 }));
  render(<ContextualBackLink />); expect(screen.getByRole("link", { name: fresh ? "Back to Louvre guide" : "Back to guide" })).toHaveAttribute("href", "/guides/louvre");
});
it("shares and cleans up the history tracker", async () => {
  const original = history.pushState; const view = render(<><PageBackNavigation /><ContextualBackLink /></>); await push("/artists");
  expect(screen.getAllByRole("link", { name: "Back to Books" })).toHaveLength(2); view.unmount(); expect(history.pushState).toBe(original);
});
