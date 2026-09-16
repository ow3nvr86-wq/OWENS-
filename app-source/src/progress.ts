// Streaks, badges and calendar data, all derived from the training log.
// Nothing here stores anything new; it reads what the app already records.

import { LogEntry } from './storage';

export const dayKey = (d: Date) => d.toISOString().slice(0, 10);

const DAY = 24 * 60 * 60 * 1000;

/** Distinct dates trained, oldest first. */
export function trainedDates(log: LogEntry[]): string[] {
  return Array.from(new Set(log.map((e) => e.date))).sort();
}

function daysBetween(a: string, b: string): number {
  return Math.round((Date.parse(b) - Date.parse(a)) / DAY);
}

export type Streak = { current: number; longest: number; trainedToday: boolean };

/**
 * A streak survives one missed day.
 *
 * Resetting to zero the moment someone misses a single day is the fastest way
 * to lose them, so a gap of one rest day keeps the run alive. Two days off
 * ends it.
 */
export function streakFrom(log: LogEntry[], today = dayKey(new Date())): Streak {
  const dates = trainedDates(log);
  if (dates.length === 0) return { current: 0, longest: 0, trainedToday: false };

  let longest = 1;
  let run = 1;
  for (let i = 1; i < dates.length; i++) {
    run = daysBetween(dates[i - 1], dates[i]) <= 2 ? run + 1 : 1;
    if (run > longest) longest = run;
  }

  // The current run only counts if the last session was today or yesterday.
  const last = dates[dates.length - 1];
  const sinceLast = daysBetween(last, today);
  let current = 0;
  if (sinceLast <= 1) {
    current = 1;
    for (let i = dates.length - 1; i > 0; i--) {
      if (daysBetween(dates[i - 1], dates[i]) <= 2) current++;
      else break;
    }
  }

  return { current, longest, trainedToday: last === today };
}

export type Badge = {
  id: string;
  name: string;
  detail: string;
  earned: boolean;
};

export type BadgeInput = {
  log: LogEntry[];
  cycle: number;
  streak: Streak;
};

export function badgesFrom({ log, cycle, streak }: BadgeInput): Badge[] {
  const sessions = log.length;
  const days = trainedDates(log).length;

  const make = (id: string, name: string, detail: string, earned: boolean): Badge =>
    ({ id, name, detail, earned });

  return [
    make('first', 'First Session', 'Finish your first day', sessions >= 1),
    make('ten', 'Ten Down', 'Finish ten sessions', sessions >= 10),
    make('twentyfive', 'Regular', 'Finish twenty five sessions', sessions >= 25),
    make('fifty', 'Committed', 'Finish fifty sessions', sessions >= 50),
    make('hundred', 'Century', 'Finish one hundred sessions', sessions >= 100),
    make('week', 'Full Week', 'Bank a complete week', cycle >= 1),
    make('fiveweeks', 'Five Weeks', 'Bank five complete weeks', cycle >= 5),
    make('streak3', 'Three in a Row', 'Train three sessions running', streak.longest >= 3),
    make('streak7', 'Seven in a Row', 'Train seven sessions running', streak.longest >= 7),
    make('streak14', 'Fourteen in a Row', 'Train fourteen running', streak.longest >= 14),
    make('tendays', 'Ten Days', 'Train on ten separate days', days >= 10),
    make('thirtydays', 'Thirty Days', 'Train on thirty separate days', days >= 30),
  ];
}

/** Grid of a month, padded so the first row starts on the right weekday. */
export function monthGrid(year: number, month: number): (string | null)[] {
  const first = new Date(Date.UTC(year, month, 1));
  const startPad = (first.getUTCDay() + 6) % 7; // weeks start Monday
  const daysInMonth = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();

  const cells: (string | null)[] = Array(startPad).fill(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(dayKey(new Date(Date.UTC(year, month, d))));
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}
