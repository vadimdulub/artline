import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
const state = vi.hoisted(() => ({ path: "/books", query: "", back: vi.fn() }));
vi.mock("next/navigation", () => ({ usePathname: () => state.path, useSearchParams: () => new URLSearchParams(state.query), useRouter: () => ({ back: state.back }) }));
vi.mock("@/components/MemberLink", () => ({ default: ({ children, prefetch, ...props }: React.ComponentProps<"a"> & { prefetch?: boolean }) => { void prefetch; return <a {...props}>{children}</a>; } }));
import { BackNavigation, PageBackNavigation, backDestination } from "./BackNavigation";
beforeEach(() => { state.path = "/books"; state.query = ""; state.back.mockReset(); window.history.replaceState({}, "", "/books"); });
afterEach(cleanup);
it.each([["/artists/monet/works/123", "/artists/monet"], ["/artists/monet", "/artists"], ["/museums/louvre", "/museums"], ["/guides/louvre/ar", "/guides"], ["/studies/123", "/studies"], ["/shared/studies/token", "/"], ["/privacy", "/"]])("provides a direct-entry fallback for %s", (path, expected) => { expect(backDestination(path)).toBe(expected); });
it("does not use unrelated browser history on direct entry", async () => {
  render(<BackNavigation />);
  expect(screen.getByRole("link", { name: "Explore the timeline" })).toHaveAttribute("href", "/");
  expect(window.history.state.artlineCanGoBack).toBeUndefined();
});
it("uses internal history and preserves Next state", async () => {
  const view = render(<BackNavigation />);
  await act(async () => window.history.pushState({ __NA: true }, "", "/artists?country=fr"));
  state.path = "/artists"; state.query = "country=fr"; view.rerender(<BackNavigation />);
  expect(window.history.state).toEqual({ __NA: true, artlineCanGoBack: true });
  fireEvent.click(screen.getByRole("link", { name: "Back" })); expect(state.back).toHaveBeenCalledOnce();
});
it("retains the destination entry's marker on back traversal", async () => {
  const view = render(<BackNavigation />); state.path = "/artists";
  window.history.replaceState({}, "", "/artists"); window.dispatchEvent(new PopStateEvent("popstate")); view.rerender(<BackNavigation />);
  expect(window.history.state.artlineCanGoBack).toBeUndefined();
});
it("leaves modified clicks to the browser", async () => {
  render(<BackNavigation />); await act(async () => window.history.replaceState({ artlineCanGoBack: true }, ""));
  fireEvent.click(screen.getByRole("link", { name: "Back" }), { ctrlKey: true }); expect(state.back).not.toHaveBeenCalled();
});
it("does not mistake a replaced filter URL for a new history entry", async () => {
  const view = render(<BackNavigation />);
  window.history.replaceState({ __NA: true }, "", "/books?start=1800");
  state.query = "start=1800"; view.rerender(<BackNavigation />);
  expect(window.history.state).toEqual({ __NA: true });
});
it("marks a pushed filter on the same page", async () => {
  render(<BackNavigation />);
  await act(async () => window.history.pushState({ __NA: true }, "", "/books?start=1800"));
  expect(window.history.state.artlineCanGoBack).toBe(true);
});

it("preserves internal return history across Next filter replacements", async () => {
  render(<BackNavigation />);
  await act(async () => window.history.pushState({ __NA: true }, "", "/books?start=1800"));
  await act(async () => window.history.replaceState({ __NA: true }, "", "/books?start=1850"));
  expect(window.history.state).toEqual({ __NA: true, artlineCanGoBack: true });
});

it("hides both controls on an initial homepage visit", async () => {
  state.path = "/"; render(<><BackNavigation /><PageBackNavigation /></>);
  expect(screen.queryByRole("link")).toBeNull();
});
it("offers Back on the homepage after internal navigation", async () => {
  state.path = "/"; render(<PageBackNavigation />);
  await act(async () => window.history.pushState({ __NA: true }, "", "/?artist=monet"));
  expect(screen.getByRole("link", { name: "Back" })).toBeInTheDocument();
});
it("distinguishes artwork history from its predictable artist destination", async () => {
  state.path = "/artists/monet/works/123"; render(<PageBackNavigation />);
  expect(screen.getByRole("link", { name: "Artist" })).toHaveAttribute("href", "/artists/monet");
  await act(async () => window.history.pushState({ __NA: true }, "", state.path));
  expect(screen.getByRole("link", { name: "Back" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Artist" })).toHaveAttribute("href", "/artists/monet");
});
it.each(["/artists/monet", "/museums/louvre", "/guides/louvre/en", "/studies/123"])("keeps existing parent navigation for %s", async path => {
  state.path = path; render(<PageBackNavigation />);
  expect(screen.queryByRole("navigation")).toBeNull();
  await act(async () => window.history.pushState({ __NA: true }, "", path));
  expect(screen.getByRole("navigation", { name: "Return navigation" })).toBeInTheDocument();
  expect(screen.getAllByRole("link")).toHaveLength(1);
});
it("shares one history tracker between desktop and mobile controls", async () => {
  const original = window.history.pushState;
  const view = render(<><BackNavigation /><PageBackNavigation /></>);
  await act(async () => window.history.pushState({ __NA: true }, "", "/books?start=1800"));
  expect(screen.getAllByRole("link", { name: "Back" })).toHaveLength(2);
  view.unmount(); expect(window.history.pushState).toBe(original);
});
