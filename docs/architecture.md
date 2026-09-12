# Artline architecture

## Runtime

```text
Browser
  |
  v
Next.js on Cloud Run
  |  same-origin /api/backend proxy
  v
Go API on Cloud Run
  |
  v
Cloud SQL for PostgreSQL
```

The frontend owns presentation, accessible interaction, and Markdown essays.
The API owns structured catalogue queries, validation, authorization, and
database writes. Browser code never connects to PostgreSQL.

## Content decision

Painter essays use Markdown with YAML front matter:

```md
---
title: Hilma af Klint
artist_slug: hilma-af-klint
status: draft
sources:
  - https://example.org/authority-page
---

Essay prose starts here.
```

Markdown is preferable to YAML for long prose because paragraphs, links,
citations, headings, and revisions remain readable. YAML is retained only for
short document metadata. Catalogue facts used for filtering belong in the
database, not duplicated in the essay.

## Media decision

Images are versioned local files under `apps/web/public/assets`. The production
container is immutable and Cloud Run's writable filesystem is ephemeral;
therefore the first release intentionally has no runtime image-upload flow.
A future upload workflow must use persistent object storage rather than writing
inside a running container.

## Authorization

Public reads return only published artists and published representative works.
All catalogue/coverage reads and mutations require an exact Bearer token from
`ARTLINE_EDITOR_TOKEN`. Research preview requires `preview=1` plus that token.
The Next.js development server can attach an explicitly configured local
preview token to GET requests; this behavior is disabled in production.

This is a single-owner token mechanism, not the specification's owner/editor/
reviewer identity and role system. `editor_accounts` is not wired into
authorization. That work remains a production milestone.

Audit triggers retain artist, artwork, and influence before/after JSON. They
do not yet attribute changes to a signed-in editor. Publication revalidates
the artist and dependencies inside a transaction with catalogue table locks.
This favors consistency for the small catalogue; finer-grained locks may be
needed as concurrent editing grows.
