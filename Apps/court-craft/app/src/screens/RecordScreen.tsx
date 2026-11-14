import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { LogEntry, loadCycle, loadLog } from '../storage';
import { badgesFrom, dayKey, monthGrid, streakFrom, trainedDates } from '../progress';
import { Palette, useTheme } from '../theme';

const WEEKDAYS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export default function RecordScreen() {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [log, setLog] = useState<LogEntry[]>([]);
  const [cycle, setCycle] = useState(0);

  const now = new Date();
  const [view, setView] = useState({ year: now.getUTCFullYear(), month: now.getUTCMonth() });

  useEffect(() => {
    (async () => {
      const [l, c] = await Promise.all([loadLog(), loadCycle()]);
      setLog(l);
      setCycle(c);
    })();
  }, []);

  const streak = useMemo(() => streakFrom(log), [log]);
  const badges = useMemo(() => badgesFrom({ log, cycle, streak }), [log, cycle, streak]);
  const trained = useMemo(() => new Set(trainedDates(log)), [log]);
  const cells = useMemo(() => monthGrid(view.year, view.month), [view]);
  const today = dayKey(new Date());

  const sorted = useMemo(
    () => [...log].sort((a, b) => (a.date === b.date ? b.day - a.day : b.date.localeCompare(a.date))),
    [log],
  );

  // How many sessions fall inside the month on screen.
  const monthCount = cells.filter((c) => c && trained.has(c)).length;

  function shift(by: number) {
    setView(({ year, month }) => {
      const m = month + by;
      if (m < 0) return { year: year - 1, month: 11 };
      if (m > 11) return { year: year + 1, month: 0 };
      return { year, month: m };
    });
  }

  const earned = badges.filter((b) => b.earned).length;

  return (
    <ScrollView style={s.root} contentContainerStyle={s.scroll}>
      <Text style={s.title}>Record</Text>

      <View style={s.stats}>
        <View style={s.stat}>
          <Text style={s.statNum}>{streak.current}</Text>
          <Text style={s.statLabel}>day streak</Text>
        </View>
        <View style={s.stat}>
          <Text style={s.statNum}>{log.length}</Text>
          <Text style={s.statLabel}>sessions</Text>
        </View>
        <View style={s.stat}>
          <Text style={s.statNum}>{cycle}</Text>
          <Text style={s.statLabel}>weeks banked</Text>
        </View>
      </View>
      {streak.longest > 0 ? (
        <Text style={s.note}>
          Longest run so far: {streak.longest}. A single rest day keeps a streak alive.
        </Text>
      ) : null}

      <Text style={s.section}>CALENDAR</Text>
      <View style={s.calCard}>
        <View style={s.calHead}>
          <TouchableOpacity onPress={() => shift(-1)} hitSlop={14} accessibilityRole="button"
            accessibilityLabel="Previous month">
            <Text style={s.arrow}>‹</Text>
          </TouchableOpacity>
          <View style={s.calTitleWrap}>
            <Text style={s.calTitle}>{MONTHS[view.month]} {view.year}</Text>
            <Text style={s.calSub}>{monthCount} {monthCount === 1 ? 'day' : 'days'} trained</Text>
          </View>
          <TouchableOpacity onPress={() => shift(1)} hitSlop={14} accessibilityRole="button"
            accessibilityLabel="Next month">
            <Text style={s.arrow}>›</Text>
          </TouchableOpacity>
        </View>

        <View style={s.weekRow}>
          {WEEKDAYS.map((d, i) => (
            <Text key={i} style={s.weekday}>{d}</Text>
          ))}
        </View>

        <View style={s.grid}>
          {cells.map((cell, i) => {
            if (!cell) return <View key={i} style={s.cell} />;
            const on = trained.has(cell);
            const isToday = cell === today;
            return (
              <View key={i} style={s.cell}>
                <View style={[s.dot, on && s.dotOn, isToday && !on && s.dotToday]}>
                  <Text style={[s.dotText, on && s.dotTextOn]}>
                    {Number(cell.slice(8, 10))}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>
      </View>

      <Text style={s.section}>BADGES  ·  {earned} of {badges.length}</Text>
      <View style={s.badges}>
        {badges.map((b) => (
          <View key={b.id} style={[s.badge, b.earned && s.badgeOn]}>
            <Text style={[s.badgeName, b.earned && s.badgeNameOn]}>{b.name}</Text>
            <Text style={s.badgeDetail}>{b.detail}</Text>
          </View>
        ))}
      </View>

      {sorted.length > 0 ? (
        <>
          <Text style={s.section}>HISTORY</Text>
          {sorted.slice(0, 40).map((e, i) => (
            <View key={`${e.cycle}-${e.day}-${i}`} style={s.row}>
              <View>
                <Text style={s.rowTitle}>Day {e.day}</Text>
                <Text style={s.rowMeta}>Week {e.cycle + 1}</Text>
              </View>
              <Text style={s.rowDate}>{new Date(e.date).toLocaleDateString()}</Text>
            </View>
          ))}
        </>
      ) : (
        <Text style={s.empty}>
          Nothing logged yet. Finish a day on the Plan tab and it shows up here.
        </Text>
      )}
    </ScrollView>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    root: { flex: 1, backgroundColor: p.bg },
    scroll: { padding: 24, paddingBottom: 60, maxWidth: 560, width: '100%', alignSelf: 'center' },
    title: { fontSize: 34, fontWeight: '800', color: p.fg, letterSpacing: -1.2, marginBottom: 20 },
    stats: { flexDirection: 'row', gap: 10 },
    stat: {
      flex: 1, backgroundColor: p.surface, borderRadius: p.radius,
      borderWidth: 1, borderColor: p.line, padding: 16,
    },
    statNum: { fontSize: 30, fontWeight: '800', color: p.fg, letterSpacing: -1 },
    statLabel: { fontSize: 12, color: p.muted, marginTop: 2 },
    note: { fontSize: 13, color: p.muted, marginTop: 12, lineHeight: 19 },
    section: {
      fontSize: 11, fontWeight: '800', letterSpacing: 1.6,
      color: p.faint, marginTop: 30, marginBottom: 12,
    },
    calCard: {
      backgroundColor: p.surface, borderRadius: p.radiusLg,
      borderWidth: 1, borderColor: p.line, padding: 16,
    },
    calHead: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    calTitleWrap: { alignItems: 'center' },
    calTitle: { fontSize: 17, fontWeight: '700', color: p.fg },
    calSub: { fontSize: 12, color: p.muted, marginTop: 1 },
    arrow: { fontSize: 26, fontWeight: '700', color: p.muted, paddingHorizontal: 10 },
    weekRow: { flexDirection: 'row', marginTop: 16, marginBottom: 6 },
    weekday: {
      flex: 1, textAlign: 'center', fontSize: 11,
      fontWeight: '800', color: p.faint, letterSpacing: .5,
    },
    grid: { flexDirection: 'row', flexWrap: 'wrap' },
    cell: { width: `${100 / 7}%`, aspectRatio: 1, alignItems: 'center', justifyContent: 'center' },
    dot: {
      width: 34, height: 34, borderRadius: 17,
      alignItems: 'center', justifyContent: 'center',
      borderWidth: 2, borderColor: 'transparent',
    },
    dotOn: { backgroundColor: p.accent },
    dotToday: { borderColor: p.muted },
    dotText: { fontSize: 13, color: p.muted, fontWeight: '600' },
    dotTextOn: { color: p.onAccent, fontWeight: '800' },
    badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
    badge: {
      width: '47.5%', backgroundColor: p.surface, borderRadius: p.radius,
      borderWidth: 1, borderColor: p.line, padding: 14, opacity: .55,
    },
    badgeOn: { opacity: 1, borderColor: p.accent },
    badgeName: { fontSize: 14, fontWeight: '700', color: p.muted },
    badgeNameOn: { color: p.fg },
    badgeDetail: { fontSize: 11, color: p.faint, marginTop: 3, lineHeight: 15 },
    empty: { fontSize: 15, color: p.muted, lineHeight: 22, marginTop: 24 },
    row: {
      flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
      backgroundColor: p.surface, borderRadius: p.radius, borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 14, marginBottom: 8,
    },
    rowTitle: { fontSize: 16, fontWeight: '700', color: p.fg },
    rowMeta: { fontSize: 12, color: p.muted, marginTop: 2 },
    rowDate: { fontSize: 13, color: p.muted },
  });
