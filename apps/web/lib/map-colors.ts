import type { MapItem } from "./map";

export type MapIdentityColor = { id: string; name: string; hex: string; fill: string };
// Shared with the reviewed fifty-color map concept. The surrounding UI stays neutral.
export const mapIdentityPalette: readonly MapIdentityColor[] = [
  {
    "id": "atlas-01",
    "name": "Lapis",
    "hex": "#315F9C",
    "fill": "#EAEEF2"
  },
  {
    "id": "atlas-02",
    "name": "Pine",
    "hex": "#356B50",
    "fill": "#EAEFEC"
  },
  {
    "id": "atlas-03",
    "name": "Carmine",
    "hex": "#A23E52",
    "fill": "#F3EBED"
  },
  {
    "id": "atlas-04",
    "name": "Violet",
    "hex": "#77529A",
    "fill": "#F0EDF2"
  },
  {
    "id": "atlas-05",
    "name": "Ochre",
    "hex": "#8A641F",
    "fill": "#F1EEE8"
  },
  {
    "id": "atlas-06",
    "name": "Teal",
    "hex": "#246D75",
    "fill": "#E9EFEF"
  },
  {
    "id": "atlas-07",
    "name": "Burnt sienna",
    "hex": "#A64F34",
    "fill": "#F3ECEA"
  },
  {
    "id": "atlas-08",
    "name": "Indigo",
    "hex": "#535398",
    "fill": "#EDEDF2"
  },
  {
    "id": "atlas-09",
    "name": "Olive",
    "hex": "#62712D",
    "fill": "#EEEFEA"
  },
  {
    "id": "atlas-10",
    "name": "Mulberry",
    "hex": "#954675",
    "fill": "#F2ECEF"
  },
  {
    "id": "atlas-11",
    "name": "Slate",
    "hex": "#4C677D",
    "fill": "#ECEEF0"
  },
  {
    "id": "atlas-12",
    "name": "Copper",
    "hex": "#9A5B2F",
    "fill": "#F2EDEA"
  },
  {
    "id": "atlas-13",
    "name": "Myrtle",
    "hex": "#257863",
    "fill": "#E9F0EE"
  },
  {
    "id": "atlas-14",
    "name": "Amethyst",
    "hex": "#86528C",
    "fill": "#F1EDF1"
  },
  {
    "id": "atlas-15",
    "name": "Brick",
    "hex": "#A3463E",
    "fill": "#F3ECEB"
  },
  {
    "id": "atlas-16",
    "name": "Prussian blue",
    "hex": "#34536F",
    "fill": "#EAEDEF"
  },
  {
    "id": "atlas-17",
    "name": "Fern",
    "hex": "#527345",
    "fill": "#EDEFEC"
  },
  {
    "id": "atlas-18",
    "name": "Plum",
    "hex": "#794269",
    "fill": "#F0EBEE"
  },
  {
    "id": "atlas-19",
    "name": "Marigold",
    "hex": "#85660F",
    "fill": "#F1EEE7"
  },
  {
    "id": "atlas-20",
    "name": "Marine",
    "hex": "#296E8C",
    "fill": "#E9EFF1"
  },
  {
    "id": "atlas-21",
    "name": "Rosewood",
    "hex": "#995466",
    "fill": "#F2EDEE"
  },
  {
    "id": "atlas-22",
    "name": "Cypress",
    "hex": "#416749",
    "fill": "#EBEEEC"
  },
  {
    "id": "atlas-23",
    "name": "Iris",
    "hex": "#6862A1",
    "fill": "#EEEEF3"
  },
  {
    "id": "atlas-24",
    "name": "Cinnamon",
    "hex": "#9B5134",
    "fill": "#F2ECEA"
  },
  {
    "id": "atlas-25",
    "name": "Peacock",
    "hex": "#137779",
    "fill": "#E8F0F0"
  },
  {
    "id": "atlas-26",
    "name": "Cranberry",
    "hex": "#A33267",
    "fill": "#F3EAEE"
  },
  {
    "id": "atlas-27",
    "name": "Blue grey",
    "hex": "#576D88",
    "fill": "#EDEFF1"
  },
  {
    "id": "atlas-28",
    "name": "Avocado",
    "hex": "#6F6D2A",
    "fill": "#EFEFE9"
  },
  {
    "id": "atlas-29",
    "name": "Orchid",
    "hex": "#95528D",
    "fill": "#F2EDF1"
  },
  {
    "id": "atlas-30",
    "name": "Sea blue",
    "hex": "#207298",
    "fill": "#E9EFF2"
  },
  {
    "id": "atlas-31",
    "name": "Mahogany",
    "hex": "#864739",
    "fill": "#F1ECEB"
  },
  {
    "id": "atlas-32",
    "name": "Jade",
    "hex": "#377560",
    "fill": "#EAEFEE"
  },
  {
    "id": "atlas-33",
    "name": "Heather",
    "hex": "#77618B",
    "fill": "#F0EEF1"
  },
  {
    "id": "atlas-34",
    "name": "Garnet",
    "hex": "#933544",
    "fill": "#F2EAEB"
  },
  {
    "id": "atlas-35",
    "name": "Juniper",
    "hex": "#426E68",
    "fill": "#EBEFEE"
  },
  {
    "id": "atlas-36",
    "name": "Saffron",
    "hex": "#896510",
    "fill": "#F1EEE7"
  },
  {
    "id": "atlas-37",
    "name": "Cornflower",
    "hex": "#4E68AC",
    "fill": "#ECEEF4"
  },
  {
    "id": "atlas-38",
    "name": "Forest",
    "hex": "#497149",
    "fill": "#ECEFEC"
  },
  {
    "id": "atlas-39",
    "name": "Mauve",
    "hex": "#915976",
    "fill": "#F2EDEF"
  },
  {
    "id": "atlas-40",
    "name": "Petrol",
    "hex": "#386876",
    "fill": "#EAEEEF"
  },
  {
    "id": "atlas-41",
    "name": "Terracotta",
    "hex": "#A3553B",
    "fill": "#F3EDEB"
  },
  {
    "id": "atlas-42",
    "name": "Sage",
    "hex": "#616F50",
    "fill": "#EEEFEC"
  },
  {
    "id": "atlas-43",
    "name": "Royal blue",
    "hex": "#4359A2",
    "fill": "#EBEDF3"
  },
  {
    "id": "atlas-44",
    "name": "Raspberry",
    "hex": "#AC426C",
    "fill": "#F4EBEF"
  },
  {
    "id": "atlas-45",
    "name": "Umber",
    "hex": "#7D5D3B",
    "fill": "#F0EDEB"
  },
  {
    "id": "atlas-46",
    "name": "Emerald",
    "hex": "#24734D",
    "fill": "#E9EFEC"
  },
  {
    "id": "atlas-47",
    "name": "Wisteria",
    "hex": "#7F5BA0",
    "fill": "#F0EDF3"
  },
  {
    "id": "atlas-48",
    "name": "Burgundy",
    "hex": "#7C3D54",
    "fill": "#F0EBED"
  },
  {
    "id": "atlas-49",
    "name": "Aegean",
    "hex": "#357284",
    "fill": "#EAEFF1"
  },
  {
    "id": "atlas-50",
    "name": "Bronze",
    "hex": "#7D6928",
    "fill": "#F0EEE9"
  }
];

export function mapIdentity(item: MapItem): string { return item.colorKey ?? `${item.kind}:${item.id}`; }

// Allocate from the entire loaded selection, not the checked subset. Up to fifty
// identities receive distinct colors; larger pages retain names and kind symbols.
export function mapIdentityColors(items: readonly MapItem[]): Record<string, MapIdentityColor> {
  const used = new Set<number>(), assignments: Record<string, MapIdentityColor> = {};
  for (const key of [...new Set(items.map(mapIdentity))].sort()) {
    let hash = 2166136261;
    for (const character of key) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
    let index = (hash >>> 0) % mapIdentityPalette.length;
    if (used.size < mapIdentityPalette.length) while (used.has(index)) index = (index + 1) % mapIdentityPalette.length;
    used.add(index); assignments[key] = mapIdentityPalette[index];
  }
  return assignments;
}
