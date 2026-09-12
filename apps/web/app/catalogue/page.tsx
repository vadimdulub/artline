import type { Metadata } from "next";
import { CatalogueClient } from "@/components/CatalogueClient";

export const metadata: Metadata = { title: "Catalogue" };

export default function CataloguePage() {
  return <CatalogueClient />;
}

