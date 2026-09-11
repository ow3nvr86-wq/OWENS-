import React, { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Palette, useTheme } from '../theme';

export const AGREEMENT_VERSION = '1.0';

type Props = { onAccept: (name: string) => void };

const POINTS = [
  'I understand that football and strength training involve running, jumping, sudden changes of direction and heavy effort, and that these carry a real risk of injury.',
  'I understand that injuries from this kind of training can be serious, including sprains, strains, broken bones, head injuries and heat illness, and in rare cases can be permanent or life threatening.',
  'I understand that Court Craft is a general training guide, that it cannot see me or assess me, and that nothing in it is medical advice or personal coaching.',
  'I confirm I am medically fit to train, or that a doctor has cleared me, and that I will stop and seek help if I am hurt or unwell.',
  'I understand that every contact drill here is form work only, and I will not use this app to practise live tackling, blocking or collisions with another person.',
  'I am taking part voluntarily, I accept the risks, and I am responsible for choosing what I attempt and for training within my ability.',
  'If I am under 18, a parent, guardian or coach has read this with me and agrees to it.',
];

export default function AgreementScreen({ onAccept }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [checked, setChecked] = useState<boolean[]>(POINTS.map(() => false));
  const [name, setName] = useState('');

  const allChecked = checked.every(Boolean);
  const canAccept = allChecked && name.trim().length > 1;
  const today = new Date().toLocaleDateString();

  function toggle(i: number) {
    setChecked((prev) => prev.map((v, idx) => (idx === i ? !v : v)));
  }

  return (
    <View style={s.root}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.eyebrow}>BEFORE YOU START</Text>
        <Text style={s.title}>Acknowledgement of risk</Text>
        <Text style={s.lede}>
          Tick each line to show you have read and understood it. This stays on your phone.
        </Text>

        {POINTS.map((point, i) => (
          <TouchableOpacity
            key={i}
            style={[s.row, checked[i] && s.rowOn]}
            onPress={() => toggle(i)}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: checked[i] }}
          >
            <View style={[s.box, checked[i] && s.boxOn]}>
              {checked[i] ? <Text style={s.tick}>✓</Text> : null}
            </View>
            <Text style={s.rowText}>{point}</Text>
          </TouchableOpacity>
        ))}

        <Text style={s.signLabel}>Type your full name to accept</Text>
        <TextInput
          style={s.input}
          placeholder="Full name"
          placeholderTextColor={palette.faint}
          value={name}
          onChangeText={setName}
          autoCapitalize="words"
        />
        <Text style={s.date}>Dated {today}</Text>
      </ScrollView>

      <View style={s.footer}>
        <TouchableOpacity
          style={[s.cta, !canAccept && s.ctaOff]}
          onPress={() => canAccept && onAccept(name.trim())}
          disabled={!canAccept}
          accessibilityRole="button"
        >
          <Text style={[s.ctaText, !canAccept && s.ctaTextOff]}>
            {allChecked ? 'I agree' : `Tick all ${POINTS.length} to continue`}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    root: { flex: 1, backgroundColor: p.bg },
    scroll: { padding: 24, paddingBottom: 12, maxWidth: 560, width: '100%', alignSelf: 'center' },
    eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.8, color: p.accent },
    title: { fontSize: 32, fontWeight: '800', color: p.fg, letterSpacing: -1, marginTop: 6 },
    lede: { fontSize: 15, color: p.muted, marginTop: 8, marginBottom: 20, lineHeight: 22 },
    row: {
      flexDirection: 'row', backgroundColor: p.surface, borderRadius: p.radius,
      padding: 16, marginBottom: 10, borderWidth: 2, borderColor: 'transparent',
    },
    rowOn: { borderColor: p.accent },
    box: {
      width: 24, height: 24, borderRadius: 7, borderWidth: 2, borderColor: p.line,
      marginRight: 14, alignItems: 'center', justifyContent: 'center',
    },
    boxOn: { backgroundColor: p.accent, borderColor: p.accent },
    tick: { color: p.onAccent, fontSize: 14, fontWeight: '800' },
    rowText: { flex: 1, fontSize: 14, color: p.fg, lineHeight: 21 },
    signLabel: {
      fontSize: 11, fontWeight: '800', letterSpacing: 1.4,
      color: p.muted, marginTop: 22, marginBottom: 8,
    },
    input: {
      backgroundColor: p.surface, borderRadius: p.radius, borderWidth: 1, borderColor: p.line,
      paddingHorizontal: 18, paddingVertical: 16, fontSize: 17, color: p.fg,
    },
    date: { fontSize: 13, color: p.faint, marginTop: 10 },
    footer: {
      padding: 24, paddingTop: 14, borderTopWidth: 1, borderTopColor: p.line,
      maxWidth: 560, width: '100%', alignSelf: 'center',
    },
    cta: {
      backgroundColor: p.accent, borderRadius: p.radius,
      paddingVertical: 17, alignItems: 'center',
    },
    ctaOff: { backgroundColor: p.raised },
    ctaText: { color: p.onAccent, fontSize: 16, fontWeight: '700' },
    ctaTextOff: { color: p.faint },
  });
