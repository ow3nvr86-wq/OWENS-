/**
 * Narration voice-over slot.
 *
 * No text-to-speech provider is configured for this project, so no narration
 * audio has been generated. To integrate a recorded or TTS voice-over:
 *   1. Record/generate the script in deliverables/narration_script.md against the
 *      cue times in src/captions/narration-cues.json (or as one 32s file).
 *   2. Save it as public/audio/narration/narration.wav (32.0s, starting at 0:00).
 *   3. Set NARRATION_FILE below to "audio/narration/narration.wav" and re-render.
 * When enabled, the music automatically ducks under each narration line.
 */
export const NARRATION_FILE: string | null = null;
