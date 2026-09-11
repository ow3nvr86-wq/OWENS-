import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { ACCENTS, AccentId, Mode, Palette, useTheme } from '../theme';

type Props = {
  name?: string;
  onReadSafety: () => void;
  onRedoSetup: () => void;
};

const MODES: { id: Mode; label: string }[] = [
  { id: 'system', label: 'Automatic' },
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
];

export default function SettingsScreen({ name, onReadSafety, onRedoSetup }: Props) {
  const { palette, mode, accent, setMode, setAccent } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  return (
    <ScrollView style={s.root} contentContainerStyle={s.scroll}>
      <Text style={s.title}>Settings</Text>
      {name ? <Text style={s.hello}>Signed in as {name}</Text> : null}

      <Text style={s.section}>APPEARANCE</Text>
      <View style={s.segment}>
        {MODES.map((m) => (
          <TouchableOpacity
            key={m.id}
            style={[s.segmentItem, mode === m.id && s.segmentItemOn]}
            onPress={() => setMode(m.id)}
            accessibilityRole="button"
            accessibilityState={{ selected: mode === m.id }}
          >
            <Text style={[s.segmentText, mode === m.id && s.segmentTextOn]}>{m.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text style={s.note}>
        Automatic follows whatever your phone is set to.
      </Text>

      <Text style={s.section}>COLOUR</Text>
      <View style={s.swatches}>
        {ACCENTS.map((a) => (
          <TouchableOpacity
            key={a.id}
            onPress={() => setAccent(a.id as AccentId)}
            accessibilityRole="button"
            accessibilityLabel={a.label}
            accessibilityState={{ selected: accent === a.id }}
            style={s.swatchWrap}
          >
            <View
              style={[
                s.swatch,
                { backgroundColor: a.light },
                accent === a.id && { borderColor: palette.fg, borderWidth: 3 },
              ]}
            />
            <Text style={[s.swatchLabel, accent === a.id && s.swatchLabelOn]}>{a.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={s.section}>SAFETY</Text>
      <TouchableOpacity style={s.link} onPress={onReadSafety} accessibilityRole="button">
        <Text style={s.linkText}>Read the safety notes again</Text>
      </TouchableOpacity>
      <TouchableOpacity style={s.link} onPress={onRedoSetup} accessibilityRole="button">
        <Text style={s.linkText}>Change my training setup</Text>
      </TouchableOpacity>

      <Text style={s.section}>PRIVACY</Text>
      <Text style={s.note}>
        Everything Fieldcraft knows about you is stored on this phone only. There are no
        accounts, no tracking and no advertising. Deleting the app deletes it all.
      </Text>
    </ScrollView>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    root: { flex: 1, backgroundColor: p.bg },
    scroll: { padding: 24, paddingBottom: 60, maxWidth: 560, width: '100%', alignSelf: 'center' },
    title: { fontSize: 34, fontWeight: '800', color: p.fg, letterSpacing: -1.2 },
    hello: { fontSize: 14, color: p.muted, marginTop: 4 },
    section: {
      fontSize: 11, fontWeight: '800', letterSpacing: 1.6,
      color: p.faint, marginTop: 30, marginBottom: 12,
    },
    segment: { flexDirection: 'row', backgroundColor: p.raised, borderRadius: p.radius, padding: 4 },
    segmentItem: { flex: 1, paddingVertical: 11, borderRadius: p.radius - 4, alignItems: 'center' },
    segmentItemOn: { backgroundColor: p.accent },
    segmentText: { fontSize: 14, fontWeight: '700', color: p.muted },
    segmentTextOn: { color: p.onAccent },
    note: { fontSize: 13, color: p.muted, marginTop: 10, lineHeight: 20 },
    swatches: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 },
    swatchWrap: { alignItems: 'center', width: 64 },
    swatch: { width: 44, height: 44, borderRadius: 22, borderWidth: 0, borderColor: 'transparent' },
    swatchLabel: { fontSize: 11, color: p.muted, marginTop: 6 },
    swatchLabelOn: { color: p.fg, fontWeight: '700' },
    link: {
      backgroundColor: p.surface, borderRadius: p.radius, borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 16, marginBottom: 10,
    },
    linkText: { fontSize: 15, fontWeight: '600', color: p.fg },
  });
