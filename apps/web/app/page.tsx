import { TimelineExplorer } from "@/components/TimelineExplorer";
import { researchPreviewEnabled } from "@/lib/server-api";
export default function HomePage() {
  return <main id="main-content"><TimelineExplorer preview={researchPreviewEnabled()} /></main>;
}
