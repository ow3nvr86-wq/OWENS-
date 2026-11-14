// Input cleaning and defensive parsing.
//
// Two threats are real here, even with no server:
//   1. Oversized or malformed text typed into the app, which bloats storage
//      and breaks layout.
//   2. Stored values that are not the shape we expect. On the web build the
//      store is the browser's localStorage, which the user can edit freely,
//      so anything read back has to be treated as untrusted.

export const LIMITS = {
  name: 40,
  fullName: 80,
  workoutName: 60,
  drillsPerWorkout: 60,
  workouts: 100,
  logEntries: 5000,
} as const;

/**
 * Trim to something safe to store and render: no control characters, no
 * zero-width tricks, no runaway whitespace, and a hard length cap.
 */
export function cleanText(input: unknown, maxLen: number): string {
  if (typeof input !== 'string') return '';
  const stripped = input
    // Control characters, including the ones that break layout.
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, '')
    // Zero-width and bidi overrides, which can disguise text.
    .replace(/[​-‏‪-‮⁠-⁤﻿]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return stripped.slice(0, maxLen);
}

/** True when a value is a plain finite number inside a range. */
export function isNum(v: unknown, min: number, max: number): v is number {
  return typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export type SafeLogEntry = { date: string; day: number; cycle: number };

/** Keeps only entries that are the right shape; drops anything else. */
export function parseLog(raw: unknown): SafeLogEntry[] {
  if (!Array.isArray(raw)) return [];
  const out: SafeLogEntry[] = [];
  for (const e of raw) {
    if (!e || typeof e !== 'object') continue;
    const { date, day, cycle } = e as Record<string, unknown>;
    if (typeof date !== 'string' || !DATE_RE.test(date)) continue;
    if (!isNum(day, 1, 31)) continue;
    if (!isNum(cycle, 0, 100000)) continue;
    out.push({ date, day, cycle });
    if (out.length >= LIMITS.logEntries) break;
  }
  return out;
}

export function parseCycle(raw: unknown): number {
  return isNum(raw, 0, 100000) ? Math.floor(raw) : 0;
}

/** Drill ticks are a flat map of string keys to booleans. */
export function parseTicks(raw: unknown): Record<string, boolean> {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
  const out: Record<string, boolean> = {};
  let n = 0;
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    if (typeof k !== 'string' || k.length > 120) continue;
    if (typeof v !== 'boolean') continue;
    out[k] = v;
    if (++n >= 20000) break;
  }
  return out;
}

export type SafeProfile = Record<string, string | number | string[]>;

/** Profile values are only ever strings, numbers or arrays of strings. */
export function parseProfile(raw: unknown): SafeProfile | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const out: SafeProfile = {};
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    if (typeof k !== 'string' || k.length > 40) continue;
    if (typeof v === 'string') out[k] = cleanText(v, LIMITS.name);
    else if (isNum(v, 0, 1000)) out[k] = v;
    else if (Array.isArray(v)) {
      out[k] = v.filter((x): x is string => typeof x === 'string' && x.length <= 40).slice(0, 20);
    }
  }
  return Object.keys(out).length ? out : null;
}

export type SafeWorkout = {
  id: string;
  name: string;
  drillIds: string[];
  createdAt: string;
};

export function parseWorkouts(raw: unknown): SafeWorkout[] {
  if (!Array.isArray(raw)) return [];
  const out: SafeWorkout[] = [];
  for (const w of raw) {
    if (!w || typeof w !== 'object') continue;
    const { id, name, drillIds, createdAt } = w as Record<string, unknown>;
    if (typeof id !== 'string' || !id || id.length > 40) continue;
    const cleanName = cleanText(name, LIMITS.workoutName);
    if (!cleanName) continue;
    if (!Array.isArray(drillIds)) continue;
    const ids = drillIds
      .filter((d): d is string => typeof d === 'string' && /^[a-z0-9-]{1,60}$/.test(d))
      .slice(0, LIMITS.drillsPerWorkout);
    if (!ids.length) continue;
    out.push({
      id,
      name: cleanName,
      drillIds: ids,
      createdAt: typeof createdAt === 'string' ? createdAt.slice(0, 40) : '',
    });
    if (out.length >= LIMITS.workouts) break;
  }
  return out;
}

export type SafeAgreement = { version: string; acceptedAt: string; name?: string };

export function parseAgreement(raw: unknown): SafeAgreement | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null;
  const { version, acceptedAt, name } = raw as Record<string, unknown>;
  if (typeof version !== 'string' || version.length > 20) return null;
  return {
    version,
    acceptedAt: typeof acceptedAt === 'string' ? acceptedAt.slice(0, 40) : '',
    name: typeof name === 'string' ? cleanText(name, LIMITS.fullName) : undefined,
  };
}
