import { TimelineGuide, timelineGuideMetadata } from "@/components/TimelineGuide";
import { getTimelineGuide } from "@/lib/timeline-guide";

export function generateMetadata() {
  return timelineGuideMetadata(getTimelineGuide("en")!);
}

export default function ArtHistoryTimelinePage() {
  return <TimelineGuide guide={getTimelineGuide("en")!} />;
}
