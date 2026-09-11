import React, { useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { PRIVACY_SUMMARY, WARRANTY_SUMMARY } from '../content/disclaimer';
import HuePicker from '../components/HuePicker';
import { ACCENTS, AccentId, Mode, Palette, useTheme } from '../theme';
import { Agreement, loadAgreement, resetAll } from '../storage';

type Props = {
  name?: string;
  onReadSafety: () => void;
  onRedoSetup: () => void;
  onReset: () => void;
};

const MODES: { id: Mode; label: string }[] = [
  { id: 'system', label: 'Automatic' },
  { id: 'light', label: 'Light' },
  { id: 'dark', label: 'Dark' },
];

const APP_VERSION = '1.0.0';

export default function SettingsScreen({ name, onReadSafety, onRedoSetup, onReset }: Props) {
  const { palette, mode, accent, customHue, setMode, setAccent, setCustomHue } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [agreement, setAgreement] = useState<Agreement | null>(null);
  const [openPanel, setOpenPanel] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  useEffect(() => { loadAgreement().then(setAgreement); }, []);

  const panel = (id: string, label: string, body: string) => (
    <View key={id}>
      <TouchableOpacity
        style={s.link}
        onPress={() => setOpenPanel(openPanel === id ? null : id)}
        accessibilityRole="button"
      >
        <Text style={s.linkText}>{label}</Text>
        <Text style={s.chevron}>{openPanel === id ? '−' : '+'}</Text>
      </TouchableOpacity>
      {openPanel === id ? <Text style={s.panelBody}>{body}</Text> : null}
    </View>
  );

  return (
    <ScrollView style={s.root} contentContainerStyle={s.scroll}>
      <Text style={s.title}>Settings</Text>
      {name ? <Text style={s.hello}>Training as {name}</Text> : null}

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
      <Text style={s.note}>Automatic follows whatever your phone is set to.</Text>

      <Text style={s.section}>COLOUR</Text>
      <View style={s.swatches}>
        {ACCENTS.map((a) => {
          const on = customHue === null && accent === a.id;
          return (
            <TouchableOpacity
              key={a.id}
              onPress={() => setAccent(a.id as AccentId)}
              accessibilityRole="button"
              accessibilityLabel={a.label}
              accessibilityState={{ selected: on }}
              style={s.swatchWrap}
            >
              <View
                style={[
                  s.swatch,
                  { backgroundColor: a.light },
                  on && { borderColor: palette.fg, borderWidth: 3 },
                ]}
              />
              <Text style={[s.swatchLabel, on && s.swatchLabelOn]}>{a.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={s.picker}>
        <HuePicker hue={customHue} onChange={setCustomHue} />
      </View>

      <Text style={s.section}>TRAINING</Text>
      <TouchableOpacity style={s.link} onPress={onRedoSetup} accessibilityRole="button">
        <Text style={s.linkText}>Change my training setup</Text>
        <Text style={s.chevron}>›</Text>
      </TouchableOpacity>
      <Text style={s.note}>
        Redo the seven questions to change your position, focus, days a week or equipment.
      </Text>

      <Text style={s.section}>SAFETY AND LEGAL</Text>
      <TouchableOpacity style={s.link} onPress={onReadSafety} accessibilityRole="button">
        <Text style={s.linkText}>Read the safety notes again</Text>
        <Text style={s.chevron}>›</Text>
      </TouchableOpacity>
      {panel('privacy', 'Privacy', PRIVACY_SUMMARY)}
      {panel('terms', 'Terms and liability', WARRANTY_SUMMARY)}
      {panel(
        'agreement',
        'Your risk acknowledgement',
        agreement
          ? `Accepted by ${agreement.name ?? 'you'} on ${new Date(agreement.acceptedAt).toLocaleDateString()}. Version ${agreement.version}. This record is stored on this phone only.`
          : 'No acknowledgement recorded on this device yet.',
      )}

      <Text style={s.section}>ABOUT</Text>
      <View style={s.aboutRow}>
        <Text style={s.aboutKey}>Version</Text>
        <Text style={s.aboutVal}>{APP_VERSION}</Text>
      </View>
      <View style={s.aboutRow}>
        <Text style={s.aboutKey}>Account</Text>
        <Text style={s.aboutVal}>None needed</Text>
      </View>
      <View style={s.aboutRow}>
        <Text style={s.aboutKey}>Data sent off this phone</Text>
        <Text style={s.aboutVal}>None</Text>
      </View>

      <Text style={s.section}>RESET</Text>
      {confirmReset ? (
        <View>
          <Text style={s.warn}>
            This erases your setup, your training log and your acknowledgement. It cannot be
            undone.
          </Text>
          <TouchableOpacity
            style={s.danger}
            onPress={async () => { await resetAll(); onReset(); }}
            accessibilityRole="button"
          >
            <Text style={s.dangerText}>Yes, erase everything</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={s.link}
            onPress={() => setConfirmReset(false)}
            accessibilityRole="button"
          >
            <Text style={s.linkText}>Cancel</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity
          style={s.link}
          onPress={() => setConfirmReset(true)}
          accessibilityRole="button"
        >
          <Text style={s.linkText}>Erase all my data</Text>
          <Text style={s.chevron}>›</Text>
        </TouchableOpacity>
      )}
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
    swatch: { width: 44, height: 44, borderRadius: 22, borderColor: 'transparent' },
    swatchLabel: { fontSize: 11, color: p.muted, marginTop: 6 },
    swatchLabelOn: { color: p.fg, fontWeight: '700' },
    picker: { marginTop: 20 },
    link: {
      flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      backgroundColor: p.surface, borderRadius: p.radius, borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 16, marginBottom: 10,
    },
    linkText: { fontSize: 15, fontWeight: '600', color: p.fg },
    chevron: { fontSize: 18, color: p.faint, fontWeight: '700' },
    panelBody: {
      fontSize: 13, color: p.muted, lineHeight: 20,
      paddingHorizontal: 4, marginTop: -2, marginBottom: 14,
    },
    aboutRow: {
      flexDirection: 'row', justifyContent: 'space-between',
      paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: p.line,
    },
    aboutKey: { fontSize: 14, color: p.muted },
    aboutVal: { fontSize: 14, fontWeight: '600', color: p.fg },
    warn: { fontSize: 13, color: p.muted, lineHeight: 20, marginBottom: 12 },
    danger: {
      backgroundColor: '#b3232e', borderRadius: p.radius,
      paddingVertical: 16, alignItems: 'center', marginBottom: 10,
    },
    dangerText: { color: '#ffffff', fontSize: 15, fontWeight: '700' },
  });
