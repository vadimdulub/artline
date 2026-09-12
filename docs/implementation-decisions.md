# Implementation decisions and deviations

| Date | Decision | Reason | Consequence |
| --- | --- | --- | --- |
| 2026-09-07 | Use Next.js and Go instead of Vinext/Workers | Explicit project direction | Cloud Run hosts two containers |
| 2026-09-07 | Use PostgreSQL instead of D1 | Explicit project direction and local PostgreSQL availability | SQL and migrations target PostgreSQL |
| 2026-09-07 | Use repository-local assets instead of R2 | Explicit project direction | Assets are immutable per deployment; uploads are deferred |
| 2026-09-07 | Use Markdown plus YAML front matter for painter essays | Long prose is easier to author and review in Markdown | Database remains canonical for structured facts |
| 2026-09-07 | Create only a production Terraform environment | Explicit project direction | Local development is configured outside Terraform |
| 2026-09-07 | Missing prototype seed cannot be exported | No prototype or `SAMPLE_PAINTERS` exists in the provided directories | Starter records remain visibly `review`, never falsely published |
| 2026-09-08 | Follow the supplied screenshot's dark header, paper background, and split painter/artwork layout | User provided the prototype visual baseline after the first build | Replaces the earlier cool palette; data provenance remains visible |
| 2026-09-08 | Separate public published reads from authenticated research preview | Specification §§3, 9, 15 forbid public draft exposure | Local preview remains populated; production is empty until records are reviewed and published |
| 2026-09-08 | Add a new five-work Giotto research selection | Exercise the artwork UI with sourced metadata | Not a recovery of the missing 140-work prototype; all five remain in review |
| 2026-09-08 | Keep a short DB biography and optional longer Markdown essay | Publication validation needs a single canonical short biography | Markdown edits do not silently replace validated DB content |
| 2026-09-08 | Use bounded offset pagination for the first catalogue editor | Fix previously inaccessible records after the first 200 | Cursor pagination and saved grid views remain specification gaps |
| 2026-09-08 | Keep the single-owner token during this review | Existing infrastructure has no identity provider configured | Multi-user roles and attributed audit remain incomplete, explicitly tracked in the audit |
