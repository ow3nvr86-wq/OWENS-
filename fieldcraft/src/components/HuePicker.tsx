import React, { useMemo, useRef, useState } from 'react';
import { PanResponder, StyleSheet, Text, View } from 'react-native';
import { Palette, hueToHex, useTheme } from '../theme';

type Props = {
  hue: number | null;
  onChange: (hue: number) => void;
};

const BANDS = 60; // enough to read as a smooth rainbow without a gradient library

export default function HuePicker({ hue, onChange }: Props) {
  const { palette, isDark } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);
  const [width, setWidth] = useState(0);
  const widthRef = useRef(0);

  const responder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: (e) => pick(e.nativeEvent.locationX),
        onPanResponderMove: (e) => pick(e.nativeEvent.locationX),
      }),
    [],
  );

  function pick(x: number) {
    const w = widthRef.current;
    if (!w) return;
    const clamped = Math.min(Math.max(x, 0), w);
    onChange(Math.round((clamped / w) * 359));
  }

  const shown = hue ?? 0;
  const thumbLeft = width ? (shown / 359) * width : 0;

  return (
    <View>
      <View
        style={s.track}
        onLayout={(e) => {
          widthRef.current = e.nativeEvent.layout.width;
          setWidth(e.nativeEvent.layout.width);
        }}
        {...responder.panHandlers}
        accessibilityRole="adjustable"
        accessibilityLabel="Accent colour"
      >
        {Array.from({ length: BANDS }).map((_, i) => (
          <View
            key={i}
            style={[styles.band, { backgroundColor: `hsl(${(i / BANDS) * 360}, 85%, 50%)` }]}
          />
        ))}
        {hue !== null && width > 0 ? (
          <View
            pointerEvents="none"
            style={[s.thumb, { left: Math.min(Math.max(thumbLeft - 15, 0), width - 30) }]}
          >
            <View style={[s.thumbInner, { backgroundColor: hueToHex(shown, isDark) }]} />
          </View>
        ) : null}
      </View>
      <Text style={s.hint}>
        {hue === null
          ? 'Drag the bar to mix your own colour.'
          : `Your colour  ·  hue ${shown}`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  band: { flex: 1, height: '100%' },
});

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    track: {
      flexDirection: 'row', height: 44, borderRadius: 22,
      overflow: 'hidden', borderWidth: 1, borderColor: p.line,
    },
    thumb: {
      position: 'absolute', top: -3, width: 30, height: 50, borderRadius: 25,
      backgroundColor: p.surface, alignItems: 'center', justifyContent: 'center',
      borderWidth: 2, borderColor: p.surface,
    },
    thumbInner: { width: 22, height: 42, borderRadius: 21 },
    hint: { fontSize: 13, color: p.muted, marginTop: 10 },
  });
