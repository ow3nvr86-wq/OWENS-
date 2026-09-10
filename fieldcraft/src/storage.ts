// All persistence is local to the device. Nothing here talks to a network.
// Key names are kept identical to the original build so existing installs
// keep their profile, log and purchase state.

import AsyncStorage from '@react-native-async-storage/async-storage';

export const KEYS = {
  profile: 'courtready:profile',
  log: 'courtready:log',
  cycle: 'courtready:cycle',
  drillTicks: 'courtready:drillticks',
  results: 'courtready:results',
  banked: 'courtready:banked',
  accepted: 'courtready:accepted',
  entitlement: 'courtready:entitlement',
} as const;

export async function readJSON<T>(key: string, fallback: T): Promise<T> {
  try {
    const raw = await AsyncStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

export async function writeJSON(key: string, value: unknown): Promise<void> {
  try {
    await AsyncStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage being unavailable must never crash a training session.
  }
}

export type Profile = Record<string, string | number | string[]>;

export const loadProfile = () => readJSON<Profile | null>(KEYS.profile, null);
export const saveProfile = (p: Profile) => writeJSON(KEYS.profile, p);

export const loadAccepted = () => readJSON<string | null>(KEYS.accepted, null);
export const saveAccepted = (version: string) => writeJSON(KEYS.accepted, version);

/** One completed training day. cycle counts how many times the routine has been finished. */
export type LogEntry = { date: string; day: number; cycle: number };

export const loadLog = () => readJSON<LogEntry[]>(KEYS.log, []);
export const saveLog = (log: LogEntry[]) => writeJSON(KEYS.log, log);

export const loadCycle = () => readJSON<number>(KEYS.cycle, 0);
export const saveCycle = (cycle: number) => writeJSON(KEYS.cycle, cycle);

export const todayKey = () => new Date().toISOString().slice(0, 10);

export function isDayComplete(log: LogEntry[], day: number, cycle: number): boolean {
  return log.some((e) => e.day === day && e.cycle === cycle);
}
