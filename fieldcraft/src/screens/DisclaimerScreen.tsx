import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import {
  DISCLAIMER_ITEMS,
  DISCLAIMER_TITLE,
} from '../content/disclaimer';
import { theme } from '../theme';

type Props = { onAccept: () => void };

export default function DisclaimerScreen({ onAccept }: Props) {
  return (
    <View style={styles.root}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.mark}>🏈</Text>
        <Text style={styles.title}>{DISCLAIMER_TITLE}</Text>
        <Text style={styles.lede}>
          Read this once. It is short, and it matters more than anything else in the app.
        </Text>

        {DISCLAIMER_ITEMS.map((item, index) => (
          <View key={item.heading} style={styles.item}>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{index + 1}</Text>
            </View>
            <View style={styles.itemBody}>
              <Text style={styles.heading}>{item.heading}</Text>
              <Text style={styles.body}>{item.body}</Text>
            </View>
          </View>
        ))}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.cta}
          onPress={onAccept}
          accessibilityRole="button"
          accessibilityLabel="I understand"
        >
          <Text style={styles.ctaText}>I understand</Text>
        </TouchableOpacity>
        <Text style={styles.footnote}>You can read this again any time under Settings.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.bg },
  scroll: { padding: 24, paddingBottom: 12, maxWidth: 560, width: '100%', alignSelf: 'center' },
  mark: { fontSize: 30, marginBottom: 12 },
  title: { fontSize: 34, fontWeight: '800', color: theme.fg, letterSpacing: -0.5 },
  lede: { fontSize: 15, color: theme.muted, marginTop: 8, marginBottom: 24, lineHeight: 22 },
  item: { flexDirection: 'row', marginBottom: 22 },
  badge: {
    width: 24, height: 24, borderRadius: 12, backgroundColor: theme.accent,
    alignItems: 'center', justifyContent: 'center', marginRight: 14, marginTop: 2,
  },
  badgeText: { color: theme.onAccent, fontSize: 12, fontWeight: '700' },
  itemBody: { flex: 1 },
  heading: { fontSize: 16, fontWeight: '700', color: theme.fg, marginBottom: 4 },
  body: { fontSize: 15, color: theme.muted, lineHeight: 22 },
  footer: {
    padding: 24, paddingTop: 16, borderTopWidth: 1, borderTopColor: theme.line,
    maxWidth: 560, width: '100%', alignSelf: 'center',
  },
  cta: {
    backgroundColor: theme.accent, borderRadius: theme.radius,
    paddingVertical: 17, alignItems: 'center',
  },
  ctaText: { color: theme.onAccent, fontSize: 16, fontWeight: '700' },
  footnote: { textAlign: 'center', color: theme.muted, fontSize: 12, marginTop: 10 },
});
