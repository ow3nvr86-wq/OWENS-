// Turns a player's setup answers into a repeating routine of training days.
//
// The shape follows Court Craft: N days per cycle, each day owning one or two
// focus areas and a drill list sized to the session length the player chose.

import { DRILLS, Drill, Equipment, Focus } from './content/drills';
import { QUIZ } from './content/quiz';
import { Profile } from './storage';

const EQUIPMENT_RANK: Record<Equipment, number> = { none: 0, ball: 1, cones: 2, gym: 3 };

export const FOCUS_LABELS = Object.fromEntries(
  (QUIZ.find((s) => s.key === 'focus')?.options ?? []).map((o) => [o.value, o.label]),
) as Record<string, string>;

export type RoutineDay = {
  day: number;
  focus: Focus[];
  drills: Drill[];
  totalMinutes: number;
};

/**
 * Rough time cost of one drill.
 *
 * Every drill states its work as prose ("4 rounds of 20 seconds", "3 sets of 8
 * each leg"), so rather than hand-costing 58 entries we read the round count
 * out of that string and scale a per-focus baseline by it. Close enough to
 * fill a session sensibly, and it stays correct when drills are edited.
 */
export function estimateMinutes(drill: Drill): number {
  const baseline: Record<Focus, number> = {
    speed: 5, agility: 5, power: 6, hands: 5,
    routes: 5, throwing: 6, blocking: 5, conditioning: 7,
  };
  const rounds = Number(drill.work.match(/(\d+)\s*(rounds?|sets?|runs?|reps?|jumps?|throws?|trips?|laps?|starts?|sprints?|pushes?|gassers?|lengths?)/i)?.[1] ?? 3);
  const scale = Math.min(Math.max(rounds / 4, 0.6), 1.8);
  return Math.max(3, Math.round(baseline[drill.focus] * scale));
}

/** Focus areas the player picked, falling back to a sensible general plan. */
function chosenFocus(profile: Profile): Focus[] {
  const picked = Array.isArray(profile.focus) ? (profile.focus as Focus[]) : [];
  return picked.length ? picked : (['speed', 'agility', 'conditioning'] as Focus[]);
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
      .filter((d) => d.focus === f && d.id !== 'cooldown-walk')
      .sort((a, b) => rank(a) - rank(b));

  function rank(d: Drill) {
    if (d.positions.includes('all')) return 1;
    return d.positions.some((p) => positions.includes(p)) ? 0 : 2;
  }

  // Walk each focus area's list with its own cursor, so days do not repeat
  // the same drills until the pool is exhausted.
  const cursor: Partial<Record<Focus, number>> = {};
  const cooldown = DRILLS.find((d) => d.id === 'cooldown-walk');

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

    if (cooldown) {
      drills.push(cooldown);
      minutes += estimateMinutes(cooldown);
    }

    days.push({ day: i + 1, focus: unique, drills, totalMinutes: minutes });
  }

  return days;
}

export function dayTitle(day: RoutineDay): string {
  return day.focus.map((f) => FOCUS_LABELS[f] ?? f).join(' + ');
}
