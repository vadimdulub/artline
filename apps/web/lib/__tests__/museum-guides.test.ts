import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { guidePortalLinks, guideLanguages, guideWorkPath, guideSubject, guideLocation, type MuseumGuide } from "../museum-guide-types";
import { getGuideIndex, getMuseumGuide, guidePDFPath } from "../museum-guides";
import { atlasLayers, readEntityFilters } from "../atlas-filters";
const roots=["museum-guides", "artist-guides"].map(folder=>path.join(process.cwd(),"content/articles",folder));
const folders=roots.flatMap(root=>fs.readdirSync(root,{withFileTypes:true}).filter(entry=>entry.isDirectory()).map(entry=>({root,slug:entry.name})));
describe("museum guide publication invariants",()=>{
 it("artist and museum editions resolve from separate folders without slug collisions",()=>{
  const index=getGuideIndex();expect(new Set(index.map(g=>g.slug)).size).toBe(index.length);
  for(const entry of index){
   const guide=getMuseumGuide(entry.slug);expect(guide?.kind).toBe(entry.kind);
   expect(guidePDFPath(entry.slug,"ru")).toContain(`/content/articles/${entry.kind==="artist"?"artist-guides":"museum-guides"}/${entry.slug}/ru.pdf`);
   if(entry.kind==="artist"){
    expect(guide?.artist?.slug).toBeTruthy();expect(guideSubject(guide!)).toBe(entry.artist?.name);expect(guideLocation(guide!)).toBe(entry.artist?.lifeDates);
    expect(guide?.works.every(w=>w.artists.some(a=>a.slug===guide.artist?.slug))).toBe(true);
   }
  }
  for(const [slug,locale] of [["../artist-guides/mary-cassatt","en"],["mary-cassatt","../../en"],["mary-cassatt","xx"],["unknown-guide","en"]]){
   expect(getMuseumGuide(slug,locale)).toBeNull();expect(guidePDFPath(slug,locale)).toBeNull();
  }
 });
 it("guide-only creator matches keep working artwork links and painter filters",()=>{
  const work={id:"work-id",artists:[{slug:"rembrandt",name:"Rembrandt",role:"primary"}],catalogueArtistSlug:null};
  const url=new URL(guideWorkPath(work),"https://artlines.org");
  expect(url.pathname).toBe("/all");expect(url.searchParams.get("artwork_id")).toBe(work.id);expect(url.searchParams.get("item")).toBe(work.id);
  expect(new URL(guidePortalLinks({works:[work] as MuseumGuide["works"],context:{start:1620,end:1650}}).painters,"https://artlines.org").searchParams.getAll("painter")).toEqual(["rembrandt"]);
  expect(guideWorkPath({...work,catalogueArtistSlug:undefined})).toBe("/artists/rembrandt/works/work-id");
  expect(guideWorkPath({...work,catalogueArtistSlug:"catalogue-artist"})).toBe("/artists/catalogue-artist/works/work-id");
 });
 for(const {root,slug} of folders){
  const en: MuseumGuide=JSON.parse(fs.readFileSync(path.join(root,slug,"en.json"),"utf8"));
  it(`${slug}: exact artwork selection survives every portal view`,()=>{
   const links=guidePortalLinks(en),all=new URL(links.all,"https://artlines.org").searchParams;
   expect(atlasLayers(all)).toEqual(["artwork","book","event"]);
   expect(readEntityFilters("artwork",all).getAll("id")).toEqual(en.works.map(work=>work.id));
   expect(readEntityFilters("book",all).has("id")).toBe(false);
   expect(readEntityFilters("event",all).has("id")).toBe(false);
   expect(all.has("creator")).toBe(false);
   expect(all.get("highlights")).toBe("false");
   const painters=new URL(links.painters,"https://artlines.org").searchParams;
   expect(painters.getAll("painter")).toEqual([...new Set([...en.works.flatMap(work=>work.artists.map(artist=>artist.slug)), ...(en.comparisonArtists || []).map(artist=>artist.slug)])]);
   for(const key of ["all","events","books"] as const){const q=new URL(links[key],"https://artlines.org").searchParams;expect(Number(q.get("start"))).toBe(en.context.start);expect(Number(q.get("end"))).toBe(en.context.end);}
  });
  it(`${slug}: editions preserve object identity, evidence and complete prose`,()=>{
   expect(en.works.length).toBeGreaterThanOrEqual(20);expect(en.works.length).toBeLessThanOrEqual(100);
   expect(new Set(en.works.map(w=>w.id)).size).toBe(en.works.length);
   expect(en.books.length).toBeGreaterThan(0);
   for(const locale of Object.keys(guideLanguages)){
    const g: MuseumGuide=JSON.parse(fs.readFileSync(path.join(root,slug,locale+".json"),"utf8"));
    expect(g.locale).toBe(locale);expect(g.works.length).toBe(en.works.length);expect(g.context).toEqual(en.context);expect(g.kind).toBe(en.kind);expect(g.comparisonArtists).toEqual(en.comparisonArtists);
    expect(Object.keys(g.labels)).toEqual(Object.keys(en.labels));
    expect(g.books.map(b=>b.url)).toEqual(en.books.map(b=>b.url));
    for(const [i,w] of g.works.entries()){
     for(const key of ["id","source","image","imageSource","credit","license","licenseUrl","start","end","artists","catalogueTitle"] as const)expect(w[key]).toEqual(en.works[i][key]);
     for(const value of [w.title,w.description,w.source,w.image,w.credit])expect(value.length).toBeGreaterThan(0);
     expect(w.end===null||w.end<=1970).toBe(true);
    }
    if(locale!=="en")expect(g.introduction).not.toBe(en.introduction);
    expect(g.closingSections?.length).toBeGreaterThan(0);
   }
  });
 }
});
