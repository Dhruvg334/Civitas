/**
 * Civitas Shared Incident Taxonomy.
 * 
 * Reconciled against backend/ML contracts:
 * - civitas_vision.contracts.CIVITAS_CATEGORIES
 * - civitas_vision.contracts.REAL_MEDIA_CATEGORIES
 * - Backend report creation and spatial clustering categories.
 */

export interface IncidentCategoryDef {
  id: string; // Used in UI & Report creation (e.g. "Water leak")
  slug: string; // Canonical slug (e.g. "water_leakage")
  label: string;
  desc: string;
  icon: string;
  isCore: boolean;
}

export const INCIDENT_CATEGORIES: readonly IncidentCategoryDef[] = [
  {
    id: "Water leak",
    slug: "water_leakage",
    label: "Water Leak / Pipe Burst",
    desc: "Pipeline rupture, standing puddle, or flooded street surface",
    icon: "water",
    isCore: true,
  },
  {
    id: "Pothole or road damage",
    slug: "pothole_road_damage",
    label: "Pothole / Road Damage",
    desc: "Deep asphalt cavity, road erosion, or sunken manhole",
    icon: "pothole",
    isCore: true,
  },
  {
    id: "Broken streetlight",
    slug: "broken_streetlight",
    label: "Broken Streetlight & Power",
    desc: "Dark luminaire, exposed wiring, or damaged lamp post",
    icon: "streetlight",
    isCore: true,
  },
  {
    id: "Fallen tree",
    slug: "fallen_tree",
    label: "Fallen Tree & Branches",
    desc: "Snapped branch, fallen trunk, or sidewalk blockage",
    icon: "tree",
    isCore: true,
  },
  {
    id: "Garbage overflow",
    slug: "garbage_overflow",
    label: "Garbage & Waste Dumping",
    desc: "Uncollected municipal solid waste or debris mound",
    icon: "garbage",
    isCore: true,
  },
  {
    id: "Drain blockage",
    slug: "drainage_damage",
    label: "Drain Blockage & Sewage",
    desc: "Clogged stormwater grate, overflow, or refuse backflow",
    icon: "drain",
    isCore: false,
  },
  {
    id: "Pests and mold",
    slug: "pest_infestation",
    label: "Pests & Vector Hazards",
    desc: "Standing stagnant water vector breeding or public health hazard",
    icon: "hazard",
    isCore: false,
  },
  {
    id: "Traffic signal damage",
    slug: "other_infrastructure_damage",
    label: "Traffic Signal & Signs",
    desc: "Flickering traffic signals or damaged pedestrian signage",
    icon: "crossing",
    isCore: false,
  },
] as const;

export function getCategoryBySlug(slug: string): IncidentCategoryDef | undefined {
  return INCIDENT_CATEGORIES.find((c) => c.slug === slug || c.id.toLowerCase() === slug.toLowerCase());
}

export function getCategoryById(id: string): IncidentCategoryDef | undefined {
  return INCIDENT_CATEGORIES.find((c) => c.id === id || c.slug === id);
}

export function normalizeCategorySlug(input: string): string {
  const match = getCategoryById(input) || getCategoryBySlug(input);
  return match ? match.slug : "other_infrastructure_damage";
}
