import { MuseumsIndex } from "@/components/MuseumsIndex";
import { researchPreviewEnabled } from "@/lib/server-api";
export const metadata = { title: "Museums and collections · Artline" };
export default function MuseumsPage() { return <MuseumsIndex preview={researchPreviewEnabled()} />; }
