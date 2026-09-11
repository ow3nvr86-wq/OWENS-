import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { DISCLAIMER_ITEMS, DISCLAIMER_TITLE } from '../content/disclaimer';
import { Palette, useTheme } from '../theme';

type Props = { onAccept: () => void; ctaLabel?: string };

export default function DisclaimerScreen({ onAccept, ctaLabel = 'I understand' }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  return (
    <View style={s.root}>
      <ScrollView contentContainerStyle={s.scroll}>
        <View style={s.badge}>
          <Text style={s.badgeMark}>🏈</Text>
        </View>
        <Text style={s.title}>{DISCLAIMER_TITLE}</Text>
        <Text style={s.lede}>
          Read this once. It is short, and it matters more than anything else in the app.
        </Text>

        {DISCLAIMER_ITEMS.map((item, index) => (
          <View key={item.heading} style={s.card}>
            <View style={s.num}>
              <Text style={s.numText}>{index + 1}</Text>
            </View>
            <View style={s.cardBody}>
              <Text style={s.heading}>{item.heading}</Text>
              <Text style={s.body}>{item.body}</Text>
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={s.footer}>
        <TouchableOpacity style={s.cta} onPress={onAccept} accessibilityRole="button">
          <Text style={s.ctaText}>{ctaLabel}</Text>
        </TouchableOpacity>
        <Text style={s.footnote}>You can read this again any time in Settings.</Text>
      </View>
    </View>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    root: { flex: 1, backgroundColor: p.bg },
    scroll: { padding: 24, paddingBottom: 12, maxWidth: 560, width: '100%', alignSelf: 'center' },
    badge: {
      width: 60, height: 60, borderRadius: 18, backgroundColor: p.ink,
      alignItems: 'center', justifyContent: 'center', marginBottom: 18,
    },
    badgeMark: { fontSize: 30 },
    title: { fontSize: 34, fontWeight: '800', color: p.fg, letterSpacing: -1.2 },
    lede: { fontSize: 15, color: p.muted, marginTop: 8, marginBottom: 22, lineHeight: 22 },
    card: {
      flexDirection: 'row', backgroundColor: p.surface, borderRadius: p.radius,
      padding: 18, marginBottom: 10, borderWidth: 1, borderColor: p.line,
    },
    num: {
      width: 26, height: 26, borderRadius: 13, backgroundColor: p.accent,
      alignItems: 'center', justifyContent: 'center', marginRight: 14, marginTop: 1,
    },
    numText: { color: p.onAccent, fontSize: 12, fontWeight: '800' },
    cardBody: { flex: 1 },
    heading: { fontSize: 16, fontWeight: '700', color: p.fg, marginBottom: 5 },
    body: { fontSize: 14, color: p.muted, lineHeight: 21 },
    footer: {
      padding: 24, paddingTop: 14, borderTopWidth: 1, borderTopColor: p.line,
      maxWidth: 560, width: '100%', alignSelf: 'center',
    },
    cta: {
      backgroundColor: p.accent, borderRadius: p.radius,
      paddingVertical: 17, alignItems: 'center',
    },
    ctaText: { color: p.onAccent, fontSize: 16, fontWeight: '700' },
    footnote: { textAlign: 'center', color: p.faint, fontSize: 12, marginTop: 10 },
  });
