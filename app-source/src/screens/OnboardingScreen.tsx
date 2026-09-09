import React, { useMemo, useState } from 'react';
import {
  ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View,
} from 'react-native';
import { QUIZ, QuizOption } from '../content/quiz';
import { Profile } from '../storage';
import { theme } from '../theme';

type Props = { onDone: (profile: Profile) => void };

export default function OnboardingScreen({ onDone }: Props) {
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Profile>({});
  const step = QUIZ[index];

  const current = answers[step.key];

  // A step is answerable once it holds a non-empty value.
  const canContinue = useMemo(() => {
    if (step.input === 'text') return typeof current === 'string' && current.trim().length > 0;
    if (step.multi) return Array.isArray(current) && current.length > 0;
    return current !== undefined;
  }, [current, step]);

  function toggle(option: QuizOption) {
    setAnswers((prev) => {
      if (!step.multi) return { ...prev, [step.key]: option.value };
      const picked = Array.isArray(prev[step.key]) ? (prev[step.key] as string[]) : [];
      const value = String(option.value);
      return {
        ...prev,
        [step.key]: picked.includes(value)
          ? picked.filter((v) => v !== value)
          : [...picked, value],
      };
    });
  }

  function isPicked(option: QuizOption) {
    if (step.multi) {
      const picked = Array.isArray(current) ? (current as string[]) : [];
      return picked.includes(String(option.value));
    }
    return current === option.value;
  }

  function next() {
    if (!canContinue) return;
    if (index < QUIZ.length - 1) setIndex(index + 1);
    else onDone(answers);
  }

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.brand}>COURT CRAFT</Text>
        <Text style={styles.count}>{index + 1}/{QUIZ.length}</Text>
      </View>

      <View style={styles.progress}>
        {QUIZ.map((s, i) => (
          <View key={s.key} style={[styles.tick, i <= index && styles.tickOn]} />
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.prompt}>{step.prompt}</Text>
        {step.hint ? <Text style={styles.hint}>{step.hint}</Text> : null}

        {step.input === 'text' ? (
          <TextInput
            style={styles.input}
            placeholder={step.placeholder}
            placeholderTextColor={theme.muted}
            value={typeof current === 'string' ? current : ''}
            onChangeText={(text) => setAnswers((p) => ({ ...p, [step.key]: text }))}
            autoFocus
            returnKeyType="next"
            onSubmitEditing={next}
          />
        ) : (
          step.options.map((option) => (
            <TouchableOpacity
              key={String(option.value)}
              style={[styles.option, isPicked(option) && styles.optionOn]}
              onPress={() => toggle(option)}
              accessibilityRole="button"
              accessibilityState={{ selected: isPicked(option) }}
            >
              <Text style={[styles.optionText, isPicked(option) && styles.optionTextOn]}>
                {option.label}
              </Text>
              {option.hint ? <Text style={styles.optionHint}>{option.hint}</Text> : null}
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.cta, !canContinue && styles.ctaOff]}
          onPress={next}
          disabled={!canContinue}
          accessibilityRole="button"
        >
          <Text style={[styles.ctaText, !canContinue && styles.ctaTextOff]}>Continue</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const wrap = { maxWidth: 560, width: '100%', alignSelf: 'center' } as const;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: theme.bg },
  header: {
    ...wrap, flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', paddingHorizontal: 24, paddingTop: 24,
  },
  brand: { fontSize: 13, fontWeight: '800', letterSpacing: 2, color: theme.fg },
  count: { fontSize: 13, fontWeight: '700', color: theme.muted },
  progress: { ...wrap, flexDirection: 'row', gap: 6, paddingHorizontal: 24, paddingTop: 14 },
  tick: { flex: 1, height: 5, borderRadius: 3, backgroundColor: theme.fill },
  tickOn: { backgroundColor: theme.accent },
  scroll: { ...wrap, padding: 24 },
  prompt: { fontSize: 30, fontWeight: '800', color: theme.fg, letterSpacing: -0.5, marginTop: 22 },
  hint: { fontSize: 14, color: theme.muted, marginTop: 8, lineHeight: 20 },
  input: {
    marginTop: 26, backgroundColor: theme.fill, borderRadius: theme.radius,
    paddingHorizontal: 18, paddingVertical: 18, fontSize: 18, color: theme.fg,
  },
  option: {
    marginTop: 12, backgroundColor: theme.fill, borderRadius: theme.radius,
    paddingHorizontal: 18, paddingVertical: 16, borderWidth: 2, borderColor: 'transparent',
  },
  optionOn: { borderColor: theme.accent, backgroundColor: theme.bg },
  optionText: { fontSize: 17, fontWeight: '600', color: theme.fg },
  optionTextOn: { color: theme.fg },
  optionHint: { fontSize: 13, color: theme.muted, marginTop: 3 },
  footer: { ...wrap, padding: 24, paddingTop: 8 },
  cta: {
    backgroundColor: theme.accent, borderRadius: theme.radius,
    paddingVertical: 17, alignItems: 'center',
  },
  ctaOff: { backgroundColor: theme.fill },
  ctaText: { color: theme.onAccent, fontSize: 16, fontWeight: '700' },
  ctaTextOff: { color: theme.muted },
});
