import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { EvidenceNote } from "./EvidenceNote";
import { SourceList } from "./ArtistRecord";

afterEach(cleanup);

it("renders image rights receipts as readable facts and working source links", () => {
  const citations = [{
    field_name: "image_rights_and_identity", source_name: "The Metropolitan Museum of Art",
    source_url: "https://www.metmuseum.org/art/collection/search/465941",
    evidence_note: JSON.stringify({
      artwork_id: "0dc95728-4ab7-52bd-bc33-50be12849826", title: "Devotional Icon", provider: "met",
      source_image_url: "https://images.metmuseum.org/CRDImages/md/original/sf18-88s1.jpg",
      original_path: "/private/source-images/original.source", original_sha256: "internal-checksum",
      rights: { rights_status: "cc0", license_label: "CC0 1.0", license_url: "https://creativecommons.org/publicdomain/zero/1.0/", credit: "The Metropolitan Museum of Art; Gift of Percy Stickney Grant, 1918" },
      checked_at: "2026-09-20T16:00:41.129621+00:00",
      source_capture: { path: "docs/research/private-capture.body", sha256: "capture-checksum" },
      selection: { path: "docs/research/selection.json" },
      transformation: "Full composition; proportional resize, EXIF orientation and JPEG compression; no cropping"
    })
  }];
  const { container } = render(<><SourceList citations={citations} /><EvidenceNote note={citations[0].evidence_note} /></>);
  expect(screen.getByText("Artwork: Devotional Icon")).toBeVisible();
  expect(screen.getByText("Image rights: CC0 1.0")).toBeVisible();
  expect(screen.getByText("Credit: The Metropolitan Museum of Art; Gift of Percy Stickney Grant, 1918")).toBeVisible();
  expect(screen.getByText("Evidence checked: Sep 20, 2026.")).toBeVisible();
  expect(screen.getByRole("link", { name: "The Metropolitan Museum of Art" })).toHaveAttribute("href", "https://www.metmuseum.org/art/collection/search/465941");
  expect(screen.getByRole("link", { name: "License details" })).toHaveAttribute("href", "https://creativecommons.org/publicdomain/zero/1.0/");
  expect(screen.getByRole("link", { name: "Original source image" })).toHaveAttribute("href", "https://images.metmuseum.org/CRDImages/md/original/sf18-88s1.jpg");
  expect(container.textContent).not.toMatch(/original_path|source_capture|sha256|private-capture|internal-checksum|\{\s*"/);
});

it.each(["nested", "flat"])("summarizes %s official object evidence without exposing its full capture", shape => {
  const object = { title: "Devotional Icon", objectDate: "19th century", medium: "Copper alloy, surrey enamel", accessionNumber: "18.88", creditLine: "Gift of Percy Stickney Grant, 1918", GalleryNumber: "999" };
  render(<EvidenceNote note={JSON.stringify({
    source_fields: shape === "nested" ? { object } : object,
    editorial_note: "Creator remains unidentified.",
    notes: ["No current-display claim."]
  })} />);
  expect(screen.getByText("Source date: 19th century")).toBeVisible();
  expect(screen.getByText("Collection number: 18.88")).toBeVisible();
  expect(screen.getByText("No current-display claim.")).toBeVisible();
  expect(screen.getByText("Creator remains unidentified.")).toBeVisible();
  expect(screen.queryByText(/999|GalleryNumber/)).not.toBeInTheDocument();
});

it("supports image identity notes without inventing rights or accepting unsafe links", () => {
  const { container } = render(<EvidenceNote note={JSON.stringify({ identity: "Matched by accession number.", image_url: "https://example.com/icon.jpg", license_url: "javascript:alert(1)", checked_at: "invalid", authorization: "Internal workflow details" })} />);
  expect(screen.getByText("Identity evidence: Matched by accession number.")).toBeVisible();
  expect(screen.getByRole("link", { name: "Original source image" })).toHaveAttribute("href", "https://example.com/icon.jpg");
  expect(screen.queryByRole("link", { name: "License details" })).not.toBeInTheDocument();
  expect(container.textContent).not.toMatch(/Image rights|Evidence checked|Internal workflow/);
});

it.each([
  '{"unexpected":{"path":"/private/secret"}}',
  '[{"path":"/private/secret"}]',
  '{"rights":',
  JSON.stringify('{"unexpected":"/private/secret"}')
])("does not fall back to displaying unrecognized or malformed JSON: %s", note => {
  const { container } = render(<EvidenceNote note={note} />);
  expect(screen.getByText("See the linked source for supporting information.")).toBeVisible();
  expect(container.textContent).not.toMatch(/private|unexpected|rights|\{|\}/);
});

it("reads double-encoded receipts", () => {
  render(<EvidenceNote note={JSON.stringify(JSON.stringify({ rights: { license_label: "CC BY 4.0" } }))} />);
  expect(screen.getByText("Image rights: CC BY 4.0")).toBeVisible();
});

it.each(["The museum records an approximate date.", "[Uncertain] Attribution under review.", "1918"])("preserves ordinary research notes: %s", note => {
  render(<EvidenceNote note={note} />);
  expect(screen.getByText(note)).toBeVisible();
});
