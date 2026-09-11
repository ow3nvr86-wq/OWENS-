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
};

export default function Hero({ name, done, total, ticks, cycles }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  return (
    <View style={s.hero}>
      <Text style={s.ball}>🏀</Text>

      <View style={s.top}>
        <Text style={s.label}>{name ? `${name.toUpperCase()}'S WEEK` : 'THIS WEEK'}</Text>
        {cycles > 0 ? (
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
    },
    ball: { position: 'absolute', right: -26, top: -22, fontSize: 130, opacity: 0.13 },
    top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    label: { fontSize: 11, fontWeight: '800', letterSpacing: 1.8, color: p.onInkMuted },
    streak: { fontSize: 12, fontWeight: '600', color: p.onInkMuted },
    number: {
      fontSize: 64, lineHeight: 72, fontWeight: '800',
      color: p.onInk, letterSpacing: -3, marginTop: 4,
    },
    of: { fontSize: 30, fontWeight: '800', color: p.onInkMuted, letterSpacing: -1 },
    track: { flexDirection: 'row', gap: 6, marginTop: 14 },
    tick: { flex: 1, height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.20)' },
    tickOn: { backgroundColor: p.onInk },
    caption: { fontSize: 13, color: p.onInkMuted, marginTop: 14 },
  });
