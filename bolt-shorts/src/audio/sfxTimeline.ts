import timeline from "../timeline.json";
const B = timeline.beats;

/**
 * Sound-effect cue sheet. Each file lives in public/audio/sound-effects/ and is
 * synthesised by scripts/build_audio.py (original, no third-party samples).
 * time: seconds, vol: linear gain.
 */
export type SfxCue = { time: number; file: string; vol: number };

export const SFX: SfxCue[] = [
  // Scene 1 — hook
  { time: B.hookImpact, file: "impact_big", vol: 0.9 },
  { time: 0.08, file: "whoosh_long", vol: 0.55 },
  { time: B.titleSlam, file: "slam", vol: 0.75 },
  { time: B.cashRegister, file: "cash_register", vol: 0.8 },
  { time: B.eyesWiden, file: "boing", vol: 0.6 },
  { time: B.countdownAppear, file: "board_drop", vol: 0.7 },
  { time: B.countdownAppear + 0.24, file: "beep_low", vol: 0.45 },
  { time: 2.3, file: "servo", vol: 0.4 },
  // Scene 2 — start
  { time: 2.98, file: "whoosh_short", vol: 0.6 },
  { time: B.floorOpen, file: "hatch_open", vol: 0.75 },
  { time: B.panStart, file: "whoosh_long", vol: 0.5 },
  { time: B.panEnd, file: "whoosh_short", vol: 0.6 },
  { time: B.beep3, file: "beep", vol: 0.6 },
  { time: B.beep2, file: "beep", vol: 0.6 },
  { time: B.beep1, file: "beep", vol: 0.6 },
  { time: B.go, file: "buzzer_go", vol: 0.75 },
  { time: B.go + 0.05, file: "spin_feet", vol: 0.5 },
  { time: B.launch, file: "launch_whoosh", vol: 0.75 },
  // running footsteps (cartoon tonks)
  ...Array.from({ length: 22 }).map((_, i) => ({ time: B.launch + 0.12 + i * (1 / 6), file: i % 2 ? "step_b" : "step_a", vol: 0.32 })).filter(
    (c) => !(c.time > B.jumpTakeoff - 0.05 && c.time < B.jumpLand + 0.1) && !(c.time > B.hammer1Duck - 0.1 && c.time < B.hammer1Duck + 0.15),
  ),
  // Scene 3 — obstacles
  { time: B.hammer1Duck - 0.32, file: "whoosh_hammer", vol: 0.7 },
  { time: B.hammer1Duck - 0.05, file: "squish", vol: 0.5 },
  { time: B.hammer1Duck + 0.5, file: "whoosh_hammer", vol: 0.45 },
  { time: B.jumpTakeoff, file: "jump", vol: 0.65 },
  { time: B.jumpLand, file: "land_thud", vol: 0.7 },
  { time: B.hammer2NearMiss - 0.3, file: "whoosh_hammer", vol: 0.8 },
  { time: B.hammer2NearMiss, file: "ping_antenna", vol: 0.65 },
  { time: B.hammer2NearMiss + 0.05, file: "yikes", vol: 0.45 },
  ...Array.from({ length: 8 }).map((_, i) => ({ time: 11.1 + i * (1 / 6), file: i % 2 ? "step_b" : "step_a", vol: 0.3 })),
  ...Array.from({ length: 9 }).map((_, i) => ({ time: 12.7 + i * (1 / 6), file: i % 2 ? "step_b" : "step_a", vol: 0.3 })),
  // Scene 4 — near disaster
  { time: B.slip - 0.05, file: "squeak_slip", vol: 0.75 },
  { time: B.slip + 0.05, file: "whoosh_slowmo", vol: 0.55 },
  { time: B.grab, file: "clang_grab", vol: 0.85 },
  { time: 16.0, file: "alarm", vol: 0.35 },
  { time: B.closeUpStart, file: "servo_panic", vol: 0.4 },
  { time: 18.15, file: "clank", vol: 0.55 },
  { time: B.pullUp + 0.05, file: "servo_strain", vol: 0.5 },
  { time: 19.75, file: "land_thud", vol: 0.5 },
  // Scene 5 — the win
  { time: B.onPlatform + 0.04, file: "jump", vol: 0.55 },
  { time: B.buttonSlam, file: "button_slam", vol: 0.95 },
  { time: B.buttonSlam + 0.04, file: "confetti_pop", vol: 0.8 },
  { time: B.buttonSlam + 0.1, file: "crowd_cheer", vol: 0.7 },
  { time: B.youWon, file: "slam", vol: 0.55 },
  { time: B.celebrateJump1, file: "boing", vol: 0.45 },
  { time: B.celebrateJump2, file: "jump", vol: 0.5 },
  { time: B.celebrateJump2 - 0.2, file: "confetti_pop", vol: 0.55 },
  // Scene 6 — donation
  { time: 25.0, file: "magic_chime", vol: 0.45 },
  { time: B.lookCommunity, file: "whoosh_short", vol: 0.45 },
  { time: B.lookBack, file: "whoosh_short", vol: 0.45 },
  { time: B.smile, file: "soft_chime", vol: 0.4 },
  { time: B.donatePress, file: "donate_chime", vol: 0.8 },
  { time: B.transferStart, file: "coins_stream", vol: 0.55 },
  { time: 28.8, file: "pop_boxes", vol: 0.5 },
  { time: 28.95, file: "crowd_happy", vol: 0.6 },
  { time: B.donatedText, file: "magic_chime", vol: 0.55 },
  { time: 29.95, file: "whoosh_short", vol: 0.4 },
  { time: B.realWinner, file: "soft_chime", vol: 0.5 },
];

export const SFX_FILES = Array.from(new Set(SFX.map((s) => s.file)));
