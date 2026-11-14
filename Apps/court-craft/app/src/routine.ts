// Turns a player's setup answers into a repeating routine of training days.
//
// The shape follows Court Craft: N days per cycle, each day owning one or two
// focus areas and a drill list sized to the session length the player chose.

import { DRILLS, Drill, Equipment, Focus } from './content/drills';
import { QUIZ } from './content/quiz';
import { Profile } from './storage';

const EQUIPMENT_RANK: Record<Equipment, number> = { none: 0, ball: 1, hoop: 2, court: 3, gym: 4 };

export const FOCUS_LABELS = Object.fromEntries(
  (QUIZ.find((s) => s.key === 'focus')?.options ?? []).map((o) => [o.value, o.label]),
) as Record<string, string>;

export type RoutineDay = {
  day: number;
  focus: Focus[];
  drills: Drill[];
  totalMinutes: number;
};

/** Each drill carries its own authored length, so nothing has to be guessed. */
export function estimateMinutes(drill: Drill): number {
  return drill.minutes;
}

/** Focus areas the player picked, falling back to a sensible general plan. */
function chosenFocus(profile: Profile): Focus[] {
  const picked = Array.isArray(profile.focus) ? (profile.focus as Focus[]) : [];
  return picked.length ? picked : (['ball-handling', 'shooting', 'conditioning'] as Focus[]);
}

export function buildRoutine(profile: Profile): RoutineDay[] {
  const owned = EQUIPMENT_RANK[(profile.equipment as Equipment) ?? 'none'] ?? 0;
  const positions = Array.isArray(profile.positions) ? (profile.positions as string[]) : [];
  const dayCount = Number(profile.daysPerWeek) || 3;
  const target = Number(profile.sessionMinutes) || 30;
  const focusList = chosenFocus(profile);

  const usable = DRILLS.filter((d) => EQUIPMENT_RANK[d.equipment] <= owned);

  // Drills that match the player's position come first within a focus area.
  const byFocus = (f: Focus) =>
    usable
      .filter((d) => d.focus === f && !d.id.includes('warmup'))
      .sort((a, b) => rank(a) - rank(b));

  function rank(d: Drill) {
    if (d.positions.includes('all')) return 1;
    return d.positions.some((p) => positions.includes(p)) ? 0 : 2;
  }

  // Walk each focus area's list with its own cursor, so days do not repeat
  // the same drills until the pool is exhausted.
  const cursor: Partial<Record<Focus, number>> = {};
  // Every session opens with the warm-up the shipped app always included.
  const warmup = DRILLS.find((d) => d.id === 'dynamic-warmup');

  const days: RoutineDay[] = [];
  for (let i = 0; i < dayCount; i++) {
    // One or two focus areas per day, rotating through what was picked.
    const dayFocus: Focus[] =
      focusList.length === 1
        ? [focusList[0]]
        : [focusList[i % focusList.length], focusList[(i + 1) % focusList.length]];
    const unique = Array.from(new Set(dayFocus));

    const drills: Drill[] = [];
    let minutes = 0;
    let guard = 0;

    while (minutes < target && guard < 40) {
      guard++;
      let added = false;
      for (const f of unique) {
        const pool = byFocus(f);
        if (!pool.length) continue;
        const at = cursor[f] ?? 0;
        const drill = pool[at % pool.length];
        cursor[f] = at + 1;
        if (drills.some((d) => d.id === drill.id)) continue;
        drills.push(drill);
        minutes += estimateMinutes(drill);
        added = true;
        if (minutes >= target) break;
      }
      if (!added) break;
    }

    if (warmup) {
      drills.unshift(warmup);
      minutes += estimateMinutes(warmup);
    }

    days.push({ day: i + 1, focus: unique, drills, totalMinutes: minutes });
  }

  return days;
}

export function dayTitle(day: RoutineDay): string {
  return day.focus.map((f) => FOCUS_LABELS[f] ?? f).join(' + ');
}
