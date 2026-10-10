import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
vi.mock("./MemberSession", () => ({ useMemberSession: vi.fn() }));
import { useMemberSession } from "./MemberSession";
import { MemberAccount } from "./MemberAccount";

afterEach(cleanup);
it("explains the sign-in destination and carries the destination into Google login", () => {
  vi.mocked(useMemberSession).mockReturnValue({ session: { enabled: true, user: null }, failed: false });
  const returnTo = "/artists/monet?art_year=1900&catalogue=all";
  render(<MemberAccount signInError returnTo={returnTo} />);
  expect(screen.getByRole("heading", { name: "Sign in to Artline." })).toBeVisible();
  expect(screen.getByRole("alert")).toHaveTextContent("Please try again");
  const form = screen.getByRole("button", { name: "Sign in with Google" }).closest("form")!;
  expect(form).toHaveAttribute("method", "post");
  expect(new URL(form.action).searchParams.get("return_to")).toBe(returnTo);
});

it("keeps the existing account page when no painter was selected", () => {
  vi.mocked(useMemberSession).mockReturnValue({ session: { enabled: true, user: null }, failed: false });
  render(<MemberAccount signInError={false} />);
  expect(screen.getByRole("heading", { name: "A place for your curiosity." })).toBeVisible();
  expect(screen.getByRole("button", { name: "Sign in with Google" }).closest("form")).toHaveAttribute("action", "/api/auth/google/start");
});
