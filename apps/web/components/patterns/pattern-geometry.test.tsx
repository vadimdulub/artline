import { describe, expect, it } from "vitest";
import { spTile, spMedallion, spScene } from "./pattern-geometry";
const area = (points: number[][]) => Math.abs(points.reduce((sum, p, i) => {const q=points[(i+1)%points.length];return sum+p[0]*q[1]-q[0]*p[1];},0))/2;
describe("pattern surface coverage", () => {
 for(const id of ["starcross","rosette8","octagons","hexstar","lozenges","rosette12"]) it(`${id} covers its lattice cell`,()=>{
  const unit=200, faces=spTile(id,unit), expected=unit*unit*(["hexstar","lozenges","rosette12"].includes(id)?Math.sqrt(3)/2:1);
  expect(faces.reduce((sum,f)=>sum+area(f.points),0)).toBeCloseTo(expected,7);
  expect(faces.every(f=>area(f.points)>0 && f.points.flat().every(Number.isFinite))).toBe(true);
 });
 for(const [id,n] of [["medallion5",5],["medallion10",10]] as const) it(`${id} partitions its finite polygon`,()=>{
  const r=200, faces=spMedallion(id,r);
  expect(faces.reduce((sum,f)=>sum+area(f.points),0)).toBeCloseTo(n/2*r*r*Math.sin(2*Math.PI/n),7);
 });
 it("retains unique paint identities when a lattice is scaled and rotated",()=>{
  for(const pattern of [{id:"starcross",grid:"square"},{id:"rosette12",grid:"hex"},{id:"medallion5",grid:"radial"}]) {
   const faces=spScene(pattern,390,420,125,35);
   expect(faces.length).toBeGreaterThan(20);expect(new Set(faces.map(f=>f.key)).size).toBe(faces.length);
   expect(faces.every(f=>f.points.flat().every(Number.isFinite))).toBe(true);
  }
 });
});
