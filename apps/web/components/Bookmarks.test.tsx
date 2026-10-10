import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("./MemberSession", () => ({ useMemberSession: vi.fn() }));
vi.mock("./MemberLink", () => ({ useRequestSignIn: () => signIn }));
import { useMemberSession } from "./MemberSession";
import { BookmarkProvider, BookmarkButton } from "./Bookmarks";
const signIn = vi.fn(), upstream = vi.fn();
const id = "11111111-1111-4111-8111-111111111111";
beforeEach(() => { signIn.mockReset(); upstream.mockReset(); vi.stubGlobal("fetch", upstream); sessionStorage.clear(); vi.mocked(useMemberSession).mockReturnValue({ failed: false, session: { enabled: true, user: null } }); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
it("opens login only when the signed-out visitor clicks the star, then cancels pending intent on dismissal", () => {
  render(<BookmarkProvider><BookmarkButton kind="artist" id={id} title="Monet" /></BookmarkProvider>);
  expect(signIn).not.toHaveBeenCalled(); expect(upstream).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Save Monet to bookmarks" }));
  expect(signIn).toHaveBeenCalledWith("/", expect.any(HTMLElement), expect.objectContaining({ bookmark: true }));
  expect(JSON.parse(sessionStorage.getItem("artline:pending-bookmark")!).ref).toEqual({ kind: "artist", id });
  signIn.mock.calls[0][2].onDismiss();
  expect(sessionStorage.getItem("artline:pending-bookmark")).toBeNull();
});
it("completes the selected save after login, including React Strict Mode remounts", async () => {
  sessionStorage.setItem("artline:pending-bookmark", JSON.stringify({ ref: { kind: "artist", id }, at: Date.now() }));
  vi.mocked(useMemberSession).mockReturnValue({ failed: false, session: { enabled: true, user: { id: "member", name: "Reader", email: "reader@example.org" } } });
  upstream.mockImplementation((_path: string, options: RequestInit) => Promise.resolve(Response.json(options.method === "PUT" ? { saved: true } : { saved: [{ kind: "artist", id }] })));
  render(<StrictMode><BookmarkProvider><BookmarkButton kind="artist" id={id} title="Monet" /></BookmarkProvider></StrictMode>);
  await waitFor(() => expect(screen.getByRole("button", { name: "Remove Monet from bookmarks" })).toHaveAttribute("aria-pressed", "true"));
  await waitFor(() => expect(sessionStorage.getItem("artline:pending-bookmark")).toBeNull());
  expect(upstream.mock.calls.some(([, options]) => options.method === "PUT")).toBe(true);
});
it("does not replay an expired pending bookmark", async () => {
  sessionStorage.setItem("artline:pending-bookmark", JSON.stringify({ ref: { kind: "artist", id }, at: Date.now() - 1000000 }));
  vi.mocked(useMemberSession).mockReturnValue({ failed: false, session: { enabled: true, user: { id: "member", name: "Reader", email: "reader@example.org" } } });
  upstream.mockResolvedValue(Response.json({ saved: [] }));
  render(<BookmarkProvider><BookmarkButton kind="artist" id={id} title="Monet" /></BookmarkProvider>);
  await waitFor(() => expect(screen.getByRole("button")).not.toBeDisabled());
  expect(upstream.mock.calls.every(([, options]) => options.method !== "PUT")).toBe(true);
});
