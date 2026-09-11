import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import DisclaimerScreen from './src/screens/DisclaimerScreen';
import AgreementScreen, { AGREEMENT_VERSION } from './src/screens/AgreementScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import PlanScreen from './src/screens/PlanScreen';
import DrillsScreen from './src/screens/DrillsScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { DISCLAIMER_VERSION } from './src/content/disclaimer';
import {
  Profile, loadAccepted, loadAgreement, loadProfile,
  saveAccepted, saveAgreement, saveProfile,
} from './src/storage';
import { Palette, ThemeProvider, useTheme } from './src/theme';

type Gate = 'loading' | 'disclaimer' | 'agreement' | 'onboarding' | 'ready';
type Tab = 'plan' | 'library' | 'settings';

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'plan', label: 'Plan', icon: '▦' },
  { id: 'library', label: 'Drills', icon: '☰' },
  { id: 'settings', label: 'Settings', icon: '⚙' },
];

function Shell() {
  const { palette } = useTheme();
  const s = useMemo(() => makeStyles(palette), [palette]);

  const [gate, setGate] = useState<Gate>('loading');
  const [tab, setTab] = useState<Tab>('plan');
  const [profile, setProfile] = useState<Profile | null>(null);
  const [rereadSafety, setRereadSafety] = useState(false);

  useEffect(() => {
    (async () => {
      const [accepted, agreement, saved] = await Promise.all([
        loadAccepted(), loadAgreement(), loadProfile(),
      ]);
      if (accepted !== DISCLAIMER_VERSION) return setGate('disclaimer');
      if (agreement?.version !== AGREEMENT_VERSION) return setGate('agreement');
      if (!saved) return setGate('onboarding');
      setProfile(saved);
      setGate('ready');
    })();
  }, []);

  async function acceptDisclaimer() {
    await saveAccepted(DISCLAIMER_VERSION);
    setGate('agreement');
  }

  async function acceptAgreement(name: string) {
    await saveAgreement({
      version: AGREEMENT_VERSION,
      acceptedAt: new Date().toISOString(),
      name,
    });
    setGate(profile ? 'ready' : 'onboarding');
  }

  async function finishOnboarding(answers: Profile) {
    await saveProfile(answers);
    setProfile(answers);
    setGate('ready');
    setTab('plan');
  }

  if (rereadSafety) {
    return (
      <DisclaimerScreen ctaLabel="Done" onAccept={() => setRereadSafety(false)} />
    );
  }

  if (gate === 'loading') {
    return (
      <View style={s.centre}>
        <ActivityIndicator color={palette.fg} />
      </View>
    );
  }
  if (gate === 'disclaimer') return <DisclaimerScreen onAccept={acceptDisclaimer} />;
  if (gate === 'agreement') return <AgreementScreen onAccept={acceptAgreement} />;
  if (gate === 'onboarding') return <OnboardingScreen onDone={finishOnboarding} />;
  if (!profile) return <View style={s.centre} />;

  return (
    <View style={s.app}>
      <View style={s.content}>
        {tab === 'plan' && (
          <PlanScreen profile={profile} onOpenLibrary={() => setTab('library')} />
        )}
        {tab === 'library' && (
          <DrillsScreen profile={profile} onBack={() => setTab('plan')} />
        )}
        {tab === 'settings' && (
          <SettingsScreen
            name={typeof profile.name === 'string' ? profile.name : undefined}
            onReadSafety={() => setRereadSafety(true)}
            onRedoSetup={() => setGate('onboarding')}
            onReset={() => { setProfile(null); setTab('plan'); setGate('disclaimer'); }}
          />
        )}
      </View>

      <View style={s.tabBar}>
        {TABS.map((t) => (
          <TouchableOpacity
            key={t.id}
            style={s.tab}
            onPress={() => setTab(t.id)}
            accessibilityRole="tab"
            accessibilityState={{ selected: tab === t.id }}
            accessibilityLabel={t.label}
          >
            <Text style={[s.tabIcon, tab === t.id && s.tabOn]}>{t.icon}</Text>
            <Text style={[s.tabLabel, tab === t.id && s.tabOn]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

function Themed() {
  const { palette, isDark } = useTheme();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: palette.bg }} edges={['top', 'bottom']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <Shell />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <SafeAreaProvider>
        <Themed />
      </SafeAreaProvider>
    </ThemeProvider>
  );
}

const makeStyles = (p: Palette) =>
  StyleSheet.create({
    app: { flex: 1, backgroundColor: p.bg },
    content: { flex: 1 },
    centre: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: p.bg },
    tabBar: {
      flexDirection: 'row', borderTopWidth: 1, borderTopColor: p.line,
      backgroundColor: p.surface, paddingTop: 8, paddingBottom: 6,
    },
    tab: { flex: 1, alignItems: 'center', paddingVertical: 4 },
    tabIcon: { fontSize: 19, color: p.faint, marginBottom: 2 },
    tabLabel: { fontSize: 11, fontWeight: '700', color: p.faint },
    tabOn: { color: p.accent },
  });
