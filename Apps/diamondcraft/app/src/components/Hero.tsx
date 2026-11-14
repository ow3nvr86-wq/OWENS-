import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Palette, useTheme } from '../theme';

type Props = {
  name?: string;
  done: number;
  total: number;
  /** Which days of the current cycle are finished, in order. */
  ticks: boolean[];
  cycles: number;
  /** Sessions in a row, counting a single rest day as not breaking the run. */
  streak?: number;
};

export default function Hero({ name, done, total, ticks, cycles, streak = 0 }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  return (
    <View style={s.hero}>
      <Text style={s.ball}>⚾</Text>

      <View style={s.top}>
        <Text style={s.label}>{name ? `${name.toUpperCase()}'S WEEK` : 'THIS WEEK'}</Text>
        {streak > 1 ? (
          <Text style={s.streak}>🔥 {streak} in a row</Text>
        ) : cycles > 0 ? (
          <Text style={s.streak}>
            {cycles} week{cycles === 1 ? '' : 's'} banked
          </Text>
        ) : null}
      </View>

      <Text style={s.number}>
        {done}
        <Text style={s.of}>/{total}</Text>
      </Text>

      <View style={s.track}>
        {ticks.map((on, i) => (
          <View key={i} style={[s.tick, on && s.tickOn]} />
        ))}
      </View>

      <Text style={s.caption}>
        {done === 0
          ? 'Nothing done yet this week. Start with Day 1.'
          : done >= total
            ? 'Every day done. Bank it and go again.'
            : `${total - done} day${total - done === 1 ? '' : 's'} to go.`}
      </Text>
    </View>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    hero: {
      backgroundColor: p.ink, borderRadius: p.radiusLg,
      padding: 22, overflow: 'hidden', marginBottom: 22,
      boxShadow: p.shadowStrong,
    },
    ball: { position: 'absolute', right: -26, top: -26, fontSize: 138, opacity: 0.12 },
    top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    label: { fontSize: 11, fontWeight: '800', letterSpacing: 2.2, color: p.onInkMuted },
    streak: {
      fontSize: 12, fontWeight: '800', color: p.onInk,
      backgroundColor: p.inkRaised, overflow: 'hidden',
      paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999,
    },
    number: {
      fontSize: 76, lineHeight: 82, fontWeight: '800',
      color: p.onInk, letterSpacing: -4, marginTop: 2,
      fontVariant: ['tabular-nums'],
    },
    of: { fontSize: 32, fontWeight: '800', color: p.onInkMuted, letterSpacing: -1.2 },
    track: { flexDirection: 'row', gap: 6, marginTop: 14 },
    tick: { flex: 1, height: 7, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.18)' },
    tickOn: { backgroundColor: p.accent },
    caption: { fontSize: 13, color: p.onInkMuted, marginTop: 14 },
  });
