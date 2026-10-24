import { describe, expect, it } from "vitest";
import { mapIdentityColors, mapIdentityPalette } from "./map-colors";
import type { MapItem } from "./map";
describe("map identity colors", () => {
 it("keeps assignments stable across response order and gives fifty compared identities different colors", () => {
  const items: MapItem[] = Array.from({ length:50 },(_,index)=>({ id:String(index),kind:"artist",title:`Artist ${index}` }));
  const colors=mapIdentityColors(items);
  expect(new Set(Object.values(colors).map(color=>color.hex)).size).toBe(50);
  expect(mapIdentityColors([...items].reverse())).toEqual(colors);
 });
 it("uses a supplied owner identity for related works without inventing creator links", () => {
  const colors=mapIdentityColors([{ id:"creator",kind:"artist",title:"Artist" },{ id:"work",kind:"artwork",title:"Work",colorKey:"artist:creator" }]);
  expect(Object.keys(colors)).toEqual(["artist:creator"]);
 });
 it("preserves the reviewed minimum ink and fill contrast for all fifty label colors", () => {
  const luminance=(hex:string)=>hex.slice(1).match(/../g)!.map(c=>parseInt(c,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
  for(const color of mapIdentityPalette) expect((luminance(color.fill)+.05)/(luminance(color.hex)+.05)).toBeGreaterThanOrEqual(4.5);
 });
});
