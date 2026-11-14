import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View, Vibration, Platform } from 'react-native';
import { Palette, useTheme } from '../theme';

type Props = {
  /** How long this drill should take, in minutes. */
  minutes: number;
  /** Fired once when the countdown reaches zero. */
  onComplete?: () => void;
};

/**
 * Countdown for a single drill.
 *
 * Time left is derived from a target timestamp rather than counted down tick by
 * tick, so the clock stays right even when the browser or phone throttles
 * timers in the background.
 */
export default function DrillTimer({ minutes, onComplete }: Props) {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const total = Math.max(1, Math.round(minutes * 60));
  const [left, setLeft] = useState(total);
  const [running, setRunning] = useState(false);
  const endAt = useRef<number | null>(null);
  const fired = useRef(false);

  // Reset whenever the drill's length changes, so reopening a card starts fresh.
  useEffect(() => {
    setLeft(total);
    setRunning(false);
    endAt.current = null;
    fired.current = false;
  }, [total]);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      if (endAt.current === null) return;
      const remaining = Math.max(0, Math.round((endAt.current - Date.now()) / 1000));
      setLeft(remaining);
      if (remaining === 0) {
        setRunning(false);
        endAt.current = null;
        if (!fired.current) {
          fired.current = true;
          if (Platform.OS !== 'web') Vibration.vibrate(600);
          onComplete?.();
        }
      }
    }, 250);
    return () => clearInterval(id);
  }, [running, onComplete]);

  const start = useCallback(() => {
    fired.current = false;
    endAt.current = Date.now() + (left > 0 ? left : total) * 1000;
    if (left === 0) setLeft(total);
    setRunning(true);
  }, [left, total]);

  const pause = useCallback(() => {
    setRunning(false);
    endAt.current = null;
  }, []);

  const reset = useCallback(() => {
    setRunning(false);
    endAt.current = null;
    fired.current = false;
    setLeft(total);
  }, [total]);

  const mm = Math.floor(left / 60);
  const ss = left % 60;
  const pct = total === 0 ? 0 : ((total - left) / total) * 100;
  const done = left === 0;

  return (
    <View style={s.wrap}>
      <View style={s.row}>
        <Text style={[s.clock, done && s.clockDone]}>
          {mm}:{ss.toString().padStart(2, '0')}
        </Text>

        <View style={s.buttons}>
          <TouchableOpacity
            style={[s.btn, s.btnPrimary]}
            onPress={running ? pause : start}
            accessibilityRole="button"
            accessibilityLabel={running ? 'Pause timer' : 'Start timer'}
          >
            <Text style={s.btnPrimaryText}>
              {running ? 'Pause' : done ? 'Again' : 'Start'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={s.btn}
            onPress={reset}
            accessibilityRole="button"
            accessibilityLabel="Reset timer"
          >
            <Text style={s.btnText}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={s.track}>
        <View style={[s.fill, { width: `${pct}%` }]} />
      </View>

      <Text style={s.caption}>
        {done ? 'Time. Take your rest, then go again.' : `Set for ${minutes} min`}
      </Text>
    </View>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    wrap: {
      marginTop: 14, paddingTop: 14,
      borderTopWidth: 1, borderTopColor: p.line,
    },
    row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
    clock: {
      fontSize: 38, fontWeight: '800', color: p.fg,
      letterSpacing: -1.5, fontVariant: ['tabular-nums'],
    },
    clockDone: { color: p.accent },
    buttons: { flexDirection: 'row', gap: 8 },
    btn: {
      paddingHorizontal: 16, paddingVertical: 10, borderRadius: 999,
      backgroundColor: p.bg, borderWidth: 1, borderColor: p.line,
    },
    btnPrimary: { backgroundColor: p.accent, borderColor: p.accent },
    btnText: { fontSize: 14, fontWeight: '700', color: p.fg },
    btnPrimaryText: { fontSize: 14, fontWeight: '700', color: p.onAccent },
    track: {
      height: 6, borderRadius: 3, backgroundColor: p.bg,
      marginTop: 12, overflow: 'hidden',
    },
    fill: { height: '100%', backgroundColor: p.accent },
    caption: { fontSize: 12, color: p.muted, marginTop: 8 },
  });
