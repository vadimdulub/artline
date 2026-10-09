import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ArtworkFacts } from "./ArtworkFacts";
import type { Artwork } from "@/lib/types";
afterEach(cleanup);
it("omits unknown rows while preserving attribution, holding and rights", () => {
 const work = { date_precision: "unknown", work_type: "unknown", medium_text: null, dimensions_text: "Not recorded", creation_place_display: null, attribution_role: "attributed_to", holding: { slug: "museum", name: "Museum" }, license_label: "Public domain Egypt", license_url: "https://example.org/license" } as Artwork;
 render(<ArtworkFacts work={work} attribution />);
 for (const label of ["Dating", "Medium", "Dimensions", "Made in", "Collection no."]) expect(screen.queryByText(label)).not.toBeInTheDocument();
 expect(screen.getByText("Attributed to the artist")).toBeVisible();
 expect(screen.getByRole("link", { name: "Museum" })).toHaveAttribute("href", "/museums/museum");
 expect(screen.getByText("Public domain Egypt")).toBeVisible();
 expect(screen.getByRole("link", { name: "License details" })).toHaveAttribute("href", "https://example.org/license");
});
