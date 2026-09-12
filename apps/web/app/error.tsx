"use client";
export default function ErrorPage({ reset }: { reset: () => void }) { return <main id="main-content" className="admin-page prose-page"><h1>The catalogue is unavailable</h1><p>Please try again in a moment.</p><button className="primary-button" onClick={reset}>Try again</button></main>; }
