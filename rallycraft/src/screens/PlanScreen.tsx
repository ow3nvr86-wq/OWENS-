import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Drill } from '../content/drills';
import { badgesFrom, streakFrom } from '../progress';
import SessionSummary from '../components/SessionSummary';
import { RoutineDay, buildRoutine, dayTitle, estimateMinutes } from '../routine';
import {
  DrillTicks, LogEntry, Profile, isDayComplete, loadCycle, loadLog, loadTicks,
  saveCycle, saveLog, saveTicks, tickKey, todayKey,
} from '../storage';
import { Palette, useTheme } from '../theme';
import Hero from '../components/Hero';
import DrillTimer from '../components/DrillTimer';

type Props = { profile: Profile; onOpenLibrary: () => void };

export default function PlanScreen({ profile, onOpenLibrary }: Props) {
  const { palette } = useTheme();
  const styles = useMemo(() => makeStyles(palette), [palette]);
  const routine = useMemo(() => buildRoutine(profile), [profile]);
  const [selected, setSelected] = useState(0);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [cycle, setCycle] = useState(0);
  const [open, setOpen] = useState<string | null>(null);
  const bodyRef = useRef<ScrollView>(null);
  const [ticks, setTicks] = useState<DrillTicks>({});
  const [summary, setSummary] = useState<null | {
    dayNumber: number; drillsDone: number; drillsTotal: number;
    minutes: number; streak: number; daysDone: number;
    daysTotal: number; newBadges: string[];
  }>(null);

  useEffect(() => {
    (async () => {
      const [storedLog, storedCycle, storedTicks] = await Promise.all([
        loadLog(), loadCycle(), loadTicks(),
      ]);
      setTicks(storedTicks);
      setLog(storedLog);
      setCycle(storedCycle);
      // Open on the first day of this cycle that is not done yet.
      const next = routine.findIndex((d) => !isDayComplete(storedLog, d.day, storedCycle));
      setSelected(next === -1 ? 0 : next);
    })();
  }, [routine]);

  useEffect(() => {
    bodyRef.current?.scrollTo({ y: 0, animated: false });
  }, [selected]);

  const day = routine[selected];
  const done = day ? isDayComplete(log, day.day, cycle) : false;
  const doneCount = routine.filter((d) => isDayComplete(log, d.day, cycle)).length;

  async function toggleTick(drillId: string) {
    if (!day) return;
    const key = tickKey(cycle, day.day, drillId);
    const next = { ...ticks, [key]: !ticks[key] };
    setTicks(next);
    await saveTicks(next);
  }

  const doneDrills = day
    ? day.drills.filter((d) => ticks[tickKey(cycle, day.day, d.id)]).length
    : 0;

  async function toggleComplete() {
    if (!day) return;
    let nextLog: LogEntry[];
    if (done) {
      nextLog = log.filter((e) => !(e.day === day.day && e.cycle === cycle));
    } else {
      nextLog = [...log, { date: todayKey(), day: day.day, cycle }];
    }
    // Badges earned by this session are the ones that were not earned before it.
    const before = badgesFrom({ log, cycle, streak: streakFrom(log) })
      .filter((b) => b.earned).map((b) => b.id);
    const afterStreak = streakFrom(nextLog);
    const gained = badgesFrom({ log: nextLog, cycle, streak: afterStreak })
      .filter((b) => b.earned && !before.includes(b.id));

    setLog(nextLog);
    await saveLog(nextLog);

    if (!done) {
      setSummary({
        dayNumber: day.day,
        drillsDone: day.drills.filter((d) => ticks[tickKey(cycle, day.day, d.id)]).length,
        drillsTotal: day.drills.length,
        minutes: day.totalMinutes,
        streak: afterStreak.current,
        daysDone: routine.filter((r) => isDayComplete(nextLog, r.day, cycle)).length,
        daysTotal: routine.length,
        newBadges: gained.map((b) => b.name),
      });
    }

    // Finishing every day rolls the routine over into a fresh cycle.
    const finished = routine.every((d) => isDayComplete(nextLog, d.day, cycle));
    if (finished) {
      const nextCycle = cycle + 1;
      setCycle(nextCycle);
      await saveCycle(nextCycle);
      setSelected(0);
    }
  }

  if (!day) return <View style={styles.root} />;

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.brand}>RALLYCRAFT</Text>
        <TouchableOpacity onPress={onOpenLibrary} accessibilityRole="button" hitSlop={12}>
          <Text style={styles.headerLink}>Library</Text>
        </TouchableOpacity>
      </View>

      {/* Progress across the routine: one pill per day, ticked when complete. */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.pillsRow}
        contentContainerStyle={styles.pills}
      >
        {routine.map((d, i) => {
          const complete = isDayComplete(log, d.day, cycle);
          const on = i === selected;
          return (
            <TouchableOpacity
              key={d.day}
              onPress={() => { setSelected(i); setOpen(null); }}
              accessibilityRole="tab"
              accessibilityState={{ selected: on }}
              accessibilityLabel={`Day ${d.day}`}
              style={[styles.pill, on && styles.pillOn]}
            >
              <Text style={[styles.pillText, on && styles.pillTextOn]}>
                {complete ? '✓  ' : ''}Day {d.day}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <ScrollView ref={bodyRef} contentContainerStyle={styles.body}>
        <Hero
          name={typeof profile.name === 'string' ? profile.name : undefined}
          done={doneCount}
          total={routine.length}
          ticks={routine.map((d) => isDayComplete(log, d.day, cycle))}
          cycles={cycle}
          streak={streakFrom(log).current}
        />
        <Text style={styles.dayFocus}>{dayTitle(day).toUpperCase()}</Text>
        <Text style={styles.dayTitle}>Day {day.day}</Text>
        <Text style={styles.dayMeta}>
          {doneDrills} of {day.drills.length} drills  ·  about {day.totalMinutes} min  ·{' '}
          {doneCount} of {routine.length} days done
        </Text>

        {day.drills.map((d: Drill) => {
          const isOpen = open === d.id;
          const ticked = !!ticks[tickKey(cycle, day.day, d.id)];
          return (
            <TouchableOpacity
              key={d.id}
              style={[styles.card, ticked && styles.cardDone]}
              onPress={() => setOpen(isOpen ? null : d.id)}
              accessibilityRole="button"
            >
              <View style={styles.cardHead}>
                <TouchableOpacity
                  style={[styles.tick, ticked && styles.tickOn]}
                  onPress={() => toggleTick(d.id)}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: ticked }}
                  accessibilityLabel={`Mark ${d.name} done`}
                  hitSlop={8}
                >
                  {ticked ? <Text style={styles.tickMark}>✓</Text> : null}
                </TouchableOpacity>
                <View style={styles.cardText}>
                  <Text style={[styles.name, ticked && styles.nameDone]}>{d.name}</Text>
                  <Text style={styles.work}>{d.work}  ·  ~{estimateMinutes(d)} min</Text>
                </View>
              </View>
              {isOpen && (
                <View style={styles.detail}>
                  {d.setup ? <Text style={styles.setup}>Set up: {d.setup}</Text> : null}
                  {d.how.map((line, i) => (
                    <View key={i} style={styles.stepRow}>
                      <Text style={styles.stepNum}>{i + 1}</Text>
                      <Text style={styles.stepText}>{line}</Text>
                    </View>
                  ))}
                  <Text style={styles.cue}>{d.cue}</Text>
                  <DrillTimer
                    minutes={estimateMinutes(d)}
                    onComplete={() => { if (!ticked) toggleTick(d.id); }}
                  />
                </View>
              )}
            </TouchableOpacity>
          );
        })}

        <TouchableOpacity
          style={[styles.cta, done && styles.ctaDone]}
          onPress={toggleComplete}
          accessibilityRole="button"
        >
          <Text style={[styles.ctaText, done && styles.ctaTextDone]}>
            {done ? '✓  Completed' : 'Mark day complete'}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {summary ? (
        <SessionSummary visible {...summary} onClose={() => setSummary(null)} />
      ) : null}
    </View>
  );
}

const wrap = { maxWidth: 560, width: '100%', alignSelf: 'center' } as const;

const makeStyles = (p: Palette) =>
  StyleSheet.create({
  root: { flex: 1, backgroundColor: p.bg },
  header: {
    ...wrap, flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 24, paddingTop: 20,
  },
  brand: { fontSize: 13, fontWeight: '800', letterSpacing: 2, color: p.fg },
  headerLink: { fontSize: 14, fontWeight: '700', color: p.muted },
  pillsRow: { ...wrap, flexGrow: 0, flexShrink: 0, paddingHorizontal: 18, paddingTop: 14 },
  pills: { gap: 8, alignItems: 'center' },
  pill: {
    borderRadius: 999, backgroundColor: p.raised,
    paddingHorizontal: 18, paddingVertical: 10, marginRight: 8,
  },
  pillOn: { backgroundColor: p.accent },
  pillText: { fontSize: 14, fontWeight: '700', color: p.muted },
  pillTextOn: { color: p.onAccent },
  body: { ...wrap, paddingHorizontal: 24, paddingBottom: 40, paddingTop: 18 },
  dayFocus: { fontSize: 11, fontWeight: '800', letterSpacing: 1.6, color: p.muted },
  dayTitle: {
    fontSize: 40, lineHeight: 44, fontWeight: '800',
    color: p.fg, letterSpacing: -1.6, marginTop: 2,
  },
  dayMeta: { fontSize: 14, color: p.muted, marginTop: 4, marginBottom: 20 },
  card: {
    backgroundColor: p.raised, borderRadius: p.radius,
    padding: 18, marginBottom: 12,
  },
  cardDone: { opacity: 0.65 },
  cardHead: { flexDirection: 'row', alignItems: 'flex-start' },
  cardText: { flex: 1 },
  tick: {
    width: 26, height: 26, borderRadius: 13, borderWidth: 2, borderColor: p.line,
    marginRight: 14, alignItems: 'center', justifyContent: 'center', marginTop: 1,
  },
  tickOn: { backgroundColor: p.accent, borderColor: p.accent },
  tickMark: { color: p.onAccent, fontSize: 14, fontWeight: '800' },
  name: { fontSize: 17, fontWeight: '700', color: p.fg },
  nameDone: { color: p.muted, textDecorationLine: 'line-through' },
  work: { fontSize: 14, color: p.muted, marginTop: 3 },
  detail: { marginTop: 14, borderTopWidth: 1, borderTopColor: p.line, paddingTop: 14 },
  setup: { fontSize: 14, color: p.muted, marginBottom: 10, fontStyle: 'italic' },
  stepRow: { flexDirection: 'row', marginBottom: 8 },
  stepNum: { width: 20, fontSize: 13, fontWeight: '800', color: p.muted, marginTop: 1 },
  stepText: { flex: 1, fontSize: 15, color: p.fg, lineHeight: 21 },
  cue: {
    marginTop: 8, fontSize: 14, fontWeight: '700', color: p.fg,
    backgroundColor: p.bg, padding: 12, borderRadius: 10, lineHeight: 20,
  },
  cta: {
    marginTop: 10, backgroundColor: p.accent,
    borderRadius: p.radius, paddingVertical: 17, alignItems: 'center',
  },
  ctaDone: { backgroundColor: p.bg, borderWidth: 2, borderColor: p.accent },
  ctaText: { color: p.onAccent, fontSize: 16, fontWeight: '700' },
  ctaTextDone: { color: p.fg },
  });
