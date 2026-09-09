import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

import DisclaimerScreen from './src/screens/DisclaimerScreen';
import OnboardingScreen from './src/screens/OnboardingScreen';
import { DISCLAIMER_VERSION } from './src/content/disclaimer';
import {
  Profile, loadAccepted, loadProfile, saveAccepted, saveProfile,
} from './src/storage';
import { theme } from './src/theme';

type Stage = 'loading' | 'disclaimer' | 'onboarding' | 'home';

export default function App() {
  const [stage, setStage] = useState<Stage>('loading');
  const [, setProfile] = useState<Profile | null>(null);

  // Decide the entry screen from what is already stored on this device.
  useEffect(() => {
    (async () => {
      const [accepted, saved] = await Promise.all([loadAccepted(), loadProfile()]);
      if (accepted !== DISCLAIMER_VERSION) return setStage('disclaimer');
      if (!saved) return setStage('onboarding');
      setProfile(saved);
      setStage('home');
    })();
  }, []);

  async function acceptDisclaimer() {
    await saveAccepted(DISCLAIMER_VERSION);
    setStage('onboarding');
  }

  async function finishOnboarding(answers: Profile) {
    await saveProfile(answers);
    setProfile(answers);
    setStage('home');
  }

  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.root} edges={['top', 'bottom']}>
        {stage === 'loading' && (
          <View style={styles.centre}>
            <ActivityIndicator color={theme.fg} />
          </View>
        )}
        {stage === 'disclaimer' && <DisclaimerScreen onAccept={acceptDisclaimer} />}
        {stage === 'onboarding' && <OnboardingScreen onDone={finishOnboarding} />}
        {stage === 'home' && <View style={styles.centre} />}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.bg },
  centre: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
