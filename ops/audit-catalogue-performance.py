#!/usr/bin/env python3
"""Sequential, read-only HTTP samples; no cache flushing or load generation."""

import argparse
import datetime
import json
import pathlib
import statistics
import subprocess
import tempfile
import time
import urllib.parse


ROUTES = {
    "timeline": "/timeline?start=1100&end=2000&popular=true&women=false",
    "timeline_rembrandt": "/timeline?painter=rembrandt",
    "artworks": "/artworks?limit=24",
    "artwork_search": "/artworks?q=Madonna&limit=24",
    "artist_directory": "/artists?limit=24",
    "painter_options": "/painters/options?q=Rembrandt",
    "artist_detail": "/artists/rembrandt",
    "artist_works": "/artists/rembrandt/works?limit=24",
    "museum_directory": "/museums?limit=24",
    "met_detail": "/museums/the-met",
    "met_works": "/museums/the-met/works?limit=24",
    "nga_detail": "/museums/national-gallery-of-art",
    "louvre_detail": "/museums/musee-du-louvre",
    "louvre_works": "/museums/musee-du-louvre/works?limit=24",
    "books": "/books?limit=24",
    "events": "/events?limit=24",
    "atlas_artwork": "/atlas?type=artwork&artwork_popular=false&limit=24",
    "atlas_search": "/atlas?type=artwork&artwork_q=Rossetti&artwork_popular=false&limit=24",
    "seo_directory": "/seo/artists",
    "sitemap_index": "/seo/sitemaps",
    "sitemap_artworks": "/seo/sitemaps/artworks/000",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="API prefix, e.g. https://host/api/v1")
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--samples", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--route", action="append", choices=ROUTES)
    args = parser.parse_args()
    url = urllib.parse.urlsplit(args.base)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.query or url.fragment:
        parser.error("base must be an HTTP origin and path without credentials, query or fragment")
    report = {
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "base": args.base,
        "method": "sequential GETs, fresh curl connection per request, no cache invalidation; first sample is not necessarily cold",
        "routes": {},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name in args.route or ROUTES:
        records = []
        with tempfile.TemporaryDirectory(prefix="artline-http-audit-") as temporary:
            headers = pathlib.Path(temporary) / "headers"
            body = pathlib.Path(temporary) / "body"
            for attempt in range(args.samples):
                headers.unlink(missing_ok=True)
                body.unlink(missing_ok=True)
                result = subprocess.run([
                    "curl", "--silent", "--show-error", "--compressed", "--max-time", "35",
                    "--user-agent", "Artline-performance-audit/20261009",
                    "--dump-header", str(headers), "--output", str(body),
                    "--write-out", "%{json}", args.base.rstrip("/") + ROUTES[name],
                ], capture_output=True, text=True)
                metrics = json.loads(result.stdout) if result.stdout else {}
                response_headers = {}
                if headers.exists():
                    for line in headers.read_text().splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            response_headers[key.lower()] = value.strip()
                record = {
                    "sample": attempt + 1,
                    "status": metrics.get("http_code"),
                    "ttfb_ms": round(metrics.get("time_starttransfer", 0) * 1000, 1),
                    "total_ms": round(metrics.get("time_total", 0) * 1000, 1),
                    "connect_ms": round(metrics.get("time_appconnect", 0) * 1000, 1),
                    "wire_bytes": metrics.get("size_download"),
                    "decoded_bytes": body.stat().st_size if body.exists() else 0,
                    "cache": response_headers.get("x-artline-cache", "unmarked"),
                    "encoding": response_headers.get("content-encoding"),
                    "cache_control": response_headers.get("cache-control"),
                }
                if result.returncode:
                    record["curl_error"] = result.stderr.strip()
                records.append(record)
                print(json.dumps({"route": name, **record}), flush=True)
                report["routes"][name] = {
                    "path": ROUTES[name], "samples": records,
                    "median_total_ms": statistics.median(item["total_ms"] for item in records),
                }
                overloaded = result.returncode or record["status"] == 429 or (record["status"] or 0) >= 500
                if overloaded:
                    report["stopped"] = "Transport or service capacity error; investigate before further sampling"
                args.output.write_text(json.dumps(report, indent=2) + "\n")
                if overloaded:
                    return
                time.sleep(0.25)
        report["routes"][name] = {
            "path": ROUTES[name], "samples": records,
            "median_total_ms": statistics.median(item["total_ms"] for item in records),
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
