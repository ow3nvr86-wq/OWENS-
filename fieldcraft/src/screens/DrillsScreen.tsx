import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { DRILLS, Drill, Equipment, Focus } from '../content/drills';
import { QUIZ } from '../content/quiz';
import { Profile } from '../storage';
import { theme } from '../theme';

type Props = { profile: Profile };

// How much kit each level unlocks. A player with a field and weights can run
// everything below it; someone with only open space cannot run ball drills.
const EQUIPMENT_RANK: Record<Equipment, number> = { none: 0, ball: 1, cones: 2, gym: 3 };

const FOCUS_LABELS = Object.fromEntries(
  (QUIZ.find((s) => s.key === 'focus')?.options ?? []).map((o) => [o.value, o.label]),
) as Record<string, string>;

export default function DrillsScreen({ profile }: Props) {
  const chosenFocus = Array.isArray(profile.focus) ? (profile.focus as string[]) : [];
  const [filter, setFilter] = useState<string>(chosenFocus[0] ?? 'all');
  const [open, setOpen] = useState<string | null>(null);

  const owned = EQUIPMENT_RANK[(profile.equipment as Equipment) ?? 'none'] ?? 0;
  const positions = Array.isArray(profile.positions) ? (profile.positions as string[]) : [];

  // Only show what this player can actually run today.
  const available = useMemo(
    () => DRILLS.filter((d) => EQUIPMENT_RANK[d.equipment] <= owned),
    [owned],
  );

  const shown = useMemo(() => {
    const byFocus = filter === 'all' ? available : available.filter((d) => d.focus === filter);
    // Put drills matching the player's position first, without hiding the rest.
    return [...byFocus].sort((a, b) => rank(a) - rank(b));
    function rank(d: Drill) {
      if (d.positions.includes('all')) return 1;
      return d.positions.some((p) => positions.includes(p)) ? 0 : 2;
    }
  }, [available, filter, positions]);

  const tabs = ['all', ...chosenFocus, ...uniqueRest(chosenFocus)];

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.brand}>FIELDCRAFT</Text>
        <Text style={styles.count}>{shown.length} drills</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabRow}>
        {tabs.map((t) => (
          <TouchableOpacity
            key={t}
            style={[styles.tab, filter === t && styles.tabOn]}
            onPress={() => setFilter(t)}
            accessibilityRole="button"
          >
            <Text style={[styles.tabText, filter === t && styles.tabTextOn]}>
              {t === 'all' ? 'All' : FOCUS_LABELS[t] ?? t}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView contentContainerStyle={styles.list}>
        {shown.length === 0 && (
          <Text style={styles.empty}>
            Nothing here needs only the kit you have. Change your equipment in setup.
          </Text>
        )}

        {shown.map((d) => {
          const isOpen = open === d.id;
          return (
            <TouchableOpacity
              key={d.id}
              style={styles.card}
              onPress={() => setOpen(isOpen ? null : d.id)}
              accessibilityRole="button"
            >
              <Text style={styles.name}>{d.name}</Text>
              <Text style={styles.work}>{d.work}</Text>

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
      </ScrollView>
    </View>
  );
}

/** Focus areas the player did not pick, so the whole library stays reachable. */
function uniqueRest(chosen: string[]) {
  const all = Array.from(new Set(DRILLS.map((d) => d.focus))) as Focus[];
  return all.filter((f) => !chosen.includes(f));
}

const wrap = { maxWidth: 560, width: '100%', alignSelf: 'center' } as const;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.bg },
  header: {
    ...wrap, flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 24, paddingTop: 20,
  },
  brand: { fontSize: 13, fontWeight: '800', letterSpacing: 2, color: theme.fg },
  count: { fontSize: 13, fontWeight: '700', color: theme.muted },
  tabRow: { ...wrap, flexGrow: 0, paddingHorizontal: 18, paddingTop: 14 },
  tab: {
    paddingHorizontal: 14, paddingVertical: 8, marginHorizontal: 5,
    borderRadius: 20, backgroundColor: theme.fill,
  },
  tabOn: { backgroundColor: theme.accent },
  tabText: { fontSize: 13, fontWeight: '700', color: theme.muted },
  tabTextOn: { color: theme.onAccent },
  list: { ...wrap, padding: 24, paddingTop: 16 },
  empty: { color: theme.muted, fontSize: 15, lineHeight: 22 },
  card: {
    backgroundColor: theme.fill, borderRadius: theme.radius,
    padding: 18, marginBottom: 12,
  },
  name: { fontSize: 17, fontWeight: '700', color: theme.fg },
  work: { fontSize: 14, color: theme.muted, marginTop: 3 },
  detail: { marginTop: 14, borderTopWidth: 1, borderTopColor: theme.line, paddingTop: 14 },
  setup: { fontSize: 14, color: theme.muted, marginBottom: 10, fontStyle: 'italic' },
  stepRow: { flexDirection: 'row', marginBottom: 8 },
  stepNum: {
    width: 20, fontSize: 13, fontWeight: '800', color: theme.muted, marginTop: 1,
  },
  stepText: { flex: 1, fontSize: 15, color: theme.fg, lineHeight: 21 },
  cue: {
    marginTop: 8, fontSize: 14, fontWeight: '700', color: theme.fg,
    backgroundColor: theme.bg, padding: 12, borderRadius: 10, lineHeight: 20,
  },
});
