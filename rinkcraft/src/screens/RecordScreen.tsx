import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { LogEntry, loadCycle, loadLog } from '../storage';
import { Palette, useTheme } from '../theme';

export default function RecordScreen() {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [log, setLog] = useState<LogEntry[]>([]);
  const [cycle, setCycle] = useState(0);

  useEffect(() => {
    (async () => {
      const [l, c] = await Promise.all([loadLog(), loadCycle()]);
      setLog(l);
      setCycle(c);
    })();
  }, []);

  // Newest first, and grouped so a week's worth reads together.
  const sorted = useMemo(
    () => [...log].sort((a, b) => (a.date === b.date ? b.day - a.day : b.date.localeCompare(a.date))),
    [log],
  );

  const distinctDates = useMemo(
    () => Array.from(new Set(log.map((e) => e.date))).sort().reverse(),
    [log],
  );

  return (
    <ScrollView style={s.root} contentContainerStyle={s.scroll}>
      <Text style={s.title}>Record</Text>

      <View style={s.stats}>
        <View style={s.stat}>
          <Text style={s.statNum}>{log.length}</Text>
          <Text style={s.statLabel}>sessions done</Text>
        </View>
        <View style={s.stat}>
          <Text style={s.statNum}>{cycle}</Text>
          <Text style={s.statLabel}>weeks banked</Text>
        </View>
        <View style={s.stat}>
          <Text style={s.statNum}>{distinctDates.length}</Text>
          <Text style={s.statLabel}>days trained</Text>
        </View>
      </View>

      {sorted.length === 0 ? (
        <Text style={s.empty}>
          Nothing logged yet. Finish a day on the Plan tab and it shows up here.
        </Text>
      ) : (
        <>
          <Text style={s.section}>HISTORY</Text>
          {sorted.map((e, i) => (
            <View key={`${e.cycle}-${e.day}-${i}`} style={s.row}>
              <View>
                <Text style={s.rowTitle}>Day {e.day}</Text>
                <Text style={s.rowMeta}>Week {e.cycle + 1}</Text>
              </View>
              <Text style={s.rowDate}>{new Date(e.date).toLocaleDateString()}</Text>
            </View>
          ))}
        </>
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
    section: {
      fontSize: 11, fontWeight: '800', letterSpacing: 1.6,
      color: p.faint, marginTop: 30, marginBottom: 12,
    },
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
