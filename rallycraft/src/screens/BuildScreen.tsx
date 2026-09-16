import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { DRILLS, Drill, Equipment } from '../content/drills';
import { FOCUS_LABELS, estimateMinutes } from '../routine';
import { CustomWorkout, Profile, loadWorkouts, saveWorkouts } from '../storage';
import DrillTimer from '../components/DrillTimer';
import { Palette, useTheme } from '../theme';

type Props = { profile: Profile };
type Mode = { kind: 'list' } | { kind: 'edit'; draft: CustomWorkout } | { kind: 'run'; id: string };

const EQUIPMENT_RANK: Record<Equipment, number> = { none: 0, ball: 1, wall: 2, net: 3, gym: 4 };

export default function BuildScreen({ profile }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [workouts, setWorkouts] = useState<CustomWorkout[]>([]);
  const [mode, setMode] = useState<Mode>({ kind: 'list' });
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => { loadWorkouts().then(setWorkouts); }, []);

  const owned = EQUIPMENT_RANK[(profile.equipment as Equipment) ?? 'none'] ?? 0;
  const usable = useMemo(
    () => DRILLS.filter((d) => EQUIPMENT_RANK[d.equipment] <= owned),
    [owned],
  );

  // Drills grouped by focus, so the picker reads like the library rather than
  // one long undifferentiated list.
  const grouped = useMemo(() => {
    const out: Record<string, Drill[]> = {};
    for (const d of usable) (out[d.focus] ||= []).push(d);
    return out;
  }, [usable]);

  async function persist(next: CustomWorkout[]) {
    setWorkouts(next);
    await saveWorkouts(next);
  }

  function startNew() {
    setMode({
      kind: 'edit',
      draft: { id: String(Date.now()), name: '', drillIds: [], createdAt: new Date().toISOString() },
    });
  }

  // ---------------------------------------------------------------- editing
  if (mode.kind === 'edit') {
    const { draft } = mode;
    const chosen = draft.drillIds;
    const minutes = chosen.reduce((sum, id) => {
      const d = DRILLS.find((x) => x.id === id);
      return sum + (d ? estimateMinutes(d) : 0);
    }, 0);
    const canSave = draft.name.trim().length > 0 && chosen.length > 0;

    const toggle = (id: string) =>
      setMode({
        kind: 'edit',
        draft: {
          ...draft,
          drillIds: chosen.includes(id) ? chosen.filter((x) => x !== id) : [...chosen, id],
        },
      });

    return (
      <View style={s.root}>
        <ScrollView contentContainerStyle={s.scroll}>
          <Text style={s.title}>New workout</Text>
          <TextInput
            style={s.input}
            placeholder="Name it. Shooting night, pre season, anything."
            placeholderTextColor={palette.faint}
            value={draft.name}
            onChangeText={(name) => setMode({ kind: 'edit', draft: { ...draft, name } })}
          />
          <Text style={s.meta}>
            {chosen.length} {chosen.length === 1 ? 'drill' : 'drills'} · about {minutes} min
          </Text>

          {Object.keys(grouped).map((focus) => (
            <View key={focus}>
              <Text style={s.section}>{(FOCUS_LABELS[focus] ?? focus).toUpperCase()}</Text>
              {grouped[focus].map((d) => {
                const on = chosen.includes(d.id);
                return (
                  <TouchableOpacity
                    key={d.id}
                    style={[s.pick, on && s.pickOn]}
                    onPress={() => toggle(d.id)}
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: on }}
                  >
                    <View style={[s.box, on && s.boxOn]}>
                      {on ? <Text style={s.boxTick}>✓</Text> : null}
                    </View>
                    <View style={s.pickText}>
                      <Text style={s.pickName}>{d.name}</Text>
                      <Text style={s.pickWork}>{d.work} · ~{estimateMinutes(d)} min</Text>
                    </View>
                  </TouchableOpacity>
                );
              })}
            </View>
          ))}
        </ScrollView>

        <View style={s.footer}>
          <TouchableOpacity
            style={[s.cta, !canSave && s.ctaOff]}
            disabled={!canSave}
            onPress={async () => {
              await persist([...workouts.filter((w) => w.id !== draft.id), { ...draft, name: draft.name.trim() }]);
              setMode({ kind: 'list' });
            }}
            accessibilityRole="button"
          >
            <Text style={[s.ctaText, !canSave && s.ctaTextOff]}>
              {canSave ? 'Save workout' : 'Name it and pick a drill'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setMode({ kind: 'list' })} accessibilityRole="button">
            <Text style={s.cancel}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // ---------------------------------------------------------------- running
  if (mode.kind === 'run') {
    const workout = workouts.find((w) => w.id === mode.id);
    if (!workout) { setMode({ kind: 'list' }); return <View style={s.root} />; }
    const drills = workout.drillIds
      .map((id) => DRILLS.find((d) => d.id === id))
      .filter(Boolean) as Drill[];
    const total = drills.reduce((n, d) => n + estimateMinutes(d), 0);

    return (
      <ScrollView style={s.root} contentContainerStyle={s.scroll}>
        <TouchableOpacity onPress={() => setMode({ kind: 'list' })} accessibilityRole="button">
          <Text style={s.back}>‹ All workouts</Text>
        </TouchableOpacity>
        <Text style={s.title}>{workout.name}</Text>
        <Text style={s.meta}>{drills.length} drills · about {total} min</Text>

        {drills.map((d) => {
          const isOpen = open === d.id;
          return (
            <TouchableOpacity
              key={d.id}
              style={s.card}
              onPress={() => setOpen(isOpen ? null : d.id)}
              accessibilityRole="button"
            >
              <Text style={s.cardName}>{d.name}</Text>
              <Text style={s.cardWork}>{d.work} · ~{estimateMinutes(d)} min</Text>
              {isOpen && (
                <View style={s.detail}>
                  {d.cue ? <Text style={s.cue}>{d.cue}</Text> : null}
                  <DrillTimer minutes={estimateMinutes(d)} />
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    );
  }

  // ------------------------------------------------------------------- list
  return (
    <View style={s.root}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.title}>Build</Text>
        <Text style={s.lede}>
          Make your own session out of any drills you can run with the kit you have.
        </Text>

        {workouts.length === 0 ? (
          <Text style={s.empty}>
            No workouts yet. Build one and it stays on this phone, ready whenever you want it.
          </Text>
        ) : (
          workouts.map((w) => {
            const drills = w.drillIds
              .map((id) => DRILLS.find((d) => d.id === id))
              .filter(Boolean) as Drill[];
            const total = drills.reduce((n, d) => n + estimateMinutes(d), 0);
            return (
              <View key={w.id} style={s.row}>
                <TouchableOpacity
                  style={s.rowMain}
                  onPress={() => { setOpen(null); setMode({ kind: 'run', id: w.id }); }}
                  accessibilityRole="button"
                >
                  <Text style={s.rowTitle}>{w.name}</Text>
                  <Text style={s.rowMeta}>{drills.length} drills · about {total} min</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => persist(workouts.filter((x) => x.id !== w.id))}
                  hitSlop={12}
                  accessibilityRole="button"
                  accessibilityLabel={`Delete ${w.name}`}
                >
                  <Text style={s.delete}>Delete</Text>
                </TouchableOpacity>
              </View>
            );
          })
        )}
      </ScrollView>

      <View style={s.footer}>
        <TouchableOpacity style={s.cta} onPress={startNew} accessibilityRole="button">
          <Text style={s.ctaText}>Build a workout</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    root: { flex: 1, backgroundColor: p.bg },
    scroll: { padding: 24, paddingBottom: 30, maxWidth: 560, width: '100%', alignSelf: 'center' },
    title: { fontSize: 34, fontWeight: '800', color: p.fg, letterSpacing: -1.2 },
    lede: { fontSize: 15, color: p.muted, marginTop: 6, marginBottom: 20, lineHeight: 22 },
    back: { fontSize: 14, fontWeight: '700', color: p.muted, marginBottom: 12 },
    meta: { fontSize: 14, color: p.muted, marginTop: 8, marginBottom: 14 },
    empty: { fontSize: 15, color: p.muted, lineHeight: 22, marginTop: 20 },
    input: {
      marginTop: 18, backgroundColor: p.surface, borderRadius: p.radius,
      borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 16, fontSize: 16, color: p.fg,
    },
    section: {
      fontSize: 11, fontWeight: '800', letterSpacing: 1.6,
      color: p.faint, marginTop: 24, marginBottom: 10,
    },
    pick: {
      flexDirection: 'row', alignItems: 'center',
      backgroundColor: p.surface, borderRadius: p.radius,
      borderWidth: 2, borderColor: 'transparent',
      paddingHorizontal: 16, paddingVertical: 14, marginBottom: 8,
    },
    pickOn: { borderColor: p.accent },
    box: {
      width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: p.line,
      marginRight: 14, alignItems: 'center', justifyContent: 'center',
    },
    boxOn: { backgroundColor: p.accent, borderColor: p.accent },
    boxTick: { color: p.onAccent, fontSize: 12, fontWeight: '800' },
    pickText: { flex: 1 },
    pickName: { fontSize: 15, fontWeight: '700', color: p.fg },
    pickWork: { fontSize: 12, color: p.muted, marginTop: 2 },
    row: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      backgroundColor: p.surface, borderRadius: p.radius, borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 16, marginBottom: 10,
    },
    rowMain: { flex: 1 },
    rowTitle: { fontSize: 17, fontWeight: '700', color: p.fg },
    rowMeta: { fontSize: 13, color: p.muted, marginTop: 2 },
    delete: { fontSize: 13, fontWeight: '700', color: p.faint, paddingLeft: 12 },
    card: {
      backgroundColor: p.raised, borderRadius: p.radius, padding: 18, marginBottom: 12,
    },
    cardName: { fontSize: 17, fontWeight: '700', color: p.fg },
    cardWork: { fontSize: 14, color: p.muted, marginTop: 3 },
    detail: { marginTop: 14, borderTopWidth: 1, borderTopColor: p.line, paddingTop: 14 },
    cue: {
      fontSize: 14, fontWeight: '700', color: p.fg,
      backgroundColor: p.bg, padding: 12, borderRadius: 10, lineHeight: 20,
    },
    footer: {
      padding: 24, paddingTop: 12, borderTopWidth: 1, borderTopColor: p.line,
      maxWidth: 560, width: '100%', alignSelf: 'center',
    },
    cta: {
      backgroundColor: p.accent, borderRadius: p.radius,
      paddingVertical: 17, alignItems: 'center',
    },
    ctaOff: { backgroundColor: p.raised },
    ctaText: { color: p.onAccent, fontSize: 16, fontWeight: '700' },
    ctaTextOff: { color: p.faint },
    cancel: { textAlign: 'center', color: p.muted, fontSize: 14, fontWeight: '600', marginTop: 12 },
  });
