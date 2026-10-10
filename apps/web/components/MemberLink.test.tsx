import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
vi.mock("./MemberSession", () => ({ useMemberSession: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
import { useMemberSession } from "./MemberSession";
import MemberLink, { MemberAccessProvider } from "./MemberLink";
const push = vi.fn();
beforeEach(() => {
  push.mockReset();
  vi.mocked(useMemberSession).mockReturnValue({ session: { enabled: true, user: null }, failed: false });
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
});
afterEach(cleanup);

it.each(["/museums", "/museums/the-met?artist=monet"])("opens sign-in and preserves destination %s", destination => {
  render(<MemberAccessProvider><MemberLink href={destination}>Open record</MemberLink></MemberAccessProvider>);
  const link = screen.getByRole("link", { name: "Open record" });
  link.focus(); fireEvent.click(link);
  const dialog = screen.getByRole("dialog", { name: "Sign in to Artline" });
  expect(dialog).toBeVisible();
  expect(new URL(screen.getByRole("button", { name: "Sign in with Google" }).closest("form")!.action).searchParams.get("return_to")).toBe(destination);
  fireEvent.click(screen.getByRole("button", { name: "Close sign-in window" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(link).toHaveFocus();
});
it("dismisses on Escape without navigation", () => {
  render(<MemberAccessProvider><MemberLink href="/museums">Museums</MemberLink></MemberAccessProvider>);
  fireEvent.click(screen.getByRole("link"));
  fireEvent(screen.getByRole("dialog"), new Event("cancel", { cancelable: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(push).not.toHaveBeenCalled();
});
it("continues once a pending session check establishes membership", () => {
  vi.mocked(useMemberSession).mockReturnValue({ session: null, failed: false });
  const children = <MemberLink href="/museums/the-met">Museum</MemberLink>;
  const view = render(<MemberAccessProvider>{children}</MemberAccessProvider>);
  fireEvent.click(screen.getByRole("link"));
  expect(screen.getByRole("status")).toHaveTextContent("Loading");
  vi.mocked(useMemberSession).mockReturnValue({ session: { enabled: true, user: { id: "member", name: "Reader", email: "reader@example.org" } }, failed: false });
  view.rerender(<MemberAccessProvider>{children}</MemberAccessProvider>);
  expect(push).toHaveBeenCalledWith("/museums/the-met");
  expect(screen.queryByRole("dialog")).toBeNull();
});
it("fails closed and explains a session outage", () => {
  vi.mocked(useMemberSession).mockReturnValue({ session: null, failed: true });
  render(<MemberAccessProvider><MemberLink href="/museums">Museums</MemberLink></MemberAccessProvider>);
  fireEvent.click(screen.getByRole("link"));
  expect(screen.getByRole("alert")).toHaveTextContent("temporarily unavailable");
  expect(screen.queryByRole("button", { name: "Sign in with Google" })).toBeNull();
});
