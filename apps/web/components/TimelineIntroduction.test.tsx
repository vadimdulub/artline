import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { TimelineIntroduction } from "./TimelineIntroduction";
import { timelineIntroductionCopy } from "@/lib/timeline-introduction";
import type { GuideLocale } from "@/lib/museum-guide-types";

beforeEach(() => localStorage.clear());
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("explains the first visit, remembers dismissal, and lets the visitor reopen it", () => {
  const { container, unmount } = render(<TimelineIntroduction kind="artworks" />);
  expect(container.querySelector("details")).toHaveAttribute("open");
  expect(screen.getByText(timelineIntroductionCopy.en.artworks)).toBeVisible();
  expect(screen.getByText(timelineIntroductionCopy.en.contextNote)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Got it" }));
  expect(container.querySelector("details")).not.toHaveAttribute("open");
  expect(container.querySelector("summary")).toHaveFocus();
  expect(localStorage.getItem("artline:timeline-introduction:v1:artworks")).toBe("1");
  unmount();
  const next = render(<TimelineIntroduction kind="artworks" />);
  expect(next.container.querySelector("details")).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("How this view works"));
  expect(next.container.querySelector("details")).toHaveAttribute("open");
  fireEvent.click(screen.getByText("Your guide in context"));
  expect(next.container.querySelector("details")).not.toHaveAttribute("open");
});

it("remembers artwork and lifespan explanations independently", () => {
  localStorage.setItem("artline:timeline-introduction:v1:artworks", "1");
  const { container } = render(<TimelineIntroduction kind="lifespans" fromGuide />);
  expect(container.querySelector("details")).toHaveAttribute("open");
  expect(screen.getByText(/This view starts with the artists linked from your guide/)).toBeVisible();
  expect(screen.getByText(timelineIntroductionCopy.en.overlapNote)).toBeVisible();
});

it("does not claim a guide selection on a normal lifespan visit", () => {
  render(<TimelineIntroduction kind="lifespans" />);
  expect(screen.queryByText(/This view starts with/)).toBeNull();
  expect(screen.getByText(timelineIntroductionCopy.en.lifespans)).toBeVisible();
});

it("still dismisses and reopens when browser storage is blocked", () => {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("Blocked"); });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Blocked"); });
  const { container } = render(<TimelineIntroduction kind="artworks" />);
  fireEvent.click(screen.getByRole("button", { name: "Got it" }));
  expect(container.querySelector("details")).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("How this view works"));
  expect(container.querySelector("details")).toHaveAttribute("open");
});

it.each(Object.keys(timelineIntroductionCopy) as GuideLocale[])("uses the guide’s %s language and direction", locale => {
  const { container } = render(<TimelineIntroduction kind="artworks" locale={locale} />);
  expect(container.querySelector("aside")).toHaveAttribute("lang", locale);
  expect(container.querySelector("aside")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
  expect(screen.getByText(timelineIntroductionCopy[locale].artworks)).toBeVisible();
  expect(screen.getByRole("button", { name: timelineIntroductionCopy[locale].dismiss })).toBeVisible();
});
