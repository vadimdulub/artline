"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function EditorNav() {
  const pathname = usePathname();
  return <nav className="admin-subnav" aria-label="Catalogue tools">{[["/catalogue", "Painters"], ["/coverage", "Coverage"], ["/imports", "Imports"]].map(([href, label]) => <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>{label}{href === "/imports" && <small>Planned</small>}</Link>)}</nav>;
}
