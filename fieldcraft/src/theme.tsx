import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';
import { readJSON, writeJSON } from './storage';

export type Mode = 'system' | 'light' | 'dark';
export type AccentId =
  | 'ink' | 'grass' | 'blaze' | 'royal' | 'crimson' | 'violet' | 'teal' | 'gold';

export const ACCENTS: { id: AccentId; label: string; light: string; dark: string }[] = [
  { id: 'ink',     label: 'Ink',     light: '#141413', dark: '#f2f2ef' },
  { id: 'grass',   label: 'Grass',   light: '#1c7c3f', dark: '#4ade80' },
  { id: 'blaze',   label: 'Blaze',   light: '#d2601a', dark: '#fb923c' },
  { id: 'royal',   label: 'Royal',   light: '#2547c4', dark: '#7c9bff' },
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

/** White text on a mid-dark accent, near-black on a light one. */
function onAccentFor(hex: string): string {
  const n = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16) / 255);
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return lum > 0.55 ? '#141413' : '#ffffff';
}

export function buildPalette(dark: boolean, accentId: AccentId): Palette {
  const base = dark ? DARK : LIGHT;
  const accentDef = ACCENTS.find((a) => a.id === accentId) ?? ACCENTS[0];
  const accent = dark ? accentDef.dark : accentDef.light;
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
  isDark: boolean;
  setMode: (m: Mode) => void;
  setAccent: (a: AccentId) => void;
};

const PREFS_KEY = 'fieldcraft:appearance';

const ThemeContext = createContext<ThemeState | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const system = useColorScheme();
  const [mode, setModeState] = useState<Mode>('system');
  const [accent, setAccentState] = useState<AccentId>('grass');

  useEffect(() => {
    (async () => {
      const saved = await readJSON<{ mode?: Mode; accent?: AccentId }>(PREFS_KEY, {});
      if (saved.mode) setModeState(saved.mode);
      if (saved.accent) setAccentState(saved.accent);
    })();
  }, []);

  const isDark = mode === 'system' ? system === 'dark' : mode === 'dark';
  const palette = useMemo(() => buildPalette(isDark, accent), [isDark, accent]);

  const value: ThemeState = {
    palette, mode, accent, isDark,
    setMode: (m) => { setModeState(m); writeJSON(PREFS_KEY, { mode: m, accent }); },
    setAccent: (a) => { setAccentState(a); writeJSON(PREFS_KEY, { mode, accent: a }); },
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
}
