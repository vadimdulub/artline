"use client";
import { useEffect, useRef } from "react";
import type { TimelineBin } from "@/lib/types";
export function DensityCanvas({ bins, start, end }: { bins: TimelineBin[]; start: number; end: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    function draw() {
      if (!canvas) return;
      const ratio = window.devicePixelRatio || 1;
      const width = canvas.clientWidth, height = canvas.clientHeight;
      canvas.width = width * ratio; canvas.height = height * ratio;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.scale(ratio, ratio);
      const totals = new Map<number, number>(), offsets = new Map<number, number>();
      bins.forEach(bin => totals.set(bin.start_year, (totals.get(bin.start_year) ?? 0) + bin.count));
      const maximum = Math.max(1, ...totals.values());
      bins.forEach(bin => {
        const x = (bin.start_year - start) / Math.max(1, end - start) * width;
        const w = Math.max(2, (bin.end_year - bin.start_year + 1) / Math.max(1, end - start) * width - 2);
        const h = bin.count / maximum * (height - 75);
        const y = offsets.get(bin.start_year) ?? 0;
        context.fillStyle = bin.color;
        context.fillRect(x, height - 20 - y - h, w, Math.max(1, h));
        offsets.set(bin.start_year, y + h);
      });
    }
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [bins, start, end]);
  return <canvas className="density-canvas" ref={canvasRef} aria-hidden="true" />;
}
