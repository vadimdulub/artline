import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ArtistBiography } from "./ArtistBiography";
import type { ArtistDetail } from "../lib/types";
afterEach(cleanup);
const source = { text: "The artist's first paragraph.\nA second paragraph about their work.\nA third paragraph about their career.", attribution: "Wikipedia contributors", source_url: "https://en.wikipedia.org/wiki/Rembrandt", license_url: "https://creativecommons.org/licenses/by-sa/4.0/", revision_url: "https://en.wikipedia.org/w/index.php?oldid=123" };
const artist = { id: "artist", biography_md: null, reference_biography: source } as ArtistDetail;
it("shows all source paragraphs on the full page and keeps the painter preview compact", () => {
  const { container, unmount } = render(<ArtistBiography artist={artist} embedded={false} />);
  expect(container.querySelectorAll(".biography-copy > p")).toHaveLength(3);
  expect(screen.getByRole("link", { name: "Wikipedia contributors" })).toHaveAttribute("href", source.source_url);
  unmount();
  const preview = render(<ArtistBiography artist={artist} embedded />);
  expect(preview.container.querySelectorAll(".biography-copy > p")).toHaveLength(1);
  fireEvent.click(screen.getByRole("button", { name: "Read full biography" }));
  expect(preview.container.querySelectorAll(".biography-copy > p")).toHaveLength(3);
});
it("retains editorial emphasis, links, headings and lists when formatting long prose", () => {
  const sentence = "The artist developed a distinctive approach to drawing and painted many portraits of people in the surrounding towns. ";
  const editorial = `## Early life\n\n**The artist** studied with [a teacher](https://example.org). ${sentence.repeat(9)}\n\n- *Paintings*\n- Drawings`;
  const { container } = render(<ArtistBiography artist={{ ...artist, reference_biography: undefined, biography_md: editorial }} embedded={false} />);
  expect(screen.getByRole("heading", { name: "Early life" })).toBeVisible();
  expect(screen.getByRole("link", { name: "a teacher" })).toHaveAttribute("href", "https://example.org");
  expect(container.querySelector("strong")).toHaveTextContent("The artist");
  expect(container.querySelector("em")).toHaveTextContent("Paintings");
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
  expect(container.querySelectorAll(".biography-copy > p").length).toBeGreaterThan(1);
  expect(container.querySelector(".biography-copy")!.textContent!.replace(/\s+/g, " ")).toContain(sentence.trim());
});
it("omits absent biographies instead of displaying a research notice", () => {
  const { container } = render(<ArtistBiography artist={{ ...artist, reference_biography: undefined }} embedded={false} />);
  expect(container).toBeEmptyDOMElement();
});
