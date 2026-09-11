import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';
import { readJSON, writeJSON } from './storage';

export type Mode = 'system' | 'light' | 'dark';
export type AccentId =
  | 'court' | 'navy' | 'forest' | 'clay' | 'slate'
  | 'blaze' | 'crimson' | 'violet' | 'teal' | 'gold';

export const ACCENTS: { id: AccentId; label: string; light: string; dark: string }[] = [
  // The first five are the themes the shipped Court Craft build already offered.
  { id: 'court',   label: 'Court',   light: '#0a0a0a', dark: '#f2f2ef' },
  { id: 'navy',    label: 'Navy',    light: '#16233f', dark: '#8ba4de' },
  { id: 'forest',  label: 'Forest',  light: '#123a2c', dark: '#5fc08d' },
  { id: 'clay',    label: 'Clay',    light: '#7a3b1e', dark: '#e08c5a' },
  { id: 'slate',   label: 'Slate',   light: '#2b3642', dark: '#9db0c4' },
  // Added alongside them.
  { id: 'blaze',   label: 'Blaze',   light: '#d2601a', dark: '#fb923c' },
  { id: 'crimson', label: 'Crimson', light: '#b3232e', dark: '#f8717a' },
  { id: 'violet',  label: 'Violet',  light: '#6d31c4', dark: '#a98bff' },
  { id: 'teal',    label: 'Teal',    light: '#0d7b7b', dark: '#4dd4d4' },
  { id: 'gold',    label: 'Gold',    light: '#9a7209', dark: '#e5b93c' },
];

export type Palette = {
  bg: string; surface: string; raised: string;
  fg: string; muted: string; faint: string; line: string;
  accent: string; onAccent: string;
  ink: string; onInk: string; onInkMuted: string;
  radius: number; radiusLg: number; radiusPill: number;
};

const LIGHT = {
  bg: '#fbfaf8', surface: '#ffffff', raised: '#f3f2ee',
  fg: '#141413', muted: '#6b6b66', faint: '#9a9a93', line: '#e6e5e0',
  ink: '#141413', onInk: '#ffffff', onInkMuted: 'rgba(255,255,255,0.62)',
};

const DARK = {
  bg: '#0f0f0e', surface: '#1a1a18', raised: '#232320',
  fg: '#f4f4f1', muted: '#a2a29b', faint: '#6f6f69', line: '#2c2c28',
  ink: '#1f1f1c', onInk: '#f7f7f4', onInkMuted: 'rgba(247,247,244,0.60)',
};

/** Any hue on the wheel, tuned so it stays readable in each mode. */
export function hueToHex(hue: number, dark: boolean): string {
  const h = ((hue % 360) + 360) % 360;
  // Light mode wants a deeper colour behind white text; dark mode a brighter one.
  const sat = dark ? 0.72 : 0.62;
  const light = dark ? 0.66 : 0.38;
  return hslToHex(h, sat, light);
}

function hslToHex(h: number, s: number, l: number): string {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  const [r, g, b] =
    h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x]
    : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  const to = (v: number) =>
    Math.round((v + m) * 255).toString(16).padStart(2, '0');
  return `#${to(r)}${to(g)}${to(b)}`;
}

/** White text on a mid-dark accent, near-black on a light one. */
function onAccentFor(hex: string): string {
  const n = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16) / 255);
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return lum > 0.55 ? '#141413' : '#ffffff';
}

export function buildPalette(dark: boolean, accentId: AccentId, customHue: number | null): Palette {
  const base = dark ? DARK : LIGHT;
  const accentDef = ACCENTS.find((a) => a.id === accentId) ?? ACCENTS[0];
  const accent =
    customHue === null ? (dark ? accentDef.dark : accentDef.light) : hueToHex(customHue, dark);
  return {
    ...base,
    accent,
    onAccent: onAccentFor(accent),
    radius: 16, radiusLg: 24, radiusPill: 999,
  };
}

type ThemeState = {
  palette: Palette;
  mode: Mode;
  accent: AccentId;
  /** Null when one of the preset accents is in use. */
  customHue: number | null;
  isDark: boolean;
  setMode: (m: Mode) => void;
  setAccent: (a: AccentId) => void;
  setCustomHue: (h: number | null) => void;
};

const PREFS_KEY = 'courtready:appearance';

type Saved = { mode?: Mode; accent?: AccentId; customHue?: number | null };

const ThemeContext = createContext<ThemeState | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [mode, setModeState] = useState<Mode>('system');
  const [accent, setAccentState] = useState<AccentId>('court');
  const [customHue, setCustomHueState] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      const saved = await readJSON<Saved>(PREFS_KEY, {});
      if (saved.mode) setModeState(saved.mode);
      if (saved.accent) setAccentState(saved.accent);
      if (typeof saved.customHue === 'number') setCustomHueState(saved.customHue);
    })();
  }, []);

  const isDark = mode === 'system' ? system === 'dark' : mode === 'dark';
  const palette = useMemo(
    () => buildPalette(isDark, accent, customHue),
    [isDark, accent, customHue],
  );

  const persist = (next: Saved) =>
    writeJSON(PREFS_KEY, { mode, accent, customHue, ...next });

  const value: ThemeState = {
    palette, mode, accent, customHue, isDark,
    setMode: (m) => { setModeState(m); persist({ mode: m }); },
    // Picking a preset clears any custom hue, so the swatch you tapped is what you get.
    setAccent: (a) => { setAccentState(a); setCustomHueState(null); persist({ accent: a, customHue: null }); },
    setCustomHue: (h) => { setCustomHueState(h); persist({ customHue: h }); },
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
}
