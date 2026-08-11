#!/usr/bin/env node
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..");
const SKILL_FILE = "SKILL.md";
const NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const KNOWN_KEYS = new Set(["name", "description", "license", "compatibility", "metadata"]);

const errors = [];
const checked = [];

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (entry === ".git" || entry === "node_modules" || entry === ".venv") continue;
    const st = statSync(full);
    if (st.isDirectory()) {
      walk(full);
    } else if (entry === SKILL_FILE) {
      checked.push(full);
    }
  }
}

function parseFrontmatter(text) {
  const match = text.match(/^\uFEFF?---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!match) return null;
  const values = {};
  let currentKey = null;
  for (const rawLine of match[1].split(/\r?\n/)) {
    if (/^\s*$/.test(rawLine) || /^\s*#/.test(rawLine)) continue;
    const top = rawLine.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (top) {
      currentKey = top[1];
      values[currentKey] = top[2];
    } else if (currentKey) {
      const trimmed = rawLine.replace(/^\s+/, "").replace(/\s+$/, "");
      values[currentKey] = `${values[currentKey]} ${trimmed}`.trim();
    } else {
      throw new Error(`unparseable frontmatter line: ${rawLine}`);
    }
  }
  for (const [key, value] of Object.entries(values)) {
    let v = value;
    if (/^\[.*\]$/.test(v)) {
      v = v.slice(1, -1).split(",").map((s) => s.trim()).join(", ");
    }
    values[key] = v.replace(/^(["'])(.*)\1$/, "$2").replace(/^\s+|\s+$/g, "");
  }
  return values;
}

function validateSkill(file) {
  const folder = dirname(file);
  const skillName = folder.split(/[\\/]/).pop();
  const text = readFileSync(file, "utf8");
  let meta;
  try {
    meta = parseFrontmatter(text);
  } catch (err) {
    errors.push(`${relative(ROOT, file)}: ${err.message}`);
    return;
  }
  if (!meta) {
    errors.push(`${relative(ROOT, file)}: missing frontmatter (must start with "---" and end with "---")`);
    return;
  }
  const unknown = Object.keys(meta).filter((k) => !KNOWN_KEYS.has(k));
  for (const k of unknown) {
    errors.push(`${relative(ROOT, file)}: unknown frontmatter key "${k}" (known keys: ${[...KNOWN_KEYS].join(", ")})`);
  }
  const name = meta.name;
  if (!name) {
    errors.push(`${relative(ROOT, file)}: frontmatter "name" is required`);
  } else if (name !== skillName) {
    errors.push(`${relative(ROOT, file)}: frontmatter name "${name}" does not match folder name "${skillName}"`);
  } else if (name.length > 64) {
    errors.push(`${relative(ROOT, file)}: name "${name}" exceeds 64 characters`);
  } else if (!NAME_RE.test(name)) {
    errors.push(`${relative(ROOT, file)}: name "${name}" must be lowercase, hyphen-separated (e.g. "my-skill")`);
  }
  if (!meta.description) {
    errors.push(`${relative(ROOT, file)}: frontmatter "description" is required (skills without one are never surfaced)`);
  }
}

walk(ROOT);
if (checked.length === 0) {
  console.log("No SKILL.md files found; nothing to validate.");
  process.exit(0);
}
for (const file of checked) validateSkill(file);

if (errors.length > 0) {
  console.error(`Skills validation failed (${errors.length} error(s)):`);
  for (const err of errors) console.error(`  - ${err}`);
  process.exit(1);
}
console.log(`Skills validation passed (${checked.length} skill(s) checked).`);
