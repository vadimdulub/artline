export type PatternFace = {points: number[][]; tone: number; kind: string; key: string; cx: number; cy: number};
export function spTile(id: string, unit: number): PatternFace[];
export function spMedallion(id: string, radius: number): PatternFace[];
export function spScene(pattern: {id: string; grid: string}, width: number, height: number, scale?: number, angle?: number, thumbnail?: boolean): PatternFace[];
