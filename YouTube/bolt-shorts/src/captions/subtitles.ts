import cues from "./narration-cues.json";

export type CaptionWord = { text: string; start: number; end: number; keyword: boolean };
export type CaptionChunk = { start: number; end: number; words: CaptionWord[]; lineId: string };

/**
 * Parse narration cues into word-timed caption chunks.
 * Words wrapped in *asterisks* (possibly spanning several words) are keywords.
 * Word timings are distributed inside each chunk by word length (syllable proxy).
 */
export const buildChunks = (): CaptionChunk[] => {
  const chunks: CaptionChunk[] = [];
  for (const line of cues.lines) {
    for (const c of line.chunks) {
      let inKw = false;
      const raw = c.text.split(/\s+/).filter(Boolean);
      const parsed = raw.map((w) => {
        let word = w;
        let kw = inKw;
        if (word.startsWith("*")) {
          inKw = true;
          kw = true;
          word = word.slice(1);
        }
        if (word.endsWith("*")) {
          inKw = false;
          word = word.slice(0, -1);
        }
        return { text: word, keyword: kw };
      });
      const weights = parsed.map((p) => p.text.replace(/[^A-Z0-9]/gi, "").length + 2);
      const total = weights.reduce((a, b) => a + b, 0);
      let acc = c.start;
      const dur = c.end - c.start;
      const words = parsed.map((p, i) => {
        const s = acc;
        acc += (weights[i] / total) * dur;
        return { ...p, start: s, end: acc };
      });
      chunks.push({ start: c.start, end: c.end, words, lineId: line.id });
    }
  }
  return chunks;
};

export const CHUNKS = buildChunks();

/** Caption chunk visible at time t (chunks linger up to 0.35s into short gaps). */
export const activeChunk = (t: number): CaptionChunk | null => {
  for (let i = 0; i < CHUNKS.length; i++) {
    const c = CHUNKS[i];
    const next = CHUNKS[i + 1];
    const linger = next ? Math.min(0.35, Math.max(0, next.start - c.end)) : 0.35;
    if (t >= c.start && t < c.end + linger) return c;
  }
  return null;
};

export const NARRATION_LINES = cues.lines;
