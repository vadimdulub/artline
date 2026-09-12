import type { Metadata } from "next";
import { CatalogueClient } from "@/components/CatalogueClient";
import { researchPreviewEnabled } from "@/lib/server-api";

export const metadata: Metadata = { title: "Catalogue" };

export default function CataloguePage() {
  return <CatalogueClient preview={researchPreviewEnabled()} />;
}
