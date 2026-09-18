import type { ReactNode } from "react";

export function AtlasPageHeader({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <header className="atlas-page-heading"><div><h1>{title}</h1><p>{description}</p></div>{children && <div className="atlas-page-aside">{children}</div>}</header>;
}
