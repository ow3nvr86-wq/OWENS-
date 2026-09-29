// All persistence is local to the device. Nothing here talks to a network.
// Rallycraft has never shipped, so its keys carry its own name rather than
// the ones inherited when this project was copied from Court Craft.

import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  parseAgreement, parseCycle, parseLog, parseProfile, parseTicks, parseWorkouts,
} from './sanitize';

export const KEYS = {
  profile: 'rallycraft:profile',
  log: 'rallycraft:log',
  cycle: 'rallycraft:cycle',
  drillTicks: 'rallycraft:drillticks',
  results: 'rallycraft:results',
  banked: 'rallycraft:banked',
  accepted: 'rallycraft:accepted',
  entitlement: 'rallycraft:entitlement',
  agreement: 'rallycraft:agreement',
} as const;

export async function readJSON<T>(key: string, fallback: T): Promise<T> {
  try {
    const raw = await AsyncStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

/** Refuse to persist anything absurdly large, whatever produced it. */
const MAX_VALUE_BYTES = 512 * 1024;

export async function writeJSON(key: string, value: unknown): Promise<void> {
  try {
    const payload = JSON.stringify(value);
    if (payload.length > MAX_VALUE_BYTES) return;
    await AsyncStorage.setItem(key, payload);
  } catch {
    // Storage being unavailable must never crash a training session.
  }
}

export type Profile = Record<string, string | number | string[]>;

export const loadProfile = async (): Promise<Profile | null> =>
  parseProfile(await readJSON<unknown>(KEYS.profile, null));
export const saveProfile = (p: Profile) => writeJSON(KEYS.profile, p);

export const loadAccepted = () => readJSON<string | null>(KEYS.accepted, null);
export const saveAccepted = (version: string) => writeJSON(KEYS.accepted, version);

/** One completed training day. cycle counts how many times the routine has been finished. */
export type LogEntry = { date: string; day: number; cycle: number };

export const loadLog = async (): Promise<LogEntry[]> =>
  parseLog(await readJSON<unknown>(KEYS.log, []));
export const saveLog = (log: LogEntry[]) => writeJSON(KEYS.log, log);

export const loadCycle = async (): Promise<number> =>
  parseCycle(await readJSON<unknown>(KEYS.cycle, 0));
export const saveCycle = (cycle: number) => writeJSON(KEYS.cycle, cycle);

export const todayKey = () => new Date().toISOString().slice(0, 10);

export function isDayComplete(log: LogEntry[], day: number, cycle: number): boolean {
  return log.some((e) => e.day === day && e.cycle === cycle);
}

/** Recorded when the player accepts the injury acknowledgement. */
export type Agreement = { version: string; acceptedAt: string; name?: string };

export const loadAgreement = async (): Promise<Agreement | null> =>
  parseAgreement(await readJSON<unknown>(KEYS.agreement, null));
export const saveAgreement = (a: Agreement) => writeJSON(KEYS.agreement, a);

/** Wipes everything this app has stored on the device. */
export async function resetAll(): Promise<void> {
  try {
    for (const key of Object.values(KEYS)) await AsyncStorage.removeItem(key);
  } catch {
    // Nothing to do; the app simply keeps whatever it could not clear.
  }
}

/** Per-drill ticks, keyed so each cycle and day is tracked separately. */
export type DrillTicks = Record<string, boolean>;

export const tickKey = (cycle: number, day: number, drillId: string) =>
  `${cycle}:${day}:${drillId}`;

export const loadTicks = async (): Promise<DrillTicks> =>
  parseTicks(await readJSON<unknown>(KEYS.drillTicks, {}));
export const saveTicks = (t: DrillTicks) => writeJSON(KEYS.drillTicks, t);

/** A workout the player built themselves, as an ordered list of drill ids. */
export type CustomWorkout = {
  id: string;
  name: string;
  drillIds: string[];
  createdAt: string;
};

const WORKOUTS_KEY = 'rallycraft:workouts';

export const loadWorkouts = async (): Promise<CustomWorkout[]> =>
  parseWorkouts(await readJSON<unknown>(WORKOUTS_KEY, []));
export const saveWorkouts = (w: CustomWorkout[]) => writeJSON(WORKOUTS_KEY, w);
