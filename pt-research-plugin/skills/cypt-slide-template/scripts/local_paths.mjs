// Node twin of scripts/local_paths.py: resolves machine-specific settings and private reference decks with the
// same order, so the Python tools and the template builder always agree. No personal path is embedded here.
//
// Setting order: environment variable -> <PT_RESEARCH_HOME>/local.paths.json (user level, survives plugin updates)
//   -> <plugin-root>/local.paths.json -> <plugin-root>/.env.local -> undefined.
// Local reference folder: PT_LOCAL_REFERENCES_DIR (explicit, used exclusively) -> <PT_RESEARCH_HOME>/local-references
//   -> <plugin-root>/skills/cypt-slide-template/assets/local-references.
// PT_RESEARCH_HOME defaults to ~/.config/pt-research and is read from the environment only.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const expandHome = (p) => (p === "~" ? os.homedir() : p.startsWith("~/") ? path.join(os.homedir(), p.slice(2)) : p);
const nonEmpty = (v) => (typeof v === "string" && v.trim() ? v : undefined);

export function researchHome(env = process.env) {
  const v = nonEmpty(env.PT_RESEARCH_HOME);
  return v ? path.resolve(expandHome(v.trim())) : path.join(os.homedir(), ".config", "pt-research");
}

function readJson(dir) {
  try {
    const data = JSON.parse(fs.readFileSync(path.join(dir, "local.paths.json"), "utf8"));
    if (!data || typeof data !== "object" || Array.isArray(data)) return {};
    return Object.fromEntries(Object.entries(data).filter(([k, v]) => nonEmpty(v) && !k.startsWith("_")));
  } catch { return {}; }
}

function readEnvFile(root) {
  const out = {};
  let lines;
  try { lines = fs.readFileSync(path.join(root, ".env.local"), "utf8").split(/\r?\n/); } catch { return out; }
  for (let line of lines) {
    line = line.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const i = line.indexOf("=");
    const value = line.slice(i + 1).trim().replace(/^["']+|["']+$/g, "");
    if (value) out[line.slice(0, i).trim()] = value;
  }
  return out;
}

export function setting(key, { pluginRoot, home = researchHome(), env = process.env } = {}) {
  const fromEnv = nonEmpty(env[key]);
  if (fromEnv) return fromEnv;
  for (const source of [readJson(home), readJson(pluginRoot), readEnvFile(pluginRoot)]) {
    if (nonEmpty(source[key])) return source[key];
  }
  return undefined;
}

export function localReferencesDir({ pluginRoot, home = researchHome(), env = process.env } = {}) {
  const isDir = (p) => { try { return fs.statSync(p).isDirectory(); } catch { return false; } };
  const explicit = nonEmpty(env.PT_LOCAL_REFERENCES_DIR);
  if (explicit) { const p = path.resolve(expandHome(explicit.trim())); return isDir(p) ? p : undefined; }
  for (const candidate of [
    path.join(home, "local-references"),
    path.join(pluginRoot, "skills", "cypt-slide-template", "assets", "local-references"),
  ]) if (isDir(candidate)) return candidate;
  return undefined;
}

// CLI for tests and diagnostics: node local_paths.mjs <plugin-root> setting KEY | refs
if (process.argv[1]?.endsWith("local_paths.mjs")) {
  const [pluginRoot, cmd, key] = process.argv.slice(2);
  if (pluginRoot && cmd === "setting") console.log(setting(key, { pluginRoot }) ?? "");
  else if (pluginRoot && cmd === "refs") console.log(localReferencesDir({ pluginRoot }) ?? "");
}
