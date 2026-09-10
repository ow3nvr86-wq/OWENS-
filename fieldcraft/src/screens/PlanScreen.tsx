import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Drill } from '../content/drills';
import { RoutineDay, buildRoutine, dayTitle, estimateMinutes } from '../routine';
import {
  LogEntry, Profile, isDayComplete, loadCycle, loadLog,
  saveCycle, saveLog, todayKey,
} from '../storage';
import { theme } from '../theme';

type Props = { profile: Profile; onOpenLibrary: () => void };

export default function PlanScreen({ profile, onOpenLibrary }: Props) {
  const routine = useMemo(() => buildRoutine(profile), [profile]);
  const [selected, setSelected] = useState(0);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [cycle, setCycle] = useState(0);
  const [open, setOpen] = useState<string | null>(null);
  const bodyRef = useRef<ScrollView>(null);

  useEffect(() => {
    (async () => {
      const [storedLog, storedCycle] = await Promise.all([loadLog(), loadCycle()]);
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

  async function toggleComplete() {
    if (!day) return;
    let nextLog: LogEntry[];
    if (done) {
      nextLog = log.filter((e) => !(e.day === day.day && e.cycle === cycle));
    } else {
      nextLog = [...log, { date: todayKey(), day: day.day, cycle }];
    }
    setLog(nextLog);
    await saveLog(nextLog);

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
        <Text style={styles.brand}>FIELDCRAFT</Text>
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
        <Text style={styles.dayFocus}>{dayTitle(day).toUpperCase()}</Text>
        <Text style={styles.dayTitle}>Day {day.day}</Text>
        <Text style={styles.dayMeta}>
          {day.drills.length} drills  ·  about {day.totalMinutes} min  ·  {doneCount} of{' '}
          {routine.length} days done
        </Text>

        {day.drills.map((d: Drill) => {
          const isOpen = open === d.id;
          return (
            <TouchableOpacity
              key={d.id}
              style={styles.card}
              onPress={() => setOpen(isOpen ? null : d.id)}
              accessibilityRole="button"
            >
              <Text style={styles.name}>{d.name}</Text>
              <Text style={styles.work}>{d.work}  ·  ~{estimateMinutes(d)} min</Text>
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
    </View>
  );
}

const wrap = { maxWidth: 560, width: '100%', alignSelf: 'center' } as const;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.bg },
  header: {
    ...wrap, flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 24, paddingTop: 20,
  },
  brand: { fontSize: 13, fontWeight: '800', letterSpacing: 2, color: theme.fg },
  headerLink: { fontSize: 14, fontWeight: '700', color: theme.muted },
  pillsRow: { ...wrap, flexGrow: 0, flexShrink: 0, paddingHorizontal: 18, paddingTop: 14 },
  pills: { gap: 8, alignItems: 'center' },
  pill: {
    borderRadius: 999, backgroundColor: theme.fill,
    paddingHorizontal: 18, paddingVertical: 10, marginRight: 8,
  },
  pillOn: { backgroundColor: theme.accent },
  pillText: { fontSize: 14, fontWeight: '700', color: theme.muted },
  pillTextOn: { color: theme.onAccent },
  body: { ...wrap, paddingHorizontal: 24, paddingBottom: 40, paddingTop: 18 },
  dayFocus: { fontSize: 11, fontWeight: '800', letterSpacing: 1.6, color: theme.muted },
  dayTitle: {
    fontSize: 40, lineHeight: 44, fontWeight: '800',
    color: theme.fg, letterSpacing: -1.6, marginTop: 2,
  },
  dayMeta: { fontSize: 14, color: theme.muted, marginTop: 4, marginBottom: 20 },
  card: {
    backgroundColor: theme.fill, borderRadius: theme.radius,
    padding: 18, marginBottom: 12,
  },
  name: { fontSize: 17, fontWeight: '700', color: theme.fg },
  work: { fontSize: 14, color: theme.muted, marginTop: 3 },
  detail: { marginTop: 14, borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 14 },
  setup: { fontSize: 14, color: theme.muted, marginBottom: 10, fontStyle: 'italic' },
  stepRow: { flexDirection: 'row', marginBottom: 8 },
  stepNum: { width: 20, fontSize: 13, fontWeight: '800', color: theme.muted, marginTop: 1 },
  stepText: { flex: 1, fontSize: 15, color: theme.fg, lineHeight: 21 },
  cue: {
    marginTop: 8, fontSize: 14, fontWeight: '700', color: theme.fg,
    backgroundColor: theme.bg, padding: 12, borderRadius: 10, lineHeight: 20,
  },
  cta: {
    marginTop: 10, backgroundColor: theme.accent,
    borderRadius: theme.radius, paddingVertical: 17, alignItems: 'center',
  },
  ctaDone: { backgroundColor: theme.bg, borderWidth: 2, borderColor: theme.accent },
  ctaText: { color: theme.onAccent, fontSize: 16, fontWeight: '700' },
  ctaTextDone: { color: theme.fg },
});
