import React, { useMemo } from 'react';
import { Modal, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Palette, useTheme } from '../theme';

type Props = {
  visible: boolean;
  dayNumber: number;
  drillsDone: number;
  drillsTotal: number;
  minutes: number;
  streak: number;
  daysDone: number;
  daysTotal: number;
  /** Badges earned by this session, if any. */
  newBadges: string[];
  onClose: () => void;
};

export default function SessionSummary(props: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);
  const {
    visible, dayNumber, drillsDone, drillsTotal, minutes,
    streak, daysDone, daysTotal, newBadges, onClose,
  } = props;

  const weekDone = daysDone >= daysTotal;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={s.backdrop}>
        <View style={s.sheet}>
          <ScrollView contentContainerStyle={s.sheetBody}>
            <Text style={s.eyebrow}>DAY {dayNumber} COMPLETE</Text>
            <Text style={s.headline}>
              {weekDone ? 'Week banked.' : 'Work done.'}
            </Text>

            <View style={s.stats}>
              <View style={s.stat}>
                <Text style={s.statNum}>{drillsDone}/{drillsTotal}</Text>
                <Text style={s.statLabel}>drills ticked</Text>
              </View>
              <View style={s.stat}>
                <Text style={s.statNum}>{minutes}</Text>
                <Text style={s.statLabel}>minutes planned</Text>
              </View>
              <View style={s.stat}>
                <Text style={s.statNum}>{streak}</Text>
                <Text style={s.statLabel}>day streak</Text>
              </View>
            </View>

            <Text style={s.line}>
              {daysDone} of {daysTotal} days done this week.
            </Text>

            {newBadges.length > 0 ? (
              <View style={s.badgeBox}>
                <Text style={s.badgeHead}>
                  {newBadges.length === 1 ? 'NEW BADGE' : 'NEW BADGES'}
                </Text>
                {newBadges.map((b) => (
                  <Text key={b} style={s.badgeName}>{b}</Text>
                ))}
              </View>
            ) : null}
          </ScrollView>

          <TouchableOpacity style={s.cta} onPress={onClose} accessibilityRole="button">
            <Text style={s.ctaText}>Done</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    backdrop: {
      flex: 1, backgroundColor: 'rgba(0,0,0,0.55)',
      alignItems: 'center', justifyContent: 'center', padding: 24,
    },
    sheet: {
      backgroundColor: p.bg, borderRadius: p.radiusLg,
      width: '100%', maxWidth: 420, maxHeight: '86%', padding: 24,
    },
    sheetBody: { paddingBottom: 8 },
    eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.8, color: p.accent },
    headline: {
      fontSize: 30, fontWeight: '800', color: p.fg,
      letterSpacing: -1, marginTop: 6, marginBottom: 20,
    },
    stats: { flexDirection: 'row', gap: 8 },
    stat: {
      flex: 1, backgroundColor: p.surface, borderRadius: p.radius,
      borderWidth: 1, borderColor: p.line, padding: 12,
    },
    statNum: { fontSize: 20, fontWeight: '800', color: p.fg, letterSpacing: -.5 },
    statLabel: { fontSize: 11, color: p.muted, marginTop: 2 },
    line: { fontSize: 14, color: p.muted, marginTop: 16, lineHeight: 20 },
    badgeBox: {
      marginTop: 18, borderWidth: 2, borderColor: p.accent,
      borderRadius: p.radius, padding: 14,
    },
    badgeHead: { fontSize: 11, fontWeight: '800', letterSpacing: 1.6, color: p.accent },
    badgeName: { fontSize: 16, fontWeight: '700', color: p.fg, marginTop: 6 },
    cta: {
      backgroundColor: p.accent, borderRadius: p.radius,
      paddingVertical: 16, alignItems: 'center', marginTop: 18,
    },
    ctaText: { color: p.onAccent, fontSize: 16, fontWeight: '700' },
  });
